# OrchestAI: Advanced Agent Orchestration Framework

## Project Overview

OrchestAI is a highly dynamic, advanced multi-agent orchestration system built using the LangChain framework and the LLaMA 3.1 model (via Groq). Rather than treating every query identically, it features a sophisticated multi-stage routing system ensuring optimal speed, domain-specific accuracy, and persistent memory.

The core goal of this project is to demonstrate a dynamic multi-agent pipeline where tasks are intelligently routed, researched using external tools, mathematically analyzed, and synthesized into a beautiful format for the user, fully equipped with conversational memory and analytics.

---

## 🌟 Unique Dashboard Features

1. **📌 Pin (Starred Messages):** A "Save for Later" button for the AI's best answers. It saves critical messages to a special permanent side-panel so they are always one click away, no matter how many new messages you send.
2. **⚡ Quick Prompt (Smart Routing):** The system instantly figures out what the user is asking and routes it to the right AI process without slowing down. It uses regex caching to completely bypass the heavy AI-router when handling obvious math or weather queries.
3. **📚 Full History & Document Uploads:** A full workspace environment that extracts text from PDFs, Excel sheets, and Word Docs. Every conversation is saved into unique filterable workspaces, completely searchable by date, keywords, or the pipeline used.
4. **📊 Analytics & Dashboard:** Built-in charts tracking AI performance. View metrics like Average Response Time, daily active chats, and pie charts showing the traffic distribution across different Agent Domains.
5. **🧠 Neural Core Memory:** Allows the AI to permanently remember details about you across entirely different chat sessions. You can set rules in your persistent memory database, and the AI will reference them before answering.

---

## 🏗️ Step-by-Step AI Orchestration Workflow

This is what happens under the hood when a user hits "Send" inside the OrchestAI interface:

**Step 1: The Gateway & Workspace**
When the AI Chat interface loads, the backend executes several tasks:
* Queries SQLite for available Workspaces, Pinned Messages, and Neural Core Memory variables.
* Parses any uploaded files (PDF, DOCX, CSV, PPTX) and covertly injects their text into the prompt.

**Step 2: The Fast-Lane (Keyword Pre-Routing)**
The system runs lightning-fast Regex checks. If a prompt triggers `[TOOL]` or `[CONTENT]` patterns logically, it immediately bypasses the secondary AI Router, saving seconds of load time.

**Step 3: The AI Router (Fallback Routing)**
If regex fails, the **Router Agent** analyzes the intent and assigns one of 4 main pipelines: `SIMPLE`, `TOOL`, `CONTENT`, or `COMPLEX`.

**Step 4: Pipeline Execution (The Engine)**
Depending on the assigned tag, an army of agents takes over:
*   `[SIMPLE]`: Disables all agents and queries the underlying LLM directly.
*   `[TOOL]`: Activates the **Research Agent**. It uses LangChain's ZERO_SHOT_REACT_DESCRIPTION to write math equations, query OpenWeather API, or scrape DuckDuckGo.
*   `[CONTENT]`: Triggers a debate loop. The **Content Agent** drafts text, the **Evaluator Agent** grades it, and if it fails, the **Optimizer Agent** rewrites it professionally.
*   `[COMPLEX]`: Triggers the **UseCase Router** categorizing the query into domains (*Medical, Shopping, Debug, Decision, General*). 
    * *Example:* A 3-part General question is split into 3 separate threads, researched in parallel, and merged.

**Step 5: Review & Save**
The **Summarizer Agent** cleans the chaotic research into beautiful Markdown. The **Confidence Agent** does a final check for accuracy. Finally, the raw input, text answer, tools used, and response time speeds are committed to the Langchain `shared_memory` and SQLite DB.

---

## 🧠 System Components Breakdown

### 🤖 The Language Model
*   **Model:** `llama-3.1-8b-instant` connected via `ChatGroq`.

### 🧰 Tools (5 Total)
Assigned to the Research Agent for physical execution:
1.  **Calculator:** Arithmetic and calculus via Python `sympy`.
2.  **Weather:** Real-time metrics via OpenWeatherMap.
3.  **Web Search:** Live duckduckgo search snippets.
4.  **Unit Converter:** Convert Km, °C, Kg using Python.
5.  **Time:** Live server clock and date.

### 🧩 Intelligence Agents (16 Total)
The framework consists of 16 specifically prompted Agents, including:
*   **Routing Agents:** Top-Level Router, UseCase Router.
*   **Execution Agent:** Research Agent.
*   **Domain Experts:** Medical, Decision, Debug, Shopping, General, Analysis Agents.
*   **Content Generators:** Content Agent, Email Agent, Summarizer Agent.
*   **Quality Control Evaluators:** Confidence Agent, Refinement Agent, Evaluator Agent, Optimizer Agent.

---

## 💻 Installation and Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/repository-name.git
cd repository-name
```

### 2. Create a Virtual Environment
```bash
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
*(Packages include: flask, langchain, langchain-groq, duckduckgo-search, sympy, pypdf, python-docx, pandas, python-pptx, werkzeug)*

### 4. Configure API Keys
Create a `.env` file in the project directory:
```ini
GROQ_API_KEY=your_groq_key
WEATHER_API_KEY=your_openweather_key
```

### 5. Run the Application
```bash
python app.py
```
*The app will be available on `http://127.0.0.1:5000`*

---

## 🔥 Query Testing Examples

Try these directly in the dashboard to watch the orchestrator switch pipelines:

*   **⚡ Simple Pipeline:** `"Who discovered penicillin?"`
*   **🛠️ Tool Pipeline:** `"Calculate 45 * 18.5 - (300 / 4)"` or `"What is the current weather in Tokyo?"`
*   **✍️ Content Pipeline:** `"Draft a professional email to my client, Sarah, apologizing for the project delay."`
*   **🧠 Complex (Medical):** `"What are the common symptoms of a migraine, and what are some over-the-counter treatments?"`
*   **🧠 Complex (Debug):** `"Debug this error: Exception: IndexError: list index out of range at line 45."`
*   **🧠 Complex (Multi-part General):** `"Explain how electric motors work, why they are more efficient than gas engines, and who the leading manufacturers are right now."`

---

## 📁 System Structure
```text
/
├── app.py              # Flask Server, Auth, Workspaces & DB Logic
├── orchestration.py    # Master Workflow Logic, Domain Splitting, Regex Pre-Routing
├── agents.py           # 16 LLM Agent Prompt Templates & Initialization
├── tools.py            # 5 Custom Agent Tools (SymPy, Weather, DDG)
├── memory.py           # LangChain Shared Memory Logic
├── database.db         # SQLite User, Chat History, Memory tracking
├── static/
│   ├── style.css       # Dashboards, Glassmorphism, Layouts
│   └── script.js       # Frontend UI handling, badging, timers, markdown rendering
└── templates/
    ├── index.html      # Main Chat Dashboard View
    ├── analytics.html  # Live Charts and Distribution Graphics
    ├── history.html    # Filterable Conversation Table Logs
    ├── login.html      # Authentication UI
    └── register.html   # Onboarding UI
```
