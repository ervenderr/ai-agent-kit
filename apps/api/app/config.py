from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../../.env"), extra="ignore")

    anthropic_api_key: str = ""
    database_url: str = "postgresql+asyncpg://agent:agent@localhost:5433/agent"
    cors_origins: list[str] = ["http://localhost:3000"]
    prompts_dir: Path = REPO_ROOT / "prompts"

    llm_model: str = "claude-sonnet-5-5"
    llm_max_tokens: int = 4096
    llm_timeout_s: float = 60.0
    llm_max_retries: int = 3
    # USD per million tokens; used only for the per-run cost cap.
    price_in_per_mtok: float = 2.0
    price_out_per_mtok: float = 10.0

    cap_max_steps: int = 8
    cap_max_tool_calls: int = 10
    cap_max_seconds: float = 60.0
    cap_max_input_tokens: int = 200_000
    cap_max_cost_usd: float = 0.50
    cap_max_arg_repairs: int = 1

    tool_result_max_chars: int = 4000
    max_concurrent_runs: int = 2


@lru_cache
def get_settings() -> Settings:
    return Settings()
