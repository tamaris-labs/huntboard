import pytest
from fastapi.testclient import TestClient

from huntboard import llm, veille
from huntboard.sources.email_imap import parse_linkedin_alert
from huntboard.store import Store, VersionConflict


def test_store_versions_and_merge():
    s = Store(":memory:")
    assert s.set("notes", "a", {"status": "creuser", "tags": {"x": 1}}) == 1
    assert s.update("notes", "a", {"tags": {"y": 2}}) == 2
    assert s.data("notes", "a") == {"status": "creuser", "tags": {"x": 1, "y": 2}}
    with pytest.raises(VersionConflict):
        s.set("notes", "a", {}, if_version=1)
    s.update("notes", "a", {"status": {"__delete__": True}})
    assert "status" not in s.data("notes", "a")


def test_parse_json_tolerant():
    assert llm.parse_json('Voici :\n```json\n[{"a": 1}]\n```') == [{"a": 1}]
    assert llm.parse_json('Résultat {"ok": true} fin') == {"ok": True}
    with pytest.raises(ValueError):
        llm.parse_json("aucun json")


def test_linkedin_alert_parser():
    text = (
        "Votre alerte Emploi pour product owner (Lyon) Product Owner IA Exemple SA Lyon "
        "Voir l’offre d’emploi : https://www.linkedin.com/comm/jobs/view/123456/?trk=x "
        "Chef de projet data Autre SAS Villeurbanne Voir l’offre d’emploi : "
        "https://www.linkedin.com/comm/jobs/view/987654?trk=y"
    )
    items = parse_linkedin_alert(text)
    assert [i["linkedin_id"] for i in items] == ["123456", "987654"]
    assert items[0]["url"] == "https://www.linkedin.com/jobs/view/123456/"
    assert "Product Owner IA" in items[0]["title_block"]


def test_dedupe_and_slug():
    assert veille.dedupe_key({"url": "https://www.linkedin.com/jobs/view/42/"}) == "li:42"
    assert veille.slug("Société Générale", "Chef de projet IA") == "societe-generale-chef-de-projet-ia"


def test_api_roundtrip_and_page():
    from huntboard.main import app

    c = TestClient(app)
    assert c.get("/api/health").json()["ok"] is True
    cfg = c.get("/api/db/config/main").json()["data"]
    assert cfg["onboarded"] is False and not cfg["profile"]  # configuration vierge, sans données personnelles
    r = c.put("/api/db/offers/test-offre", json={"data": {"id": "test-offre", "title": "Test", "url": "https://exemple.fr"}})
    assert r.status_code == 200 and r.json()["version"] == 1
    assert c.put("/api/db/offers/test-offre", json={"data": {}, "if_version": 7}).status_code == 409
    assert c.get("/api/db/inconnue").status_code == 404
    page = c.get("/").text
    assert "/shim.js" in page and "Huntboard" in page and "I18N" in page
    assert c.post("/api/llm/sample", json={"input": "test"}).status_code == 503  # pas de clé configurée


def test_score_merges_breakdown_and_limits_far(monkeypatch):
    items = [{"title": f"Poste {i}", "company": "Exemple", "url": f"https://exemple.fr/{i}"} for i in range(5)]
    reply = [{"exclude": i == 0, "score": 60 - i, "tier": "far", "breakdown": {"geo": 20, "tech": 20}, "reasons": "r"} for i in range(5)]
    monkeypatch.setattr(llm, "complete_json", lambda *a, **k: reply)
    out = veille.score({"lang": "fr"}, {"lessons": []}, items)
    assert len(out) == 3  # une exclusion, puis au plus 3 offres « far »
    assert out[0]["breakdown"]["geo"] == 20 and out[0]["url"] == "https://exemple.fr/1"


def test_assets_round_trip(tmp_path, monkeypatch):
    monkeypatch.setenv("HUNTBOARD_DATA_DIR", str(tmp_path))
    import importlib

    from huntboard import main, settings as st

    importlib.reload(st)
    importlib.reload(main)
    from fastapi.testclient import TestClient

    c = TestClient(main.app)
    r = c.post("/api/assets", content=b"%PDF-1.4 test", headers={"Content-Type": "application/pdf"})
    assert r.status_code == 200
    a = r.json()
    assert a["sizeBytes"] == 13 and a["url"] == f"/_blob/{a['id']}"
    g = c.get(a["url"])
    assert g.status_code == 200 and g.headers["content-type"].startswith("application/pdf")
    assert c.post("/api/assets", content=b"x", headers={"Content-Type": "application/x-msdownload"}).status_code == 415
    assert c.get("/_blob/../../etc").status_code == 404
    assert c.delete(f"/api/assets/{a['id']}").json()["ok"]
    assert c.get(a["url"]).status_code == 404


def test_tracks_due_and_config():
    from datetime import datetime

    from huntboard.veille import track_config, tracks_due

    cfg = {
        "roles": "CTO", "geo": "Marseille", "salary_min_k": 65, "partners": "oui",
        "sources": [{"name": "Main"}],
        "tracks": [
            {"id": "freelance", "name": "Freelance", "active": True, "frequency": "weekly", "roles": "Missions IA",
             "pay": "TJM 600 € minimum", "sources": [{"name": "Malt", "active": True}, {"name": "Off", "active": False}]},
            {"id": "intl", "active": True, "frequency": "daily"},
            {"id": "off", "active": False, "frequency": "daily"},
        ],
    }
    monday, tuesday = datetime(2026, 10, 26), datetime(2026, 10, 27)
    assert [t["id"] for t in tracks_due(cfg, monday)] == ["freelance", "intl"]
    assert [t["id"] for t in tracks_due(cfg, tuesday)] == ["intl"]
    assert [t["id"] for t in tracks_due(cfg, tuesday, force=True)] == ["freelance", "intl"]
    tc = track_config(cfg, cfg["tracks"][0])
    assert tc["roles"] == "Missions IA" and tc["geo"] == "" and tc["salary_min_k"] is None
    assert tc["partners"] == "" and "TJM 600" in tc["free"] and [s["name"] for s in tc["sources"]] == ["Malt"]
    assert "tracks" not in tc


def test_keep_postings_and_empty_message(tmp_path):
    from datetime import datetime

    from huntboard.store import Store
    from huntboard.veille import empty_message, keep_postings

    st = Store(str(tmp_path / "t.sqlite3"))
    offers = {
        "a": {"url": "https://jobs.example.com/a"},
        "b": {"url": "https://www.linkedin.com/jobs/view/1/"},
        "c": {"url": "https://jobs.example.com/c"},
    }
    notes = {"a": {"status": "creuser"}, "b": {"status": "postule"}, "c": {"status": "ecartee"}}
    calls = []

    def fake(url):
        calls.append(url)
        return "Texte complet de l'annonce. " * 40

    assert keep_postings(st, offers, notes, fetch=fake) == 1
    assert calls == ["https://jobs.example.com/a"]
    assert st.data("postings", "a")["method"] == "web"
    assert st.data("postings", "b")["status"] == "unavailable" and st.data("postings", "b")["attempts"] == 1
    assert st.data("postings", "c") is None
    keep_postings(st, offers, notes, fetch=fake)
    assert calls == ["https://jobs.example.com/a"]  # texte déjà conservé : pas de nouvel appel
    msg = empty_message({"lang": "en"}, notes, datetime(2026, 10, 23))
    assert msg and "{active}" not in msg
    assert empty_message({"lang": "fr"}, notes, datetime(2026, 10, 24)) != empty_message({"lang": "fr"}, notes, datetime(2026, 10, 25))


def test_to_openai_messages():
    from huntboard.llm import to_openai_messages

    msgs = [
        {"role": "user", "content": "Bonjour"},
        {"role": "assistant", "content": [{"type": "text", "text": "Je regarde."},
                                          {"type": "tool_use", "id": "t1", "name": "search_offers", "input": {"query": "ia"}}]},
        {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t1", "content": "[]"}]},
    ]
    out = to_openai_messages(msgs)
    assert out[0] == {"role": "user", "content": "Bonjour"}
    assert out[1]["tool_calls"][0]["function"]["name"] == "search_offers"
    assert out[2] == {"role": "tool", "tool_call_id": "t1", "content": "[]"}


def test_step_endpoint_without_key():
    from huntboard.main import app

    c = TestClient(app)
    r = c.post("/api/llm/step", json={"messages": [{"role": "user", "content": "x"}], "tools": []})
    assert r.status_code in (200, 503)
