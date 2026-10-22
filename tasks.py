"""
Tasks Definition for AI Orchestra v2
Coordinates the sequential workflow with customizable thinking depth,
domain/language filters, and output language.
"""
from crewai import Task, Agent
from typing import Dict, Any, Optional


def _build_filter_instructions(settings: Dict[str, Any]) -> str:
    """Build search filter instruction text from query settings."""
    parts = []
    domain = settings.get("domain_filter", "")
    lang = settings.get("language_filter", "")
    if domain:
        parts.append(f"IMPORTANT DOMAIN RESTRICTION: You MUST only search and accept sources from the following domain(s): {domain}. Reject any source that does not match.")
    if lang:
        parts.append(f"IMPORTANT LANGUAGE RESTRICTION: You MUST only consider sources written in '{lang}' language. Discard sources in other languages.")
    return "\n".join(parts)


def create_research_task(agent: Agent, query: str, settings: Optional[Dict[str, Any]] = None) -> Task:
    settings = settings or {}
    profile = settings.get("depth_profile", {})
    search_instruction = profile.get("search_instruction", "Conduct a thorough multi-source search.")
    filter_instructions = _build_filter_instructions(settings)
    domain = settings.get("domain_filter", "")

    # Build the search query hint for domain operators
    domain_hint = ""
    if domain:
        domain_hint = f"\nWhen using the search tool, append 'site:{domain}' to your search queries to restrict results."

    return Task(
        description=(
            f"Investigate the following user query thoroughly:\n"
            f"'{query}'\n\n"
            f"Research Directives:\n"
            f"{search_instruction}\n"
            f"{filter_instructions}\n"
            f"{domain_hint}\n\n"
            f"Your objectives:\n"
            f"1. Use the search tool to find authoritative, credible documentation and research.\n"
            f"2. Filter out unverified claims; extract core empirical facts and verifiable evidence.\n"
            f"3. For each source, document: exact Title, URL, and summary of critical takeaways.\n"
            f"4. Hand over this structured research briefing to the Problem Solver."
        ),
        expected_output=(
            "A structured research dossier containing verified facts, empirical evidence, and a curated list of credible sources with URLs."
        ),
        agent=agent
    )


def create_solve_task(agent: Agent, query: str, research_task: Task, settings: Optional[Dict[str, Any]] = None) -> Task:
    settings = settings or {}
    profile = settings.get("depth_profile", {})
    solve_instruction = profile.get("solve_instruction", "Analyze step-by-step and deliver a proven solution.")

    return Task(
        description=(
            f"User Challenge: '{query}'\n\n"
            f"Analytical Directives:\n"
            f"{solve_instruction}\n\n"
            f"Using the research dossier provided by the Researcher Agent:\n"
            f"1. Critically analyze the empirical evidence and findings.\n"
            f"2. Apply rigorous reasoning to solve the problem step-by-step.\n"
            f"3. Resolve any contradictions using the verified references.\n"
            f"4. Deliver a definitive solution and reasoned conclusions for the Writer."
        ),
        expected_output=(
            "A comprehensive, step-by-step analytical solution supported by reasoned deductions and citations."
        ),
        agent=agent,
        context=[research_task]
    )


def create_write_task(agent: Agent, query: str, research_task: Task, solve_task: Task, settings: Optional[Dict[str, Any]] = None) -> Task:
    settings = settings or {}
    profile = settings.get("depth_profile", {})
    write_instruction = profile.get("write_instruction", "Compose a well-structured executive report.")
    output_language = settings.get("output_language", "en")

    lang_instruction = ""
    if output_language and output_language.lower() != "en":
        lang_instruction = f"\nCRITICAL: The ENTIRE report MUST be written in '{output_language}' language. All headings, body text, summaries, and recommendations must be in '{output_language}'. Only source titles and URLs may remain in their original language."

    return Task(
        description=(
            f"Original Query: '{query}'\n\n"
            f"Writing Directives:\n"
            f"{write_instruction}\n"
            f"{lang_instruction}\n\n"
            f"Craft the definitive report based on the Solver's solution and Researcher's sources:\n"
            f"1. Compose a polished, engaging report in clean Markdown.\n"
            f"2. Include these sections:\n"
            f"   - Executive Title\n"
            f"   - Executive Summary\n"
            f"   - Key Findings & Evidence Analysis\n"
            f"   - In-Depth Solution & Step-by-Step Breakdown\n"
            f"   - Practical Takeaways & Recommendations\n"
            f"   - Verified Sources & Bibliography (with Title, Type, and URL)\n"
            f"3. Tone: authoritative, clear, professional, and free of fluff."
        ),
        expected_output=(
            "A complete, beautifully formatted Markdown report ready for publication, with full source citations and actionable conclusions."
        ),
        agent=agent,
        context=[research_task, solve_task]
    )
