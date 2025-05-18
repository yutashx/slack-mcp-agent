import os
import logging
import sqlite3

class LocalSQLiteClient:
    def __init__(self, env: dict):
        self.env = env
        self.db_path = env.get("SQLITE_DB_PATH", "./db/app.db")
        self.logger = logging.getLogger(__name__)

    def cron_start(self):
        """(ダミー) AzureBlobSQLiteClientと同じインターフェース用"""
        self.logger.info("[LocalSQLiteClient] cron_start called (noop)")

    def cron_end(self):
        """(ダミー) AzureBlobSQLiteClientと同じインターフェース用"""
        self.logger.info("[LocalSQLiteClient] cron_end called (noop)")

    def upload(self):
        """(ダミー) AzureBlobSQLiteClientと同じインターフェース用"""
        self.logger.info("[LocalSQLiteClient] upload called (noop)")

    def download(self):
        """(ダミー) AzureBlobSQLiteClientと同じインターフェース用"""
        self.logger.info("[LocalSQLiteClient] download called (noop)")

    def query(self, sql, params=None):
        """データベースをクエリする"""
        self.logger.info(f"Executing query: {sql} | params: {params}")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                if params:
                    cur.execute(sql, params)
                else:
                    cur.execute(sql)
                if sql.strip().lower().startswith("select"):
                    result = cur.fetchall()
                    self.logger.info(f"Query result: {result}")
                    return result
                else:
                    conn.commit()
                    self.logger.info("Query committed.")
        except Exception as e:
            msg = f"Query failed: {e}"
            self.logger.error(msg)
            return msg

    def get_schema(self):
        """データベースのスキーマを取得する"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute("SELECT sql FROM sqlite_master WHERE type='table'")
                result = cur.fetchall()
                return "\n".join([row[0] for row in result if row[0]])
        except Exception as e:
            return f"Schema fetch failed: {e}"
