# OrchestAI: Agent Orchestration Framework with LangChain

## Project Overview

OrchestAI is an advanced multi-agent orchestration system built using the LangChain framework and the LLaMA model (via Groq). It features a sleek, glassmorphism web dashboard that visualizes the intelligent routing of user queries across multiple specialized AI agents.

The core goal of this project is to demonstrate a dynamic multi-agent pipeline where tasks are intelligently routed, researched using external tools, mathematically analyzed, and synthesized into a beautiful format for the user, fully equipped with conversational memory and document parsing capabilities.

## Key Features

- **Multi-Agent Pipeline**: 
  - 🚦 **Supervisor Router**: Intelligently decides if a query needs quick research or deep complex multi-step reasoning.
  - 🔎 **Research Agent**: Uses tools to gather facts, scrape the web, and evaluate math.
  - 🧠 **Analysis Agent**: Breaks down research data and extracts deep logical insights.
  - ✨ **Synthesis Agent**: Generates a strictly formatted, professional response for the user.
- **Advanced Tool Integrations**:
  - 🧮 **Math & Logic Solver**: Powered by the **SymPy** library to securely evaluate and solve complex algebra, calculus, and mathematical equations.
  - 🌤️ **Real-time Weather**: Uses the **OpenWeather API** to pull live climate and geographical conditions dynamically.
  - 🌐 **Web Search Toolkit**: Integrates the **DuckDuckGo Search API (`ddgs`)** to fetch real-time web snippet results for up-to-date knowledge facts.
  - 📏 **Unit Converter**: Engineered using native Python logic and Regex to dynamically convert various physical measurements (e.g., distance, temperature, weight).
  - 🕒 **Time Interface**: Uses Python's native `datetime` module to retrieve localized current time information, grounding the AI agent to the present.
- **Rich Dashboard UI**: A fully functional browser GUI built with Python and modern web frameworks, featuring a glassmorphism aesthetic, active workspace tracking, and a live trace visualization of the agent pipeline.
- **Document Knowledge Context**: Users can upload `.pdf`, `.docx`, `.xlsx`, `.csv`, and `.pptx` documents directly into the chat for agents to analyze.

---

## Technologies Used

- **AI & Orchestration**: Python, LLM frameworks, Large Language Models (LLM API Integrations), Vector Memory, Text Embeddings.
- **Web App**: Python Web Server, Vanilla JavaScript, CSS3 (Glassmorphism), Markdown rendering.
- **Core Integrations**: Live Weather API, Search Engine APIs.
- **Data Science / Math**: Advanced numerical and data manipulation libraries.
- **Document Parsers**: Comprehensive document extraction libraries.

---

## Project Architecture

Unlike a basic chatbot, OrchestAI runs a decision-based workflow:

1. **User Input** arrives through the Web App UI.
2. **Supervisor Router** classifies the query as `[RESEARCH]` (simple) or `[COMPLEX]`.
3. **Research Agent** executes the `Zero-Shot ReAct` chain, repeatedly invoking tools (Calculator, Weather, Web Search) until the raw data is gathered.
4. **Analysis & Synthesis Agents** (Only for Complex workflows) pass the raw data through sequential LLM chains to explain the *how* and *why* behind the answer.
5. The final output is streamed back to the frontend along with the tools used, intelligently triggering Markdown parsers in the browser to display structured text.

---

## Technical Deep-Dive

### 🧠 Intelligent Memory Management
Instead of just passing a simple chat history, OrchestAI utilizes a hybrid memory system:
- It maintains short-term conversational context natively so the agents remember the current topic during a single reasoning loop.
- It leverages vector-based semantic search to mathematically convert past interactions into searchable memories. This allows the system to recall distant, relevant facts without overloading the AI's internal context window.

### 📄 Multi-Format Document Parsing
The dashboard accepts drag-and-drop document uploads. The backend (`app.py`) parses text directly from the attachment and injects it as context into the LLM's prompt. Supported formats:
- **`.pdf`** (via PyPDF)
- **`.docx`** (via python-docx)
- **`.xlsx` / `.csv`** (via pandas)
- **`.pptx`** (via python-pptx)

### 🗄️ Workspace State Management
All chats are saved via **SQLite3**. The backend maintains isolated histories for multiple workspaces, dynamically generating names for new workspaces using an LLM summary, and sorting them gracefully in the sidebar.

---

## Installation and Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/repository-name.git
cd repository-name
```

### 2. Create a Virtual Environment
```bash
python -m venv venv
```
Activate environment:
- Windows: `venv\Scripts\activate`
- macOS/Linux: `source venv/bin/activate`

### 3. Install Dependencies
```bash
pip install -r requirements.txt
# If no requirements.txt exists yet, install the core packages:
pip install flask langchain langchain-groq requests python-dotenv duckduckgo-search sympy pypdf python-docx pandas python-pptx faiss-cpu sentence-transformers
```

### 4. Configure API Keys
Create a `.env` file in the project directory and insert your keys:
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

## Workspace Navigation (Examples)

Try these queries inside your OrchestAI dashboard to see the routing system in real-time:

### 🟢 `[RESEARCH]` Pipeline (Simple Queries)
*Designed to return exact answers quickly using specific tools.*
- *"weather in Pune"*
- *"who won the 2024 super bowl?"*
- *"convert 100 kg to g"*

### 🟣 `[COMPLEX]` Pipeline (Deep Reasoning)
*Triggers the entire 4-stage pipeline resulting in formatted, detailed responses.*
- *"calculate x^2 - 5x + 6 = 0 and explain the quadratic formula step by step"*
- *"what are the current trends in artificial intelligence, write a highly detailed summary"*
- *"draft a professional email to a recruiter explaining my expertise in python"*

---

## System Structure
```text
/
├── app.py              # Flask Web Server & Authentication
├── orchestration.py    # Master Workflow Logic and Data Cleaning
├── agents.py           # LLM Prompts and Agent Chain Definitions
├── tools.py            # Custom Agent Tools (SymPy, Weather, DDG)
├── memory.py           # FAISS Vector Memory implementation
├── database.db         # SQLite Chat History and User tracking
├── static/
│   ├── style.css       # Glassmorphism UI Styles
│   └── script.js       # Frontend Pipeline Animations & Markdown
└── templates/
    ├── index.html      # Main Dashboard View
    ├── login.html      # Authentication UI
    └── register.html   # Onboarding UI
```
