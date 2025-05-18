# Azure Container Appsへのデプロイ手順

このドキュメントでは、Slack MCP AgentアプリケーションをAzure Container Appsにデプロイする手順を説明します。

## 前提条件

- Azure CLIがインストールされていること
- Azureアカウントを持っていること
- Dockerがインストールされていること
- `config.json`がプロジェクトルートに存在すること

## デプロイ手順

```sh
# 1. Azureへログイン
az login

# 2. リソースグループの作成
az group create --name <RESOURCE_GROUP_NAME> --location <LOCATION>

# 3. Azure Container Registry(ACR)の作成
az acr create --resource-group <RESOURCE_GROUP_NAME> --name <ACR_NAME> --sku Basic

# 4. ACRへログイン
az acr login --name <ACR_NAME>

# 5. Dockerイメージのビルド
# (プロジェクトルートで実行)
docker build -t <ACR_NAME>.azurecr.io/<IMAGE_NAME>:latest . --platform=linux/amd64

# 6. イメージをACRへプッシュ
docker push <ACR_NAME>.azurecr.io/<IMAGE_NAME>:latest

# 7. Container Apps環境の作成
az containerapp env create --name <CONTAINERAPPS_ENV_NAME> --resource-group <RESOURCE_GROUP_NAME> --location <LOCATION>

# 8. シークレット(config.json)の登録
az containerapp secret set --name <APP_NAME> --resource-group <RESOURCE_GROUP_NAME> --secrets configjson=@config.json

# 9. Container Appの作成
az containerapp create \
  --name <APP_NAME> \
  --resource-group <RESOURCE_GROUP_NAME> \
  --environment <CONTAINERAPPS_ENV_NAME> \
  --image <ACR_NAME>.azurecr.io/<IMAGE_NAME>:latest \
  --registry-server <ACR_NAME>.azurecr.io \
  --target-port 80 \
  --ingress external \
  --cpu 0.5 \
  --memory 1.0Gi \
  --min-replicas 1 \
  --max-replicas 1 \
  --secrets configjson=@config.json \
  --secret-volume-mount /app/config \
  --env-vars LOG_LEVEL=info CONFIG_PATH=/app/config/configjson
```

※ 各`<...>`はご自身の環境に合わせて適宜置き換えてください。

## 動作確認

デプロイ後、Container AppのFQDNにアクセスし、正常に動作しているか確認してください。

```sh
# FQDNの取得
az containerapp show --name <APP_NAME> --resource-group <RESOURCE_GROUP_NAME> --query properties.configuration.ingress.fqdn -o tsv

# ヘルスチェック
curl https://<取得したFQDN>/
# → {"status":"ok"} が返れば成功
```

## 注意事項

- 機密情報はAzure Key Vault等で安全に管理してください。
- スケーリングやリソース設定は運用状況に応じて調整してください。
- 本番運用時は監視・ログ設定もご検討ください。 