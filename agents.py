from langchain.agents import initialize_agent, Tool, AgentType
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from tools import (
    calculator,
    weather_tool,
    web_search,
    unit_converter,
    current_time
)

from memory import create_agent_memory

load_dotenv()


def create_agents():

    #  LLM 
    llm = ChatGroq(
        # model="llama-3.3-70b-versatile",
        model = "llama-3.1-8b-instant",
        temperature=0
    )

    #  Tools
    tools = [
        Tool(
            name="Calculator",
            func=calculator,
            description="Use for any mathematical calculation, symbolic math, solving equations (e.g., 'x^2-1=0'), and algebra. Return ONLY the numerical result or scientific solution."
        ),
        Tool(
            name="Weather",
            func=weather_tool,
            description="Use ONLY for real-time weather. Never guess. "
            
        ),
        Tool(
            name="Web Search",
            func=web_search,
            description="Use for general knowledge and facts give in structured format. Never guess. if needed then provide explanation."
        ),
        Tool(
            name="Unit Converter",
            func=unit_converter,
            description="Convert any units like '5 km to m', '100 c to f', etc."
        ),
        Tool(
            name="Time",
            func=current_time,
            description="Get current time"
        )
    ]

    # STRONG SYSTEM PROMPT
    prefix = """
 You are a highly intelligent and detail-oriented AI assistant.

CORE RULES:
1. ALWAYS use tools when needed to provide accurate, up-to-date information.
2. For ANY mathematical query (arithmetic, algebra, equations) → ALWAYS use the Calculator tool first. If it's an equation, solve for the variable (usually x).
3. For weather information → ALWAYS use the Weather tool only. NEVER guess the weather.
4. For general facts and knowledge → Use the Web Search tool.
5. IF THE USER QUERY IS SIMPLE (e.g., math, weather, time, basic facts) → BE EXTREMELY BRIEF. Return ONLY the result with minimal explanation.
6. If the query is complex or asks for analysis, use tools to gather data, then provide a structured, insightful response.
7. Use previous context from memory when relevant.
8. If data is unavailable, say so clearly instead of guessing.
9. ALWAYS end with a "Final Answer: " clearly stating the result.
"""

    #  Research Agent (MAIN)
    research_agent = initialize_agent(
      tools,
      llm,
      agent = AgentType.ZERO_SHOT_REACT_DESCRIPTION,
      memory=create_agent_memory(),
      early_stopping_method="generate",
      verbose=False,
      handle_parsing_errors=True,
      max_iterations=5,
      return_intermediate_steps=True,
      agent_kwargs={
        "prefix": prefix,
      }
   )
    #  Analysis Agent (LLMChain)
    analysis_prompt = PromptTemplate(
        input_variables=["input"],
        template="""
You are a Senior Analysis Agent specializing in deep logical reasoning and mathematical synthesis.

Your job:
- Analyze the information provided by the Research Agent.
- If it's a math problem: Explain the logic, the formula used, and why this result is correct.
- If it's a general query: Identify trends, draw logical conclusions, and expand critically on the facts.
- Produce a rich, highly-detailed synthesis that adds value beyond just the raw facts.

Information:
{input}

Deep Analysis:
"""
    )

    analysis_agent = LLMChain(
        llm=llm,
        prompt=analysis_prompt
    )

    # Summarizer Agent (LLMChain)
    summary_prompt = PromptTemplate(
        input_variables=["input"],
        template="""
Act as a Senior Expert Assistant. 

Using the extensive analysis or raw data provided below, generate a professional final response to the user.

RULES FOR OUTPUT LENGTH:
1. IF THE INPUT IS SHORT (e.g., a number, weather, time, or simple fact) → DO NOT BE VERBOSE. Return ONLY the final answer in 1 sentence or just the result.
2. IF THE INPUT IS A DETAILED ANALYSIS → generate a highly detailed, comprehensive, and engaging final response.
   - Use Markdown syntax headers (##) and bullet points to structure your response beautifully.
   - Provide deep explanations, context, and insights.
   - Expand on the topic only if it's complex enough to warrant it.

Input Data:
{input}

Final Answer:
"""
    )

    summarizer_agent = LLMChain(
        llm=llm,
        prompt=summary_prompt
    )
    email_prompt = PromptTemplate(
        input_variables=["input"],
        template="""
           Generate a professional email based on this:

{input} 

Format:
Subject:
Body:
"""
    )
    email_agent = LLMChain(
        llm=llm,
        prompt=email_prompt
    )
    
    # Router Agent (LLMChain)
    llm_router = ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0
    )

    router_prompt = PromptTemplate(
        input_variables=["input"],
        template="""
        You are a highly-analytical Task Routing Supervisor. 
        Analyze the user's query and decide the depth of response needed.

        Options:
        - [RESEARCH]: Quick responses for simple lookups (e.g., current weather, current time, basic facts, or straightforward calculations).
        - [COMPLEX]: Deep thinking/multi-agent responses for queries that involve multi-step logic, analysis, comparison, detailed explanations, or creative writing.

        GUIDELINES:
        1. If the user wants to understand *HOW* or *WHY* a result was achieved (e.g., "how to solve", "show steps", "explain"), always choose [COMPLEX].
        2. If the user just wants the final answer quickly (e.g., "what is 4+4", "weather in punjab"), choose [RESEARCH].
        3. Do not rely on specific keywords; use your intelligence to determine if a simple tool-output is sufficient or if a more thorough synthesis/summary is better.

        User Query: '{input}'

        Respond with ONLY the word [RESEARCH] or [COMPLEX].
        """
    )
    router_agent = LLMChain(llm=llm_router, prompt=router_prompt)
    
    return research_agent, analysis_agent, summarizer_agent, email_agent, router_agent, llm