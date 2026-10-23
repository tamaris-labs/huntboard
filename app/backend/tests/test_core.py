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


def test_settings_overrides(tmp_path):
    from huntboard.settings import Settings

    s = Settings(data_dir=str(tmp_path), llm_api_key="", imap_password="pw-env")
    s.save_overrides({"llm_api_key": "sk-test-123456789", "llm_provider": "anthropic", "imap_port": "1993", "unknown": "x"})
    assert s.llm_enabled and s.imap_port == 1993
    s.save_overrides({"llm_api_key": ""})  # secret vide : conservé
    assert s.llm_api_key == "sk-test-123456789"
    pub = s.public()
    assert pub["llm"]["key_hint"] == "…6789" and "sk-test" not in str(pub)
    s2 = Settings(data_dir=str(tmp_path), llm_api_key="")
    s2.load_overrides()
    assert s2.llm_api_key == "sk-test-123456789" and s2.imap_port == 1993
    s2.save_overrides({"llm_api_key": None})
    assert not s2.llm_enabled


def test_follow_up_events():
    from types import SimpleNamespace as M

    from huntboard.veille import follow_up_events

    offers = {"a": {"company": "Aurora Énergie"}, "b": {"company": "Nordline Robotics"}, "c": {"company": "Zeta"}}
    notes = {
        "a": {"status": "postule", "events": []},
        "b": {"status": "entretien", "contacts": [{"email": "camille@nordline.example.com"}], "events": [{"text": "E-mail reçu de Camille : Planning"}]},
        "c": {"status": "ecartee"},
    }
    mails = [
        M(sender="RH Aurora Énergie <rh@aurora.example.com>", subject="Votre candidature", date="2026-10-22T09:00:00"),
        M(sender="Camille <camille@nordline.example.com>", subject="Planning", date="2026-10-22T10:00:00"),
        M(sender="Paul <paul@nordline.example.com>", subject="Étude de cas", date="2026-10-22T11:00:00"),
        M(sender="jobalerts-noreply@linkedin.com", subject="Aurora Énergie recrute", date="2026-10-22T12:00:00"),
        M(sender="Zeta <hello@zeta.example.com>", subject="Hello", date="2026-10-22T12:00:00"),
    ]
    ev = follow_up_events(mails, offers, notes, ["linkedin.com"])
    assert [e["text"] for e in ev["a"]] == ["E-mail reçu de RH Aurora Énergie : Votre candidature"]
    assert [e["text"] for e in ev["b"]] == ["E-mail reçu de Paul : Étude de cas"]  # « Planning » déjà connu ; domaine du contact reconnu
    assert "c" not in ev


def test_application_acks():
    from types import SimpleNamespace as M

    from huntboard.veille import application_acks, is_ack, response_weeks

    offers = {"nordline-chef-de-projet-ia": {"company": "Nordline", "title": "Chef de projet IA"},
              "nordline-architecte-data": {"company": "Nordline", "title": "Architecte data"},
              "aurora-pmo": {"company": "Aurora Énergie", "title": "PMO"}}
    notes = {"aurora-pmo": {"status": "creuser", "events": [{"at": "x", "text": "À creuser"}]}}
    acks = [
        M(sender="Jobboard <contact@emails.jobboard.example.com>", subject="Votre candidature est arrivée chez Nordline",
          date="2026-10-23T17:53:00+00:00", text="Poste : Chef de projet IA. Bonne chance !"),
        M(sender="Nordline <notification@ats.example.com>", subject="Merci pour votre candidature",
          date="2026-10-23T17:54:00+00:00", text="Nordline confirme votre candidature au poste de Chef de projet IA. "
          "Sans réponse sous 3 semaines, considérez qu'elle n'est pas retenue."),
        M(sender="Aurora Énergie <rh@aurora.example.com>", subject="Accusé de réception", date="2026-10-23T09:00:00+00:00",
          text="Nous avons bien reçu votre candidature, merci pour votre candidature."),
        M(sender="AG <ag@workday.example.com>", subject="ACME - Thank you for applying !", date="2026-10-23T17:34:00+00:00",
          text="Thank you for applying to IT Product Manager (JR1)."),
    ]
    assert all(is_ack(m) for m in acks)
    assert not is_ack(M(sender="x", subject="Suite à votre candidature", text="Malheureusement…", date=""))
    assert not is_ack(M(sender="x", subject="Invitation à un entretien — votre candidature", text="", date=""))
    assert response_weeks("sans réponse sous trois semaines") == 3

    res = application_acks(acks, offers, notes, details=lambda m: {"company": "ACME", "title": "IT Product Manager", "reference": "JR1"})
    n1, new1 = res["notes"]["nordline-chef-de-projet-ia"]
    assert new1 and n1["status"] == "postule" and n1["applied_at"] == "2026-10-23"
    assert len(n1["events"]) == 1  # deux accusés, une seule candidature (le plus ancien gagne)
    assert "nordline-architecte-data" not in res["notes"]  # l'intitulé départage les offres d'une même entreprise
    n2, new2 = res["notes"]["aurora-pmo"]
    assert not new2 and n2["status"] == "creuser" and len(n2["events"]) == 2  # statut inchangé, événement ajouté
    created = res["offers"]["acme-it-product-manager"]
    assert created["tier"] == "pending" and created["source"] == "Candidature directe" and "JR1" in created["raw_text"]
    assert res["notes"]["acme-it-product-manager"][0]["status"] == "postule"
    again = application_acks(acks, offers, {**notes, "aurora-pmo": n2}, details=lambda m: {})
    assert "aurora-pmo" not in again["notes"]  # déjà enregistrée


def test_application_acks_due_date():
    from types import SimpleNamespace as M

    from huntboard.veille import application_acks

    m = M(sender="Zeta <jobs@ats.example.com>", subject="Your application to Zeta", date="2026-10-23T10:00:00+00:00",
          text="We have received your application. Without an answer within 3 weeks, consider it unsuccessful.")
    res = application_acks([m], {"zeta-cto": {"company": "Zeta", "title": "CTO"}}, {})
    note = res["notes"]["zeta-cto"][0]
    assert note["next_due"] == "2026-11-13" and "3 semaines" in note["events"][0]["text"]


def test_score_pending(monkeypatch):
    from huntboard.veille import score_pending

    s = Store(":memory:")
    s.set("offers", "p1", {"id": "p1", "title": "PMO", "company": "Aurora", "url": "https://exemple.fr/o", "tier": "pending"})
    s.set("offers", "p2", {"id": "p2", "title": "CTO", "company": "Zeta", "tier": "match", "score": 80})
    seen = {}

    def fake_score(config, learned, items):
        seen["items"] = items
        return [{**items[0], "score": 72, "tier": "match", "breakdown": {"geo": 20}, "reasons": "ok"}]

    monkeypatch.setattr(veille, "score", fake_score)
    assert score_pending(s, {}, {}, fetch=lambda url: "Texte de l'annonce") == 1
    assert [i["id"] for i in seen["items"]] == ["p1"] and seen["items"][0]["posting_excerpt"] == "Texte de l'annonce"
    d = s.data("offers", "p1")
    assert d["tier"] == "match" and d["score"] == 72 and "posting_excerpt" not in d


def test_check_source_statuses():
    from huntboard.veille import check_source

    ok = check_source({"name": "A", "url": "https://jobs.example.com/x"}, probe=lambda u: {"code": 200, "final_url": u, "title": "Jobs"})
    assert ok["status"] == "ok" and ok["title"] == "Jobs"
    mv = check_source({"name": "B", "url": "https://old.example.com"}, probe=lambda u: {"code": 200, "final_url": "https://new.example.org/careers"})
    assert mv["status"] == "moved" and mv["url"] == "https://new.example.org/careers"
    assert check_source({"name": "C", "url": "https://c.example.com"}, probe=lambda u: {"code": 403})["status"] == "blocked"
    assert check_source({"name": "D", "url": "https://d.example.com"}, probe=lambda u: (_ for _ in ()).throw(OSError()))["status"] == "unreachable"
    assert check_source({"name": "E", "url": ""})["status"] == "no_url"
    assert check_source({"name": "F", "url": "https://www.linkedin.com/jobs"})["status"] == "not_checked"


def test_source_yield_and_merge():
    from huntboard.veille import merge_suggestions, source_yield

    config = {"sources": [{"name": "HelloWork"}, {"name": "Cabinet Exemple"}],
              "tracks": [{"id": "associes", "sources": [{"name": "Tandem - Les Deeptech"}]}]}
    offers = {"a": {"source": "Alerte HelloWork"}, "b": {"source": "Alerte HelloWork"}, "c": {"source": "Web", "track": "x"}}
    notes = {"a": {"status": "postule"}, "b": {"status": "ecartee"}}
    y = {r["name"]: r for r in source_yield(config, offers, notes)}
    assert y["HelloWork"]["found"] == 2 and y["HelloWork"]["kept"] == 1 and y["Cabinet Exemple"]["found"] == 0
    doc = merge_suggestions({}, [{"name": "Tandem – Les Deeptech"}, {"name": "LesJeudis", "url": "https://x"}, {"name": "HelloWork"}], config, "ai")
    assert [i["name"] for i in doc["items"]] == ["LesJeudis"] and doc["items"][0]["status"] == "unverified"
    doc = merge_suggestions(doc, [{"name": "lesjeudis", "why": "Offres IT"}], config, "web")
    assert len(doc["items"]) == 1 and doc["items"][0]["why"] == "Offres IT"


def test_verify_endpoint_without_key(monkeypatch):
    from huntboard import main

    s = Store(":memory:")
    monkeypatch.setattr(main, "store", s)
    s.set("sources", "suggestions", {"items": [{"name": "X", "url": "", "status": "unverified"}]})
    c = TestClient(main.app)
    r = c.post("/api/app/sources/verify", json={"more": 3})
    assert r.status_code == 200
    doc = r.json()
    assert doc["items"][0]["status"] == "no_url" and doc["verify"]["state"] == "done"
    assert c.get("/api/db/sources/suggestions").status_code == 200


def test_web_search_backend_selection():
    from huntboard.settings import Settings, web_search_backend

    def mk(**kw):
        s = Settings()
        for k, v in {"llm_api_key": "k", "llm_provider": "openai", "llm_base_url": "", "web_search": "auto",
                     "search_api_key": "", "searxng_url": "", **kw}.items():
            setattr(s, k, v)
        return s

    assert web_search_backend(mk(llm_provider="anthropic")) == "native:anthropic"
    assert web_search_backend(mk()) == "native:openai"
    assert web_search_backend(mk(llm_base_url="https://api.x.ai/v1")) == "native:xai"
    assert web_search_backend(mk(llm_base_url="https://openrouter.ai/api/v1")) == "native:openrouter"
    assert web_search_backend(mk(llm_base_url="https://generativelanguage.googleapis.com/v1beta/openai/")) == "native:gemini"
    assert web_search_backend(mk(llm_base_url="https://api.mistral.ai/v1")) == "none"
    assert web_search_backend(mk(llm_base_url="http://ollama:11434/v1", searxng_url="http://searxng:8080")) == "searxng"
    assert web_search_backend(mk(llm_base_url="http://ollama:11434/v1", search_api_key="tvly-x")) == "tavily"
    assert web_search_backend(mk(llm_base_url="http://ollama:11434/v1", search_api_key="BSAx")) == "brave"
    assert web_search_backend(mk(web_search="brave", search_api_key="")) == "none"
    assert web_search_backend(mk(web_search="searxng", searxng_url="http://s")) == "searxng"
    assert web_search_backend(mk(web_search="none")) == "none"
    assert web_search_backend(mk(web_search="native", llm_base_url="https://api.deepseek.com/v1", searxng_url="http://s")) == "none"


def test_research_tool_loop():
    from huntboard.llm import _research_with_tools

    seen = []

    def step(messages, tools, tier, max_tokens):
        if len(messages) == 1:
            return {"content": [{"type": "tool_use", "id": "t1", "name": "web_search", "input": {"query": "cto marseille"}}], "stop_reason": "tool_use"}
        if len(messages) == 3:
            seen.append(messages[2]["content"][0]["content"])
            return {"content": [{"type": "tool_use", "id": "t2", "name": "read_page", "input": {"url": "https://jobs.example.com/1"}}], "stop_reason": "tool_use"}
        return {"content": [{"type": "text", "text": '[{"title": "CTO"}]'}], "stop_reason": "end_turn"}

    out = _research_with_tools("find", "default", "searxng", "FR", step=step,
                               search=lambda q: [{"title": "Offre", "url": "https://jobs.example.com/1", "snippet": q}],
                               read=lambda u: "Texte de l'annonce")
    assert out == '[{"title": "CTO"}]' and "cto marseille" in seen[0]
