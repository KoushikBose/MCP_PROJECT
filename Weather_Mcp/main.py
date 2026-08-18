from mcp.server.fastmcp import FastMCP
from tools.weather import get_weather_data

mcp = FastMCP("Weather Checker")

@mcp.tool()
async def check_weather(location: str) -> str:
    """
    Gets Weather Information For a Specified Location.
        
    """
    return get_weather_data(location)

if __name__=="__main__":
    mcp.run(transport='stdio')











#DEFAULT_WORKSPACE=os.path.expanduser("~/mcp/workspace")


# @mcp.tool()
# def add(a: int, b: int) -> int:
#     """Add two numbers together."""
#     return a + b


# @mcp.tool()
# async def run_command(command:str)->str:
#     """
#     Run a terminal command inside the workspace directory. 
#     If a terminal command can accomplish a task, 
#     tell the user you'll use this tool to accomplish it,
#     even though you cannot directly do it

#     Args:
#         command: The shell command to run.
    
#     Returns:
#         The command output or an error message.
#     """
#     try:
#         Result=subprocess.run(command,shell=True,cwd=DEFAULT_WORKSPACE,capture_output=True,text=True)
#         return Result.stdout or Result.stderr
#     except Exception as e:
#         return str(e)

    


if __name__ == "__main__":
    mcp.run(transport='stdio')
