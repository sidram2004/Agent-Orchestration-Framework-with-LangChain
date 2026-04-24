from langchain.agents import initialize_agent, Tool, AgentType
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv

from tools import calculator, weather_tool, web_search, unit_converter, current_time
from memory import create_agent_memory

load_dotenv()


def get_llm(temperature=0):
    return ChatGroq(model="llama-3.1-8b-instant", temperature=temperature)


TOOLS = [
    Tool(name="Calculator",     func=calculator,     description="Solve any math, algebra, equations, or calculus. Always use for numeric problems."),
    Tool(name="Weather",        func=weather_tool,   description="Real-time weather for any city. Never guess weather."),
    Tool(name="Web Search",     func=web_search,     description="Search the web for facts, news, general knowledge."),
    Tool(name="Unit Converter", func=unit_converter, description="Convert units: km to m, C to F, kg to g, etc."),
    Tool(name="Time",           func=current_time,   description="Get the current date and time."),
]

RESEARCH_PREFIX = """
You are a highly intelligent AI Research Agent.

CORE RULES:
1. For math/equations -> Use Calculator tool.
2. For weather -> Use Weather tool ONLY.
3. For unit conversions -> Use Unit Converter tool.
4. For current time -> Use Time tool.
5. For latest news/prices/unknown facts -> Use Web Search tool.
6. For well-known facts (capitals, definitions, history) -> Answer DIRECTLY without tools.
7. NEVER use a tool if you already know the answer.
8. Be BRIEF for simple queries. Return only the result.
9. ALWAYS end your response with "Final Answer:" followed by the result.
10. If you decide no tool is needed, immediately write: Final Answer: [your answer]

### USER CORE CONTEXT (PERSISTENT MEMORY) ###
If provided, use the facts in this block to personalize your search and answers. 
Always respect user names, preferences, and recurring context saved here.
"""


def create_agents():
    llm = get_llm()

    # 1. Research Agent
    research_agent = initialize_agent(
        TOOLS, llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        memory=create_agent_memory(),
        early_stopping_method="generate",
        verbose=False,
        handle_parsing_errors=True,
        max_iterations=5,
        return_intermediate_steps=True,
        agent_kwargs={"prefix": RESEARCH_PREFIX}
    )

    # 2. Analysis Agent
    analysis_agent = LLMChain(llm=llm, prompt=PromptTemplate(
        input_variables=["input"],
        template="""You are a Senior Analysis Agent specializing in deep logical reasoning.

Analyze the research data:
- For math: explain logic, formula, and why the result is correct.
- For general: identify trends, draw conclusions, expand critically on facts.

Research Data:
{input}

Deep Analysis:"""
    ))

    # 3. Summarizer Agent
    summarizer_agent = LLMChain(llm=llm, prompt=PromptTemplate(
        input_variables=["input"],
        template="""Act as a Senior Expert generating a professional final response.

RULES:
1. Short input (number, time, fact) -> Return ONLY the result in 1 sentence.
2. Detailed analysis -> Comprehensive Markdown with ## headers and bullets.
3. ALWAYS personalize based on any provided ### USER CORE CONTEXT ### in the input.

Input Data:
{input}

Final Answer:"""
    ))

    # 4. Email Agent
    email_agent = LLMChain(llm=llm, prompt=PromptTemplate(
        input_variables=["input"],
        template="""Generate a professional email:

{input}

Format:
Subject: [Subject]
Body:
[Body]"""
    ))

    # 5. Top-Level Router
    router_agent = LLMChain(llm=llm, prompt=PromptTemplate(
        input_variables=["input"],
        template="""You are a Task Routing Supervisor. Classify the user's intent into EXACTLY ONE:
[DOC]      - Query related to an uploaded document, file, or PDF context.
[SIMPLE]   - Direct answer, small talk, or general facts,no tools needed.
[TOOL]     - Needs a tool: math, weather, time,web search,unit conversion,or any tool.
[CONTENT]  - Creative/writing: email, essay, story, code generation.
[COMPLEX]  - Multi-step analysis requiring deep reasoning.

Respond with ONLY the tag.

User Query: '{input}'"""
    ))

    # 6. Use-Case Router
    usecase_router = LLMChain(llm=llm, prompt=PromptTemplate(
        input_variables=["input"],
        template="""Classify this complex query into EXACTLY ONE domain:

[MEDICAL]   - Health, symptoms, medications
[DECISION]  - Comparisons, recommendations, pros/cons
[DEBUG]     - Code errors, bugs, technical issues
[SHOPPING]  - Products, prices, reviews, what to buy
[GENERAL]   - Research, explanations, how/why questions

Respond with ONLY the tag.

Query: '{input}'"""
    ))

    # 7. Medical Agent
    medical_agent = LLMChain(llm=llm, prompt=PromptTemplate(
        input_variables=["input"],
        template="""You are a Medical Information Agent.

RULES:
- Always recommend consulting a real doctor.
- Evidence-based information only.
- Structure: Condition Overview -> Possible Causes -> General Guidance -> When to See a Doctor

Query: {input}

Medical Analysis:"""
    ))

    # 8. Decision Agent
    decision_agent = LLMChain(llm=llm, prompt=PromptTemplate(
        input_variables=["input", "research_data"],
        template="""You are a Senior Decision Analysis Agent.

## Options Analysis
## Risk Assessment
## Recommendation
## Conclusion

Research Data: {research_data}
Query: {input}

Decision Analysis:"""
    ))

    # 9. Debug Agent
    debug_agent = LLMChain(llm=llm, prompt=PromptTemplate(
        input_variables=["input"],
        template="""You are an Expert Debug Agent.

## Error Detected
## Root Cause
## Fixed Code
## Explanation

Problem: {input}

Debug Analysis:"""
    ))

    # 10. Shopping Agent
    shopping_agent = LLMChain(llm=llm, prompt=PromptTemplate(
        input_variables=["input", "research_data"],
        template="""You are a Shopping Research Agent.

## Products Found
## Price Comparison
## Reviews and Ratings
## Best Pick and Why

Research Data: {research_data}
Query: {input}

Shopping Analysis:"""
    ))

    # 11. General Research Agent
    general_agent = LLMChain(llm=llm, prompt=PromptTemplate(
        input_variables=["input", "research_data"],
        template="""You are a General Research and Synthesis Agent.

## Overview
## Key Findings
## Deep Dive
## Conclusion

Research Data: {research_data}
Query: {input}

Research Synthesis:"""
    ))

    # 12. Confidence Agent
    confidence_agent = LLMChain(llm=llm, prompt=PromptTemplate(
        input_variables=["input"],
        template="""Evaluate if this response is complete and accurate.

Respond ONLY with:
[GOOD]    - Complete, accurate, well-structured
[IMPROVE] - Needs refinement

Response:
{input}"""
    ))

    # 13. Refinement Agent
    refinement_agent = LLMChain(llm=llm, prompt=PromptTemplate(
        input_variables=["input"],
        template="""Improve this response - add missing details, fix unclear sections, ensure proper Markdown formatting.

Original:
{input}

Refined Response:"""
    ))

    # 14. Content Agent
    content_agent = LLMChain(llm=llm, prompt=PromptTemplate(
        input_variables=["input"],
        template="""You are a Senior Content Creation Agent.

- Emails: Subject + professional Body.
- Essays: ## headers, structured paragraphs.
- Code: Clean, commented, working.
- Creative: Engaging and vivid.
- Personalization: Always check the ### USER CORE CONTEXT ### in the request to tailor the tone and specific details (names, roles, tech stack) to the user.

Request: {input}

Generated Content:"""
    ))

    # 15. Evaluator Agent
    evaluator_agent = LLMChain(llm=llm, prompt=PromptTemplate(
        input_variables=["input"],
        template="""Evaluate content quality.

Respond ONLY with:
[APPROVED] - High quality, ready to deliver
[IMPROVE]  - Needs improvement

Content:
{input}"""
    ))

    # 16. Optimizer Agent
    optimizer_agent = LLMChain(llm=llm, prompt=PromptTemplate(
        input_variables=["input"],
        template="""Optimize this content. Make it more professional, engaging, and complete.

Original:
{input}

Optimized Version:"""
    ))

    return {
        "research":       research_agent,
        "analysis":       analysis_agent,
        "summarizer":     summarizer_agent,
        "email":          email_agent,
        "router":         router_agent,
        "usecase_router": usecase_router,
        "medical":        medical_agent,
        "decision":       decision_agent,
        "debug":          debug_agent,
        "shopping":       shopping_agent,
        "general":        general_agent,
        "confidence":     confidence_agent,
        "refinement":     refinement_agent,
        "content":        content_agent,
        "evaluator":      evaluator_agent,
        "optimizer":      optimizer_agent,
        "llm":            llm,
    }