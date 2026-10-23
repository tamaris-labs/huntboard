"""Application web Huntboard : API, interface et planification de la veille."""

from __future__ import annotations

import base64
import json
import logging
import secrets
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response, StreamingResponse
from pydantic import BaseModel

from . import llm, veille
from .settings import settings
from .store import Store, VersionConflict

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("huntboard")

HERE = Path(__file__).resolve().parent
FRONTEND = HERE.parent.parent / "frontend"
KIT = HERE.parent.parent.parent / "kit" / "skills" / "huntboard"
COLLECTIONS = {"offers", "notes", "prep", "config", "profile", "coach", "documents", "geo", "postings", "memos", "sources"}
ASSET_TYPES = {"application/pdf", "text/plain", "text/markdown", "text/csv", "application/json", "image/png", "image/jpeg", "image/webp"}
ASSET_MAX = 15 * 1024 * 1024

store = Store(settings.db_path)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    sched = schedule()
    yield
    if sched:
        sched.shutdown(wait=False)


app = FastAPI(title="Huntboard", version="1.0.0", lifespan=lifespan)


def _first_existing(*paths: Path) -> Path:
    for p in paths:
        if p.exists():
            return p
    raise FileNotFoundError(", ".join(str(p) for p in paths))


def seed() -> None:
    """Configuration d'exemple au premier démarrage (aucune donnée personnelle)."""
    if not store.get("geo", "basemap"):
        store.set("geo", "basemap", {"url": "/basemap.json"})
    if store.get("config", "main"):
        return
    path = _first_existing(FRONTEND / "config.example.json", KIT / "config.example.json")
    store.set("config", "main", json.loads(path.read_text(encoding="utf-8")))
    log.info("Configuration d'exemple chargée : personnalisez-la dans l'onglet Critères.")


seed()


# Authentification simple (facultative) ----------------------------------------
@app.middleware("http")
async def basic_auth(request: Request, call_next):
    if settings.app_password and request.url.path != "/api/health":
        header = request.headers.get("authorization", "")
        ok = False
        if header.startswith("Basic "):
            try:
                _, pwd = base64.b64decode(header[6:]).decode().split(":", 1)
                ok = secrets.compare_digest(pwd, settings.app_password)
            except Exception:  # noqa: BLE001
                ok = False
        if not ok:
            return Response(status_code=401, headers={"WWW-Authenticate": 'Basic realm="Huntboard"'})
    return await call_next(request)


# Interface ----------------------------------------------------------------------
_RESET = (
    ":root{color-scheme:light;padding-top:env(safe-area-inset-top);padding-bottom:env(safe-area-inset-bottom)}"
    "body{margin:0;font:14px system-ui,sans-serif}img{max-width:100%}[hidden]{display:none!important}"
)


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    page = _first_existing(FRONTEND / "huntboard.html", KIT / "template" / "huntboard.html").read_text(encoding="utf-8")
    page = page.replace("<script>", '<script src="/shim.js"></script>\n<script>', 1)
    return (
        '<!doctype html><html lang="fr"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        f"<style>{_RESET}</style></head><body>{page}</body></html>"
    )


@app.get("/basemap.json")
def basemap() -> Response:
    path = _first_existing(FRONTEND / "basemap.json", KIT / "assets" / "basemap.json")
    return Response(path.read_bytes(), media_type="application/json", headers={"Cache-Control": "public, max-age=604800"})


@app.get("/shim.js")
def shim() -> Response:
    return Response((FRONTEND / "shim.js").read_text(encoding="utf-8"), media_type="application/javascript")


# Données ------------------------------------------------------------------------
class DocBody(BaseModel):
    data: dict[str, Any]
    if_version: int | None = None


def _check(collection: str) -> None:
    if collection not in COLLECTIONS:
        raise HTTPException(404, "Collection inconnue")


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"ok": True, "llm": settings.llm_enabled, "imap": settings.imap_enabled, "provider": settings.llm_provider}


# Réglages de l'application (moteur d'IA, messagerie, notification) -------------
@app.get("/api/app/status")
def app_status() -> dict[str, Any]:
    runs = store.runs(1)
    return {"mode": "app", **settings.public(), "last_run": runs[0] if runs else None}


@app.put("/api/app/settings")
def app_settings(patch: dict[str, Any]) -> dict[str, Any]:
    settings.save_overrides(patch)
    return app_status()


@app.post("/api/app/imap/test")
def app_imap_test() -> dict[str, Any]:
    """Connexion en lecture seule et décompte des alertes des 7 derniers jours (aucun message modifié)."""
    if not settings.imap_enabled:
        return {"ok": False, "error": "Messagerie non configurée."}
    from .sources import email_imap
    try:
        heads = email_imap.fetch_headers(days=7, limit=500)
        alerts = sum(1 for m in heads if any(s.lower() in (m.sender or "").lower() for s in settings.alert_senders))
        return {"ok": True, "recent": len(heads), "alerts": alerts}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)[:300]}


@app.post("/api/app/sources/verify")
def app_sources_verify(body: dict[str, Any]) -> dict[str, Any]:
    """Vérifie les sources suggérées (adresse joignable, redirection) et, si « more », en cherche d'autres sur le web."""
    items = body.get("items")
    more = max(0, min(int(body.get("more") or 0), 10))
    return veille.verify_and_suggest(store, items=items if isinstance(items, list) else None, more=more)


@app.post("/api/app/llm/test")
def app_llm_test() -> dict[str, Any]:
    if not settings.llm_enabled:
        return {"ok": False, "error": "Aucune clé d'API configurée."}
    try:
        text = llm.complete("Reply with the single word OK.", tier="quick", max_tokens=10)
        return {"ok": True, "text": text.strip()[:40], "model": settings.model_quick}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)[:300]}


@app.get("/api/db/{collection}")
def list_docs(collection: str) -> list[dict[str, Any]]:
    _check(collection)
    return store.list(collection)


@app.get("/api/db/{collection}/{doc_id}")
def get_doc(collection: str, doc_id: str) -> dict[str, Any]:
    _check(collection)
    d = store.get(collection, doc_id)
    if not d:
        raise HTTPException(404, "Document introuvable")
    return d


@app.put("/api/db/{collection}/{doc_id}")
def put_doc(collection: str, doc_id: str, body: DocBody) -> dict[str, Any]:
    _check(collection)
    try:
        return {"version": store.set(collection, doc_id, body.data, body.if_version)}
    except VersionConflict as e:
        raise HTTPException(409, str(e)) from e


@app.patch("/api/db/{collection}/{doc_id}")
def patch_doc(collection: str, doc_id: str, body: DocBody) -> dict[str, Any]:
    _check(collection)
    try:
        return {"version": store.update(collection, doc_id, body.data, body.if_version)}
    except KeyError as e:
        raise HTTPException(404, str(e)) from e
    except VersionConflict as e:
        raise HTTPException(409, str(e)) from e


@app.delete("/api/db/{collection}/{doc_id}")
def delete_doc(collection: str, doc_id: str) -> dict[str, bool]:
    _check(collection)
    store.delete(collection, doc_id)
    return {"ok": True}


# Fichiers (CV originaux, traductions, lettres) ----------------------------------
def _assets_dir() -> Path:
    d = Path(settings.data_dir) / "assets"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _asset_path(asset_id: str) -> Path:
    if not asset_id.isalnum() or len(asset_id) != 32:
        raise HTTPException(404, "unknown asset")
    return _assets_dir() / asset_id


@app.post("/api/assets")
async def upload_asset(request: Request) -> dict[str, Any]:
    ctype = (request.headers.get("content-type") or "").split(";")[0].strip().lower()
    if ctype not in ASSET_TYPES:
        raise HTTPException(415, f"type not accepted: {ctype}")
    body = await request.body()
    if not body or len(body) > ASSET_MAX:
        raise HTTPException(413, "empty or too large")
    asset_id = secrets.token_hex(16)
    path = _asset_path(asset_id)
    path.write_bytes(body)
    path.with_suffix(".type").write_text(ctype)
    return {"id": asset_id, "url": f"/_blob/{asset_id}", "sizeBytes": len(body), "contentType": ctype}


@app.get("/_blob/{asset_id}")
def get_asset(asset_id: str) -> Response:
    path = _asset_path(asset_id)
    if not path.exists():
        raise HTTPException(404, "unknown asset")
    ctype = path.with_suffix(".type").read_text() if path.with_suffix(".type").exists() else "application/octet-stream"
    return Response(path.read_bytes(), media_type=ctype, headers={"X-Content-Type-Options": "nosniff", "Content-Security-Policy": "sandbox"})


@app.delete("/api/assets/{asset_id}")
def delete_asset(asset_id: str) -> dict[str, bool]:
    path = _asset_path(asset_id)
    path.unlink(missing_ok=True)
    path.with_suffix(".type").unlink(missing_ok=True)
    return {"ok": True}


# Modèle de langage (préparation d'entretien) ------------------------------------
class SampleBody(BaseModel):
    input: str | list[dict[str, str]]
    tier: str = "default"


@app.post("/api/llm/sample")
def sample(body: SampleBody):
    if not settings.llm_enabled:
        return JSONResponse({"code": "sampling_disabled", "message": "Aucun modèle configuré (LLM_API_KEY)."}, 503)
    tier = body.tier if body.tier in {"quick", "default", "complex"} else "default"

    def gen():
        try:
            yield from llm.stream(body.input, tier=tier, max_tokens=6000)
        except Exception as e:  # noqa: BLE001
            log.warning("Appel au modèle en échec : %s", e)
            yield "\n\n[Erreur : la réponse a été interrompue.]"

    return StreamingResponse(gen(), media_type="text/plain; charset=utf-8")


class StepBody(BaseModel):
    messages: list[dict[str, Any]]
    tools: list[dict[str, Any]] = []
    tier: str = "default"


@app.post("/api/llm/step")
def llm_step(body: StepBody):
    """Un tour de l'assistant avec outils ; les outils s'exécutent dans la page (shim)."""
    if not settings.llm_enabled:
        return JSONResponse({"code": "sampling_disabled", "message": "Aucun modèle configuré (LLM_API_KEY)."}, 503)
    tier = body.tier if body.tier in {"quick", "default", "complex"} else "default"
    try:
        return llm.tool_step(body.messages, body.tools, tier=tier)
    except Exception as e:  # noqa: BLE001
        log.warning("Tour d'outils en échec : %s", e)
        return JSONResponse({"code": "upstream_error", "message": str(e)[:300]}, 502)


# Veille -------------------------------------------------------------------------
_running = threading.Lock()


def _run_veille() -> None:
    if not _running.acquire(blocking=False):
        log.info("Un passage de veille est déjà en cours.")
        return
    try:
        veille.run(store)
    finally:
        _running.release()


@app.post("/api/veille/run")
def run_now() -> dict[str, str]:
    threading.Thread(target=_run_veille, daemon=True).start()
    return {"status": "lancée"}


@app.get("/api/veille/runs")
def runs() -> list[dict[str, Any]]:
    return store.runs()


@app.get("/api/veille/last", response_class=PlainTextResponse)
def last_run() -> str:
    r = store.runs(1)
    return r[0]["summary"] or r[0]["status"] if r else "Aucun passage pour l'instant."


def schedule():
    """Planifie la veille selon VEILLE_CRON ; renvoie le planificateur (ou None)."""
    if not settings.veille_enabled:
        return None
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger

    sched = BackgroundScheduler(timezone=settings.timezone)
    sched.add_job(_run_veille, CronTrigger.from_crontab(settings.veille_cron, timezone=settings.timezone), id="veille")
    sched.start()
    log.info("Veille planifiée : %s (%s)", settings.veille_cron, settings.timezone)
    return sched
