# Weather MCP Server

A minimal [Model Context Protocol](https://modelcontextprotocol.io) server that exposes a single tool — `check_weather` — letting any MCP-compatible client (Claude Desktop, Claude Code, etc.) fetch current weather conditions for a location in natural language.

## Architecture

```
┌────────────────┐   stdio (JSON-RPC)   ┌───────────────┐   HTTPS    ┌───────────┐
│  MCP Client     │ ───────────────────► │  main.py       │ ─────────► │ wttr.in   │
│ (Claude, etc.)  │ ◄─────────────────── │  (FastMCP)     │ ◄───────── │  (weather │
└────────────────┘                       └───────┬────────┘             service) │
                                                   │                    └───────────┘
                                                   ▼
                                          tools/weather.py
                                          get_weather_data()
```

- **`main.py`** — Entry point. Instantiates a `FastMCP` server named `"Weather Checker"` and registers `check_weather` as an MCP tool via the `@mcp.tool()` decorator. The server communicates over **stdio**, so it's designed to be launched as a subprocess by an MCP host rather than run as a standalone network service.
- **`tools/weather.py`** — Contains `get_weather_data(location)`, a synchronous function that queries [wttr.in](https://wttr.in) (a free, no-key-required weather API) and returns a one-line summary (`format=3`, e.g. `London: ☀️ +22°C`).

## Data flow

1. The MCP client sends a `tools/call` request for `check_weather` with a `location` string argument.
2. `main.py`'s `check_weather` handler (async) calls the synchronous `get_weather_data`.
3. `get_weather_data` URL-encodes the location, issues a `GET` to `https://wttr.in/<location>?format=3` with a `curl/8.0` User-Agent (wttr.in blocks requests without a recognized UA), and reads the response with a 10s timeout.
4. The result string is returned unmodified to the MCP client. Any exception is caught and returned as `"Error:<message>"` rather than raised, so the tool call never throws — it always yields a text result.

## Project layout

```
Weather_Mcp/
├── main.py              # MCP server entry point, tool registration
├── tools/
│   ├── __init__.py       # (empty) package marker
│   └── weather.py        # get_weather_data(): wttr.in HTTP client
├── pyproject.toml        # project metadata + dependencies (uv-managed)
├── requirements.txt      # pip-compatible dependency list
└── uv.lock               # locked dependency versions
```

## Requirements

- Python >= 3.12
- Dependencies (see `pyproject.toml` / `requirements.txt`):
  - `mcp[cli]` — MCP server SDK (FastMCP)
  - `python-dotenv` — environment variable loading
  - `pandas`

## Setup

Using [uv](https://docs.astral.sh/uv/) (recommended, matches `uv.lock`):

```bash
uv sync
```

Or with pip:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Running

The server speaks MCP over stdio, so it isn't meant to be run interactively on its own — an MCP host launches it as a subprocess. To smoke-test it directly:

```bash
python main.py
```

To test the weather-fetching logic in isolation:

```bash
python tools/weather.py
# -> London: ☀️ +22°C
```

## Registering with an MCP client

Add an entry to the client's MCP server config (e.g. Claude Desktop's `claude_desktop_config.json`) pointing at this project's interpreter and `main.py`:

```json
{
  "mcpServers": {
    "weather": {
      "command": "python",
      "args": ["c:/Users/koush/OneDrive/Desktop/Mcp_Project/Weather_Mcp/main.py"]
    }
  }
}
```

Once connected, the client can invoke the `check_weather` tool with a `location` argument (e.g. `"Amsterdam"`, `"New York"`) and receive a one-line weather summary.

## Tool reference

| Tool | Argument | Returns | Description |
|---|---|---|---|
| `check_weather` | `location: str` | `str` | Current weather for the given city, formatted as `"<city>: <condition emoji> <temperature>"`. Returns `"Error:<message>"` on failure (invalid location, network error, timeout). |

## Notes

- `wttr.in` is queried without an API key; it rate-limits aggressively for automated/no-UA traffic, hence the spoofed `curl/8.0` User-Agent.
- `.env` is gitignored — if `python-dotenv` is used to load secrets, none are required for the current `check_weather` tool.
