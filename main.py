from langchain_groq import ChatGroq
from langchain.agents import initialize_agent, Tool
from dotenv import load_dotenv
from tools import calculator, weather_api
import os

# Load environment variables
load_dotenv()

# Initialize LLM (Groq hosted model)
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.7
)

#  Tools
# def calculator(query):
#     try:
#         return str(eval(query))
#     except:
#         return "Invalid math expression"

tools = [
    Tool(
        name="Calculator",
        func=calculator,
        description="Useful for solving math problems"
    ),
    Tool(
        name="Weather",
        func=weather_api,
        description="Use this tool to get weather information for any city"
    )
]

# Create agent
agent = initialize_agent(
    tools,
    llm,
    agent="zero-shot-react-description",
    verbose=True
)

print("\nLangChain Agent Ready! Type exit to stop.")

#Console interface
while True:
    user_input = input("You: ")

    if user_input.lower() == "exit":
        print("Goodbye!")
        break

    # response = agent.run(user_input)
    # print("AI:", response)
    
    try:
        response = agent.invoke(user_input)
        print("AI:", response["output"])

    except Exception as e:
        print("Error:", e)











