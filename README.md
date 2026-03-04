## 🤖 MiniBot: Stateful Conversational AI with LangGraph

This project is a mini-chatbot built to **explore and implement core concepts** essential for modern, production-ready conversational AI: **State Persistence** and **Real-time Streaming**.

### ✨ Core Features

* **Stateful Conversation:** The bot remembers the entire history of your chat sessions, even after you close and reopen the app, thanks to **Checkpointing**.
* **Real-Time Streaming:** The AI's response is streamed word-by-word for an instant, responsive user experience.
* **Structured AI Flow:** Uses **LangGraph** to define a clear, cyclical, and debuggable state machine for the conversation logic.

***

### 🧠 Core Concepts Explored

#### 1. State Persistence with LangGraph Checkpointing
To ensure the bot could pick up exactly where it left off, I utilized LangGraph's built-in **Checkpointing** feature. This moves beyond simple in-memory history.

* **Implementation:** LangGraph was configured to use a **`SqliteSaver`**, which automatically handles saving and loading the entire conversation state (stored as a list of `BaseMessage` objects) to a local database (`chatbot.db`).

#### 2. Enhanced UX with Streaming
To address the latency common in LLM applications, streaming was implemented from the model to the UI.

* **Implementation:** The Gemini LLM is called with a streaming endpoint, and the output is immediately consumed by the Streamlit chat element, displaying the text in real-time for an interactive feel.

***

## 🚀 Upgrade: Long-Term Memory

MiniBot has now been upgraded with a **Long-Term Memory system**, enabling the chatbot to remember important user information across different conversation threads.

Unlike basic chatbots that only remember messages within a single conversation, this upgrade allows the system to **store and reuse important user facts permanently**, making responses more **personalized and context-aware**.

### 🧠 What Long-Term Memory Means

Long-term memory allows the bot to store key user information and reuse it in future conversations.

Example:

User says in one thread:

> "I am a software engineer by profession."

This information is stored as **important memory**.

Later, in a completely different thread, if the user asks:

> "Suggest some ways I can improve my career."

The chatbot retrieves the stored memory and generates advice specifically tailored for **software engineers**.

This enables **true cross-thread personalization**.

---

### 🧩 The Challenge

Large Language Models are **stateless by default**.

Even though MiniBot supports **multiple chat threads**, the model itself does not remember previous conversations when switching threads.

To solve this, I built a **Long-Term Memory Layer**.

---

### 🛠 How It Works

#### Memory Extraction

A dedicated **Memory LLM** checks whether a user message contains important long-term information.

Model used:

`gpt-oss-20b` via **Groq**

If the message contains useful information about the user, it gets extracted and prepared for storage.

---

#### Memory Embeddings

The extracted memory is converted into **semantic embeddings** using:

`all-MiniLM-L6-v2` from **Hugging Face**

This allows efficient semantic similarity search.

---

#### Memory Storage

The embeddings are stored in **PostgreSQL** using **pgvector**, enabling fast vector similarity search.

---

#### Memory Retrieval

Instead of passing **all stored memories** (or blindly sending top-k memories), the system performs **semantic search based on the current user query**.

Only the **most relevant memories** are retrieved and passed to the chat model.

This helps:

✔ Reduce token usage  
✔ Avoid context window overflow  
✔ Improve relevance  
✔ Make responses more personalized  

---

### ⚙️ Models Used

| Purpose | Model |
|------|------|
| Chat Generation | GPT-OSS-20B (Groq) |
| Memory Extraction | GPT-OSS-20B (Groq) |
| Embeddings | all-MiniLM-L6-v2 (HuggingFace) |

---

### 🧠 Memory Architecture

MiniBot now uses **two levels of memory**:

| Memory Type | Description |
|-------------|-------------|
| **Short-Term Memory** | Conversation history stored using LangGraph checkpointing with SQLite |
| **Long-Term Memory** | Important user information stored using embeddings in PostgreSQL + pgvector |

This architecture allows the system to maintain **context within conversations** and **personalization across conversations**.

---

### ⚙️ Technology Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **LLM** | **Gemini 2.5 Flash** | Fast, efficient, and powerful model for generating responses. |
| **Logic/Flow** | **LangChain & LangGraph** | Orchestrates the conversational state machine and AI calls. |
| **State Management** | **SQLite** | Local database used for persisting the conversation thread history. |
| **User Interface** | **Streamlit** | Handles the web interface, including real-time streaming display. |

***


#### 🎬 Full Demo Video (Persistence & Streaming)

![Demo](mini_bot.gif)

### 💻 Local Setup and Installation

Follow these steps to get a copy of the project running locally.

#### Prerequisites

1.  **Python 3.9+**
2.  A **Gemini API Key**.

#### Steps

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/shashu7777/MiniBot-Stateful-Chat.git
    cd MiniBot-Stateful-Chat
    ```

2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate  # On Windows
    # source venv/bin/activate # On Linux/macOS
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Up Environment Variables:**
    Create a file named **`.env`** in the root directory and add your API key:
    ```
    GEMINI_API_KEY="YOUR_API_KEY_HERE"
    ```

5.  **Run the Streamlit App:**
    ```bash
    streamlit run app.py
    ```
    The application will open in your web browser.

***

### 🤝 Acknowledgments

* [LangGraph Tutorials by CampusX Official](https://github.com/campusx-official/langgraph-tutorials)

***

### 🏷️ Tags

`#LangChain #LangGraph #GeminiAPI #GenAI #Chatbot #Persistence #Streaming #Streamlit #LLMDev`
