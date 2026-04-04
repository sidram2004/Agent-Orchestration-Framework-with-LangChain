import time
from agents import create_agents
from memory import create_shared_memory

# Unpack the 5 agents
research, analysis, summarizer, email_agent, router_agent = create_agents()
shared_memory = create_shared_memory()

def run_workflow(user_input):

    memory_data = shared_memory.load_memory_variables({"input": user_input})
    history = memory_data.get("history", "")

    combined_input = f"""
Previous Context:
{history}

User Query:
{user_input}
"""
    
    try:
        # STEP 1: Supervisor Routing Decision
        routing_decision = router_agent.invoke({"input": user_input})["text"].strip()

        # STEP 2: Research Agent always runs first to get data
        research_result = research.invoke({"input": combined_input})
        print("🔍 Agent Output:", research_result)
        research_output = research_result.get("output") or research_result.get("text", "")
        tools_used = []
        if "intermediate_steps" in research_result:
            for action, observation in research_result["intermediate_steps"]:
                tool_dict = {}
                if hasattr(action, 'tool'):
                    tool_dict = {
                        "tool": action.tool,
                        "tool_input": action.tool_input,
                        "log": action.log,
                        "observation": str(observation)
                    }
                elif isinstance(action, dict) and "tool" in action:
                    tool_dict = {
                        "tool": action["tool"],
                        "tool_input": action.get("tool_input", ""),
                        "log": action.get("log", ""),
                        "observation": str(observation)
                    }
                if tool_dict:
                    tools_used.append(tool_dict)

        # STEP 3: SMART ROUTING based on LLM decision
        if "[SIMPLE]" in routing_decision:
            final_output = research_output
            email_output = ""
        else:
            try:
                # 📊 Analysis
                analysis_output = analysis.invoke({"input": research_output})["text"]
                # 🧾 Summary
                final_output = summarizer.invoke({"input": analysis_output})["text"]
            except Exception as analysis_err:
                print(f"Analysis/Summary skipped due to rate limit: {analysis_err}")
                final_output = research_output  # fallback to research output
            email_output = ""  # skip email to save tokens

        # 💾 STEP 5: Save correct output
        shared_memory.save_context(
            {"input": user_input},
            {"output": final_output}
        )

        # 🔥 FINAL RESPONSE
        return {
            "answer": final_output,
            "email": email_output,
            "routing": routing_decision,
            "tools_used": tools_used
        }

    except Exception as e:
        error_msg = str(e)
        print(f"Workflow Error: {error_msg}")
        # If rate limited, wait 3 seconds before responding
        if "tokens_exceeded" in error_msg or "rate_limit" in error_msg.lower():
            print("Rate limit hit — waiting 3 seconds...")
            time.sleep(3)
            return {
                "answer": "⚠️ Rate limit reached. Please wait a few seconds and try again.",
                "email": "",
                "routing": "RATE_LIMITED",
                "tools_used": []
            }
        return {
            "answer": f"❌ Error: {error_msg[:200]}",
            "email": "",
            "routing": "ERROR",
            "tools_used": []
        }


    # shared_memory.save_context(
    #     {"input": user_input},
    #     {"output": research_output}
    # )

    # return final_output