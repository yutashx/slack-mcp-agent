from azure_blob_sqlite_client import AzureBlobSQLiteClient
from local_sqlite_client import LocalSQLiteClient

class DBClient:
    def __init__(self, env: dict):
        self.env = env
        if env.get("DB_TYPE") == "azure_blob":
            self.client = AzureBlobSQLiteClient(env)
        elif env.get("DB_TYPE") == "local":
            self.client = LocalSQLiteClient(env)
        else:
            raise ValueError(f"DB_TYPE must be either 'azure_blob' or 'local': {env.get('DB_TYPE')}")

    def cron_start(self):
        self.client.cron_start()

    def cron_end(self):
        self.client.cron_end()

    def upload(self):
        self.client.upload()

    def download(self):
        self.client.download()

    def query(self, sql, params=None):
        return self.client.query(sql, params)

    def get_schema(self):
        return self.client.get_schema()
