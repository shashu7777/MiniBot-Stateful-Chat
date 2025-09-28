from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
import sqlite3
import os

load_dotenv()

google_api_key=os.getenv('GOOGLE_API_KEY')

llm=ChatGoogleGenerativeAI(
    model='gemini-2.0-flash',
    temperature=0.7,
    google_api_key=google_api_key
)

# New LLM instance for summarization with a lower temperature for consistent output
# summary_llm = ChatGoogleGenerativeAI(
#     model='gemini-2.0-flash',
#     temperature=0.2, 
#     google_api_key=google_api_key
# )

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: ChatState):
    messages = state['messages']
    response = llm.invoke(messages)
    return {"messages": [response]}

conn = sqlite3.connect(database='chatbot.db', check_same_thread=False)
# Checkpointer
checkpointer = SqliteSaver(conn=conn)

graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

chatbot = graph.compile(checkpointer=checkpointer)

# **************************************** NEW SUMMARIZATION FUNCTIONS *************************

def get_first_user_message_content(thread_id: str) -> str | None:
    """Retrieves the content of the first HumanMessage for a thread."""
    try:
        # Load the thread state
        state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
        messages = state.values.get('messages', [])
        
        # Find the first HumanMessage content
        for msg in messages:
            if isinstance(msg, HumanMessage) and msg.content:
                return msg.content.strip()
        return None
    except Exception:
        # Handle cases where the thread_id might not exist in the checkpoint yet
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
        response = llm.invoke(prompt)
        summary = response.content.strip().replace('.', '').replace('"', '')
        # Simple length check fallback
        return summary if len(summary.split()) <= 7 and len(summary) > 3 else first_message_content[:30] + '...'
    except Exception:
        return 'Conversation Summary'

def get_conversation_summary(thread_id: str) -> str:
    """Gets the short summary for a thread, generating it if necessary."""
    first_message = get_first_user_message_content(thread_id)
    
    if first_message:
        return generate_summary_from_message(first_message)
    else:
        # Fallback for empty chats
        return f'New Chat {thread_id[:4]}'

# **************************************** ALTERED retrieve_all_threads *************************

# The existing retrieve_all_threads function is modified to return a dictionary 
# mapping thread_id to its summary string, which the frontend will use.
def retrieve_all_threads() -> dict[str, str]:
    """Retrieves all thread IDs and their conversational summaries."""
    all_thread_ids = set()
    for checkpoint in checkpointer.list(None):
        all_thread_ids.add(checkpoint.config['configurable']['thread_id'])
    
    # Generate summaries for all retrieved IDs
    thread_summaries = {}
    for thread_id in all_thread_ids:
        thread_summaries[thread_id] = get_conversation_summary(thread_id)
        
    # We return the dictionary of {thread_id: summary}
    return thread_summaries