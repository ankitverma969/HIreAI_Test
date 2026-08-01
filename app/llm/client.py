from abc import ABC, abstractmethod
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from loguru import logger
from pydantic import BaseModel

from app.core.config import settings


class BaseLLMClient(ABC):
    """Abstract Base Class defining standard chat or completion wrapper endpoints."""

    @abstractmethod
    async def generate_completion(
        self,
        prompt: str,
        system_instruction: str | None = None,
        json_mode: bool = False,
        temperature: float = 0.0,
    ) -> str:
        """Invokes upstream generative language models."""
        pass


class MockChatModel(BaseChatModel):
    """Deterministic Mock Chat Model for offline/test environments."""

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any | None = None,
        **kwargs: Any
    ) -> ChatResult:
        # Standard fallback returning simple text content
        return ChatResult(
            generations=[
                ChatGeneration(
                    message=AIMessage(content="Mock LLM response output for offline pipeline testing.")
                )
            ]
        )

    @property
    def _llm_type(self) -> str:
        return "mock-chat-model"

    def with_structured_output(
        self,
        schema: type[BaseModel] | dict[str, Any],
        *,
        include_raw: bool = False,
        **kwargs: Any
    ) -> Any:
        """Stubs LangChain with_structured_output to return mock Pydantic data."""
        if not isinstance(schema, type) or not issubclass(schema, BaseModel):
            raise ValueError("Mock model expects a Pydantic BaseModel class schema.")

        class MockStructuredCallable:
            def __init__(self, target_schema: type[BaseModel]):
                self.target_schema = target_schema

            def invoke(self, *args: Any, **kwargs: Any) -> BaseModel:
                # Build mock data matching target schema fields
                fields: dict[str, Any] = {}
                for field_name, field_info in self.target_schema.model_fields.items():
                    annotation = field_info.annotation
                    origin = getattr(annotation, "__origin__", annotation)

                    if origin is list:
                        args_attr = getattr(annotation, "__args__", None)
                        arg_type = args_attr[0] if args_attr else str
                        if isinstance(arg_type, type) and issubclass(arg_type, BaseModel):
                            fields[field_name] = []
                        else:
                            if "question" in field_name.lower():
                                fields[field_name] = [
                                    "How do you design REST APIs in Python?",
                                    "Can you explain your experience with Docker container orchestration?",
                                    "How do you profile performance in PostgreSQL databases?",
                                    "Explain the architecture of a custom semantic similarity engine.",
                                    "How do you manage task scheduling in distributed systems?"
                                ]
                            elif "skill" in field_name.lower():
                                fields[field_name] = ["Docker", "Kubernetes", "AWS"]
                            else:
                                fields[field_name] = ["Mock Value 1", "Mock Value 2"]
                    elif isinstance(origin, type) and issubclass(origin, BaseModel):
                        # Empty child Pydantic
                        fields[field_name] = origin()
                    elif origin is int:
                        fields[field_name] = 85
                    elif origin is float:
                        fields[field_name] = 85.0
                    elif origin is bool:
                        fields[field_name] = True
                    else:
                        # Strings
                        if field_name == "hiring_decision" or field_name == "recommendation":
                            fields[field_name] = "Consider"
                        elif "summary" in field_name:
                            fields[field_name] = "The candidate shows solid engineering fundamentals and strong core project credentials."
                        elif "strength" in field_name:
                            fields[field_name] = "Strong background in backend microservices architectures."
                        elif "weakness" in field_name:
                            fields[field_name] = "Limited exposure to frontend UI design tooling."
                        else:
                            fields[field_name] = f"Mock {field_name.replace('_', ' ').title()}"

                return self.target_schema(**fields)

            def __call__(self, *args: Any, **kwargs: Any) -> BaseModel:
                return self.invoke(*args, **kwargs)

        return MockStructuredCallable(schema)


def get_llm_client(
    model_name_override: str | None = None,
    gemini_api_base_override: str | None = None,
    temperature_override: float | None = None,
) -> BaseChatModel:
    """Provider factory returning configured ChatModel instance or custom Mock model.

    Provider selection is based on the MODEL_NAME value in Settings.
    Mock key detection is performed per-provider to prevent the OpenAI
    mock sentinel from accidentally suppressing a valid Gemini or Groq key.
    """
    # Allow runtime override of model selection and endpoint
    model_name = (model_name_override or settings.MODEL_NAME).lower()
    gemini_api_base = gemini_api_base_override or settings.GEMINI_API_BASE
    temperature = temperature_override if temperature_override is not None else 0.0

    # Respect feature toggle and allowed providers list
    provider_key = None
    if "gpt" in model_name or "openai" in model_name:
        provider_key = "openai"
    elif "gemini" in model_name:
        provider_key = "gemini"
    elif "llama" in model_name or "mixtral" in model_name or "gemma" in model_name or "groq" in model_name:
        provider_key = "groq"

    if not settings.ENABLE_LLM:
        logger.warning("LLM features are disabled in settings.ENABLE_LLM. Returning MockChatModel.")
        return cast(BaseChatModel, MockChatModel())

    if provider_key and provider_key not in [p.lower() for p in settings.ALLOWED_LLM_PROVIDERS]:
        logger.warning(
            f"Requested provider '{provider_key}' is not in ALLOWED_LLM_PROVIDERS. Returning MockChatModel."
        )
        return cast(BaseChatModel, MockChatModel())

    from typing import cast

    from pydantic import SecretStr

    # ── Determine active provider & perform per-provider mock key check ──────
    if "gpt" in model_name:
        # OpenAI path
        if settings.is_mock_key(settings.OPENAI_API_KEY):
            logger.warning(
                f"Mock/empty OPENAI_API_KEY detected. Returning MockChatModel "
                f"(requested: '{settings.MODEL_NAME}')."
            )
            return cast(BaseChatModel, MockChatModel())
        try:
            from langchain_openai import ChatOpenAI
            logger.info(f"Constructing ChatOpenAI instance: '{settings.MODEL_NAME}'")
            return cast(BaseChatModel, ChatOpenAI(
                model=settings.MODEL_NAME,
                api_key=SecretStr(settings.OPENAI_API_KEY),
                temperature=0.0,
            ))
        except Exception as e:
            logger.error(f"ChatOpenAI init failed: {e}. Falling back to MockChatModel.")
            return cast(BaseChatModel, MockChatModel())

    elif "gemini" in model_name:
        # Google Gemini path — uses its own key, never affected by OpenAI mock
        if settings.is_mock_key(settings.GEMINI_API_KEY):
            logger.warning(
                f"Mock/empty GEMINI_API_KEY detected. Returning MockChatModel "
                f"(requested: '{settings.MODEL_NAME}')."
            )
            return cast(BaseChatModel, MockChatModel())
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            logger.info(f"Constructing ChatGoogleGenerativeAI: '{settings.MODEL_NAME}'")

            # Build optional client kwargs for custom endpoint (GEMINI_API_BASE)
            client_kwargs: dict = {}
            if gemini_api_base:
                logger.info(f"Using custom Gemini API base URL: '{gemini_api_base}'")
                client_kwargs["client_options"] = {"api_endpoint": gemini_api_base}

            return cast(BaseChatModel, ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=SecretStr(settings.GEMINI_API_KEY),
                temperature=temperature,
                **client_kwargs,
            ))
        except Exception as e:
            logger.error(f"ChatGoogleGenerativeAI init failed: {e}. Falling back to MockChatModel.")
            return cast(BaseChatModel, MockChatModel())

    elif "llama" in model_name or "mixtral" in model_name or "gemma" in model_name:
        # Groq path
        if settings.is_mock_key(settings.GROQ_API_KEY):
            logger.warning(
                f"Mock/empty GROQ_API_KEY detected. Returning MockChatModel "
                f"(requested: '{settings.MODEL_NAME}')."
            )
            return cast(BaseChatModel, MockChatModel())
        try:
            from langchain_groq import ChatGroq
            logger.info(f"Constructing ChatGroq instance: '{settings.MODEL_NAME}'")
            return cast(BaseChatModel, ChatGroq(
                model=model_name,
                api_key=SecretStr(settings.GROQ_API_KEY),
                temperature=temperature,
            ))
        except Exception as e:
            logger.error(f"ChatGroq init failed: {e}. Falling back to MockChatModel.")
            return cast(BaseChatModel, MockChatModel())

    else:
        # Default fallback → OpenAI
        if settings.is_mock_key(settings.OPENAI_API_KEY):
            logger.warning(
                f"Unknown model '{settings.MODEL_NAME}' with mock OpenAI key. "
                "Returning MockChatModel."
            )
            return cast(BaseChatModel, MockChatModel())
        try:
            from langchain_openai import ChatOpenAI
            logger.info(f"Fallback constructing default ChatOpenAI: '{settings.MODEL_NAME}'")
            return cast(BaseChatModel, ChatOpenAI(
                model=model_name,
                api_key=SecretStr(settings.OPENAI_API_KEY),
                temperature=temperature,
            ))
        except Exception as e:
            logger.error(f"Fallback ChatOpenAI init failed: {e}. Returning MockChatModel.")
            return cast(BaseChatModel, MockChatModel())
