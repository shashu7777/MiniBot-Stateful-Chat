import streamlit as st
from backend import chatbot, retrieve_all_threads, get_conversation_summary
from langchain_core.messages import HumanMessage
import uuid
import collections

# ----------------- 1. CUSTOM CSS FOR STYLING (Final Look) -----------------
st.markdown("""
<style>
/* -------------------- GENERAL LAYOUT & SPACING -------------------- */
.stApp {
    background-color: #0d1117; 
    color: #c9d1d9;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

/* Sidebar Top Alignment Fix */
[data-testid="stSidebar"] {
    background-color: #161b22;
    border-right: 1px solid #30363d;
    padding-top: 10px;
}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div:first-child {
    padding-top: 0px !important;
}

/* Sidebar Header (My Conversations) */
[data-testid="stSidebar"] h2 {
    color: #58a6ff; 
    margin-top: 10px;
    font-size: 18px;
    font-weight: 600;
    border-bottom: 1px solid #30363d;
    padding-bottom: 5px;
}

/* -------------------- CHAT MESSAGE STYLING (User Border Removed) -------------------- */
[data-testid="stChatMessage"] {
    max-width: 700px; 
    width: fit-content;
    margin-top: 10px;
}
[data-testid="stChatMessage"]:has(> div > [data-testid="stMarkdownContainer"]:nth-child(2)) {
    margin-left: auto; /* User bubble to the right */
}
[data-testid="stChatMessage"] > div {
    padding: 10px 15px; 
    border-radius: 15px;
    /* Base border color for all messages, will be overridden for user */
    border: 1px solid #30363d; 
    word-break: break-word;
    max-width: 100%;
}

/* User Bubble Color (Right side) - BORDER REMOVAL IS HERE */
[data-testid="stChatMessage"]:has(> div > [data-testid="stMarkdownContainer"]:nth-child(2)) > div {
    background-color: #21262d; 
    border-radius: 15px 15px 0 15px;
    /* <<<< MAJOR CHANGE: Remove border for user message >>>> */
    border: none !important; 
}

/* Assistant Bubble Color (Left side) - BORDER KEPT */
[data-testid="stChatMessage"]:has(> div > [data-testid="stMarkdownContainer"]:nth-child(3)) > div {
    background-color: #161b22;
    border-radius: 15px 15px 15px 0;
    /* The border is inherited: border: 1px solid #30363d; */
}

/* -------------------- SIDEBAR BUTTON STYLING (Highlight Fix) -------------------- */

/* Style for all chat conversation buttons */
.stButton button {
    width: 100%;
    text-align: left;
    margin-top: 5px;
    padding: 10px 12px;
    border-radius: 6px;
    border: 1px solid #30363d; 
    background-color: #161b22;
    color: #c9d1d9;
    transition: background-color 0.2s, border 0.2s;
    line-height: 1.2;
}

/* Hover state */
.stButton button:hover {
    background-color: #21262d;
    color: #f0f6fc;
    border-color: #58a6ff;
}

/* New Chat Button (separate styling, ensure visibility) */
[data-testid="stSidebar"] [data-testid="stButton"][key="new_chat_btn"] button {
    background-color: #30363d;
    color: #58a6ff;
    border: 1px solid #58a6ff;
    font-weight: bold;
    margin-bottom: 15px;
}

/* <<<< MAJOR CHANGE: Active Conversation Highlight FIX >>>> */
/* This targets the button that follows the specific data-active="true" markdown marker */
[data-testid="stSidebar"] div[data-active="true"] + [data-testid="stButton"] button {
    background-color: #30363d !important;
    color: #58a6ff !important;
    font-weight: bold !important;
    border: 3px solid #58a6ff !important; /* Thick, distinct border */
    padding-left: 10px !important; 
}

</style>
""", unsafe_allow_html=True)


# **************************************** utility functions *************************

def generate_thread_id():
    thread_id = str(uuid.uuid4())
    return thread_id

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    st.session_state['message_history'] = []

def add_thread(thread_id, summary=None):
    if summary is not None:
        # Prepend the new conversation to the dictionary (latest first)
        new_dict = collections.OrderedDict([(thread_id, summary)])
        new_dict.update(st.session_state['chat_threads'])
        st.session_state['chat_threads'] = new_dict

def load_conversation(thread_id):
    state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
    return state.values.get('messages', [])

def switch_chat(thread_id):
    st.session_state['thread_id'] = thread_id
    messages = load_conversation(thread_id)

    temp_messages = []
    for msg in messages:
        role = 'user' if isinstance(msg, HumanMessage) else 'assistant'
        temp_messages.append({'role': role, 'content': msg.content})

    st.session_state['message_history'] = temp_messages
    st.rerun()


# **************************************** Session Setup ******************************

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    retrieved_threads = retrieve_all_threads()
    st.session_state['chat_threads'] = collections.OrderedDict(retrieved_threads)


# **************************************** Sidebar UI (Highlighting) *********************************

st.sidebar.title('LangGraph Chatbot')

if st.sidebar.button('➕ New Chat', help='Start a new conversation', key='new_chat_btn', type='primary'):
    reset_chat()
    st.rerun() 

st.sidebar.header('My Conversations')

current_thread_id = st.session_state['thread_id']

# Iterate over the OrderedDict items (latest conversation first)
for thread_id, summary in st.session_state['chat_threads'].items():
    
    is_active = (thread_id == current_thread_id)
    
    # 1. Inject the data-active attribute marker (st.markdown div)
    # The CSS uses the adjacent sibling selector (+) to style the button that FOLLOWS this div.
    if is_active:
         st.sidebar.markdown('<div data-active="true"></div>', unsafe_allow_html=True)
    else:
         st.sidebar.markdown('<div data-active="false"></div>', unsafe_allow_html=True)

    # 2. Render the actual st.button.
    # This button is styled by the CSS based on the marker above it.
    if st.sidebar.button(summary, key=f"sidebar_btn_{thread_id}"):
        
        if thread_id != current_thread_id:
            switch_chat(thread_id)


# **************************************** Main UI ************************************

for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

user_input = st.chat_input('Type here')

if user_input:

    is_first_turn = len(st.session_state['message_history']) == 0

    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.markdown(user_input)

    CONFIG = {
        "configurable": {"thread_id": st.session_state["thread_id"]},
        "metadata": {
            "thread_id": st.session_state["thread_id"]
        },
        "run_name": "chat_turn",
    }
    
    with st.chat_message('assistant'):

        ai_message = st.write_stream(
            message_chunk.content for message_chunk, metadata in chatbot.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config= CONFIG,
                stream_mode= 'messages'
            )
        )

    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})
    
    if is_first_turn:
        
        new_summary = get_conversation_summary(st.session_state['thread_id'])
        add_thread(st.session_state['thread_id'], summary=new_summary)
        st.rerun()