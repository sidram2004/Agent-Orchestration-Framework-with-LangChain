---
title: Agent Orchestration Framework with LangChain
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
license: mit
---

# 🤖 Agent Orchestration Framework with LangChain

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![LangChain](https://img.shields.io/badge/🦜🔗-LangChain-black)](https://python.langchain.com/)

**Created by Sidram Patil**

---

## 📌 1. What is the Agent Orchestration Framework? (The Basics)

At its core, the **Agent Orchestration Framework** is a highly dynamic, advanced multi-agent orchestration system. It is built using Python, the LangChain framework, and the lightning-fast LLaMA 3.1 model (powered by Groq).

Most standard AI chatbots have a major flaw: they suffer from "amnesia" (forgetting who you are), they cannot search the live internet, they cannot do complex math, and they treat every single question the exact same way. 

This framework solves this by transforming a simple chat interface into a **scalable AI platform capable of real-world problem-solving**. Instead of one AI trying to do everything, this system acts as a manager that routes your question to a team of **16 specialized AI agents** equipped with real-world tools.

---

## 🚀 2. Core Features (From Basic to Advanced)

### 📄 Multi-modal Document RAG System
If you upload a file (PDF, Word, Excel, CSV, PowerPoint, or Text), the backend instantly intercepts it. Using specialized Python libraries (`pypdf`, `python-docx`, `pandas`, `python-pptx`), the system physically extracts the text and securely injects it into the AI’s prompt. This allows you to chat directly with your documents and data instantly.

### 🧠 Persistent Neural Core Memory (Vector DB RAG)
Traditional bots forget facts when you start a new chat. This system uses a **FAISS Vector Database** to create permanent, long-term memory. If you tell the AI "I am a Python Developer," it stores this fact as a vector embedding. In every future chat session you ever create, the system searches this database and personalizes its answers based on your unique profile.

### 🛠️ Live External Tools
The AI is not limited to its training data. The **Research Agent** operates on a ReAct (Reason + Act) framework and autonomously decides when to use its arsenal of 5 custom Python tools:
1.  🌐 **Web Search (DuckDuckGo):** Uses the `duckduckgo-search` library to scrape the live internet for news, real-time facts, and current events. It fetches and reads the top 8 search results instantly.
2.  🧮 **Advanced Calculator (SymPy):** Goes far beyond simple arithmetic. Uses Python's `SymPy` library to solve complex algebra, quadratic equations, and even calculus integrals safely.
3.  🌦️ **Weather API (OpenWeatherMap):** Uses the OpenWeatherMap API to fetch real-time global weather data, returning precise temperatures, humidity, wind speeds, and current conditions for any city.
4.  ⏳ **Global Time Zone Tracker:** Uses API timezone offsets to accurately fetch the exact current local time, date, and UTC offset for any city or country in the world.
5.  📏 **Unit Converter:** A custom Regex-based tool that instantly converts physical units (Kilometers ↔ Meters, Celsius ↔ Fahrenheit, Kilograms ↔ Grams).

### 📌 Dashboard & Workspace Management
*   **Workspaces:** Every chat is saved as an isolated workspace in a SQLite database.
*   **Search History:** A dedicated page allows you to search through all past conversations instantly using AJAX.
*   **Pin Messages:** Save the AI's most important answers to a permanent side panel so you never lose critical code or information.
*   **Analytics:** An admin dashboard tracking system performance, average response times, and an exact breakdown of which AI agents are being used the most.

---

## 🧠 3. Deep Dive: The Orchestration Architecture (Advanced)

If you look under the hood, here is exactly how the framework processes a message:

### 🤖 The 16 Specialized Agents
Instead of relying on one generic LLM prompt, the system delegates tasks to a massive roster of 16 highly specialized AI agents:
*   **Routing Agents (2):** `Router Agent` (Top-level pipeline supervisor) & `UseCase Router` (Domain-specific supervisor).
*   **Research & Analysis (3):** `Research Agent` (Autonomous tool execution), `Analysis Agent` (Deep logical reasoning), & `General Agent` (Data synthesis).
*   **Domain Experts (4):** `Medical Agent` (Health data), `Debug Agent` (Code fixing), `Shopping Agent` (Product comparison), & `Decision Agent` (Pros/cons analysis).
*   **Content Creators (2):** `Content Agent` (Essays, creative writing) & `Email Agent` (Professional formatting).
*   **Quality Assurance & Output (5):** `Evaluator Agent` & `Optimizer Agent` (Content drafting loop), `Confidence Agent` & `Refinement Agent` (Final accuracy verification), and the `Summarizer Agent` (Markdown formatting).

### Step 1: Lightning-Fast Pre-Routing
Before wasting money or time asking the LLM what to do, the system runs a fast Regex check. If it sees a pattern like "What's the weather", it instantly bypasses heavy processing and equips the Weather tool. This preserves extreme speed.

### Step 2: The AI Router Agent
If the regex can't figure it out, the prompt goes to the **Router Agent**. The Router classifies the query into one of **Four Execution Pipelines**:

1.  ⚡ **[SIMPLE] Pipeline:** Bypasses all agents and hits the LLM directly. Used for basic facts and "hellos" for maximum speed.
2.  🧰 **[TOOL] Pipeline:** Triggers the **Research Agent** (using a ReAct framework). The agent autonomously decides whether it needs to use the Calculator, Web Search, or Weather API to find the answer.
3.  ✍️ **[CONTENT] Pipeline:** Enters a cyclical Quality Assurance (QA) loop. The **Content Agent** drafts an email/essay. It passes the draft to the **Evaluator Agent**, who grades it. If it fails, the **Optimizer Agent** rewrites it until it is perfectly professional.
4.  🏥 **[COMPLEX] Pipeline:** Hits a second router called the **UseCase Router**. It categorizes the prompt into domains:
    *   *Medical Agent:* Formats health data and forces doctor disclaimers.
    *   *Debug/Shopping/Decision Agents:* Searches the web to compare products, map out pros/cons, or fix code bugs.

### Step 3: Output Generation
Before you see the text on your screen, the **Summarizer Agent** takes the chaotic research data and formats it beautifully in Markdown. Finally, a **Confidence Agent** does a last check to ensure the answer is highly accurate.

---

## 🛠️ 4. Tech Stack

*   **Backend:** Python, Flask, Gunicorn
*   **AI Engine:** LangChain, Groq API (`llama-3.1-8b-instant`)
*   **Memory & Databases:** SQLite (Users, Chats, Analytics), FAISS (Vector DB for RAG memory)
*   **Frontend UI:** HTML5, Vanilla CSS, JavaScript (AJAX)
*   **Document Parsers:** `pypdf`, `python-docx`, `pandas`, `openpyxl`, `python-pptx`

---

## 💻 5. Local Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/Agent-Orchestration-Framework-with-LangChain.git
   cd Agent-Orchestration-Framework-with-LangChain
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Environment Variables:**
   Create a `.env` file in the root directory and add your API keys:
   ```env
   GROQ_API_KEY=your_groq_api_key
   OPENWEATHER_API_KEY=your_openweather_api_key
   ```

5. **Run the Application:**
   ```bash
   python app.py
   ```
   Open your browser and navigate to `http://127.0.0.1:5000`

---

## ☁️ 6. Deployment (Docker & Hugging Face Spaces)

This project is fully containerized and optimized for deployment on **Hugging Face Spaces**.

A `Dockerfile` is included that:
*   Exposes the app on Port `7860` via Gunicorn.
*   Modifies folder permissions (`chmod 777`) so the FAISS Vector Database and SQLite database remain persistent and writeable by the cloud's non-root user.

**To Deploy for free:**
1. Create a new "Docker Space" on Hugging Face.
2. Select "MIT License" from the dropdown.
3. Upload all project files directly to the Space.
4. The Space will automatically build the Docker image and host your Agent Orchestration platform securely.

---

## 🔮 7. Future Scope

While the current version uses standard LangChain agent chains, future iterations plan to:
*   Integrate **LangGraph** for highly complex, stateful, cyclical graph-based execution.
*   Implement Semantic Chunking for even more advanced Document RAG retrieval.
*   Deploy on scalable cloud infrastructure with parallel async agent execution.

---

## 📄 8. License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
