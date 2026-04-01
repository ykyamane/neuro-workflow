# server.py
import sys, logging
from mcp.server.fastmcp import FastMCP

# set up logging to stderr and to a file
logger = logging.getLogger("mcp-server")
logger.setLevel(logging.DEBUG)
fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

stderr_h = logging.StreamHandler(sys.stderr)
stderr_h.setFormatter(fmt)
file_h = logging.FileHandler("server.log", encoding="utf-8")
file_h.setFormatter(fmt)

logger.handlers.clear()
logger.addHandler(stderr_h)
logger.addHandler(file_h)

mcp = FastMCP("demo")

@mcp.tool()
def add(a: int, b: int) -> int:
    """
    Add two integers and return the sum.

    When to use:
      - Any arithmetic addition request, including multi-step math where a sum is needed.

    Constraints:
      - Only integers. For floats, round first or ask the user to confirm.

    Examples:
      add(a=2, b=40) -> 42
      add(a=321, b=123) -> 444
    """
    logger.debug(f"add() called with a={a}, b={b}")
    return a + b

@mcp.tool()
def echo(text: str) -> str:
    """
    Return the same text that was passed in.

    When to use:
      - The user asks to reflect, quote, or transform exactly without changes.

    Examples:
      echo(text="MCP works") -> "MCP works"
    """
    logger.debug(f"echo() called with text={text!r}")
    return text

if __name__ == "__main__":
    logger.debug("MCP server starting...")
    mcp.run("stdio")

