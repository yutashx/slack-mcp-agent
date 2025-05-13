import datetime
from agents import function_tool

@function_tool
async def clock() -> str:
    """Get current time in JST."""
    print("call clock")
    t = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return t

@function_tool
async def get_str_lenth(text: str) -> int:
    """Get the length of a string."""
    print("call get_str_lenth")
    return len(text)

@function_tool
async def read_stdout() -> str:
    print("call read_stdout")
    with open("./log/stdout.log", "r") as f:
        return f.readlines()

@function_tool
async def read_stderr() -> str:
    print("call read_stderr")
    with open("./log/stderr.log", "r") as f:
        return f.readlines()