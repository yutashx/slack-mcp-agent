import os
import logging
from openai import AsyncOpenAI, AsyncAzureOpenAI

logger = logging.getLogger(__name__)

class AIClient:
    def __init__(self, provider: str, env: dict):
        self.provider = provider
        self.env = env
        self.tracing_disabled = False
        self.client = self._select_aiclient(provider, env)
        logger.info(f"use {provider} as default openai client")

    def _select_aiclient(self, provider: str, env: dict):
        if provider == "openai":
            return self._set_openai_client(env)
        elif provider == "azure":
            return self._set_azure_openai_client(env)
        else:
            logger.error(f"Invalid provider: {provider}")
            raise ValueError(f"Invalid provider: {provider}")

    def _set_openai_client(self, env: dict):
        if os.getenv("OPENAI_API_KEY") is None:
            logger.error("OPENAI_API_KEY is not set")
            raise ValueError("OPENAI_API_KEY is not set")
        openai_client = AsyncOpenAI(api_key=env["OPENAI_API_KEY"])
        self.tracing_disabled = False
        logger.info("Initialized OpenAI AsyncOpenAI client")
        return openai_client

    def _set_azure_openai_client(self, env: dict):
        for key in ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_API_VERSION", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_DEPLOYMENT"]:
            if key not in env:
                logger.error(f"{key} is not set")
                raise ValueError(f"{key} is not set")
        openai_client = AsyncAzureOpenAI(
            api_key=env["AZURE_OPENAI_API_KEY"],
            api_version=env["AZURE_OPENAI_API_VERSION"],
            azure_endpoint=env["AZURE_OPENAI_ENDPOINT"],
            azure_deployment=env["AZURE_OPENAI_DEPLOYMENT"]
        )
        self.tracing_disabled = True
        logger.info("Initialized Azure OpenAI AsyncAzureOpenAI client")
        return openai_client

