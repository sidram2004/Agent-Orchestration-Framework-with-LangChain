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
        model="llama-3.3-70b-versatile",
        # model = "llama-3.1-8b-instant",
        temperature=0
    )

    #  Tools
    tools = [
        Tool(
            name="Calculator",
            func=calculator,
            description="Use ONLY for mathematical calculations like 45*6"
        ),
        Tool(
            name="Weather",
            func=weather_tool,
            description="Use ONLY for real-time weather. Never guess."
        ),
        Tool(
            name="Web Search",
            func=web_search,
            description="Use for general knowledge and facts"
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

RULES:
1. ALWAYS use tools when needed to conduct deep research.
2. For math → ALWAYS use Calculator.
3. For weather → ALWAYS use Weather tool only.
4. NEVER guess answers; rely on tool outputs.
5. Use previous conversation context seamlessly.
6. If specific data is not found, clearly state what is missing instead of guessing.
7. Be highly comprehensive! Provide deep, analytical, and detailed explanations using professional formatting (bullet points, Markdown formatting). Do NOT be brief.
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
You are a Senior Analysis Agent capable of deep, multi-faceted thinking.

Your job:
- Analyze the given information thoroughly.
- Draw logical conclusions, identify trends, and expand critically on the facts.
- Produce a rich, highly-detailed synthesis of the data.

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




        
                        Using the extensive analysis provided below, generate a highly detailed, comprehensive, and engaging final response to the user. 
        - Use Markdown syntax headers (##) and bullet points to structure your response beautifully.
        - Provide deep explanations, context, and insights just like an advanced analytical AI (like ChatGPT) would.
        - Do not be brief! Expand carefully on the topic, ensuring absolute clarity and depth.

Analysis Data:
{input}

Comprehensive Final Answer:
"""
    )

    summarizer_agent = LLMChain(
        llm=llm,
        prompt=summary_prompt
    )
    # Email Agent (LLMChain)
    

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
        You are a task routing supervisor.
        Analyze the user's query and decide what type of task it is.

        Options:
        - [SIMPLE]: Task requires just a quick tool lookup (e.g., getting weather, current time, simple math, quick unit conversion).
        - [COMPLEX]: Task requires deep analysis, drawing conclusions, or drafting an email/report.

        User Query: '{input}'

        Respond with ONLY the word [SIMPLE] or [COMPLEX]. Do not add any extra text.
        """
    )
    router_agent = LLMChain(llm=llm_router, prompt=router_prompt)
    
    return research_agent, analysis_agent, summarizer_agent, email_agent, router_agent