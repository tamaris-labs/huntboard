/* Huntboard — adaptateur de l'interface pour l'application autonome.
 *
 * La page de Huntboard est écrite pour l'environnement des artifacts Claude
 * (window.claude.use("db") et window.claude.use("sample")). Ce fichier fournit
 * la même interface au-dessus de l'API FastAPI, ce qui permet de partager une
 * seule page entre le kit Claude et l'application.
 */
(function () {
  "use strict";
  const POLL_MS = 8000;
  const listeners = []; // {kind:"col"|"doc", path, next, last}

  async function api(method, url, body) {
    const r = await fetch(url, {
      method,
      headers: body ? { "Content-Type": "application/json" } : {},
      body: body ? JSON.stringify(body) : undefined,
      credentials: "same-origin",
    });
    if (r.status === 404 && method === "GET") return null;
    if (!r.ok) {
      const err = new Error((await r.text()) || r.statusText);
      err.code = r.status === 409 ? "conflict" : "unavailable";
      throw err;
    }
    return r.json();
  }

  const snapDoc = (id, d) => ({
    id,
    exists: !!d,
    data: () => (d ? d.data : undefined),
    metadata: { fromCache: false, hasPendingWrites: false },
  });

  async function refresh(l) {
    try {
      if (l.kind === "col") {
        const rows = (await api("GET", `/api/db/${l.path}`)) || [];
        const sig = JSON.stringify(rows.map((r) => [r.id, r.version]));
        if (sig === l.last) return;
        l.last = sig;
        const docs = rows.map((r) => snapDoc(r.id, r));
        l.next({ docs, size: docs.length, empty: !docs.length, docChanges: () => [], metadata: { fromCache: false, hasPendingWrites: false } });
      } else {
        const [c, id] = l.path.split("/");
        const d = await api("GET", `/api/db/${c}/${id}`);
        const sig = d ? String(d.version) : "none";
        if (sig === l.last) return;
        l.last = sig;
        l.next(snapDoc(id, d));
      }
    } catch (e) {
      /* réseau indisponible : nouvel essai au prochain cycle */
    }
  }
  setInterval(() => listeners.forEach(refresh), POLL_MS);
  const touch = (collection) => listeners.filter((l) => l.path.split("/")[0] === collection).forEach((l) => { l.last = null; refresh(l); });

  function docRef(collection, id) {
    const path = `${collection}/${id}`;
    return {
      id,
      path,
      get: async () => snapDoc(id, await api("GET", `/api/db/${path}`)),
      set: async (data) => { await api("PUT", `/api/db/${path}`, { data }); touch(collection); },
      update: async (data) => { await api("PATCH", `/api/db/${path}`, { data }); touch(collection); },
      delete: async () => { await api("DELETE", `/api/db/${path}`); touch(collection); },
      onSnapshot(next) {
        const l = { kind: "doc", path, next, last: null };
        listeners.push(l);
        refresh(l);
        return () => listeners.splice(listeners.indexOf(l), 1);
      },
    };
  }

  function colRef(collection) {
    return {
      path: collection,
      doc: (id) => docRef(collection, id || Math.random().toString(36).slice(2, 12)),
      add: async (data) => { const ref = docRef(collection, Math.random().toString(36).slice(2, 12)); await ref.set(data); return ref; },
      get: async () => {
        const rows = (await api("GET", `/api/db/${collection}`)) || [];
        const docs = rows.map((r) => snapDoc(r.id, r));
        return { docs, size: docs.length, empty: !docs.length };
      },
      onSnapshot(next) {
        const l = { kind: "col", path: collection, next, last: null };
        listeners.push(l);
        refresh(l);
        return () => listeners.splice(listeners.indexOf(l), 1);
      },
    };
  }

  const db = {
    collection: (p) => colRef(p),
    doc: (p) => { const [c, id] = p.split("/"); return docRef(c, id); },
  };

  async function sampleWithTools(input, opts) {
    const tools = opts.tools || [];
    const schema = tools.map((t) => ({ name: t.name, description: t.description || "", input_schema: t.inputSchema || { type: "object", properties: {} } }));
    const messages = (typeof input === "string" ? [{ role: "user", content: input }] : input.map((m) => ({ role: m.role, content: m.content })));
    let text = "";
    for (let round = 0; round < 6; round++) {
      if (opts.signal && opts.signal.aborted) throw { code: "cancelled", message: "cancelled", text };
      let r;
      try {
        r = await fetch("/api/llm/step", {
          method: "POST", headers: { "Content-Type": "application/json" }, credentials: "same-origin", signal: opts.signal,
          body: JSON.stringify({ messages, tools: round < 5 ? schema : [], tier: opts.modelTier || "default" }),
        });
      } catch (e) {
        throw { code: e && e.name === "AbortError" ? "cancelled" : "upstream_error", message: String(e), text };
      }
      let j = {};
      try { j = await r.json(); } catch (_) { /* corps vide */ }
      if (!r.ok) throw { code: j.code || "upstream_error", message: j.message || r.statusText, text };
      const blocks = j.content || [];
      const said = blocks.filter((b) => b.type === "text").map((b) => b.text).join("\n").trim();
      if (said) { text = text ? text + "\n\n" + said : said; if (opts.onText) opts.onText({ text, delta: said }); }
      const calls = blocks.filter((b) => b.type === "tool_use");
      if (!calls.length) break;
      messages.push({ role: "assistant", content: blocks });
      const results = [];
      for (const c of calls) {
        const tool = tools.find((t) => t.name === c.name);
        let out;
        try {
          if (!tool) throw new Error("unknown tool");
          out = await tool.execute(c.input || {}, { signal: opts.signal || new AbortController().signal });
          out = typeof out === "string" ? out : JSON.stringify(out ?? null);
        } catch (e) {
          out = "Error: " + (e && e.message ? e.message : String(e));
        }
        results.push({ type: "tool_result", tool_use_id: c.id, content: String(out).slice(0, 32000) });
      }
      messages.push({ role: "user", content: results });
    }
    if (!text.trim()) throw { code: "empty_completion", message: "Réponse vide" };
    return { text, truncated: false, modelTierApplied: opts.modelTier || "default" };
  }

  async function sample(input, opts = {}) {
    if (opts.tools && opts.tools.length) return sampleWithTools(input, opts);
    let r;
    try {
      r = await fetch("/api/llm/sample", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ input, tier: opts.modelTier || "default" }),
        signal: opts.signal,
        credentials: "same-origin",
      });
    } catch (e) {
      throw { code: e && e.name === "AbortError" ? "cancelled" : "upstream_error", message: String(e) };
    }
    if (!r.ok) {
      let j = {};
      try { j = await r.json(); } catch (_) { /* corps vide */ }
      throw { code: j.code || "upstream_error", message: j.message || r.statusText };
    }
    const reader = r.body.getReader();
    const dec = new TextDecoder();
    let text = "";
    try {
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        const delta = dec.decode(value, { stream: true });
        if (!delta) continue;
        text += delta;
        if (opts.onText) opts.onText({ text, delta });
      }
    } catch (e) {
      throw { code: e && e.name === "AbortError" ? "cancelled" : "upstream_error", message: String(e), text };
    }
    if (!text.trim()) throw { code: "empty_completion", message: "Réponse vide" };
    return { text, truncated: false, modelTierApplied: opts.modelTier || "default" };
  }

  const downloads = {
    async save({ filename, data }) {
      const blob = data instanceof Blob ? data : new Blob([data], { type: "application/octet-stream" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = filename;
      document.body.append(a);
      a.click();
      setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
    },
  };

  const assets = {
    async upload(blob, { type } = {}) {
      const r = await fetch("/api/assets", { method: "POST", headers: { "Content-Type": type || blob.type }, body: blob });
      if (!r.ok) throw { code: r.status === 415 ? "unsupported_type" : r.status === 413 ? "too_large" : "upload_failed", message: await r.text() };
      return r.json();
    },
    async delete(id) {
      await fetch("/api/assets/" + encodeURIComponent(id), { method: "DELETE" });
    },
  };

  sample.limits = async () => ({ maxPromptBytes: 262144, tools: { maxCount: 24 } });
  const caps = { db, sample, downloads, assets };
  window.claude = { use: async (name) => caps[name] || null };

  // Commande propre à l'application : lancer la veille et afficher le dernier passage.
  document.addEventListener("DOMContentLoaded", () => {
    const header = document.querySelector("header");
    if (!header) return;
    const bar = document.createElement("div");
    bar.className = "row";
    bar.style.marginTop = "10px";
    bar.innerHTML = '<button class="btn ghost sm" type="button" id="run-veille"></button><span class="meta" id="last-run"></span>';
    header.append(bar);
    let en = false;
    const runBtn = bar.querySelector("#run-veille");
    const last = bar.querySelector("#last-run");
    let lastRun = null;
    const paint = () => {
      en = (document.documentElement.lang || "fr") === "en";
      runBtn.textContent = en ? "Run the watch now" : "Lancer la veille maintenant";
      const r = lastRun;
      last.textContent = r
        ? `${en ? "Last run" : "Dernier passage"} : ${new Date(r.started_at).toLocaleString(en ? "en-GB" : "fr-FR")} · ${r.status === "running" ? (en ? "running" : "en cours") : r.status}`
        : (en ? "No run yet." : "Aucun passage pour l'instant.");
    };
    const showLast = () => fetch("/api/veille/runs").then((r) => r.json()).then((runs) => { lastRun = runs[0] || null; paint(); }).catch(() => {});
    new MutationObserver(paint).observe(document.documentElement, { attributes: true, attributeFilter: ["lang"] });
    runBtn.onclick = async () => {
      await fetch("/api/veille/run", { method: "POST" });
      last.textContent = en ? "Watch started: offers will appear over the next few minutes." : "Veille lancée : les offres apparaîtront au fil du passage (quelques minutes).";
      setTimeout(showLast, 15000);
    };
    paint();
    showLast();
  });
})();
