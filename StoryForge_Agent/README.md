# StoryForge Agent

StoryForge Agent is a Streamlit app that turns any topic into a research brief: it searches the live web with [Tavily](https://tavily.com), summarizes the findings with a Hugging Face-hosted LLM, and can spin the summary into a short-form video script (YouTube Shorts / Instagram Reels style). The same research pipeline is also exposed as an [MCP](https://modelcontextprotocol.io) server so it can be called as a tool from any MCP-compatible client (Claude Desktop, Claude Code, etc.).

## Features

- **Live web search** — queries [Tavily](https://tavily.com) with configurable focus (`General` / `News` / `Finance`), result count, and time range.
- **AI summaries** — condenses search results into a human-readable brief with three styles: Concise, Balanced, Detailed.
- **Video script generation** — converts a summary into a ~100-120 word short-form video script with a hook and call-to-action.
- **Search history** — recent queries are cached in-session and can be revisited or cleared from the sidebar.
- **Downloadable output** — summaries and scripts can be downloaded as `.txt` files.
- **MCP server** — the same fetch/summarize/script pipeline is exposed as MCP tools over stdio for use in agentic workflows.

## Architecture

```
                         ┌────────────────────┐
                         │   Tavily Search API │
                         └─────────▲──────────┘
                                   │ fetch_search_results()
┌───────────────┐   imports   ┌────┴─────┐   chat_completion()   ┌──────────────────────┐
│   app.py       │────────────▶  core.py │───────────────────────▶ Hugging Face Inference │
│ (Streamlit UI) │            └────┬─────┘                        │ (Qwen2.5 / Llama 3.3) │
└───────────────┘                 │                                └──────────────────────┘
                                   │ imports
                         ┌─────────┴──────────┐
                         │   mcp_server.py     │
                         │ (FastMCP, stdio)    │
                         └────────────────────┘
```

`core.py` is the shared engine — both the Streamlit UI (`app.py`) and the MCP server (`mcp_server.py`) call into it, so search/summarization/script logic lives in exactly one place.

## Tech stack

| Layer            | Technology                                                                 |
|-------------------|-----------------------------------------------------------------------------|
| UI                | [Streamlit](https://streamlit.io) `>=1.60.0`                               |
| Web search        | [Tavily](https://pypi.org/project/tavily-python/) (`tavily-python`)         |
| LLM inference     | [Hugging Face Inference Client](https://pypi.org/project/huggingface-hub/) (`huggingface-hub`) |
| Summarization model | `Qwen/Qwen2.5-7B-Instruct`                                                |
| Script model      | `meta-llama/Llama-3.3-70B-Instruct`                                         |
| Agent protocol    | [Model Context Protocol](https://modelcontextprotocol.io) (`mcp[cli]`), stdio transport |
| Config            | `python-dotenv`                                                            |
| Package manager   | [uv](https://docs.astral.sh/uv/) (`uv.lock`, `pyproject.toml`)             |
| Runtime           | Python `>=3.12`                                                            |

## Project structure

```
StoryForge_Agent/
├── app.py              # Streamlit UI: search form, tabs (summary / sources / script), history
├── core.py              # Shared engine: Tavily search, HF summarization, script generation
├── mcp_server.py         # FastMCP server exposing fetch_news_mcp / generate_script as MCP tools
├── pyproject.toml        # Project metadata and dependencies (uv-managed)
├── requirements.txt       # Plain pip-installable dependency list
├── uv.lock               # Locked dependency versions
├── .streamlit/config.toml # Dark theme configuration for the Streamlit UI
├── .python-version        # Pinned Python version (3.12)
└── .env                  # HF_TOKEN / TAVILY_API_KEY (not committed)
```

## Prerequisites

- Python 3.12+
- A [Hugging Face](https://huggingface.co/settings/tokens) access token with Inference API access
- A [Tavily](https://app.tavily.com) API key

## Setup

1. **Clone and enter the project**

   ```bash
   git clone https://github.com/KoushikBose/MCP_PROJECT.git
   cd MCP_PROJECT/StoryForge_Agent
   ```

2. **Install dependencies**

   Using [uv](https://docs.astral.sh/uv/) (recommended, matches the committed lockfile):

   ```bash
   uv sync
   ```

   Or with plain `pip`:

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # .venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

3. **Configure credentials**

   Create a `.env` file in `StoryForge_Agent/`:

   ```env
   HF_TOKEN="your_huggingface_token"
   TAVILY_API_KEY="your_tavily_api_key"
   ```

   The app checks for both variables on startup and shows an error in the UI if either is missing.

## Running the app

```bash
streamlit run app.py
```

Then open the URL Streamlit prints (typically `http://localhost:8501`).

### Using the app

1. Type a topic in the search box, or click one of the example chips.
2. Adjust search settings in the sidebar: focus area, number of sources, time range, and summary style.
3. Click **Search** to fetch sources and generate a summary.
4. Use the tabs to read the **Summary**, browse **Sources**, or generate a **Video script** from the summary.
5. Download the summary or script as a `.txt` file, or revisit a past query from **Recent searches**.

## Running the MCP server

The MCP server exposes the same research pipeline as tools over stdio, for use with MCP-compatible clients:

```bash
python mcp_server.py
```

### Exposed tools

| Tool               | Parameters                                                              | Description                                                        |
|---------------------|--------------------------------------------------------------------------|----------------------------------------------------------------------|
| `fetch_news_mcp`     | `query: str`, `topic: str = "General"`, `max_results: int = 5`, `time_range: str = "Any time"` | Fetches real-time search results for a query via Tavily.            |
| `generate_script`    | `query: str`, `topic: str = "General"`, `max_results: int = 5`, `time_range: str = "Any time"` | Fetches real-time results for a query and turns them into a short video script. |

To use it from an MCP client (e.g. Claude Desktop), point the client at `mcp_server.py` with the `stdio` transport and ensure `HF_TOKEN` / `TAVILY_API_KEY` are available in its environment.

## Core module reference (`core.py`)

- `get_clients()` — lazily constructs and caches (`lru_cache`) the `InferenceClient` and `TavilyClient` instances; raises `RuntimeError` if credentials are missing.
- `fetch_search_results(query, topic, max_results, time_range)` — runs a Tavily search and returns the raw list of result dicts.
- `build_source_text(results, query)` — flattens search results into a single text block used as LLM context.
- `summarize(query, source_text, style)` — calls the summarization model (`Qwen/Qwen2.5-7B-Instruct`) with a style-specific prompt (`Concise` / `Balanced` / `Detailed`) and returns the generated summary.
- `generate_script(info_text)` — calls the script model (`meta-llama/Llama-3.3-70B-Instruct`) to turn a summary into a short-form video script.

## Notes

- `.env`, `.venv`, and `__pycache__` are excluded from version control via `.gitignore` — never commit real API keys.
- The summarization and script models are called through the Hugging Face Inference API, so usage is subject to Hugging Face's inference rate limits/quotas for your account.
