# Agent Orchestration Framework with LangChain 

## Project Overview
Agent Orchestration Framework with LangChain is an AI agent system built using the LangChain framework and the LLaMA model.
The goal of this project is to demonstrate how an intelligent agent can understand user queries, decide the correct action, and use external tools or APIs to produce accurate responses.

The system connects a **LangChain agent with an LLM (LLaMA via Groq API)** and extends its functionality by integrating tools such as a **calculator and weather service**.

Instead of only generating text responses, the agent can **perform tasks using tools**, making the system more practical and interactive.


# Technologies Used

### Python

Python is used as the main programming language for developing the agent system.

### LangChain

LangChain is the framework used to build AI agents and manage interactions between the language model and external tools.

### LLaMA (via Groq API)

The project uses the **LLaMA language model** hosted on Groq servers.
The model processes user queries and helps the agent decide whether to respond directly or use a tool.

### OpenWeather API

Used to retrieve weather information for any city.

### Requests Library

Used for sending HTTP requests to external APIs.

### Virtual Environment (venv)

A virtual environment is used to manage project dependencies and avoid conflicts with other Python packages.

### dotenv

Used to securely store API keys in an environment file.

# Project Architecture

The system works as an intelligent agent pipeline:

User Input
↓
Console Interface
↓
LangChain Agent (Zero-Shot Agent)
↓
LLaMA Model (Groq API)
↓
Agent decides action
↓
Tool Invocation (Calculator / Weather API)
↓
Response returned to user

The agent uses reasoning to determine whether a tool is needed to answer the user query.

# Milestone 1 – Basic Agent Setup

## Objective

The first milestone focused on creating a basic LangChain agent and setting up the development environment.

## Tasks Completed

• Created a Python virtual environment
• Installed LangChain and required dependencies
• Connected the system to the LLaMA model using Groq API
• Built a **zero-shot LangChain agent**
• Implemented a console interface for interaction
• Added a simple calculator tool

## Features Implemented

The agent can:

• Understand user prompts
• Perform mathematical calculations
• Generate responses using the LLaMA model
• Interact with users through a console interface

Example interaction:

User: 25*4
AI: The result is 100

The calculator functionality works like a basic calculator application where users can perform arithmetic operations.

# Milestone 2 – Tool Integration & API Calling

## Objective

Extend the agent's capabilities by integrating external tools and APIs.

The goal was to allow the agent to perform real tasks beyond text generation.

## Tasks Completed

• Studied LangChain **Tool abstraction**
• Implemented two tools
• Integrated tools into the agent context
• Designed prompts to guide tool usage
• Tested tool invocation and response handling
• Added error handling for API failures

# Implemented Tools

## Calculator Tool

The calculator tool allows the agent to solve mathematical expressions.

Example queries:

45*6
120/4
78+34

Example output:

The result is 270

Purpose:
This tool allows the agent to execute calculations instead of relying only on the language model.

## Weather API Tool

The weather tool retrieves weather information for any city using the OpenWeather API.

Example query:

weather in Pune

Example output:

Weather Report for Pune
Temperature: 28°C
Condition: Clear sky
Humidity: 40%
Wind Speed: 3 m/s

Purpose:
Demonstrates how AI agents can interact with real external APIs.

# Tool Integration with LangChain Agent

LangChain tools were defined using the `Tool` class.

Each tool contains:

• Name
• Function
• Description explaining when the tool should be used

The agent reads the description and decides whether the tool should be invoked.

Example:

User Query → Tool Used

45*6 → Calculator Tool
weather in Mumbai → Weather Tool

# Error Handling

The project includes error handling mechanisms to ensure stable execution.

Handled situations include:

• Invalid mathematical expressions
• Unknown city names
• Weather API request failures
• Network issues

If an error occurs, the agent returns a safe message instead of crashing.

Example:
Invalid mathematical expression
or
Weather service unavailable

# Console Interface

The system currently runs through a **console interface**, allowing users to interact with the agent in real time.

Example interaction:

You: 45*6
AI: The result is 270
You: weather in Delhi
AI: Temperature: 30°C, Clear sky

Users can continue interacting until they type: exit

# Installation and Setup

## Clone the Repository

git clone https://github.com/your-username/repository-name.git

cd repository-name

## Create Virtual Environment

python -m venv venv

Activate environment

Windows:
venv\Scripts\activate

## Install Dependencies

pip install langchain
pip install langchain-groq
pip install requests
pip install python-dotenv

## Add API Keys

Create a `.env` file in the project root.

Example:

GROQ_API_KEY=your_groq_key
WEATHER_API_KEY=your_openweather_key

## Run the Project

python main.py

# Example Queries

Try these commands:

45*6
120/4
weather in Pune
weather in London

Type **exit** to stop the program.

# Project Structure

project-folder
│
├── main.py
├── tools.py
├── .env
├── .gitignore
└── venv

# Current Achievements

✔ Working LangChain zero-shot agent
✔ Integration with LLaMA language model
✔ Calculator tool implementation
✔ Weather API integration
✔ Automatic tool selection by the agent
✔ Console-based interaction system
✔ Error handling for reliable execution

# Future Work

The next stages of the project will focus on building a **complete Agent Orchestration Framework**, including:

• Multiple collaborating agents
• Task planning and workflow management
• Conversation memory
• Advanced reasoning and automation

These improvements will transform the system into a **fully orchestrated AI agent platform** capable of handling complex tasks.

# Project Title
**Agent Orchestration Framework with LangChain **
