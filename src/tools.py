import datetime
from agents import function_tool
from dbclient import DBClient

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


class Tool:
    def __init__(self, db_client: DBClient):
        self.db_client = db_client

        # function toolのschema定義に合わせるために、インスタンス変数を使ったラップ関数にする
        @function_tool
        async def db_query(query: str) -> str:
            """Query the database."""
            print("call db_query")
            return self.db_client.query(query)
        self.db_query = db_query

        @function_tool
        async def get_db_schema() -> str:
            """Get the schema of the database."""
            print("call get_db_schema")
            return self.db_client.get_schema()
        self.get_db_schema = get_db_schema

        @function_tool
        async def agent_log_reader() -> str:
            """Read the log file."""
            print("call agent_log_reader")
            with open("./log/app.log", "r") as f:
                return f.read()
        self.agent_log_reader = agent_log_reader