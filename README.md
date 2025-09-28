## 🤖 MiniBot: Stateful Conversational AI with LangGraph

This project is a mini-chatbot built to **explore and implement core concepts** essential for modern, production-ready conversational AI: **State Persistence** and **Real-time Streaming**.

### ✨ Core Features

* **Stateful Conversation:** The bot remembers the entire history of your chat sessions, even after you close and reopen the app, thanks to **Checkpointing**.
* **Real-Time Streaming:** The AI's response is streamed word-by-word for an instant, responsive user experience.
* **Structured AI Flow:** Uses **LangGraph** to define a clear, cyclical, and debuggable state machine for the conversation logic.

***

### ⚙️ Technology Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **LLM** | **Gemini 2.5 Flash** | Fast, efficient, and powerful model for generating responses. |
| **Logic/Flow** | **LangChain & LangGraph** | Orchestrates the conversational state machine and AI calls. |
| **State Management** | **SQLite** | Local database used for persisting the conversation thread history. |
| **User Interface** | **Streamlit** | Handles the web interface, including real-time streaming display. |

***

### 🧠 Core Concepts Explored

#### 1. State Persistence with LangGraph Checkpointing
To ensure the bot could pick up exactly where it left off, I utilized LangGraph's built-in **Checkpointing** feature. This moves beyond simple in-memory history.

* **Implementation:** LangGraph was configured to use a **`SqliteSaver`**, which automatically handles saving and loading the entire conversation state (stored as a list of `BaseMessage` objects) to a local database (`chat_history.db`).

#### 2. Enhanced UX with Streaming
To address the latency common in LLM applications, streaming was implemented from the model to the UI.

* **Implementation:** The Gemini LLM is called with a streaming endpoint, and the output is immediately consumed by the Streamlit chat element, displaying the text in real-time for an interactive feel.

***
#### 🎬 Full Demo Video (Persistence & Streaming)

<p align="center">
  <video src="mini_bot.mp4" controls width="600"></video>
</p>

### 💻 Local Setup and Installation

Follow these steps to get a copy of the project running locally.

#### Prerequisites

1.  **Python 3.9+**
2.  A **Gemini API Key**.

#### Steps

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/shashu7777/MiniBot-Stateful-Chat.git
    cd YOUR_REPOSITORY_NAME
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
