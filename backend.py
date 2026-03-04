# ================================
# IMPORTS
# ================================
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated, List
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langgraph.store.postgres import PostgresStore
from langgraph.store.base import BaseStore
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from sentence_transformers import SentenceTransformer
import sqlite3
import psycopg
import os
import uuid

# ================================
# ENV + DB CONNECTION
# ================================
load_dotenv()

POSTGRES_URL = os.getenv("POSTGRES_URL")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

pg_conn = psycopg.connect(POSTGRES_URL)

# ================================
# EMBEDDING MODEL (FREE LOCAL)
# ================================
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def embed_text(text: str) -> list[float]:
    return embedding_model.encode(
        text,
        normalize_embeddings=True
    ).tolist()

# ================================
# SEMANTIC SEARCH HELPERS
# ================================
def insert_memory_vector(namespace: str, memory_key: str, content: str):
    vector = embed_text(content)

    with pg_conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO memory_vectors (id, namespace, memory_key, content, embedding)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (str(uuid.uuid4()), namespace, memory_key, content, vector)
        )
    pg_conn.commit()


def semantic_search_memories(
    namespace: str,
    query: str,
    k: int = 5,
    max_distance: float = 1.3
) -> list[str]:

    query_vector = embed_text(query)

    # Convert Python list -> pgvector format string
    vector_str = "[" + ",".join(map(str, query_vector)) + "]"

    with pg_conn.cursor() as cur:
        cur.execute(
            """
            SELECT content, (embedding <-> %s::vector) AS distance
            FROM memory_vectors
            WHERE namespace = %s
            ORDER BY distance
            LIMIT %s
            """,
            (vector_str, namespace, k)
        )

        rows = cur.fetchall()

    return [
        content for content, distance in rows
        if distance is not None and distance <= max_distance
    ]


# ================================
# LLM SETUP
# ================================
chat_llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0.7,
    api_key=GROQ_API_KEY
)

memory_llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0,
    api_key=GROQ_API_KEY
)

# ================================
# STRUCTURED MEMORY SCHEMAs
# ================================
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

class MemoryItem(BaseModel):
    text: str = Field(description="Atomic user memory")
    is_new: bool = Field(description="True if new, false if duplicate")

class MemoryDecision(BaseModel):
    should_write: bool
    memories: List[MemoryItem] = Field(default_factory=list)

memory_extractor = memory_llm.with_structured_output(MemoryDecision)

MEMORY_PROMPT = """You are responsible for updating and maintaining accurate user memory.

CURRENT USER DETAILS:
{user_details_content}

Extract stable long-term user information only.
Return short atomic sentences.
If nothing important, return should_write=false.
"""
print("remember node: ", MEMORY_PROMPT)
# ================================
# REMEMBER NODE
# ================================
def remember_node(state: ChatState, config: RunnableConfig, *, store: BaseStore):
    
    ns = ("global", "user", "details")
    namespace_str = "global_user_memories"

    last_text = state["messages"][-1].content

    relevant_memories = semantic_search_memories(namespace_str, last_text)
    existing_context = "\n".join(relevant_memories) if relevant_memories else "(empty)"

    decision: MemoryDecision = memory_extractor.invoke(
        [
            SystemMessage(content=MEMORY_PROMPT.format(
                user_details_content=existing_context
            )),
            {"role": "user", "content": last_text},
        ]
    )

    if not decision.should_write:
        return {}

    # Prevent duplicates globally
    existing_items = store.search(ns)
    existing_texts = {
        it.value.get("data", "").strip().lower()
        for it in existing_items
    }

    for mem in decision.memories:
        text = mem.text.strip()
        if not text or not mem.is_new:
            continue

        if text.lower() in existing_texts:
            continue

        memory_key = str(uuid.uuid4())
        # Save to global store and global vector DB
        store.put(ns, memory_key, {"data": text})
        insert_memory_vector(namespace_str, memory_key, text)

    return {}

# ================================
# CHAT NODE
# ================================
def chat_node(state: ChatState, config: RunnableConfig):
    # 🌍 Point to the global namespace instead of thread-based
    namespace_str = "global_user_memories"
    
    last_text = state["messages"][-1].content

    # This will now find memories created in ANY previous thread
    relevant_memories = semantic_search_memories(namespace_str, last_text)

    memory_block = "\n".join(relevant_memories[:5])
    
    system_prompt = f"""
You are a helpful AI assistant.
Below are retrieved long-term memories. Use them ONLY if relevant.

Long-term memories:
{memory_block if memory_block else "None"}
"""
    response = chat_llm.invoke(
        [SystemMessage(content=system_prompt), *state["messages"]]
    )

    return {"messages": [response]}
# ================================
# SQLITE CHECKPOINTER
# ================================
conn = sqlite3.connect("chatbot.db", check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)

# ================================
# POSTGRES BASESTORE
# ================================
store_cm = PostgresStore.from_conn_string(POSTGRES_URL)
store = store_cm.__enter__()
store.setup()

# ================================
# GRAPH BUILD
# ================================
graph = StateGraph(ChatState)

graph.add_node("remember", remember_node)
graph.add_node("chat_node", chat_node)

graph.add_edge(START, "remember")
graph.add_edge("remember", "chat_node")
graph.add_edge("chat_node", END)

chatbot = graph.compile(
    checkpointer=checkpointer,
    store=store
)



# **************************************** NEW SUMMARIZATION FUNCTIONS *************************

def get_first_user_message_content(thread_id: str) -> str | None:
    """Retrieves the content of the first HumanMessage for a thread."""
    try:
    
        state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
        messages = state.values.get('messages', [])
      
        for msg in messages:
            if isinstance(msg, HumanMessage) and msg.content:
                return msg.content.strip()
        return None
    except Exception:
        
        return None

def generate_summary_from_message(first_message_content: str) -> str:
    """Generates a short, conversational summary from the first user message using the LLM."""
    if not first_message_content:
        return 'Empty Chat'

    prompt = (
        "You are a helpful assistant. "
        "Summarize the following user message into a short (under 7 words), "
        "descriptive phrase suitable for a chat title. Do not include quotes or end punctuation."
        f"\n\nUser Message: {first_message_content}"
    )
    
    try:
        response = chat_llm.invoke(prompt)
        summary = response.content.strip().replace('.', '').replace('"', '')
        return summary if len(summary.split()) <= 7 and len(summary) > 3 else first_message_content[:30] + '...'
    except Exception:
        return 'Conversation Summary'

def get_conversation_summary(thread_id: str) -> str:
    """Gets the short summary for a thread, generating it if necessary."""
    first_message = get_first_user_message_content(thread_id)
    
    if first_message:
        return generate_summary_from_message(first_message)
    else:
        return f'New Chat {thread_id[:4]}'

# **************************************** ALTERED retrieve_all_threads *************************

def retrieve_all_threads() -> dict[str, str]:
    """Retrieves all thread IDs and their conversational summaries."""
    all_thread_ids = set()
    for checkpoint in checkpointer.list(None):
        all_thread_ids.add(checkpoint.config['configurable']['thread_id'])
    
    thread_summaries = {}
    for thread_id in all_thread_ids:
        thread_summaries[thread_id] = get_conversation_summary(thread_id)

    return thread_summaries