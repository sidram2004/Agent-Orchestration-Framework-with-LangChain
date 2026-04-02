
from agents import create_agents
from memory import create_shared_memory

research, analysis, summarizer = create_agents()
shared_memory = create_shared_memory()

print("\nMulti-Agent System Ready")
print("Type 'exit' to stop\n")

while True:

    user_input = input("You: ")

    if user_input.lower() == "exit":
        print("System stopped")
        break

    try:
        # 🔹 Load memory properly
        memory_data = shared_memory.load_memory_variables({"input": user_input})
        history = memory_data.get("history", "")

        # 🔹 Combine memory + input
        combined_input = f"""
Previous Context:
{history}

User Query:
{user_input}
"""

        #  Research Agent
        research_result = research.invoke({"input": combined_input})
        research_output = research_result["output"]

        #  Analysis Agent
        analysis_result = analysis.invoke({"input": research_output})
        analysis_output = analysis_result["text"]

        #  Summarizer Agent
        final_result = summarizer.invoke({"input": analysis_output})
        final_output = final_result["text"]

        #  Store useful memory
        shared_memory.save_context(
            {"input": user_input},
            {"output": research_output}
        )

        # Final clean output
        print("\nAI:", final_output)

    except Exception as e:
        print("Error:", str(e))










