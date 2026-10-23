"""Configuration de l'application, lue depuis les variables d'environnement (.env)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _list(name: str, default: str = "") -> list[str]:
    return [x.strip() for x in _env(name, default).split(",") if x.strip()]


@dataclass
class Settings:
    data_dir: str = field(default_factory=lambda: _env("HUNTBOARD_DATA_DIR", "./data"))
    timezone: str = field(default_factory=lambda: _env("TZ", "Europe/Paris"))
    veille_cron: str = field(default_factory=lambda: _env("VEILLE_CRON", "30 8 * * 1-5"))
    veille_enabled: bool = field(default_factory=lambda: _env("VEILLE_ENABLED", "true").lower() == "true")
    app_password: str = field(default_factory=lambda: _env("APP_PASSWORD"))

    # Modèle de langage
    llm_provider: str = field(default_factory=lambda: _env("LLM_PROVIDER", "anthropic"))  # anthropic | openai
    llm_api_key: str = field(default_factory=lambda: _env("LLM_API_KEY") or _env("ANTHROPIC_API_KEY") or _env("OPENAI_API_KEY"))
    llm_base_url: str = field(default_factory=lambda: _env("LLM_BASE_URL"))  # OpenAI-compatible : Gemini, Ollama, etc.
    model_quick: str = field(default_factory=lambda: _env("LLM_MODEL_QUICK", "claude-haiku-5-5"))
    model_default: str = field(default_factory=lambda: _env("LLM_MODEL_DEFAULT", "claude-sonnet-5-5"))
    model_complex: str = field(default_factory=lambda: _env("LLM_MODEL_COMPLEX", "claude-opus-5-5"))
    web_search_max_uses: int = field(default_factory=lambda: int(_env("WEB_SEARCH_MAX_USES", "15")))

    # Messagerie (lecture seule)
    imap_host: str = field(default_factory=lambda: _env("IMAP_HOST"))
    imap_port: int = field(default_factory=lambda: int(_env("IMAP_PORT", "993")))
    imap_user: str = field(default_factory=lambda: _env("IMAP_USER"))
    imap_password: str = field(default_factory=lambda: _env("IMAP_PASSWORD"))
    imap_folder: str = field(default_factory=lambda: _env("IMAP_FOLDER", "INBOX"))
    alert_senders: list[str] = field(
        default_factory=lambda: _list(
            "ALERT_SENDERS",
            "jobalerts-noreply@linkedin.com,jobs-noreply@linkedin.com,emails.hellowork.com,michaelpage",
        )
    )

    # Notification (ntfy, Gotify, webhook générique recevant du texte)
    notify_url: str = field(default_factory=lambda: _env("NOTIFY_URL"))

    @property
    def db_path(self) -> str:
        return os.path.join(self.data_dir, "huntboard.sqlite3")

    @property
    def llm_enabled(self) -> bool:
        return bool(self.llm_api_key) or self.llm_provider == "openai" and bool(self.llm_base_url)

    @property
    def imap_enabled(self) -> bool:
        return bool(self.imap_host and self.imap_user and self.imap_password)


settings = Settings()
