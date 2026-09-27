"""
Multi-Model Gateway & Router for MaxIM.
Supports Ollama (local), Google (Gemini), OpenAI (ChatGPT), DeepSeek, OmniRoute, and Custom providers.
Standardizes all endpoints onto the OpenAI-compatible function-calling protocol.
"""
import os
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple, AsyncIterator
from pydantic import BaseModel, Field
from openai import AsyncOpenAI, OpenAI
from config import config

class ProviderType(str, Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    GOOGLE = "google"
    DEEPSEEK = "deepseek"
    OPENROUTER = "openrouter"
    NOUS = "nous"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    MISTRAL = "mistral"
    XAI = "xai"
    TOGETHER = "together"
    FIREWORKS = "fireworks"
    CEREBRAS = "cerebras"
    PERPLEXITY = "perplexity"
    COHERE = "cohere"
    SAMBANOVA = "sambanova"
    AZURE = "azure"
    OMNIROUTE = "omniroute"
    UNSLOTH = "unsloth"
    CUSTOM = "custom"
    LOCAL = "local"

class ProviderConfig(BaseModel):
    name: str
    base_url: str
    api_key: str
    default_model: str
    headers: Dict[str, str] = Field(default_factory=dict)

    @property
    def model_name(self) -> str:
        return self.default_model

    @model_name.setter
    def model_name(self, value: str):
        self.default_model = value

class ModelRouter:
    def __init__(self):
        try:
            self.active_provider: ProviderType = ProviderType(config.active_provider.lower())
        except ValueError:
            self.active_provider = ProviderType.CUSTOM
        self.fallback_provider: Optional[str] = None
        self.connection_roles: Dict[str, Dict[str, Optional[str]]] = {
            "primary": {"provider": config.active_provider, "model": None},
            "subagents": {"provider": "ollama", "model": config.local_model_name},
            "fast": {"provider": "google", "model": "gemini-2.0-flash"},
            "reasoning": {"provider": "deepseek", "model": "deepseek-chat"},
        }
        self._custom_providers: Dict[str, ProviderConfig] = {}
        self._async_clients: Dict[str, AsyncOpenAI] = {}
        self._sync_clients: Dict[str, OpenAI] = {}
        self._init_default_providers()

    def set_connection_role(self, role: str, provider: str, model: Optional[str] = None) -> None:
        """Sets target provider and model for a specific operational role (primary, subagents, fast, reasoning)."""
        self.connection_roles[role] = {"provider": provider, "model": model}

    def get_connection_for_role(self, role: str) -> Tuple[str, Optional[str]]:
        """Resolves provider and model for a given operational role."""
        if role in self.connection_roles:
            info = self.connection_roles[role]
            return info["provider"], info.get("model")
        active_name = self.active_provider.value if isinstance(self.active_provider, ProviderType) else str(self.active_provider)
        return active_name, None

    def set_fallback_provider(self, provider: str) -> None:
        """Sets the secondary provider for automatic failover."""
        self.fallback_provider = provider

    @property
    def providers(self) -> Dict[str, ProviderConfig]:
        p = {k.value: v for k, v in self._configs.items()}
        p.update(self._custom_providers)
        return p

    def list_providers(self) -> Dict[str, Dict[str, Any]]:
        active_val = self.active_provider.value if isinstance(self.active_provider, ProviderType) else str(self.active_provider)
        res = {
            name: {
                "name": cfg.name,
                "base_url": cfg.base_url,
                "model_name": cfg.default_model,
                "configured": bool(cfg.api_key and cfg.api_key != "dummy-key") or "localhost" in cfg.base_url,
                "is_active": (name == active_val),
            }
            for name, cfg in self.providers.items()
        }
        if "openai" in res:
            res["chatgpt"] = dict(res["openai"])
            res["chatgpt"]["name"] = "chatgpt"
        return res

    def get_connected_cloud_providers(self) -> List[Dict[str, Any]]:
        """Returns all cloud providers that have a configured and valid API key."""
        local_names = {"ollama", "unsloth", "custom", "local"}
        connected = []
        display_names = {
            "openai": "OpenAI",
            "anthropic": "Anthropic Claude",
            "google": "Google Gemini",
            "deepseek": "DeepSeek",
            "groq": "Groq",
            "openrouter": "OpenRouter",
            "nous": "Nous Portal",
            "mistral": "Mistral AI",
            "xai": "xAI Grok",
            "together": "Together AI",
            "fireworks": "Fireworks AI",
            "cerebras": "Cerebras",
            "perplexity": "Perplexity",
            "cohere": "Cohere",
            "sambanova": "SambaNova",
            "azure": "Azure OpenAI",
            "omniroute": "OmniRoute",
        }
        for name, cfg in self.providers.items():
            if name.lower() in local_names:
                continue
            is_configured = bool(cfg.api_key and cfg.api_key.strip() and cfg.api_key not in ("dummy-key", "none", "null"))
            if is_configured:
                connected.append({
                    "provider": name,
                    "name": display_names.get(name.lower(), cfg.name.title()),
                    "model_name": cfg.default_model,
                    "base_url": cfg.base_url,
                    "is_cloud": True,
                })
        return connected

    def _init_default_providers(self):
        """Initializes default configurations from config."""
        self._configs: Dict[ProviderType, ProviderConfig] = {
            ProviderType.OLLAMA: ProviderConfig(
                name="ollama",
                base_url=config.local_model_url,
                api_key="ollama",
                default_model=config.local_model_name,
            ),
            ProviderType.OPENAI: ProviderConfig(
                name="openai",
                base_url="https://api.openai.com/v1",
                api_key=config.openai_api_key,
                default_model=config.openai_model_name,
            ),
            ProviderType.GOOGLE: ProviderConfig(
                name="google",
                base_url=config.google_base_url,
                api_key=config.google_api_key,
                default_model=config.google_model_name,
            ),
            ProviderType.DEEPSEEK: ProviderConfig(
                name="deepseek",
                base_url=config.deepseek_base_url,
                api_key=config.deepseek_api_key,
                default_model=config.deepseek_model_name,
            ),
            ProviderType.OPENROUTER: ProviderConfig(
                name="openrouter",
                base_url=config.openrouter_base_url,
                api_key=config.openrouter_api_key,
                default_model=config.openrouter_model_name,
                headers={"HTTP-Referer": "https://maxim.local", "X-Title": "MaxIM Agent"},
            ),
            ProviderType.NOUS: ProviderConfig(
                name="nous",
                base_url=config.nous_base_url,
                api_key=config.nous_api_key,
                default_model=config.nous_model_name,
            ),
            ProviderType.ANTHROPIC: ProviderConfig(
                name="anthropic",
                base_url=config.anthropic_base_url,
                api_key=config.anthropic_api_key,
                default_model=config.anthropic_model_name,
            ),
            ProviderType.GROQ: ProviderConfig(
                name="groq",
                base_url=config.groq_base_url,
                api_key=config.groq_api_key,
                default_model=config.groq_model_name,
            ),
            ProviderType.MISTRAL: ProviderConfig(
                name="mistral",
                base_url=config.mistral_base_url,
                api_key=config.mistral_api_key,
                default_model=config.mistral_model_name,
            ),
            ProviderType.XAI: ProviderConfig(
                name="xai",
                base_url=config.xai_base_url,
                api_key=config.xai_api_key,
                default_model=config.xai_model_name,
            ),
            ProviderType.TOGETHER: ProviderConfig(
                name="together",
                base_url=config.together_base_url,
                api_key=config.together_api_key,
                default_model=config.together_model_name,
            ),
            ProviderType.FIREWORKS: ProviderConfig(
                name="fireworks",
                base_url=config.fireworks_base_url,
                api_key=config.fireworks_api_key,
                default_model=config.fireworks_model_name,
            ),
            ProviderType.CEREBRAS: ProviderConfig(
                name="cerebras",
                base_url=config.cerebras_base_url,
                api_key=config.cerebras_api_key,
                default_model=config.cerebras_model_name,
            ),
            ProviderType.PERPLEXITY: ProviderConfig(
                name="perplexity",
                base_url=config.perplexity_base_url,
                api_key=config.perplexity_api_key,
                default_model=config.perplexity_model_name,
            ),
            ProviderType.COHERE: ProviderConfig(
                name="cohere",
                base_url=config.cohere_base_url,
                api_key=config.cohere_api_key,
                default_model=config.cohere_model_name,
            ),
            ProviderType.SAMBANOVA: ProviderConfig(
                name="sambanova",
                base_url=config.sambanova_base_url,
                api_key=config.sambanova_api_key,
                default_model=config.sambanova_model_name,
            ),
            ProviderType.AZURE: ProviderConfig(
                name="azure",
                base_url=config.azure_base_url,
                api_key=config.azure_api_key,
                default_model=config.azure_model_name,
            ),
            ProviderType.OMNIROUTE: ProviderConfig(
                name="omniroute",
                base_url=config.omniroute_base_url,
                api_key=config.omniroute_api_key,
                default_model=config.omniroute_model_name,
            ),
            ProviderType.UNSLOTH: ProviderConfig(
                name="unsloth",
                base_url=config.unsloth_base_url,
                api_key=config.unsloth_api_key,
                default_model=config.unsloth_model_name,
            ),
            ProviderType.CUSTOM: ProviderConfig(
                name="custom",
                base_url=config.custom_base_url,
                api_key=config.custom_api_key,
                default_model=config.custom_model_name,
            ),
            ProviderType.LOCAL: ProviderConfig(
                name="local",
                base_url=os.getenv("LOCAL_LLAMA_BASE_URL", "http://127.0.0.1:8080/v1"),
                api_key="none",
                default_model="default",
            ),
        }

    def set_active_provider(self, provider: ProviderType | str) -> None:
        """Sets the default active model provider."""
        if isinstance(provider, str):
            try:
                self.active_provider = ProviderType(provider.lower())
            except ValueError:
                self.active_provider = ProviderType.CUSTOM
        else:
            self.active_provider = provider

    def register_custom_provider(
        self,
        name: str,
        base_url: str,
        api_key: str,
        default_model: Optional[str] = None,
        model_name: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """Dynamically registers or updates an arbitrary OpenAI-compatible provider."""
        target_model = default_model or model_name or "custom-model"
        spec = ProviderConfig(
            name=name,
            base_url=base_url,
            api_key=api_key or "dummy-key",
            default_model=target_model,
            headers=headers or {},
        )
        self._custom_providers[name.lower()] = spec

    def get_provider_config(self, provider: Optional[ProviderType | str] = None) -> ProviderConfig:
        """Resolves configuration for the given or active provider."""
        if provider is None:
            provider = self.active_provider

        # Check custom dynamic registry first
        if isinstance(provider, str) and provider.lower() in self._custom_providers:
            return self._custom_providers[provider.lower()]

        # Common provider alias mappings
        alias_map = {
            "chatgpt": ProviderType.OPENAI,
            "gemini": ProviderType.GOOGLE,
            "claude": ProviderType.ANTHROPIC,
            "grok": ProviderType.XAI,
            "nous-portal": ProviderType.NOUS,
            "together-ai": ProviderType.TOGETHER,
            "fireworks-ai": ProviderType.FIREWORKS,
            "cerebras-ai": ProviderType.CEREBRAS,
            "azure-openai": ProviderType.AZURE,
            "azure-foundry": ProviderType.AZURE,
            "unsloth": ProviderType.UNSLOTH,
            "unsloth-ai": ProviderType.UNSLOTH,
        }
        if isinstance(provider, str) and provider.lower() in alias_map:
            return self._configs[alias_map[provider.lower()]]

        # Convert to ProviderType enum if string matches
        if isinstance(provider, str):
            try:
                provider = ProviderType(provider.lower())
            except ValueError:
                # Default to custom with default settings
                return self._configs[ProviderType.CUSTOM]

        return self._configs.get(provider, self._configs[ProviderType.OLLAMA])

    def get_async_client(
        self, provider: Optional[ProviderType | str] = None
    ) -> Tuple[AsyncOpenAI, str]:
        """Returns configured AsyncOpenAI client (reused from connection pool) and target model name."""
        cfg = self.get_provider_config(provider)
        cache_key = f"{cfg.name}:{cfg.base_url}:{cfg.api_key}"
        if cache_key not in self._async_clients:
            self._async_clients[cache_key] = AsyncOpenAI(
                base_url=cfg.base_url,
                api_key=cfg.api_key or "dummy-key",
                default_headers=cfg.headers if cfg.headers else None,
            )
        return self._async_clients[cache_key], cfg.default_model

    def get_sync_client(
        self, provider: Optional[ProviderType | str] = None
    ) -> Tuple[OpenAI, str]:
        """Returns configured sync OpenAI client (reused from connection pool) and target model name."""
        cfg = self.get_provider_config(provider)
        cache_key = f"{cfg.name}:{cfg.base_url}:{cfg.api_key}"
        if cache_key not in self._sync_clients:
            self._sync_clients[cache_key] = OpenAI(
                base_url=cfg.base_url,
                api_key=cfg.api_key or "dummy-key",
                default_headers=cfg.headers if cfg.headers else None,
            )
        return self._sync_clients[cache_key], cfg.default_model

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        provider: Optional[ProviderType | str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        enable_failover: bool = True,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
    ) -> Any:
        """Executes a chat completion across the selected provider with optional automatic failover."""
        target_provider = provider or self.active_provider
        try:
            client, default_model = self.get_async_client(target_provider)
            target_model = model or default_model

            kwargs: Dict[str, Any] = {
                "model": target_model,
                "messages": messages,
                "temperature": temperature,
            }
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = tool_choice or "auto"

            return await client.chat.completions.create(**kwargs)
        except Exception as primary_err:
            if enable_failover and self.fallback_provider and self.fallback_provider != target_provider:
                # Automatic failover to secondary provider
                fallback_client, fallback_default_model = self.get_async_client(self.fallback_provider)
                fallback_target_model = model or fallback_default_model
                kwargs["model"] = fallback_target_model
                return await fallback_client.chat.completions.create(**kwargs)
            raise primary_err

    async def stream_chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        provider: Optional[ProviderType | str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
    ) -> AsyncIterator[Any]:
        """Streams chat completion tokens in real-time."""
        client, default_model = self.get_async_client(provider)
        target_model = model or default_model

        kwargs: Dict[str, Any] = {
            "model": target_model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice or "auto"

        stream = await client.chat.completions.create(**kwargs)
        async for chunk in stream:
            yield chunk

# Singleton router instance
model_router = ModelRouter()
