"""
Multi-tier Credible Source Search Tool for AI Orchestra v2
Supports domain filtering and language restrictions via environment variables.
"""
import os
import json
import urllib.parse
import requests
from bs4 import BeautifulSoup
from crewai.tools import tool


def _build_query(base_query: str) -> str:
    """Enhance the search query with domain and language filters from environment."""
    domain_filter = os.environ.get("ORCHESTRA_DOMAIN_FILTER", "").strip()
    lang_filter = os.environ.get("ORCHESTRA_LANG_FILTER", "").strip()
    enhanced = base_query
    if domain_filter:
        # Support comma-separated domains
        domains = [d.strip() for d in domain_filter.split(",") if d.strip()]
        if len(domains) == 1:
            enhanced += f" site:{domains[0]}"
        elif domains:
            site_parts = " OR ".join(f"site:{d}" for d in domains)
            enhanced += f" ({site_parts})"
    if lang_filter:
        enhanced += f" language:{lang_filter}"
    return enhanced


def _search_serper(query: str, api_key: str) -> str:
    url = "https://google.serper.dev/search"
    lang_filter = os.environ.get("ORCHESTRA_LANG_FILTER", "").strip()
    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
    payload = {"q": query, "num": 5}
    if lang_filter:
        payload["hl"] = lang_filter
        payload["gl"] = lang_filter
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
        if response.status_code == 200:
            data = response.json()
            results = []
            for item in data.get("organic", [])[:5]:
                title = item.get("title", "No title")
                link = item.get("link", "")
                snippet = item.get("snippet", "")
                results.append(f"Title: {title}\nURL: {link}\nSummary: {snippet}\n---")
            if results:
                return "\n".join(results)
    except Exception:
        pass
    return ""


def _search_tavily(query: str, api_key: str) -> str:
    url = "https://api.tavily.com/search"
    headers = {"Content-Type": "application/json"}
    payload = {"api_key": api_key, "query": query, "max_results": 5}
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
        if response.status_code == 200:
            data = response.json()
            results = []
            for item in data.get("results", [])[:5]:
                title = item.get("title", "No title")
                url_item = item.get("url", "")
                content = item.get("content", "")
                results.append(f"Title: {title}\nURL: {url_item}\nSummary: {content}\n---")
            if results:
                return "\n".join(results)
    except Exception:
        pass
    return ""


def _search_ddg(query: str) -> str:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        res = requests.post("https://html.duckduckgo.com/html/", data={"q": query}, headers=headers, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            results = []
            for result in soup.find_all("div", class_="result__body")[:5]:
                title_elem = result.find("a", class_="result__url") or result.find("a", class_="result__snippet")
                link_elem = result.find("a", class_="result__url")
                snippet_elem = result.find("a", class_="result__snippet")
                title_tag = result.find("h2")
                title = title_tag.get_text(strip=True) if title_tag else (title_elem.get_text(strip=True) if title_elem else "Source")
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                raw_href = link_elem.get("href", "") if link_elem else ""

                clean_url = raw_href
                if "uddg=" in raw_href:
                    try:
                        clean_url = urllib.parse.unquote(raw_href.split("uddg=")[1].split("&")[0])
                    except Exception:
                        clean_url = raw_href

                if clean_url and snippet:
                    results.append(f"Title: {title}\nURL: {clean_url}\nSummary: {snippet}\n---")
            if results:
                return "\n".join(results)
    except Exception:
        pass
    return ""


def _search_wikipedia(query: str) -> str:
    lang = os.environ.get("ORCHESTRA_LANG_FILTER", "en").strip() or "en"
    try:
        url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(query)}"
        headers = {"User-Agent": "AIOrchestraMVP/2.0"}
        res = requests.get(url, headers=headers, timeout=6)
        if res.status_code == 200:
            data = res.json()
            title = data.get("title", query)
            extract = data.get("extract", "")
            page_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")
            if extract:
                return f"Wikipedia Reference: {title}\nURL: {page_url}\nSummary: {extract}\n---"
    except Exception:
        pass
    return ""


@tool("Search Credible Sources Tool")
def search_credible_sources(query: str) -> str:
    """
    Search the web for authoritative, credible, and up-to-date sources on a topic.
    Automatically applies domain and language filters if configured.
    Returns titles, source URLs, and key excerpts to cite.
    """
    enhanced_query = _build_query(query)

    serper_key = os.environ.get("SERPER_API_KEY", "").strip()
    if serper_key:
        out = _search_serper(enhanced_query, serper_key)
        if out:
            return f"[Google Serper Verified Sources]\n{out}"

    tavily_key = os.environ.get("TAVILY_API_KEY", "").strip()
    if tavily_key:
        out = _search_tavily(enhanced_query, tavily_key)
        if out:
            return f"[Tavily Verified Sources]\n{out}"

    ddg_out = _search_ddg(enhanced_query)
    wiki_out = _search_wikipedia(query)
    combined = []
    if ddg_out:
        combined.append(f"[Web Sources via DuckDuckGo]\n{ddg_out}")
    if wiki_out:
        combined.append(f"[Encyclopedia Sources]\n{wiki_out}")
    if combined:
        return "\n\n".join(combined)

    return f"No external search results found for '{query}'. Please use internal knowledge and logical reasoning."
