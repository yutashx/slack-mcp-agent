import os
import asyncio
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.aiohttp import AsyncSocketModeHandler
from mcp_use import MCPClient, MCPAgent
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from utils import format_slack_event, agent_behavior_prompt

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
client = MCPClient.from_config_file(MCP_SERVER_CONFIG_PATH)
llm = ChatOpenAI(model=LLM_MODEL)

# session cache
session_cache = {}

# メンションイベントのハンドリング
@app.event("app_mention")
async def handle_app_mention(event, say):
    user_id = event["user"]
    text = event["text"]
    channel = event["channel"]
    thread_ts = event.get("thread_ts", event["ts"])
    print(f"Received mention from {user_id} in channel {channel}: {text}")
    print(event)

    agent = None
    # セッションキャッシュの確認
    if thread_ts in session_cache:
        agent = session_cache[thread_ts]
    else:
        agent = MCPAgent(
            llm=llm,
            client=client,
            max_steps=AGENT_MAX_STEP,
            memory_enabled=True,
            verbose=True,
        )
        session_cache[thread_ts] = agent

    try:
        # Run the agent with the user input (memory handling is automatic)
        agent_prompt = agent_behavior_prompt() + "\n" + format_slack_event(event)
        response = await agent.run(agent_prompt)
        print(response)
    except Exception as e:
        print(f"\nError: {e}")

    # 結果を返信
    await say(text=response, thread_ts=thread_ts)
    print(f"Replied to {user_id} in channel {channel}: {response}")

# アプリの起動
async def main():
    handler = AsyncSocketModeHandler(app, SLACK_APP_TOKEN)
    await handler.start_async()



if __name__ == "__main__":
    asyncio.run(main())