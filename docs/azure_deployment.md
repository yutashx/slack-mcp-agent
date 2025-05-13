# Azure Container Appsへのデプロイ手順

このドキュメントでは、Slack MCP Agentアプリケーションを Azure Container Appsにデプロイする手順を説明します。

## 前提条件

- Azure CLIがインストールされていること
- Azureアカウントを持っていること
- Dockerがインストールされていること

## 1. Azureへのログイン

```bash
az login
```

## 2. リソースグループの作成

```bash
az group create --name slack-mcp-agent-rg --location japaneast
```

## 3. Azure Container Registryの作成

```bash
# ACRの作成
az acr create --resource-group slack-mcp-agent-rg --name slackmcpacr --sku Basic

# ACRへのログイン
az acr login --name slackmcpacr
```

## 4. アプリケーションのコンテナイメージのビルドとプッシュ

```bash
# カレントディレクトリがプロジェクトルートであることを確認
cd /path/to/slack-mcp-agent

# イメージのビルド
docker build -t slackmcpacr.azurecr.io/slack-mcp-agent:latest .  --platform=linux/amd64

# イメージのプッシュ
docker push slackmcpacr.azurecr.io/slack-mcp-agent:latest
```

## 5. Azure Container Appsの環境作成

```bash
az containerapp env create \
  --name slack-mcp-env \
  --resource-group slack-mcp-agent-rg \
  --location japaneast
```

## 6. Container Appの作成とデプロイ

まず、`config.json` の内容をシークレットとして登録します：

```bash
az containerapp secret set \
  --name slack-mcp-agent \
  --resource-group slack-mcp-agent-rg \
  --secrets configjson=@config.json
```

アプリケーションの実行に必要な環境変数は、Azure Container Appsのシークレットとして設定します。

```bash
# config.jsonの内容を参考に、以下の環境変数を設定します
az containerapp create \
  --name slack-mcp-agent \
  --resource-group slack-mcp-agent-rg \
  --environment slack-mcp-env \
  --image slackmcpacr.azurecr.io/slack-mcp-agent:latest \
  --registry-server slackmcpacr.azurecr.io \
  --target-port 80 \
  --ingress external \
  --cpu 0.5 \
  --memory 1.0Gi \
  --min-replicas 1 \
  --max-replicas 1 \
  --secrets \
      configjson=@config.json \
      openai-api-key=<YOUR_OPENAI_API_KEY> \
  --secret-volume-mount /app/config \
  --env-vars \
      LOG_LEVEL=info \
      OPENAI_API_KEY=secretref:openai-api-key \
      CONFIG_PATH=/app/config/configjson
```


## 7. アプリケーションの動作確認

デプロイが完了したら、ヘルスチェックエンドポイントにアクセスして動作確認を行います。

```bash
# Container Appのホスト名を取得
HOSTNAME=$(az containerapp show --name slack-mcp-agent --resource-group slack-mcp-agent-rg --query properties.configuration.ingress.fqdn -o tsv)

# ヘルスチェックエンドポイントにアクセス
curl https://$HOSTNAME/

# 正常に動作していれば、以下のレスポンスが返ってきます
# {"status":"ok"}
```

## 注意事項

- セキュリティのために、本番環境ではAzure Key Vaultを使用して機密情報を管理することをお勧めします。
- スケーリング設定は、アプリケーションの負荷に応じて調整してください。
- 本番環境では、適切なログ監視を設定することを検討してください。
