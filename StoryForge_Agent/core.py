import os
from functools import lru_cache

from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from tavily import TavilyClient

load_dotenv()

MODEL_INFO = "Qwen/Qwen2.5-7B-Instruct"
MODEL_SCRIPT = "meta-llama/Llama-3.3-70B-Instruct"

STYLES = {
    "Concise": {"instruction": "Keep it tight and scannable, around 120-150 words.", "max_tokens": 700},
    "Balanced": {"instruction": "Aim for a well-rounded summary of around 200 words.", "max_tokens": 900},
    "Detailed": {
        "instruction": "Provide a thorough, well-structured summary of around 300-350 words.",
        "max_tokens": 1200,
    },
}

HF_TOKEN = os.getenv("HF_TOKEN")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


@lru_cache
def get_clients() -> tuple[InferenceClient, TavilyClient]:
    if not HF_TOKEN or not TAVILY_API_KEY:
        raise RuntimeError("Missing API credentials. Set HF_TOKEN and TAVILY_API_KEY in your .env file.")
    return InferenceClient(api_key=HF_TOKEN), TavilyClient(api_key=TAVILY_API_KEY)


def fetch_search_results(
    query: str, topic: str = "General", max_results: int = 5, time_range: str = "Any time"
) -> list[dict]:
    _, tavily_client = get_clients()
    kwargs = {"query": query, "max_results": max_results, "topic": topic.lower()}
    if time_range != "Any time":
        kwargs["time_range"] = time_range.lower()
    resp = tavily_client.search(**kwargs)
    return (resp.get("results") or []) if resp else []


def build_source_text(results: list[dict], query: str) -> str:
    if not results:
        return f"No relevant information found for '{query}'."
    parts = []
    for r in results:
        title = str(r.get("title") or "")
        snippet = str(r.get("content") or "")
        url = str(r.get("url") or "")
        parts.append(f"Title: {title}\nSnippet: {snippet}\nURL: {url}")
    return "\n\n----\n\n".join(parts)


def summarize(query: str, source_text: str, style: str) -> str:
    hf_client, _ = get_clients()
    prompt = f"""
You are a professional researcher and content creator with expertise in multiple fields.
Using the following real-time information, write an accurate, engaging, and human-like summary
for the topic: '{query}'.

Requirements:
- {STYLES[style]["instruction"]}
- Maintain a smooth, natural tone.
- Highlight key takeaways or trends.
- Avoid greetings or self-references.

Source information:
{source_text}

Output only the refined, human-readable content.
"""
    response = hf_client.chat_completion(
        model=MODEL_INFO,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=STYLES[style]["max_tokens"],
    )
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("The model returned an empty summary. Try again or pick a shorter style.")
    return content


def generate_script(info_text: str) -> str:
    hf_client, _ = get_clients()
    prompt = f"""
You are a creative scriptwriter.
Turn this real-time information into an engaging short video script (for YouTube Shorts or Instagram Reels).
Use a conversational tone with a strong hook and a clear call to action at the end.
Keep it around 100-120 words.

Source information:
{info_text}
"""
    response = hf_client.chat_completion(
        model=MODEL_SCRIPT,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000,
    )
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("The model returned an empty script. Please try again.")
    return content
