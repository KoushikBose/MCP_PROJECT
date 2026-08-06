import os
from urllib.parse import urlparse

from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

_client: TavilyClient | None = None

# Official U.S. government / nonprofit medical sources, preferred over
# general-interest health content sites so cited results stay authoritative.
US_MEDICAL_AGENCY_DOMAINS = [
    "cdc.gov",
    "nih.gov",
    "ncbi.nlm.nih.gov",
    "medlineplus.gov",
    "fda.gov",
    "womenshealth.gov",
    "mayoclinic.org",
    "clevelandclinic.org",
    "hhs.gov",
    "ahrq.gov",
    "who.int",
    "jamanetwork.com",
    "nejm.org",
    "thelancet.com",
    "cochranelibrary.com",
]


def _get_client() -> TavilyClient:
    global _client
    if _client is None:
        _client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    return _client


def _is_allowed_domain(url: str, domains: list[str]) -> bool:
    netloc = urlparse(url).netloc.lower()
    return any(netloc == domain or netloc.endswith(f".{domain}") for domain in domains)


def fetch_web_results(
    query: str,
    max_results: int = 5,
    include_domains: list[str] | None = US_MEDICAL_AGENCY_DOMAINS,
) -> list[dict]:
    """
    Searches the web for the given query using Tavily, restricted to trusted
    U.S. medical agency domains, and returns a list of
    {title, content, url, score} results.
    """
    try:
        # Tavily's include_domains only biases ranking rather than hard-filtering,
        # so over-fetch and enforce the domain restriction ourselves below.
        request_size = max_results * 4 if include_domains else max_results
        response = _get_client().search(
            query,
            search_depth="basic",
            max_results=request_size,
            include_answer=False,
            include_domains=include_domains,
        )
        results = [
            {
                "title": item.get("title") or "Untitled",
                "content": item.get("content") or "No summary available.",
                "url": item.get("url", ""),
                "score": item.get("score", 0.0),
            }
            for item in response.get("results", [])
        ]
        if include_domains:
            results = [r for r in results if _is_allowed_domain(r["url"], include_domains)]
        return results[:max_results]
    except Exception as e:
        print(f"Error during Tavily search: {e}")
        return []


if __name__ == "__main__":
    output = fetch_web_results("fever headache treatment")
    print(output)
