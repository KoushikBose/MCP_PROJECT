from mcp.server.fastmcp import FastMCP

from core import build_source_text, fetch_search_results
from core import generate_script as generate_video_script

mcp = FastMCP("This Is For Real Time News")


@mcp.tool()
async def fetch_news_mcp(
    query: str, topic: str = "General", max_results: int = 5, time_range: str = "Any time"
) -> list[dict]:
    """Fetches real-time news search results for a query."""
    return fetch_search_results(query=query, topic=topic, max_results=max_results, time_range=time_range)


@mcp.tool()
async def generate_script(
    query: str, topic: str = "General", max_results: int = 5, time_range: str = "Any time"
) -> str:
    """Fetches real-time news for a query and turns it into a short video script."""
    results = await fetch_news_mcp(query=query, topic=topic, max_results=max_results, time_range=time_range)
    source_text = build_source_text(results, query)
    return generate_video_script(source_text)


if __name__ == "__main__":
    mcp.run(transport="stdio")
