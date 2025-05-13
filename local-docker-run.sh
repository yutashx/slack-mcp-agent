#!/bin/bash

# ローカルでDockerコンテナを実行するスクリプト

# .envファイルから環境変数を読み込む
source .env

# Dockerイメージをビルド
docker build -t slack-mcp-agent:local .

# Dockerコンテナを実行
docker run -it --rm \
  -e CONFIG_PATH="/app/config/config.json" \
  -v $(pwd)/config.json:/app/config/config.json \
  slack-mcp-agent:local

# コンテナ実行後、ヘルスチェックエンドポイントにアクセスして確認するコマンド
# curl http://localhost:8000/
