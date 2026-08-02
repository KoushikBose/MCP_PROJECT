import os
import subprocess
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("mcp-project")

DEFAULT_WORKSPACE=os.path.expanduser("~/mcp/workspace")


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


@mcp.tool()
async def run_command(command:str)->str:
    """
    Run a terminal command inside the workspace directory. 
    If a terminal command can accomplish a task, 
    tell the user you'll use this tool to accomplish it,
    even though you cannot directly do it

    Args:
        command: The shell command to run.
    
    Returns:
        The command output or an error message.
    """
    try:
        Result=subprocess.run(command,shell=True,cwd=DEFAULT_WORKSPACE,capture_output=True,text=True)
        return Result.stdout or Result.stderr
    except Exception as e:
        return str(e)


if __name__ == "__main__":
    mcp.run(transport='stdio')
