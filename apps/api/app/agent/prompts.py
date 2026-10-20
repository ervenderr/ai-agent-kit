import re
from functools import lru_cache

from app.config import get_settings


@lru_cache
def load_system_prompt(name: str = "system") -> str:
    """Static file only: user content never goes into the system prompt (it would also break caching)."""
    text = (get_settings().prompts_dir / f"{name}.md").read_text()
    return re.sub(r"\A\s*<!--.*?-->\s*", "", text, flags=re.S)
