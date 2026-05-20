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
from memory import create_shared_memory, create_doc_retriever, has_vector_db

print("[Orchestration] Loading agents...")
AGENTS = create_agents()
# Isolated memory registry to prevent cross-chat data leakage
MEMORY_REGISTRY = {}

def get_chat_memory(chat_id):
    if not chat_id:
        from memory import create_shared_memory
        return create_shared_memory()
    if chat_id not in MEMORY_REGISTRY:
        from memory import create_shared_memory
        MEMORY_REGISTRY[chat_id] = create_shared_memory()
    return MEMORY_REGISTRY[chat_id]

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
    r"\b(current time|what time|what's the time|time in|time)\b",
    r"\b(search for|look up|find me|news about|latest)\b",
]

CONTENT_PATTERNS = [
    r"\b(write|draft|compose|create|generate)\b.*(email|letter|essay|story|blog|post|poem|code|script|report)\b",
    r"\b(email|essay|story|blog post|cover letter|poem)\b.*(write|draft|create|compose|generate)\b",
]

DOC_PATTERNS = [
    # File type mentions
    r"\b(document|pdf|file|report|presentation|doc|docx|word|excel|xlsx|powerpoint|pptx)\b",
    
    # Reference patterns — must explicitly point to an uploaded file
    r"\b(uploaded|above file|this file|that file|current file|my file|the file)\b",
    r"\b(above|this|that|the)\s+(doc|document|report|file|pdf|word|excel)\b",
    r"\bin (above|this|the|my|that) file\b",
    r"\bfrom (above|this|the|my|that) file\b",
    r"\bin above\b",
    r"\bfrom above\b",
    
    # Content-based patterns — must reference the document explicitly
    r"\b(based on the text|in the context|from the doc|in this report|in the document)\b",
    
    # Action + document patterns — must say "file/doc/report" explicitly
    r"\b(tell me about|summarize|what is in|give details about|explain|analyze)\b.*(file|doc|report|document|pdf|word)\b",
    r"\b(what|tell|give|show|explain|define)\b.*(about|in|from)?\s*(this|the|above|my)\s+(file|doc|document|report|word file|pdf)\b",
    
    # Direct question patterns about uploaded files
    r"what is (this|the|above|my) (file|doc|document|report|word|pdf)",
    r"tell me (about|short about|detailed about) (this|the|above|my) (file|doc|report|word|document)",
    r"give (detailed|summary|details|information) (about|of|from)? (this|the|above) (file|doc|report)",
    r"what('s| is) in (the|this|above|my) (file|doc|document|report|word)",
    r"(define|explain) (this |the |)?report",
    r"what is project name",
    r"tell me short about report",
    r"give detailed about",
    r"give summary of",
    r"\b(explain|summarize|tell me about)\b.*\b(chapter|section|part)\b",
    r"\b(chapter|section|part)\b\s*\d+",
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
    
    # Priority 1: Clear Tool Matches (Weather, Time, etc.)
    for p in TOOL_PATTERNS:
        if re.search(p, t, re.IGNORECASE):
            return "[TOOL]"
            
    # Priority 2: Clear Document Matches
    for p in DOC_PATTERNS:
        if re.search(p, t, re.IGNORECASE):
            return "[DOC]"
            
    # Priority 3: Other patterns
    for p in SIMPLE_PATTERNS:
        if re.search(p, t, re.IGNORECASE):
            return "[SIMPLE]"
    for p in CONTENT_PATTERNS:
        if re.search(p, t, re.IGNORECASE):
            return "[CONTENT]"
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
    from tools import weather_tool, current_time, calculator, unit_converter, web_search
    import re
    
    t_input = user_input.lower().strip()
    
    # Fast path for Weather
    if t_input.startswith("weather in ") or t_input.startswith("weather for ") or t_input.startswith("weather "):
        city = t_input.replace("weather in ", "").replace("weather for ", "").replace("weather ", "").strip()
        if city and city not in ["what", "the", "is", "like", "current"]:
            res = weather_tool(city)
            if "not found" not in res.lower() and "unavailable" not in res.lower():
                return res, [{"tool": "Weather", "tool_input": city, "observation": res}], "[TOOL] Fast Weather Match"

    # Fast path for Time
    if "time in" in t_input or "time of" in t_input or t_input in ["time", "current time", "what time is it"]:
        res = current_time(t_input)
        return res, [{"tool": "Time", "tool_input": t_input, "observation": res}], "[TOOL] Fast Time Match"

    # Fast path for Math/Calculator
    math_keywords = ["calculate", "solve", "equation", "integral", "derivative", "simplify"]
    is_math = any(t_input.startswith(kw) for kw in math_keywords) or re.search(r"\b(\d+[\s]*[\+\-\*\/\^]\s*\d+)\b", t_input)
    if is_math:
        clean_expr = t_input
        for kw in math_keywords:
            clean_expr = clean_expr.replace(kw, "")
        clean_expr = clean_expr.strip()
        
        if clean_expr:
            res = calculator(clean_expr)
            if not res.startswith("Error"):
                # Make the output look nice
                formatted_output = f"### Calculation Result\n**Expression:** `{clean_expr}`\n**Result:** `{res}`"
                return formatted_output, [{"tool": "Calculator", "tool_input": clean_expr, "observation": res}], "[TOOL] Fast Math Match"

    # Fast path for Unit Converter
    convert_keywords = ["convert", "km to", "miles to", "celsius", "fahrenheit", "kg to", "lbs", " to ", " in "]
    is_convert = any(kw in t_input for kw in convert_keywords) and bool(re.search(r"\d", t_input))
    if is_convert:
        res = unit_converter(t_input)
        if "Invalid" not in res and "not supported" not in res:
            return f"### Conversion Result\n**Input:** `{user_input}`\n**Result:** `{res}`", [{"tool": "Converter", "tool_input": user_input, "observation": res}], "[TOOL] Fast Converter Match"

    # Fast path for Web Search
    search_keywords = ["search for", "look up", "find me", "news about", "latest", "search "]
    is_search = any(t_input.startswith(kw) for kw in search_keywords)
    if is_search:
        clean_query = t_input
        for kw in search_keywords:
            if clean_query.startswith(kw):
                clean_query = clean_query[len(kw):].strip()
                break
        
        if clean_query:
            res = web_search(clean_query)
            if "Search failed" not in res:
                # Use LLM to format the raw search results
                formatted = invoke_llm(f"Format these search results nicely using Markdown for the query '{clean_query}':\n\n{res}")
                return formatted, [{"tool": "Web Search", "tool_input": clean_query, "observation": res}], "[TOOL] Fast Search Match"

    # Default logic (fallback)
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


# ── Pipeline: DOC ─────────────────────────────────────────────────────────────

def pipeline_doc(user_input: str, doc_context: str):
    """Pipeline specifically for document questions, avoiding confusion with chat history."""
    try:
        # Check if we actually have document context
        if not doc_context or "### RELEVANT DOCUMENT EXCERPTS ###" not in doc_context:
            # No document found - inform user
            return ("I don't see any uploaded document in this conversation. Please upload a document first, "
                   "then ask your question about it."), [], "[DOC] No Document Found"

        # Detect broad explanation queries — skip the summarizer to avoid compressing real content
        broad_keywords = ["explain", "detail", "summarize", "summary", "describe", "overview",
                          "tell me about", "what is in", "give details", "full report", "complete"]
        is_broad = any(kw in user_input.lower() for kw in broad_keywords)

        prompt = f"""You are a Document Analysis Expert.
Your task is to answer the user's query based STRICTLY on the document excerpts provided below.
Do NOT use outside knowledge. Focus on the ACTUAL CONTENT in the excerpts.

{doc_context}

User Query: {user_input}

{"IMPORTANT: This is a broad explanation request. Provide a COMPREHENSIVE, STRUCTURED answer covering ALL major topics, sections, and details found in the excerpts. Use ## headers and bullet points. Do NOT say 'more information is needed' — analyze what is provided." if is_broad else "Provide a focused, accurate answer based only on the document content above."}

Document Analysis & Answer:"""

        # 1. Direct LLM generation with full context
        general_output = invoke_llm(prompt)

        # 2. For specific/narrow queries: format via summarizer. For broad: return direct (richer) output.
        if is_broad:
            final_output = general_output
        else:
            final_output = AGENTS["summarizer"].invoke({"input": general_output})["text"]

        return final_output, [], "[DOC] Semantic RAG Search"
    except Exception as e:
        print(f"[Pipeline Doc Error] {e}")
        if doc_context:
            summary = invoke_llm(f"Answer the query based on the document context.\n\nQuery: {user_input}\nContext: {doc_context[:1500]}")
            return summary, [], "[DOC] Semantic RAG Search (fallback)"
        else:
            return "Error processing document. Please try uploading the file again.", [], "[DOC] Error"

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

def run_workflow(user_input: str, is_new_chat: bool = False, core_memory: str = "", doc_text: str = "", chat_id: str = None) -> dict:
    """
    Main orchestration entry point.
    Matches your Diagram: Query -> Semantic Search -> Local FAISS Database (Persistent) -> LLM
    """
    try:
        # Load memory context specifically for this chat_id
        chat_memory = get_chat_memory(chat_id)
        
        # If it's a new chat, we might want to clear the memory
        if is_new_chat:
            try:
                chat_memory.clear()
            except AttributeError:
                pass

        memory_data    = chat_memory.load_memory_variables({"input": user_input})
        history        = memory_data.get("history", "")
        
        # Step 1: Fast keyword pre-routing
        routing_raw = keyword_route(user_input)

        # Step 2: LLM router
        if routing_raw is None:
            try:
                routing_raw = AGENTS["router"].invoke({"input": user_input})["text"].strip().upper()
            except Exception as e:
                print(f"[Router Error] {e} — defaulting to SIMPLE")
                routing_raw = "[SIMPLE]"

        print(f"[Router] '{user_input[:60]}' -> {routing_raw}")

        # Step 3: Load document context if this workspace has a document
        doc_context = ""
        session_has_db = has_vector_db(chat_id)

        # TOOL queries (weather, math, time) never need the document
        is_tool_query = "[TOOL]" in routing_raw

        if not is_tool_query:
            from memory import load_doc_retriever as _ldr
            # If new file uploaded this message, create/update the DB
            # Use overwrite=is_new_chat to ensure a fresh DB for new chats
            if doc_text:
                retriever = create_doc_retriever(doc_text, chat_id=chat_id, overwrite=is_new_chat)
            # If workspace already has a document DB, always load it
            elif session_has_db:
                retriever = _ldr(chat_id)
            else:
                retriever = None

            if retriever:
                docs = retriever.get_relevant_documents(user_input)

                # ── Fallback: vague follow-up questions return 0 chunks ──────
                # If semantic search finds nothing (e.g. "tell me more", "explain"),
                # retry with a generic broad query so doc context is never lost.
                if not docs and session_has_db:
                    FALLBACK_QUERIES = [
                        "overview summary key points main topics",
                        "introduction conclusion findings results",
                        "data analysis model methodology",
                    ]
                    for fq in FALLBACK_QUERIES:
                        docs = retriever.get_relevant_documents(fq)
                        if docs:
                            print(f"[RAG] Fallback retrieval succeeded with query: '{fq}' ({len(docs)} chunks)")
                            break

                if docs:
                    doc_context = "\n### RELEVANT DOCUMENT EXCERPTS ###\n" + \
                                  "\n---\n".join([d.page_content for d in docs])
                    print(f"[RAG] Retrieved {len(docs)} chunks for: '{user_input[:50]}'")
                else:
                    print("[RAG] Retriever returned 0 chunks (even after fallback)")
            else:
                if session_has_db:
                    print("[RAG] WARNING: session has DB but retriever failed to load")
                else:
                    print("[RAG] No document in this workspace")

        # Step 3b: Decide routing
        # If workspace has a document AND doc_context was loaded AND user is NOT asking
        # something clearly unrelated (tool/weather/math) → route to [DOC]
        # If user asks something clearly unrelated → keep original route, ignore doc context
        UNRELATED_TO_DOC = ["[TOOL]", "[CONTENT]"]
        if doc_context and not any(tag in routing_raw for tag in UNRELATED_TO_DOC):
            # Document context available — always answer from document
            routing_raw = "[DOC]"
            print(f"[Router] Doc context available → forcing [DOC]")
        elif not doc_context and "[DOC]" in routing_raw:
            # Router said DOC but we have no document — give a clear message
            print(f"[Router] [DOC] route but no doc_context — will show 'no document' message")

        # Combined context for all agents
        combined_input = f"{core_memory}\n{doc_context}\nPrevious Context:\n{history}\n\nUser Query:\n{user_input}"
        agent_input = f"{core_memory}\n{doc_context}\n{user_input}"

        if   "[DOC]"     in routing_raw:
            # Bypass ReAct agent to prevent it from web-searching generic file terms
            final_output, tools_used, routing_label = pipeline_doc(user_input, doc_context)
        elif "[SIMPLE]"  in routing_raw:
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

        # Step 4: Save context to the session-specific memory
        try:
            chat_memory.save_context(
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