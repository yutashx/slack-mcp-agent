import os
import json
import asyncio
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.aiohttp import AsyncSocketModeHandler
from agents import Agent, Runner, function_tool
from agents.mcp import MCPServerStdio
from utils import format_slack_event, agent_behavior_prompt
from tools import clock, get_str_lenth, read_stdout, read_stderr

# 設定ファイルの読み込み
with open("./config.json", "r") as f:
    config = json.load(f)

mcp_servers = config["mcpServers"]
env = config["env"]

# Slack Botの立ち上げ
app = AsyncApp(token=env["SLACK_BOT_TOKEN"])

# メンションイベントのハンドリング
@app.event("app_mention")
async def handle_app_mention(event, say):
    async with MCPServerStdio(params=mcp_servers["slack"] , cache_tools_list=True, client_session_timeout_seconds=15) as slack, \
               MCPServerStdio(params=mcp_servers["notion"], cache_tools_list=True, client_session_timeout_seconds=15) as notion, \
               MCPServerStdio(params=mcp_servers["perplexity-ask"], cache_tools_list=True, client_session_timeout_seconds=30) as perplexity:
        instructions = agent_behavior_prompt(env["SLACK_USER_ID"])
        agent = Agent(
            name="AI Assistant",
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

async def main():
    handler = AsyncSocketModeHandler(app, env["SLACK_APP_TOKEN"])
    await handler.start_async()

if __name__ == "__main__":
    asyncio.run(main())