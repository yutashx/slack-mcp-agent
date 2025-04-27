import os
import asyncio
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.aiohttp import AsyncSocketModeHandler
from utils import format_slack_event, agent_behavior_prompt
import json
import datetime
from agents import Agent, Runner, function_tool
from agents.mcp import MCPServerStdio

AGENT_MAX_STEP = 15

# 初期化
with open("./config.json", "r") as f:
    config = json.load(f)

mcp_servers = config["mcpServers"]
env = config["env"]

app = AsyncApp(token=env["SLACK_BOT_TOKEN"])

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
    async with MCPServerStdio(params=mcp_servers["slack"] , cache_tools_list=True, client_session_timeout_seconds=15) as slack, \
               MCPServerStdio(params=mcp_servers["notion"], cache_tools_list=True, client_session_timeout_seconds=15) as notion, \
               MCPServerStdio(params=mcp_servers["perplexity-ask"], cache_tools_list=True, client_session_timeout_seconds=30) as perplexity:
        instructions = agent_behavior_prompt(env["SLACK_USER_ID"])
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
            model=env["LLM_MODEL"],
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
    handler = AsyncSocketModeHandler(app, env["SLACK_APP_TOKEN"])
    await handler.start_async()


if __name__ == "__main__":
    asyncio.run(main())