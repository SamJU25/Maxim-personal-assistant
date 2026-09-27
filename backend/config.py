"""
Configuration management for MaxIM native backend.
Enforces strict type safety and zero-hallucination paths.
"""
from pathlib import Path
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict
import os

def utc_now_iso() -> str:
    """Canonical ISO-8601 UTC timestamp string across all MaxIM modules."""
    return datetime.now(timezone.utc).isoformat()

class MaxIMConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Paths
    base_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    backend_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parent)
    vault_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent / "vault")
    soul_path: Path = Field(default_factory=lambda: Path(__file__).resolve().parent / "soul.md")
    db_path: Path = Field(default_factory=lambda: Path(__file__).resolve().parent / "maxim.db")
    
    # LifeOS TELOS Path
    telos_path: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parent.parent / "vault" / "00 - LifeOS" / "TELOS.md"
    )
    
    # Model Endpoints & Providers
    active_provider: str = Field(default="local")
    
    # Unsloth Local Gateway (Running on port 8080 managed llama-server)
    unsloth_api_key: str = Field(default_factory=lambda: os.getenv("UNSLOTH_API_KEY", "sk-local-token"))
    unsloth_base_url: str = Field(default_factory=lambda: os.getenv("UNSLOTH_BASE_URL", "http://127.0.0.1:8080/v1"))
    unsloth_model_name: str = Field(default_factory=lambda: os.getenv("UNSLOTH_MODEL_NAME", "unsloth/Qwen3.5-4B-GGUF"))
    
    # Ollama / Localhost
    local_model_url: str = Field(default="http://localhost:11434/v1")
    local_model_name: str = Field(default="llama3.2")
    
    # OpenAI (ChatGPT)
    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_model_name: str = Field(default="gpt-4o-mini")
    
    # Google (Gemini)
    google_api_key: str = Field(
        default_factory=lambda: os.getenv("GOOGLE_API_KEY", os.getenv("GEMINI_API_KEY", ""))
    )
    google_model_name: str = Field(default="gemini-2.0-flash")
    google_base_url: str = Field(default="https://generativelanguage.googleapis.com/v1beta/openai/")
    
    # DeepSeek
    deepseek_api_key: str = Field(default_factory=lambda: os.getenv("DEEPSEEK_API_KEY", ""))
    deepseek_model_name: str = Field(default="deepseek-chat")
    deepseek_base_url: str = Field(default="https://api.deepseek.com/v1")
    
    # OmniRoute
    omniroute_api_key: str = Field(default_factory=lambda: os.getenv("OMNIROUTE_API_KEY", ""))
    omniroute_base_url: str = Field(default_factory=lambda: os.getenv("OMNIROUTE_BASE_URL", "https://api.omniroute.ai/v1"))
    omniroute_model_name: str = Field(default="omniroute-default")
    
    # OpenRouter
    openrouter_api_key: str = Field(default_factory=lambda: os.getenv("OPENROUTER_API_KEY", ""))
    openrouter_base_url: str = Field(default_factory=lambda: os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"))
    openrouter_model_name: str = Field(default="anthropic/claude-3.5-sonnet")

    # Nous Portal
    nous_api_key: str = Field(default_factory=lambda: os.getenv("NOUS_API_KEY", os.getenv("NOUS_PORTAL_API_KEY", "")))
    nous_base_url: str = Field(default_factory=lambda: os.getenv("NOUS_BASE_URL", "https://inference-api.nousresearch.com/v1"))
    nous_model_name: str = Field(default="Hermes-3-Llama-3.1-405B")

    # Anthropic
    anthropic_api_key: str = Field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    anthropic_base_url: str = Field(default_factory=lambda: os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1"))
    anthropic_model_name: str = Field(default="claude-3-5-sonnet-20241022")

    # Groq
    groq_api_key: str = Field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    groq_base_url: str = Field(default_factory=lambda: os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"))
    groq_model_name: str = Field(default="llama-3.3-70b-versatile")

    # Mistral
    mistral_api_key: str = Field(default_factory=lambda: os.getenv("MISTRAL_API_KEY", ""))
    mistral_base_url: str = Field(default_factory=lambda: os.getenv("MISTRAL_BASE_URL", "https://api.mistral.ai/v1"))
    mistral_model_name: str = Field(default="mistral-large-latest")

    # xAI (Grok)
    xai_api_key: str = Field(default_factory=lambda: os.getenv("XAI_API_KEY", ""))
    xai_base_url: str = Field(default_factory=lambda: os.getenv("XAI_BASE_URL", "https://api.x.ai/v1"))
    xai_model_name: str = Field(default="grok-2-latest")

    # Together AI
    together_api_key: str = Field(default_factory=lambda: os.getenv("TOGETHER_API_KEY", ""))
    together_base_url: str = Field(default_factory=lambda: os.getenv("TOGETHER_BASE_URL", "https://api.together.xyz/v1"))
    together_model_name: str = Field(default="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo")

    # Fireworks AI
    fireworks_api_key: str = Field(default_factory=lambda: os.getenv("FIREWORKS_API_KEY", ""))
    fireworks_base_url: str = Field(default_factory=lambda: os.getenv("FIREWORKS_BASE_URL", "https://api.fireworks.ai/inference/v1"))
    fireworks_model_name: str = Field(default="accounts/fireworks/models/llama-v3p1-70b-instruct")

    # Cerebras
    cerebras_api_key: str = Field(default_factory=lambda: os.getenv("CEREBRAS_API_KEY", ""))
    cerebras_base_url: str = Field(default_factory=lambda: os.getenv("CEREBRAS_BASE_URL", "https://api.cerebras.ai/v1"))
    cerebras_model_name: str = Field(default="llama3.1-70b")

    # Perplexity
    perplexity_api_key: str = Field(default_factory=lambda: os.getenv("PERPLEXITY_API_KEY", ""))
    perplexity_base_url: str = Field(default_factory=lambda: os.getenv("PERPLEXITY_BASE_URL", "https://api.perplexity.ai"))
    perplexity_model_name: str = Field(default="sonar-pro")

    # Cohere
    cohere_api_key: str = Field(default_factory=lambda: os.getenv("COHERE_API_KEY", ""))
    cohere_base_url: str = Field(default_factory=lambda: os.getenv("COHERE_BASE_URL", "https://api.cohere.com/v2"))
    cohere_model_name: str = Field(default="command-r-plus-08-2024")

    # SambaNova
    sambanova_api_key: str = Field(default_factory=lambda: os.getenv("SAMBANOVA_API_KEY", ""))
    sambanova_base_url: str = Field(default_factory=lambda: os.getenv("SAMBANOVA_BASE_URL", "https://api.sambanova.ai/v1"))
    sambanova_model_name: str = Field(default="Meta-Llama-3.1-70B-Instruct")

    # Azure AI Foundry / Models
    azure_api_key: str = Field(default_factory=lambda: os.getenv("AZURE_API_KEY", os.getenv("AZURE_OPENAI_API_KEY", "")))
    azure_base_url: str = Field(default_factory=lambda: os.getenv("AZURE_BASE_URL", "https://models.inference.ai.azure.com"))
    azure_model_name: str = Field(default="gpt-4o")

    # Custom Provider (Unsloth, vLLM, LM Studio, etc.)
    custom_api_key: str = Field(default_factory=lambda: os.getenv("CUSTOM_API_KEY", "sk-local-custom"))
    custom_base_url: str = Field(default_factory=lambda: os.getenv("CUSTOM_BASE_URL", "http://127.0.0.1:8888/v1"))
    custom_model_name: str = Field(default_factory=lambda: os.getenv("CUSTOM_MODEL_NAME", "unsloth/Qwen3.5-4B-GGUF"))
    
    # Telegram Uplink
    telegram_bot_token: str = Field(default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", ""))
    telegram_chat_id: str = Field(default_factory=lambda: os.getenv("TELEGRAM_CHAT_ID", ""))
    
    # Server Settings
    host: str = "127.0.0.1"
    port: int = 8000

# Global singleton configuration
config = MaxIMConfig()
