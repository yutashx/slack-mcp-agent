import os
import logging
import subprocess
import threading
import time
import sqlite3
from datetime import datetime

class AzureBlobSQLiteClient:
    def __init__(self, env: dict):
        self.env = env
        self.db_path = env.get("SQLITE_DB_PATH", "./db/app.db")
        self.blob_url = env.get("AZURE_BLOB_URL")
        self.account_name = env.get("AZURE_STORAGE_ACCOUNT_NAME")
        self.account_key = env.get("AZURE_STORAGE_ACCOUNT_KEY")
        self.container = env.get("AZURE_BLOB_CONTAINER")
        self.blob_name = env.get("AZURE_BLOB_NAME", os.path.basename(self.db_path))
        self.logger = logging.getLogger(__name__)
        self._cron_thread = None
        self._cron_stop_event = threading.Event()
        self._cron_interval = int(env.get("SQLITE_CRON_INTERVAL_HOURS", 1)) * 3600  # 秒単位

    def cron_start(self):
        """N時間ごとにアップロードするサブプロセスを起動"""
        if self._cron_thread and self._cron_thread.is_alive():
            self.logger.info("cron already running")
            return
        self.logger.info(f"Start cron thread: every {self._cron_interval/3600} hours")
        self._cron_stop_event.clear()
        self._cron_thread = threading.Thread(target=self._cron_loop, daemon=True)
        self._cron_thread.start()

    def _cron_loop(self):
        while not self._cron_stop_event.is_set():
            self.logger.info("[cron] Triggering upload to Azure Blob Storage")
            self.upload()
            self.logger.info(f"[cron] Sleeping for {self._cron_interval/3600} hours")
            self._cron_stop_event.wait(self._cron_interval)
        self.logger.info("[cron] Cron thread stopped")

    def cron_end(self):
        """cronサブプロセスを終了"""
        if self._cron_thread and self._cron_thread.is_alive():
            self.logger.info("Stopping cron thread...")
            self._cron_stop_event.set()
            self._cron_thread.join()
            self.logger.info("Cron thread stopped.")
        else:
            self.logger.info("No cron thread to stop.")

    def upload(self):
        """Azure Blob Storageにアップロード"""
        sas_token = self.env.get("AZURE_BLOB_SAS_TOKEN")
        if sas_token:
            dest_url = f"https://{self.account_name}.blob.core.windows.net/{self.container}/{self.blob_name}?{sas_token}"
        else:
            dest_url = f"https://{self.account_name}.blob.core.windows.net/{self.container}/{self.blob_name}"
        cmd = [
            "azcopy", "copy", self.db_path, dest_url, "--overwrite=true"
        ]
        self.logger.info(f"Uploading DB to Azure Blob Storage: {dest_url}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.logger.info(f"Upload success: {result.stdout}")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Upload failed: {e.stderr}")

    def download(self):
        """Azure Blob Storageからダウンロード"""
        sas_token = self.env.get("AZURE_BLOB_SAS_TOKEN")
        if sas_token:
            src_url = f"https://{self.account_name}.blob.core.windows.net/{self.container}/{self.blob_name}?{sas_token}"
        else:
            src_url = f"https://{self.account_name}.blob.core.windows.net/{self.container}/{self.blob_name}"
        cmd = [
            "azcopy", "copy", src_url, self.db_path, "--overwrite=true"
        ]
        self.logger.info(f"Downloading DB from Azure Blob Storage: {src_url}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.logger.info(f"Download success: {result.stdout}")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Download failed: {e.stderr}")

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
            self.logger.error(f"Query failed: {e}")
            return None

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
