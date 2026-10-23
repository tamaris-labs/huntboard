"""Configuration de l'application, lue depuis les variables d'environnement (.env)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any


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
    # Recherche web : auto (recherche intégrée du fournisseur si elle existe, sinon service externe s'il est
    # configuré), native, brave, tavily, searxng ou none (lecture des pages des sources seulement).
    web_search: str = field(default_factory=lambda: _env("WEB_SEARCH", "auto").lower())
    search_api_key: str = field(default_factory=lambda: _env("SEARCH_API_KEY"))  # Brave ou Tavily
    searxng_url: str = field(default_factory=lambda: _env("SEARXNG_URL"))  # ex. http://searxng:8080

    # Messagerie (lecture seule)
    imap_host: str = field(default_factory=lambda: _env("IMAP_HOST"))
    imap_port: int = field(default_factory=lambda: int(_env("IMAP_PORT", "993")))
    imap_user: str = field(default_factory=lambda: _env("IMAP_USER"))
    imap_password: str = field(default_factory=lambda: _env("IMAP_PASSWORD"))
    imap_folder: str = field(default_factory=lambda: _env("IMAP_FOLDER", "INBOX"))
    alert_senders: list[str] = field(
        default_factory=lambda: _list(
            "ALERT_SENDERS",
            "jobalerts-noreply@linkedin.com,jobs-noreply@linkedin.com,indeed,hellowork,welcometothejungle,apec,cadremploi,michaelpage",
        )
    )

    # Suivi des candidatures : e-mails des entreprises et contacts suivis (en-têtes seulement)
    follow_ups: bool = field(default_factory=lambda: _env("MAIL_FOLLOW_UPS", "true").lower() == "true")

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

    # Réglages modifiables depuis l'interface (onglet Réglages › Connexions), enregistrés dans
    # <data_dir>/settings.json ; ils priment sur le .env.
    @property
    def overrides_path(self) -> str:
        return os.path.join(self.data_dir, "settings.json")

    def load_overrides(self) -> None:
        try:
            with open(self.overrides_path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            return
        for k, v in data.items():
            if k in EDITABLE:
                setattr(self, k, int(v) if k == "imap_port" else v)

    def save_overrides(self, patch: dict[str, Any]) -> None:
        """Applique et enregistre un sous-ensemble de réglages. Un secret vide est ignoré ; None l'efface."""
        try:
            with open(self.overrides_path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            data = {}
        for k, v in patch.items():
            if k not in EDITABLE:
                continue
            if k in SECRETS and v == "":
                continue
            v = "" if v is None else v
            if k == "imap_port":
                v = int(v or 993)
            elif k == "alert_senders":
                v = [x.strip() for x in (v if isinstance(v, list) else str(v).replace("\n", ",").split(",")) if x.strip()]
            elif isinstance(v, str):
                v = v.strip()
            data[k] = v
            setattr(self, k, v)
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.overrides_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        try:
            os.chmod(self.overrides_path, 0o600)
        except OSError:
            pass

    def public(self) -> dict[str, Any]:
        """Vue sans secret, pour l'interface."""
        hint = lambda s: ("…" + s[-4:]) if s and len(s) > 8 else ("défini" if s else "")  # noqa: E731
        return {
            "llm": {"enabled": self.llm_enabled, "provider": self.llm_provider, "base_url": self.llm_base_url,
                    "key_set": bool(self.llm_api_key), "key_hint": hint(self.llm_api_key),
                    "model_quick": self.model_quick, "model_default": self.model_default, "model_complex": self.model_complex},
            "imap": {"enabled": self.imap_enabled, "host": self.imap_host, "port": self.imap_port, "user": self.imap_user,
                     "folder": self.imap_folder, "password_set": bool(self.imap_password),
                     "alert_senders": self.alert_senders, "follow_ups": self.follow_ups},
            "search": {"mode": self.web_search, "searxng_url": self.searxng_url, "key_set": bool(self.search_api_key),
                       "key_hint": hint(self.search_api_key), "effective": web_search_backend(self)},
            "notify": {"enabled": bool(self.notify_url), "url_set": bool(self.notify_url)},
            "veille": {"enabled": self.veille_enabled, "cron": self.veille_cron, "timezone": self.timezone},
        }


EDITABLE = {"llm_provider", "llm_api_key", "llm_base_url", "model_quick", "model_default", "model_complex",
            "imap_host", "imap_port", "imap_user", "imap_password", "imap_folder", "notify_url",
            "alert_senders", "follow_ups", "web_search", "search_api_key", "searxng_url"}
SECRETS = {"llm_api_key", "imap_password", "notify_url", "search_api_key"}

SEARCH_MODES = ("auto", "native", "brave", "tavily", "searxng", "none")


def native_search_kind(s: "Settings") -> str:
    """Recherche web intégrée au fournisseur configuré : anthropic, openai, xai, openrouter, gemini, ou vide."""
    if not s.llm_enabled:
        return ""
    if s.llm_provider == "anthropic":
        return "anthropic"
    base = (s.llm_base_url or "").lower()
    if not base or "api.openai.com" in base:
        return "openai"
    for key, kind in (("api.x.ai", "xai"), ("openrouter.ai", "openrouter"), ("generativelanguage.googleapis.com", "gemini")):
        if key in base:
            return kind
    return ""


def web_search_backend(s: "Settings") -> str:
    """Mode de recherche web réellement utilisé : native:<fournisseur>, brave, tavily, searxng ou none."""
    mode = s.web_search if s.web_search in SEARCH_MODES else "auto"
    if mode == "none" or not s.llm_enabled:
        return "none"
    if mode in ("auto", "native"):
        kind = native_search_kind(s)
        if kind:
            return "native:" + kind
        if mode == "native":
            return "none"
        if s.searxng_url:
            return "searxng"
        if s.search_api_key:
            return "tavily" if s.search_api_key.startswith("tvly-") else "brave"
        return "none"
    if mode == "searxng":
        return "searxng" if s.searxng_url else "none"
    return mode if s.search_api_key else "none"

settings = Settings()
settings.load_overrides()
