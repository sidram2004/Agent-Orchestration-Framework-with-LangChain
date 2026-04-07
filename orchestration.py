import time
from agents import create_agents
from memory import create_shared_memory


# Unpack the 6 agents
research, analysis, summarizer, email_agent, router_agent, llm = create_agents()
shared_memory = create_shared_memory()





# 🔥 CLEAN OUTPUT FUNCTION
def clean_output(text):
    if not text:
        return ""

    # 1. Prioritize extracting content after "Final Answer:"
    if "Final Answer:" in text:
        return text.split("Final Answer:")[-1].strip()

    # 2. If no "Final Answer:", remove common reasoning keywords
    clean_lines = []
    for line in text.splitlines():
        if any(word in line for word in ["Thought:", "Action:", "Observation:", "Action Input:"]):
            continue
        clean_lines.append(line)

    cleaned = "\n".join(clean_lines).strip()
    
    # 3. FIX: If the cleaning accidentally deletes everything, 
    # return the original text so the dashboard is never empty!
    if not cleaned and text.strip():
        return text.strip()

    return cleaned

def suggest_chat_name(user_input):
    """Asks the LLM to provide a short, descriptive 3-4 word name for the chat."""
    try:
        name_prompt = f"Analyze this query and suggest a short, professional name for a chat workspace (max 4 words). Query: '{user_input}'. Respond ONLY with the name, no quotes, no extra text."
        response = llm.invoke(name_prompt)
        name = response.content.strip().strip('"').strip("'")
        if len(name.split()) > 6: return None
        return name
    except Exception as e:
        print(f"Naming Error: {e}")
        return None



def run_workflow(user_input, is_new_chat=False):
   
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
        routing_decision = router_agent.invoke({"input": user_input})["text"].strip().upper()

        tools_used = []
        email_output = ""
        
        # STEP 2: Research Agent runs first to get data
        research_result = research.invoke({"input": combined_input})
    
        research_output = research_result.get("output") or research_result.get("text", "")
        research_output = clean_output(research_output)   # ✅ CLEAN HERE
        
         # 🔥 TOOL TRACKING
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
        if "[RESEARCH]" in routing_decision:
            final_output =  research_output
        else:
            try:
                # 📊 Analysis
                analysis_output = analysis.invoke({"input": research_output})["text"]
                # 🧾 Summary
                final_output = summarizer.invoke({"input": analysis_output})["text"]
                final_output = clean_output(final_output)   # ✅ CLEAN COMPLEX

            except Exception as analysis_err:
                print(f"Analysis/Summary skipped due to rate limit: {analysis_err}")
                final_output = clean_output(research_output)   # ✅ CLEAN AGAIN

        # 💾 STEP 5: Save correct output
        shared_memory.save_context(
            {"input": user_input},
            {"output": final_output}
        )

        # 🔥 FINAL RESPONSE
        res = {
            "answer": final_output,
            "email": email_output,
            "routing": routing_decision,
            "tools_used": tools_used
        }

        # Suggest name if this is a new chat
        if is_new_chat:
            res["suggested_name"] = suggest_chat_name(user_input)

        return res

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