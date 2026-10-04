from typing import assert_never

from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.chat.model import ChatModelConfig, ModelProvider
from app.core.config import config


class ModelFactory:
    def get_chat_model(
        self,
        provider: ModelProvider = ModelProvider.OPENAI,
        model_options: ChatModelConfig | None = None,
    ) -> BaseChatModel:
        options = model_options or ChatModelConfig()

        if provider == ModelProvider.OPENAI:
            return ChatOpenAI(
                model=options.model or "gpt-5-nano",
                temperature=options.temperature,
                api_key=SecretStr(config.OPENAI_API_KEY),
            )

        if provider == ModelProvider.GEMINI:
            return ChatGoogleGenerativeAI(
                model=options.model or "gemini-2.5-flash",
                temperature=options.temperature,
                google_api_key=SecretStr(config.GEMINI_API_KEY),
            )

        assert_never(provider)
