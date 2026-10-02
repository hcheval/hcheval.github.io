# Lab 13: MCP Servers

The Model Context Protocol (MCP) is a standard for connecting AI coding assistants to external tools and data sources. An MCP server exposes tools that the assistant can discover and call at runtime, which means capabilities live outside the assistant itself and can be added, removed, or swapped without touching the assistant's code. We will build a small weather server in Python, expose it over two different transports (local stdio and remote HTTP), and wire both into opencode to see how each one behaves.

The weather data is hardcoded and uninteresting on purpose, since what matters here is the protocol mechanics: how tools get declared, how the assistant discovers them, and what happens at the transport layer when things go wrong.


## Setup

```bash
mkdir mcp-demo && cd mcp-demo
python -m venv .venv && source .venv/bin/activate
pip install mcp
```

Opencode should already be installed and working from previous labs.


## The server

Create `weather_server.py`. The entire server fits in one file because the SDK handles all the protocol negotiation, and a `--transport` flag at the bottom selects between stdio and HTTP so the tool logic stays identical regardless of how the client connects:

```python
import argparse
from mcp.server.fastmcp import FastMCP

parser = argparse.ArgumentParser()
parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio")
parser.add_argument("--port", type=int, default=8080)
args = parser.parse_args()

mcp = FastMCP("weather", host="127.0.0.1", port=args.port)

@mcp.tool()
def get_weather(city: str) -> str:
    """Return the current weather for a city."""
    data = {
        "london":   "12C, overcast",
        "tokyo":    "24C, sunny",
        "new york": "18C, partly cloudy",
        "paris":    "15C, light rain",
    }
    result = data.get(city.lower())
    return f"Weather in {city}: {result}" if result else f"No data for {city}."

@mcp.tool()
def list_cities() -> list[str]:
    """List all cities with available weather data."""
    return ["London", "Tokyo", "New York", "Paris"]

if __name__ == "__main__":
    mcp.run(transport=args.transport)
```

`@mcp.tool()` is the only thing needed to register a function. The SDK infers the tool's name, parameter types, and description from the function signature and docstring, which is also all the information the assistant will see when it decides whether to call it.


## Stdio transport

Try running the server directly:

```bash
python weather_server.py --transport stdio
```

Nothing visible happens, which is expected: the server is waiting on stdin for JSON-RPC messages because in stdio mode the host process spawns it as a subprocess and pipes messages to it. `Ctrl-C` to kill it.

To register it with opencode, create (or edit) `opencode.jsonc` in the project root:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "weather-local": {
      "type": "local",
      "command": ["/absolute/path/to/mcp-demo/.venv/bin/python",
                  "/absolute/path/to/mcp-demo/weather_server.py",
                  "--transport", "stdio"],
      "enabled": true
    }
  }
}
```

Both paths must be absolute because opencode spawns the process from its own working directory, and the Python binary must point into the venv where `mcp` is installed rather than the system Python. Launch opencode and try:

```
use the weather-local tool to get the weather in Tokyo
```

Opencode spawns the server process, sends a `get_weather` call over stdin, reads the result from stdout, and kills the process when the session ends.


## HTTP transport

Open a second terminal and start the server in HTTP mode, where it stays alive independently of any client:

```bash
python weather_server.py --transport sse --port 8080
```

The server should print a startup message and start listening on port 8080. The endpoint opencode will connect to is `http://localhost:8080/sse`.

Add a second entry alongside the local one in `opencode.jsonc`:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "weather-local": {
      "type": "local",
      "command": ["/absolute/path/to/mcp-demo/.venv/bin/python",
                  "/absolute/path/to/mcp-demo/weather_server.py",
                  "--transport", "stdio"],
      "enabled": true
    },
    "weather-remote": {
      "type": "remote",
      "url": "http://localhost:8080/sse",
      "enabled": true
    }
  }
}
```

Restart opencode (config is read at startup, not live-reloaded) and prompt:

```
use the weather-remote tool to list available cities
```

With both entries enabled, both servers are available in the same opencode session. The behaviour is identical, only the transport differs: stdio is tied to the client session, while a remote server runs independently and could just as well be on a different machine (the URL would simply point to a real host instead of localhost).


## Adding a tool

### Exercise 1

Add a third tool to the server, `get_forecast(city: str, days: int) -> str`, that returns a made-up multi-day forecast (something along the lines of "Day 1: 14C rain, Day 2: 16C cloudy"). After restarting opencode, verify that the assistant discovers the new tool and can call it without any changes to `opencode.jsonc`, since tool discovery happens at connection time through the protocol itself.

Then try prompting opencode with just "what's the weather going to be like in Tokyo this week" and observe whether it figures out on its own which tool to call and what arguments to pass. The docstring and type signature are the only information guiding that decision.


## Real data

### Exercise 2

Replace the hardcoded weather dictionary with a call to the open-meteo API, which we already used in Lab 1 and which requires no authentication:

```
https://api.open-meteo.com/v1/forecast?latitude=48.85&longitude=2.35&current_weather=true
```

The server should map city names to coordinates through a hardcoded dictionary (5-10 cities is enough), call the API with `urllib.request` or `httpx`, and return the actual temperature and weather code. Test through opencode to confirm it works end-to-end, and check what happens when the API is unreachable or the city is not in the dictionary.


## Resources

MCP servers can also expose resources, which are read-only data that the assistant pulls into its context. A tool is something the assistant calls to perform an action, whereas a resource is something it reads for background information. The decorator works similarly:

```python
@mcp.resource("notes://summary")
def project_summary() -> str:
    """A short summary of the project."""
    return "This project is a weather MCP server for demonstration purposes."
```

Resources can also be templated with URI parameters, so `"notes://{topic}"` would let the assistant request different topics by name.

### Exercise 3

Add two or three resources to the weather server: a static one (e.g. `"weather://info"` returning a description of what cities and data the server covers) and a templated one (e.g. `"weather://history/{city}"` returning some made-up historical averages for a given city). Restart opencode and ask it a question that requires both a resource read and a tool call, such as "what cities do we have data for and what's the weather in the warmest one?" Observe how the assistant decides which to use.
