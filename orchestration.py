"""
orchestration.py - Full Final Workflow (Fixed)
===============================================
Execution paths:
  [SIMPLE]  -> Fast LLM direct answer
  [TOOL]    -> Research Agent with tools
  [CONTENT] -> Content -> Evaluate -> Optimize -> Final
  [COMPLEX] -> Use-Case Router -> Domain Pipeline
  All paths -> Final Output -> Save Context -> Database Update
"""

import re
import time
from agents import create_agents
from memory import create_shared_memory

print("[Orchestration] Loading agents...")
AGENTS = create_agents()
shared_memory = create_shared_memory()
print("[Orchestration] All agents ready.")


# ── Helpers ────────────────────────────────────────────────────────────────────

def clean_output(text: str) -> str:
    """Strip internal ReAct reasoning, keep only the final answer."""
    if not text:
        return ""
    # Priority: extract after "Final Answer:"
    if "Final Answer:" in text:
        return text.split("Final Answer:")[-1].strip()
    # Strip reasoning lines
    clean_lines = [
        line for line in text.splitlines()
        if not any(kw in line for kw in [
            "Thought:", "Action:", "Observation:", "Action Input:",
            "I need to", "I should", "I will", "I can use", "I'll"
        ])
    ]
    cleaned = "\n".join(clean_lines).strip()
    # DO NOT fall back to text.strip() -> returning raw text leaks the ReAct thought chain!
    return cleaned


def invoke_llm(prompt: str) -> str:
    """Direct fast LLM call — no tools, no agents."""
    try:
        return AGENTS["llm"].invoke(prompt).content.strip()
    except Exception as e:
        return f"Error: {str(e)}"


def run_research(query: str):
    """
    Run Research Agent safely. Returns (output, tools_used).
    Falls back to direct LLM if agent crashes.
    """
    try:
        result     = AGENTS["research"].invoke({"input": query})
        raw_output = result.get("output") or result.get("text", "")

        # If output is empty or looks like a parsing error, fallback
        if not raw_output or "Could not parse" in raw_output or len(raw_output.strip()) < 3:
            print("[Research] Parsing failed, falling back to direct LLM")
            return invoke_llm(query), []

        output     = clean_output(raw_output)
        tools_used = []

        for action, observation in result.get("intermediate_steps", []):
            if hasattr(action, 'tool'):
                tools_used.append({
                    "tool":        action.tool,
                    "tool_input":  action.tool_input,
                    "log":         action.log,
                    "observation": str(observation)
                })
            elif isinstance(action, dict) and "tool" in action:
                tools_used.append({
                    "tool":        action["tool"],
                    "tool_input":  action.get("tool_input", ""),
                    "log":         action.get("log", ""),
                    "observation": str(observation)
                })
        return output, tools_used

    except Exception as e:
        print(f"[Research Agent Error] {e} — falling back to LLM")
        return invoke_llm(query), []


def suggest_chat_name(user_input: str):
    try:
        prompt = (f"Suggest a short professional name (max 4 words) for a chat about: '{user_input}'. "
                  f"Reply ONLY with the name, no quotes.")
        name = AGENTS["llm"].invoke(prompt).content.strip().strip('"\'')
        return name if len(name.split()) <= 6 else None
    except Exception as e:
        print(f"[Naming Error] {e}")
        return None


# ── Pre-routing: keyword-based safety net ─────────────────────────────────────

SIMPLE_PATTERNS = [
    r"^(hi|hello|hey|good morning|good evening|good night|how are you|what's up|sup)\b",
    r"^what is (a |an |the )?[a-z\s]{2,40}\?$",
    r"^who (is|was|invented|created|founded|discovered)\b",
    r"^when (did|was|is)\b",
    r"^where (is|was|are)\b",
    r"^(define|definition of|meaning of)\b",
    r"^(what does .+ mean)\b",
    r"^(capital of|population of|currency of|language of)\b",
    r"^(tell me about yourself|who are you|what can you do)\b",
]

TOOL_PATTERNS = [
    r"\b(weather|temperature|forecast|humidity|wind)\b",
    r"\b(calculate|solve|equation|integral|derivative|simplify)\b",
    r"\b(\d+[\s]*[\+\-\*\/\^]\s*\d+)\b",
    r"\b(convert|km to|miles to|celsius|fahrenheit|kg to|lbs)\b",
    r"\b(current time|what time|what's the time)\b",
    r"\b(search for|look up|find me|news about|latest)\b",
]

CONTENT_PATTERNS = [
    r"\b(write|draft|compose|create|generate)\b.*(email|letter|essay|story|blog|post|poem|code|script|report)\b",
    r"\b(email|essay|story|blog post|cover letter|poem)\b.*(write|draft|create|compose|generate)\b",
]

COMPLEX_PATTERNS = [
    r"\b(explain|how does|why does|what causes|difference between|compare|analyze|analyse)\b",
    r"\b(medical|symptom|disease|treatment|medication|diagnosis|health)\b",
    r"\b(debug|error|traceback|exception|bug|fix this code|not working)\b",
    r"\b(buy|purchase|recommend|best product|review|price|shopping)\b",
    r"\b(should i|pros and cons|better option|which is better|recommend)\b",
]

def keyword_route(text: str) -> str | None:
    """
    Fast keyword pre-routing before calling the LLM router.
    Returns routing tag or None if unclear.
    """
    t = text.lower().strip()
    for p in SIMPLE_PATTERNS:
        if re.search(p, t, re.IGNORECASE):
            return "[SIMPLE]"
    for p in CONTENT_PATTERNS:
        if re.search(p, t, re.IGNORECASE):
            return "[CONTENT]"
    for p in TOOL_PATTERNS:
        if re.search(p, t, re.IGNORECASE):
            return "[TOOL]"
    for p in COMPLEX_PATTERNS:
        if re.search(p, t, re.IGNORECASE):
            return "[COMPLEX]"
    return None


# ── Pipeline: SIMPLE ──────────────────────────────────────────────────────────

def pipeline_simple(user_input: str):
    output = invoke_llm(user_input)
    return output, [], "[SIMPLE] Fast LLM"


# ── Pipeline: TOOL ────────────────────────────────────────────────────────────

def pipeline_tool(user_input: str, combined_input: str):
    output, tools = run_research(combined_input)
    # If research returned nothing useful, fall back to direct LLM
    if not output or len(output.strip()) < 3:
        if tools and "observation" in tools[-1] and tools[-1]["observation"]:
            obs = tools[-1]["observation"]
            output = invoke_llm(
                f"User Query: {user_input}\n"
                f"Result calculated by system tool: {obs}\n\n"
                f"Task: Directly answer the user query based on this result.\n"
                f"Formatting Rules:\n"
                f"1. Use highly readable, structured Markdown (e.g. ## Headers, bullet points, bolding for emphasis).\n"
                f"2. Make the layout spacious and easy for a beginner to understand.\n"
                f"3. If the user asks for a step-by-step explanation, provide the full mathematical steps leading exactly to the known result {obs}."
            )
        else:
            output = invoke_llm(user_input)
    return output, tools, "[TOOL] Research Agent + Tools"


# ── Pipeline: CONTENT ─────────────────────────────────────────────────────────

def pipeline_content(user_input: str):
    output = AGENTS["content"].invoke({"input": user_input})["text"]
    for _ in range(2):
        try:
            eval_result = AGENTS["evaluator"].invoke({"input": output})["text"].strip().upper()
            if "[APPROVED]" in eval_result:
                break
            output = AGENTS["optimizer"].invoke({"input": output})["text"]
        except Exception:
            break
    return output, [], "[CONTENT] Generate -> Evaluate -> Optimize"


# ── Pipeline: MEDICAL ─────────────────────────────────────────────────────────

def pipeline_medical(user_input: str, combined_input: str):
    try:
        output = AGENTS["medical"].invoke({"input": combined_input})["text"]
    except Exception:
        output = invoke_llm(f"Give medical information about: {user_input}")

    specialist_check = invoke_llm(
        f"Does this medical query require specialist referral? Reply ONLY [YES] or [NO]. Query: '{user_input}'"
    ).upper()

    if "[YES]" in specialist_check:
        research_data, tools = run_research(f"specialist medical advice: {user_input}")
        output += f"\n\n---\n## Specialist Review Note\n{research_data}\n\n**Please consult a licensed medical professional.**"
        return output, tools, "[COMPLEX->MEDICAL] Initial Check -> Specialist Review -> Merge"
    return output, [], "[COMPLEX->MEDICAL] Initial Check -> Direct Output"


# ── Pipeline: DECISION ────────────────────────────────────────────────────────

def pipeline_decision(user_input: str, combined_input: str):
    research_data, tools = run_research(combined_input)
    try:
        decision_output = AGENTS["decision"].invoke({"input": user_input, "research_data": research_data})["text"]
        final = AGENTS["summarizer"].invoke({"input": decision_output})["text"]
    except Exception:
        final = invoke_llm(f"Analyze pros and cons and give a recommendation for: {user_input}")
    return final, tools, "[COMPLEX->DECISION] Analyze -> Risk -> Compare -> Decision Engine"


# ── Pipeline: DEBUG ───────────────────────────────────────────────────────────

def pipeline_debug(user_input: str, combined_input: str):
    try:
        debug_output = AGENTS["debug"].invoke({"input": combined_input})["text"]
    except Exception:
        debug_output = invoke_llm(f"Debug this and provide a fix: {user_input}")

    tools = []
    if any(kw in user_input.lower() for kw in ["error", "exception", "traceback", "failed", "bug"]):
        try:
            search_hint, tools = run_research(f"how to fix: {user_input[:200]}")
            if search_hint:
                debug_output += f"\n\n---\n## Additional Reference\n{search_hint}"
        except Exception:
            pass
    return debug_output, tools, "[COMPLEX->DEBUG] Detect -> Cause -> Fix -> Aggregator"


# ── Pipeline: SHOPPING ────────────────────────────────────────────────────────

def pipeline_shopping(user_input: str, combined_input: str):
    research_data, tools = run_research(f"best products prices reviews: {user_input}")
    try:
        shopping_output = AGENTS["shopping"].invoke({"input": user_input, "research_data": research_data})["text"]
        final = AGENTS["summarizer"].invoke({"input": shopping_output})["text"]
    except Exception:
        final = invoke_llm(f"Recommend the best options with prices and reviews for: {user_input}")
    return final, tools, "[COMPLEX->SHOPPING] Search -> Prices -> Reviews -> Merge"


# ── Pipeline: GENERAL ─────────────────────────────────────────────────────────

def pipeline_general(user_input: str, combined_input: str):
    multipart_check = invoke_llm(
        f"Is this query multi-part (multiple distinct questions)? Reply ONLY [YES] or [NO]. Query: '{user_input}'"
    ).upper()

    tools = []
    routing_suffix = ""

    if "[YES]" in multipart_check:
        routing_suffix = "Multi-Part -> Parallel Processing -> Merge"
        parts_text  = invoke_llm(f"Break into 2-3 distinct sub-questions, one per line:\n{user_input}")
        sub_qs      = [p.strip() for p in parts_text.strip().splitlines() if p.strip()][:3]
        parts       = []
        for sq in sub_qs:
            part_data, part_tools = run_research(sq)
            parts.append(f"**{sq}**\n{part_data}")
            tools.extend(part_tools)
        research_data = "\n\n".join(parts)
    else:
        routing_suffix = "Direct Analysis -> Merge"
        research_data, tools = run_research(combined_input)

    try:
        general_output = AGENTS["general"].invoke({"input": user_input, "research_data": research_data})["text"]
        summary        = AGENTS["summarizer"].invoke({"input": general_output})["text"]
        confidence     = AGENTS["confidence"].invoke({"input": summary})["text"].strip().upper()
        if "[IMPROVE]" in confidence:
            summary        = AGENTS["refinement"].invoke({"input": summary})["text"]
            routing_suffix += " -> Summarize -> Confidence -> Refine"
        else:
            routing_suffix += " -> Summarize -> Confidence (Good)"
    except Exception:
        summary        = invoke_llm(f"Give a detailed answer about: {user_input}\n\nContext: {research_data[:500]}")
        routing_suffix += " -> Direct Summary (fallback)"

    return summary, tools, f"[COMPLEX->GENERAL] Research -> {routing_suffix}"


# ── Pipeline: COMPLEX ─────────────────────────────────────────────────────────

def pipeline_complex(user_input: str, combined_input: str):
    try:
        domain = AGENTS["usecase_router"].invoke({"input": user_input})["text"].strip().upper()
    except Exception:
        domain = "[GENERAL]"

    if "[MEDICAL]"  in domain: return pipeline_medical(user_input, combined_input)
    if "[DECISION]" in domain: return pipeline_decision(user_input, combined_input)
    if "[DEBUG]"    in domain: return pipeline_debug(user_input, combined_input)
    if "[SHOPPING]" in domain: return pipeline_shopping(user_input, combined_input)
    return pipeline_general(user_input, combined_input)


# ── Main Entry Point ──────────────────────────────────────────────────────────

def run_workflow(user_input: str, is_new_chat: bool = False, core_memory: str = "") -> dict:
    """
    Main orchestration entry point.
    Returns: { answer, routing, tools_used, email, suggested_name? }
    """
    try:
        # Load memory context
        memory_data    = shared_memory.load_memory_variables({"input": user_input})
        history        = memory_data.get("history", "")
        
        # Combined context for research/complex agents
        combined_input = f"{core_memory}\nPrevious Context:\n{history}\n\nUser Query:\n{user_input}"
        
        # Primary input for simple/direct agents
        agent_input = f"{core_memory}\n{user_input}"

        # Step 1: Fast keyword pre-routing (no LLM call needed)
        routing_raw = keyword_route(user_input)

        # Step 2: LLM router only if keyword routing was unclear
        if routing_raw is None:
            try:
                routing_raw = AGENTS["router"].invoke({"input": user_input})["text"].strip().upper()
            except Exception as e:
                print(f"[Router Error] {e} — defaulting to SIMPLE")
                routing_raw = "[SIMPLE]"

        print(f"[Router] '{user_input[:60]}' -> {routing_raw}")

        # Step 3: Execute correct pipeline
        if   "[SIMPLE]"  in routing_raw:
            final_output, tools_used, routing_label = pipeline_simple(agent_input)
        elif "[TOOL]"    in routing_raw:
            final_output, tools_used, routing_label = pipeline_tool(user_input, combined_input)
        elif "[CONTENT]" in routing_raw:
            final_output, tools_used, routing_label = pipeline_content(agent_input)
        elif "[COMPLEX]" in routing_raw:
            final_output, tools_used, routing_label = pipeline_complex(user_input, combined_input)
        else:
            # Unknown tag — default to SIMPLE for safety
            print(f"[Router] Unknown tag '{routing_raw}' — using SIMPLE")
            final_output, tools_used, routing_label = pipeline_simple(agent_input)

        # Ensure we always have some output
        if not final_output or len(final_output.strip()) < 3:
            final_output = invoke_llm(user_input)

        # Step 4: Save context
        try:
            shared_memory.save_context(
                {"input": user_input},
                {"output": final_output[:1000]}
            )
        except Exception as e:
            print(f"[Memory Save Error] {e}")

        # Step 5: Build response
        response = {
            "answer":     final_output,
            "email":      "",
            "routing":    routing_label,
            "tools_used": tools_used,
        }
        if is_new_chat:
            try:
                response["suggested_name"] = suggest_chat_name(user_input)
            except Exception:
                pass
        return response

    except Exception as e:
        err = str(e)
        print(f"[Workflow Error] {err}")
        if "rate_limit" in err.lower() or "tokens_exceeded" in err.lower():
            time.sleep(3)
            return {"answer": "⚠️ Rate limit reached. Please wait a moment and try again.",
                    "email": "", "routing": "RATE_LIMITED", "tools_used": []}
        # Last resort — try direct LLM
        try:
            fallback = invoke_llm(user_input)
            return {"answer": fallback, "email": "", "routing": "[FALLBACK] Direct LLM", "tools_used": []}
        except Exception:
            return {"answer": "❌ Something went wrong. Please try again.",
                    "email": "", "routing": "ERROR", "tools_used": []}