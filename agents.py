"""
Agents Definition for AI Orchestra
Defines the specialized multi-agent roles:
- Searcher Agent (First Violin / Credible Source Scout)
- Solver Agent (Piano Soloist / Problem Solver & Reasoner)
- Writer Agent (Master Scribe / Chief Editorial Writer)
"""
from typing import List, Optional
from crewai import Agent, LLM
from tools.search_tool import search_credible_sources
from tools.language_detector import get_localized_profile, normalize_language

def create_searcher_agent(llm: LLM, custom_tools: Optional[List] = None) -> Agent:
    tools = custom_tools if custom_tools is not None else [search_credible_sources]
    return Agent(
        role="Senior Credible Source Researcher",
        goal=(
            "Search the web thoroughly to discover authoritative, peer-reviewed, or official documentation on the topic. "
            "Filter out unreliable claims, extract verified facts, key excerpts, and exact source URLs, and deliver structured research materials to the Problem Solver."
        ),
        backstory=(
            "You are the First Violinist and the intelligence scout of the AI Orchestra. Your mission is absolute truth and verification. "
            "You filter out noise, rumors, and low-credibility websites, curating only high-impact references, official docs, and scientific statistics. "
            "You provide verified citations and sources to the Piano Soloist to ensure grounded reasoning."
        ),
        tools=tools,
        llm=llm,
        verbose=True,
        memory=False
    )

def create_solver_agent(llm: LLM) -> Agent:
    return Agent(
        role="Lead Problem Solver & Analytical Strategist",
        goal=(
            "Critically analyze the research findings and verified sources provided by the Researcher Agent. "
            "Apply first-principles reasoning to solve the user's problem step-by-step, reconcile conflicting viewpoints, and produce an airtight, accurate resolution."
        ),
        backstory=(
            "You are the Piano Soloist and the analytical core of the AI Orchestra. Your forte is deductive reasoning, "
            "dissecting complex queries, and calculating or proving optimal solutions. You accept no claim without evidence, "
            "connecting every insight to the researcher's verified sources and preparing a definitive solution for the Writer."
        ),
        tools=[],
        llm=llm,
        verbose=True,
        memory=False
    )

def create_writer_agent(llm: LLM, language: str = "en") -> Agent:
    lang_code, _ = normalize_language(language)
    profile = get_localized_profile(lang_code)

    return Agent(
        role=profile["writer_role"],
        goal=profile["writer_goal"],
        backstory=profile["writer_backstory"],
        tools=[],
        llm=llm,
        verbose=True,
        memory=False
    )
