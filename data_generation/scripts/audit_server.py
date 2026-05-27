#!/usr/bin/env python3
"""Run a small local browser UI for auditing morphology candidates."""

from __future__ import annotations

import argparse
import csv
import html
import json
from collections import Counter
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from common import read_jsonl, write_jsonl


DECISIONS = ["accept", "reject", "unsure"]
MORPH_CLASSES = [
    "",
    "target_broken_plural",
    "target_form_x_verb",
    "target_form_vii_verb",
    "target_active_participle",
    "target_passive_participle",
    "target_form_viii_participle",
    "target_verbal_noun",
    "target_intensive_adjective",
    "target_instrument_noun",
    "primitive_lexical",
    "proper_name_or_place",
    "foreign_or_loanword",
    "context_mismatch",
    "wrong_root",
    "wrong_template",
    "bad_affix_parse",
    "non_target",
    "unsure",
]
DATASET_USES = [
    "",
    "main_target",
    "secondary_primitive",
    "exclude",
    "needs_review",
]
REASONS = [
    "",
    "valid_clean",
    "valid_secondary_control",
    "bad_root",
    "bad_template",
    "bad_affix_parse",
    "context_mismatch",
    "proper_name",
    "place_name",
    "loanword",
    "primitive_lexical_item",
    "ambiguous",
    "out_of_scope",
    "other",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", required=True, type=Path)
    parser.add_argument("--audit-state", type=Path)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_items(path: Path) -> list[dict[str, Any]]:
    items = list(read_jsonl(path))
    for index, item in enumerate(items, 1):
        item.setdefault("audit_id", f"audit_{index:04d}")
    return items


def load_state(path: Path) -> dict[str, Any]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"created_at": utc_now(), "updated_at": utc_now(), "decisions": {}}


def summarize(items: list[dict[str, Any]], state: dict[str, Any]) -> dict[str, Any]:
    decisions = state.get("decisions", {})
    reviewed_items = [item for item in items if item["audit_id"] in decisions]
    decision_counts = Counter(decisions[item["audit_id"]].get("decision", "") for item in reviewed_items)
    reason_counts = Counter(decisions[item["audit_id"]].get("reason", "") for item in reviewed_items)
    morph_class_counts = Counter(decisions[item["audit_id"]].get("morph_class", "") for item in reviewed_items)
    dataset_use_counts = Counter(decisions[item["audit_id"]].get("dataset_use", "") for item in reviewed_items)
    by_template_reviewed = Counter(item.get("template", "") for item in reviewed_items)
    by_template_total = Counter(item.get("template", "") for item in items)
    return {
        "total_items": len(items),
        "reviewed_items": len(reviewed_items),
        "remaining_items": len(items) - len(reviewed_items),
        "decision_counts": dict(decision_counts),
        "reason_counts": dict(reason_counts),
        "morph_class_counts": dict(morph_class_counts),
        "dataset_use_counts": dict(dataset_use_counts),
        "by_template_total": dict(by_template_total),
        "by_template_reviewed": dict(by_template_reviewed),
    }


def write_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = utc_now()
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def enrich_items(items: list[dict[str, Any]], state: dict[str, Any]) -> list[dict[str, Any]]:
    decisions = state.get("decisions", {})
    enriched = []
    for item in items:
        row = dict(item)
        decision = decisions.get(item["audit_id"], {})
        row["audit_decision"] = decision.get("decision", "")
        row["audit_reason"] = decision.get("reason", "")
        row["morph_class"] = decision.get("morph_class", "")
        row["dataset_use"] = decision.get("dataset_use", "")
        row["audit_notes"] = decision.get("notes", "")
        row["corrected_root"] = decision.get("corrected_root", "")
        row["corrected_template"] = decision.get("corrected_template", "")
        row["reviewed_at"] = decision.get("reviewed_at", "")
        enriched.append(row)
    return enriched


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "audit_id",
        "audit_decision",
        "audit_reason",
        "morph_class",
        "dataset_use",
        "audit_notes",
        "corrected_root",
        "corrected_template",
        "full_form",
        "root",
        "template",
        "base_form",
        "surface_stem",
        "prefix",
        "suffix",
        "surface_rule",
        "pos",
        "camel_ambiguity",
        "camel_pattern",
        "camel_lex",
        "camel_gloss",
        "camel_source",
        "n_token_occurrences",
        "example_sentence",
        "example_source",
        "example_url",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            out = {field: row.get(field, "") for field in fields}
            analysis = row.get("camel_analysis") or {}
            out["camel_pattern"] = analysis.get("pattern", "")
            out["camel_lex"] = analysis.get("lex", "")
            out["camel_gloss"] = analysis.get("gloss", "")
            out["camel_source"] = analysis.get("source", "")
            writer.writerow(out)


def write_exports(items: list[dict[str, Any]], state: dict[str, Any], audit_state_path: Path) -> None:
    out_dir = audit_state_path.parent
    enriched = enrich_items(items, state)
    reviewed = [row for row in enriched if row["audit_decision"]]
    accepted = [row for row in reviewed if row["audit_decision"] == "accept"]
    rejected = [row for row in reviewed if row["audit_decision"] == "reject"]
    unsure = [row for row in reviewed if row["audit_decision"] == "unsure"]
    main_target = [row for row in reviewed if row["audit_decision"] == "accept" and row["dataset_use"] == "main_target"]
    secondary_primitive = [
        row for row in reviewed if row["audit_decision"] == "accept" and row["dataset_use"] == "secondary_primitive"
    ]
    excluded = [row for row in reviewed if row["audit_decision"] == "reject" or row["dataset_use"] == "exclude"]

    write_jsonl(out_dir / "audited_items.jsonl", reviewed)
    write_jsonl(out_dir / "accepted_items.jsonl", accepted)
    write_jsonl(out_dir / "rejected_items.jsonl", rejected)
    write_jsonl(out_dir / "unsure_items.jsonl", unsure)
    write_jsonl(out_dir / "main_target_items.jsonl", main_target)
    write_jsonl(out_dir / "secondary_primitive_items.jsonl", secondary_primitive)
    write_jsonl(out_dir / "excluded_items.jsonl", excluded)
    write_csv(out_dir / "audited_items.csv", reviewed)
    (out_dir / "audit_summary.json").write_text(
        json.dumps(summarize(items, state), ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


HTML_PAGE = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Arabic Morphology Audit</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --line: #d9dee7;
      --text: #151922;
      --muted: #667085;
      --accent: #1f6feb;
      --accept: #0f7b4f;
      --reject: #b42318;
      --unsure: #936900;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--text);
    }
    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 14px 20px;
      border-bottom: 1px solid var(--line);
      background: var(--panel);
      position: sticky;
      top: 0;
      z-index: 2;
    }
    h1 { font-size: 17px; margin: 0; }
    main {
      max-width: 1180px;
      margin: 0 auto;
      padding: 18px;
      display: grid;
      grid-template-columns: minmax(0, 1fr) 340px;
      gap: 16px;
    }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
    }
    .topline {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 12px;
    }
    .word {
      font-size: 42px;
      font-weight: 750;
      direction: rtl;
      text-align: right;
      line-height: 1.2;
    }
    .meta-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      margin: 16px 0;
    }
    .meta {
      border: 1px solid var(--line);
      border-radius: 7px;
      padding: 10px;
      min-height: 64px;
    }
    .label {
      font-size: 11px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: .02em;
      margin-bottom: 5px;
    }
    .value {
      font-size: 17px;
      font-weight: 650;
      direction: rtl;
      text-align: right;
      overflow-wrap: anywhere;
    }
    .sentence {
      direction: rtl;
      text-align: right;
      font-size: 24px;
      line-height: 1.9;
      padding: 14px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfcfe;
    }
    mark {
      background: #fff1a8;
      padding: 2px 4px;
      border-radius: 4px;
    }
    .source {
      color: var(--muted);
      margin-top: 12px;
      font-size: 13px;
      overflow-wrap: anywhere;
    }
    .controls {
      display: grid;
      gap: 10px;
    }
    button, select, input, textarea {
      font: inherit;
      border: 1px solid var(--line);
      border-radius: 7px;
      background: #fff;
    }
    button {
      cursor: pointer;
      padding: 10px 12px;
      font-weight: 650;
    }
    button.primary { border-color: var(--accent); color: var(--accent); }
    button.accept { border-color: var(--accept); color: var(--accept); }
    button.reject { border-color: var(--reject); color: var(--reject); }
    button.unsure { border-color: var(--unsure); color: var(--unsure); }
    button.active {
      color: #fff;
      background: var(--accent);
      border-color: var(--accent);
    }
    button.accept.active { background: var(--accept); border-color: var(--accept); }
    button.reject.active { background: var(--reject); border-color: var(--reject); }
    button.unsure.active { background: var(--unsure); border-color: var(--unsure); }
    .button-row {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px;
    }
    .nav-row {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px;
    }
    select, input, textarea {
      width: 100%;
      padding: 9px 10px;
    }
    textarea {
      min-height: 78px;
      resize: vertical;
    }
    .progress {
      height: 9px;
      background: #edf0f5;
      border-radius: 99px;
      overflow: hidden;
    }
    .progress > div {
      height: 100%;
      background: var(--accent);
      width: 0%;
    }
    .summary {
      font-size: 13px;
      color: var(--muted);
      line-height: 1.7;
      white-space: pre-wrap;
    }
    .small {
      font-size: 12px;
      color: var(--muted);
    }
    @media (max-width: 880px) {
      main { grid-template-columns: 1fr; }
      .meta-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
  </style>
</head>
<body>
  <header>
    <h1>Arabic Morphology Audit</h1>
    <div class="small" id="status">Loading...</div>
  </header>
  <main>
    <section class="panel">
      <div class="topline">
        <div class="small" id="position"></div>
        <div class="small" id="auditId"></div>
      </div>
      <div class="word" id="word"></div>
      <div class="meta-grid">
        <div class="meta"><div class="label">Root</div><div class="value" id="root"></div></div>
        <div class="meta"><div class="label">Template</div><div class="value" id="template"></div></div>
        <div class="meta"><div class="label">Base</div><div class="value" id="base"></div></div>
        <div class="meta"><div class="label">Surface Stem</div><div class="value" id="surfaceStem"></div></div>
        <div class="meta"><div class="label">Prefix</div><div class="value" id="prefix"></div></div>
        <div class="meta"><div class="label">Suffix</div><div class="value" id="suffix"></div></div>
        <div class="meta"><div class="label">POS</div><div class="value" id="pos"></div></div>
        <div class="meta"><div class="label">Occurrences</div><div class="value" id="occurrences"></div></div>
        <div class="meta"><div class="label">CAMEL Pattern</div><div class="value" id="camelPattern"></div></div>
        <div class="meta"><div class="label">CAMEL Lex</div><div class="value" id="camelLex"></div></div>
        <div class="meta"><div class="label">CAMEL Gloss</div><div class="value" id="camelGloss"></div></div>
        <div class="meta"><div class="label">Audit Hint</div><div class="value" id="auditHint"></div></div>
      </div>
      <div class="sentence" id="sentence"></div>
      <div class="source" id="source"></div>
    </section>
    <aside class="panel controls">
      <div>
        <div class="progress"><div id="bar"></div></div>
        <div class="summary" id="summary"></div>
      </div>
      <div class="button-row">
        <button class="accept" id="acceptBtn">Accept</button>
        <button class="reject" id="rejectBtn">Reject</button>
        <button class="unsure" id="unsureBtn">Unsure</button>
      </div>
      <label>
        <div class="label">Reason</div>
        <select id="reason"></select>
      </label>
      <label>
        <div class="label">Morphology Class</div>
        <select id="morphClass"></select>
      </label>
      <label>
        <div class="label">Dataset Use</div>
        <select id="datasetUse"></select>
      </label>
      <label>
        <div class="label">Corrected Root</div>
        <input id="correctedRoot" placeholder="optional" />
      </label>
      <label>
        <div class="label">Corrected Template</div>
        <input id="correctedTemplate" placeholder="optional" />
      </label>
      <label>
        <div class="label">Notes</div>
        <textarea id="notes" placeholder="optional"></textarea>
      </label>
      <button class="primary" id="saveBtn">Save Decision</button>
      <div class="nav-row">
        <button id="prevBtn">Previous</button>
        <button id="nextBtn">Next</button>
        <button id="nextOpenBtn">Next Open</button>
      </div>
      <label>
        <div class="label">Jump To Item</div>
        <input id="jump" type="number" min="1" />
      </label>
      <div class="small">
        Shortcuts: A accept, R reject, U unsure, S save, N next open, arrow keys navigate.
      </div>
    </aside>
  </main>
  <script>
    let items = [];
    let decisions = {};
    let summary = {};
    let index = 0;
    let currentDecision = "";

    const reasons = REASONS_JSON;
    const morphClasses = MORPH_CLASSES_JSON;
    const datasetUses = DATASET_USES_JSON;

    function esc(s) {
      return String(s ?? "").replace(/[&<>"']/g, c => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
      }[c]));
    }

    function regexEsc(s) {
      return String(s).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    }

    function highlight(sentence, word) {
      const safe = esc(sentence);
      if (!word) return safe;
      const pattern = new RegExp(regexEsc(esc(word)), "g");
      return safe.replace(pattern, "<mark>" + esc(word) + "</mark>");
    }

    async function api(path, options) {
      const res = await fetch(path, options);
      if (!res.ok) throw new Error(await res.text());
      return await res.json();
    }

    async function load() {
      const data = await api("/api/items");
      items = data.items;
      decisions = data.decisions || {};
      summary = data.summary || {};
      const reasonSelect = document.getElementById("reason");
      reasonSelect.innerHTML = reasons.map(r => `<option value="${esc(r)}">${esc(r || "none")}</option>`).join("");
      const morphClassSelect = document.getElementById("morphClass");
      morphClassSelect.innerHTML = morphClasses.map(r => `<option value="${esc(r)}">${esc(r || "none")}</option>`).join("");
      const datasetUseSelect = document.getElementById("datasetUse");
      datasetUseSelect.innerHTML = datasetUses.map(r => `<option value="${esc(r)}">${esc(r || "none")}</option>`).join("");
      render();
    }

    function item() { return items[index]; }

    function render() {
      const it = item();
      const dec = decisions[it.audit_id] || {};
      currentDecision = dec.decision || "";
      document.getElementById("status").textContent = `${summary.reviewed_items || 0}/${summary.total_items || items.length} reviewed`;
      document.getElementById("position").textContent = `Item ${index + 1} of ${items.length}`;
      document.getElementById("auditId").textContent = it.audit_id || "";
      document.getElementById("word").textContent = it.full_form || "";
      document.getElementById("root").textContent = it.root || "";
      document.getElementById("template").textContent = it.template || "";
      document.getElementById("base").textContent = it.base_form || it.canonical_base_form || "";
      document.getElementById("surfaceStem").textContent = it.surface_stem || "";
      document.getElementById("prefix").textContent = it.prefix || "none";
      document.getElementById("suffix").textContent = it.suffix || "none";
      document.getElementById("pos").textContent = it.pos || "";
      document.getElementById("occurrences").textContent = it.n_token_occurrences || "";
      const analysis = it.camel_analysis || {};
      document.getElementById("camelPattern").textContent = analysis.pattern || "";
      document.getElementById("camelLex").textContent = analysis.lex || "";
      document.getElementById("camelGloss").textContent = analysis.gloss || "";
      document.getElementById("auditHint").textContent = it.audit_hint || it.audit_bucket || "";
      document.getElementById("sentence").innerHTML = highlight(it.example_sentence || "", it.full_form || "");
      document.getElementById("source").textContent = `${it.example_source || ""} ${it.example_url || ""}`;
      document.getElementById("reason").value = dec.reason || "";
      document.getElementById("morphClass").value = dec.morph_class || it.suggested_morph_class || "";
      document.getElementById("datasetUse").value = dec.dataset_use || it.suggested_dataset_use || "";
      document.getElementById("correctedRoot").value = dec.corrected_root || "";
      document.getElementById("correctedTemplate").value = dec.corrected_template || "";
      document.getElementById("notes").value = dec.notes || "";
      document.getElementById("jump").value = index + 1;
      for (const [id, value] of [["acceptBtn","accept"],["rejectBtn","reject"],["unsureBtn","unsure"]]) {
        const btn = document.getElementById(id);
        btn.classList.toggle("active", currentDecision === value);
      }
      const pct = items.length ? Math.round((summary.reviewed_items || 0) * 100 / items.length) : 0;
      document.getElementById("bar").style.width = pct + "%";
      document.getElementById("summary").textContent =
        `Reviewed: ${summary.reviewed_items || 0}\nRemaining: ${summary.remaining_items ?? items.length}\n` +
        `Decisions: ${JSON.stringify(summary.decision_counts || {})}\nReasons: ${JSON.stringify(summary.reason_counts || {})}\n` +
        `Morph: ${JSON.stringify(summary.morph_class_counts || {})}\nUse: ${JSON.stringify(summary.dataset_use_counts || {})}`;
    }

    function setDecision(value) {
      currentDecision = value;
      if (value === "accept" && !document.getElementById("reason").value) {
        document.getElementById("reason").value = "valid_clean";
      }
      if (value === "reject" && !document.getElementById("datasetUse").value) {
        document.getElementById("datasetUse").value = "exclude";
      }
      if (value === "unsure" && !document.getElementById("datasetUse").value) {
        document.getElementById("datasetUse").value = "needs_review";
      }
      for (const [id, v] of [["acceptBtn","accept"],["rejectBtn","reject"],["unsureBtn","unsure"]]) {
        document.getElementById(id).classList.toggle("active", v === value);
      }
    }

    async function saveDecision(moveNextOpen = false) {
      const it = item();
      if (!currentDecision) {
        alert("Choose accept, reject, or unsure first.");
        return;
      }
      const payload = {
        audit_id: it.audit_id,
        decision: currentDecision,
        reason: document.getElementById("reason").value,
        morph_class: document.getElementById("morphClass").value,
        dataset_use: document.getElementById("datasetUse").value,
        corrected_root: document.getElementById("correctedRoot").value,
        corrected_template: document.getElementById("correctedTemplate").value,
        notes: document.getElementById("notes").value
      };
      const data = await api("/api/decision", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload)
      });
      decisions = data.decisions;
      summary = data.summary;
      if (moveNextOpen) nextOpen(); else render();
    }

    function prev() { index = Math.max(0, index - 1); render(); }
    function next() { index = Math.min(items.length - 1, index + 1); render(); }
    function nextOpen() {
      for (let i = index + 1; i < items.length; i++) {
        if (!decisions[items[i].audit_id]) { index = i; render(); return; }
      }
      for (let i = 0; i <= index; i++) {
        if (!decisions[items[i].audit_id]) { index = i; render(); return; }
      }
      render();
    }

    document.getElementById("acceptBtn").onclick = () => setDecision("accept");
    document.getElementById("rejectBtn").onclick = () => setDecision("reject");
    document.getElementById("unsureBtn").onclick = () => setDecision("unsure");
    document.getElementById("saveBtn").onclick = () => saveDecision(false);
    document.getElementById("prevBtn").onclick = prev;
    document.getElementById("nextBtn").onclick = next;
    document.getElementById("nextOpenBtn").onclick = nextOpen;
    document.getElementById("jump").onchange = e => {
      const target = Number(e.target.value) - 1;
      if (target >= 0 && target < items.length) { index = target; render(); }
    };
    document.addEventListener("keydown", e => {
      if (["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement.tagName)) return;
      if (e.key === "a" || e.key === "A") setDecision("accept");
      if (e.key === "r" || e.key === "R") setDecision("reject");
      if (e.key === "u" || e.key === "U") setDecision("unsure");
      if (e.key === "s" || e.key === "S") saveDecision(true);
      if (e.key === "n" || e.key === "N") nextOpen();
      if (e.key === "ArrowLeft") next();
      if (e.key === "ArrowRight") prev();
    });
    load().catch(err => {
      document.getElementById("status").textContent = String(err);
      console.error(err);
    });
  </script>
</body>
</html>
"""


class AuditHandler(BaseHTTPRequestHandler):
    items: list[dict[str, Any]] = []
    state: dict[str, Any] = {}
    audit_state_path: Path

    def send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            page = HTML_PAGE.replace("REASONS_JSON", json.dumps(REASONS))
            page = page.replace("MORPH_CLASSES_JSON", json.dumps(MORPH_CLASSES))
            page = page.replace("DATASET_USES_JSON", json.dumps(DATASET_USES))
            body = page.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif path == "/api/items":
            self.send_json(
                {
                    "items": self.items,
                    "decisions": self.state.get("decisions", {}),
                    "summary": summarize(self.items, self.state),
                    "labels": {
                        "decisions": DECISIONS,
                        "reasons": REASONS,
                        "morph_classes": MORPH_CLASSES,
                        "dataset_uses": DATASET_USES,
                    },
                }
            )
        elif path == "/api/summary":
            self.send_json(summarize(self.items, self.state))
        else:
            self.send_json({"error": "not found"}, status=404)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path != "/api/decision":
            self.send_json({"error": "not found"}, status=404)
            return

        length = int(self.headers.get("Content-Length", "0"))
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except json.JSONDecodeError:
            self.send_json({"error": "invalid json"}, status=400)
            return

        audit_id = payload.get("audit_id")
        decision = payload.get("decision", "")
        if audit_id not in {item["audit_id"] for item in self.items}:
            self.send_json({"error": "unknown audit_id"}, status=400)
            return
        if decision not in DECISIONS:
            self.send_json({"error": "invalid decision"}, status=400)
            return

        self.state.setdefault("decisions", {})[audit_id] = {
            "decision": decision,
            "reason": payload.get("reason", ""),
            "morph_class": payload.get("morph_class", ""),
            "dataset_use": payload.get("dataset_use", ""),
            "notes": payload.get("notes", ""),
            "corrected_root": payload.get("corrected_root", ""),
            "corrected_template": payload.get("corrected_template", ""),
            "reviewed_at": utc_now(),
        }
        write_state(self.audit_state_path, self.state)
        write_exports(self.items, self.state, self.audit_state_path)
        self.send_json({"decisions": self.state["decisions"], "summary": summarize(self.items, self.state)})

    def log_message(self, format: str, *args: Any) -> None:
        return


def main() -> None:
    args = parse_args()
    audit_state_path = args.audit_state or args.sample.with_name("audit_state.json")
    items = load_items(args.sample)
    state = load_state(audit_state_path)
    write_state(audit_state_path, state)
    write_exports(items, state, audit_state_path)

    AuditHandler.items = items
    AuditHandler.state = state
    AuditHandler.audit_state_path = audit_state_path

    server = ThreadingHTTPServer((args.host, args.port), AuditHandler)
    url = f"http://{args.host}:{args.port}"
    print(f"Audit UI: {url}")
    print(f"sample: {args.sample}")
    print(f"audit state: {audit_state_path}")
    print("Press Ctrl-C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
