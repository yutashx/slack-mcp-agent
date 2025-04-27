import os
import asyncio
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.aiohttp import AsyncSocketModeHandler
from mcp_use import MCPClient, MCPAgent
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from utils import format_slack_event, agent_behavior_prompt
import json
import datetime
from agents import Agent, Runner, function_tool, WebSearchTool
from agents.mcp import MCPServerStdio
import contextlib, io

# .env ファイルから環境変数を読み込む
load_dotenv()

# 環境変数の取得
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
MCP_SERVER_CONFIG_PATH = os.getenv("MCP_SERVER_CONFIG_PATH")
AGENT_MAX_STEP = int(os.getenv("AGENT_MAX_STEP", 15))

# 初期化
app = AsyncApp(token=SLACK_BOT_TOKEN)
with open(MCP_SERVER_CONFIG_PATH, "r") as f:
    mcp_servers = json.load(f)["mcpServers"]

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

# メンションイベントのハンドリング
@app.event("app_mention")
async def handle_app_mention(event, say):
    print(f"Event: {event}") 

    async with MCPServerStdio(params=mcp_servers["slack"] , cache_tools_list=True, client_session_timeout_seconds=15) as slack, \
               MCPServerStdio(params=mcp_servers["notion"], cache_tools_list=True, client_session_timeout_seconds=15) as notion, \
               MCPServerStdio(params=mcp_servers["perplexity-ask"], cache_tools_list=True, client_session_timeout_seconds=30) as perplexity:
        instructions = agent_behavior_prompt(os.getenv("SLACK_USER_ID"))
        agent = Agent(
            name="Tachikoma Assistant",
            instructions=instructions,
            mcp_servers=[
                slack,
                notion,
                perplexity
            ],
            tools=[
                clock,
                get_str_lenth,
                read_stdout,
                read_stderr,
            ],
            model="gpt-4o-mini",
        )

        try:
            result = await Runner.run(
                agent,
                input=format_slack_event(event),
            )
            if result.final_output:
                print(f"Sending reply to {event['channel']} thread {event['ts']}: {result.final_output}")
        except Exception as e:
                await say(text=f"[ERROR] {e}", thread_ts=event["ts"])

# アプリの起動
async def main():
    handler = AsyncSocketModeHandler(app, SLACK_APP_TOKEN)
    await handler.start_async()


if __name__ == "__main__":
    asyncio.run(main())