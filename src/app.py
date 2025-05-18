import json
import asyncio
import os
import contextlib
import logging
import signal
from agents import Agent, Runner, set_default_openai_client, set_tracing_disabled
from agents.mcp import MCPServerStdio
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.aiohttp import AsyncSocketModeHandler
from aiohttp import web
from tools import clock, get_str_lenth, Tool
from utils import format_slack_event, agent_behavior_prompt
from aiclient import AIClient
from dbclient import DBClient

# 設定ファイルの読み込み
with open(os.environ.get("CONFIG_PATH", "../config.json"), "r") as f:
    config = json.load(f)

mcp_servers = config["mcpServers"]
env = config["env"]

# Slack Botの立ち上げ
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("./log/app.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)
app = AsyncApp(token=env["SLACK_BOT_TOKEN"], logger=logger)

# AI Clientの初期化
aiclient = AIClient(provider=env["LLM_PROVIDER"], env=env)
set_default_openai_client(aiclient.client)
set_tracing_disabled(aiclient.tracing_disabled)

# SQLiteClientの初期化
dbclient = DBClient(env)
dbclient.download()
dbclient.cron_start()
tool = Tool(dbclient)

# Slack Botのハンドリング
# メンションイベントのハンドリング
@app.event("app_mention")
async def handle_app_mention(event, say):
    async with contextlib.AsyncExitStack() as stack:
        # mcpServersのkey分だけMCPServerStdioを動的に生成し、ExitStackに登録
        servers = []
        for _, params in mcp_servers.items():
            server = await stack.enter_async_context(
                MCPServerStdio(params=params, cache_tools_list=True, client_session_timeout_seconds=60)
            )
            servers.append(server)

        # serversリストを使ってAgentを生成
        db_table_info = "利用できるDBテーブルは以下です。\n" + dbclient.get_schema()
        instructions = agent_behavior_prompt(env["SLACK_USER_ID"], env["LLM_MODEL"]) + db_table_info
        agent = Agent(
            name="AI Assistant",
            instructions=instructions,
            mcp_servers=servers,
            tools=[
                clock,
                get_str_lenth,
                tool.agent_log_reader,
                tool.db_query,
            ],
            model=env["LLM_MODEL"],
        )

        try:
            result = await Runner.run(
                agent,
                input=format_slack_event(event),
            )
            if result.final_output:
                #logger.info(f"Sending reply to {event['channel']} thread {event['ts']}: {result.final_output}")
                await say(text="--- done ---", thread_ts=event["ts"])
        except Exception as e:
            logger.exception("Error in handle_app_mention")
            await say(text=f"[ERROR] {e}", thread_ts=event["ts"])

@app.event("message")
async def handle_message_events(body, logger):
    logger.info(body)

# 動作確認用のページ
web_app = app.web_app()

async def index(request):
    revision_name = os.environ.get("K_REVISION", "unknown")
    return web.Response(text=f"Revision: {revision_name}")

web_app.router.add_get("/", index)

async def start_sock_mode():
    handler = AsyncSocketModeHandler(app, env["SLACK_APP_TOKEN"])
    await handler.start_async()

async def main():
    # SIGTERM時のハンドラ
    signal.signal(signal.SIGTERM, lambda signum, frame: dbclient.upload())

    # SocketModeをバックグラウンドで起動
    sock_mode_task = asyncio.create_task(start_sock_mode())
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(env["PORT"]))
    await site.start()
    logger.info(f"start app on port {env['PORT']}")
    await sock_mode_task

if __name__ == "__main__":
    asyncio.run(main())
