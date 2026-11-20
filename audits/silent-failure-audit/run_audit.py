#!/usr/bin/env python3
"""The Silent Failure Audit — a reproducible dataset + measurement.

Question: when an AI agent's output claims ``status: "done"`` while
shipping one of the six silent failures, does a deterministic check
catch it — and does the same check leave genuinely clean outputs alone?

Method
------
* 70 synthetic agent outputs, built deterministically by this script
  (no randomness, no hand-written results):
  * 60 *defective* outputs — 10 per silent-failure pattern
    (FL001–FL006). Each claims ``done``; each carries exactly one
    planted defect of its pattern, in one of 10 surface scenarios
    (newsletter, ticket export, invoice batch, social post, CRM sync,
    report publish, podcast cut, inventory update, release notes,
    meeting-notes distribution).
  * 10 *clean* control outputs that claim ``done`` and are, in fact,
    complete — the false-alarm control group.
* Every case is run through ``failloud.check_output`` with the default
  configuration. A defective case counts as *caught* when the check
  for its planted pattern fires at error severity. A clean case counts
  as *passed* when the overall verdict is PASS.

Outputs (written next to this script)
-------------------------------------
* ``cases.json``   — the full dataset (the outputs themselves).
* ``results.json`` — per-case verdicts + aggregate statistics.
* ``results.md``   — the human-readable summary the docs page quotes.

Reproduce: ``python run_audit.py`` (needs ``failloud`` importable —
run from a checkout with ``PYTHONPATH=src`` or an installed package).
Every number on the Silent Failure Audit page comes from this script.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from failloud import __version__, check_output  # noqa: E402

HERE = Path(__file__).resolve().parent

GEN_AT = "2026-11-18T10:00:00Z"
FRESH_AT = "2026-11-18T09:35:00Z"   # 25 minutes before the run
STALE_AT = "2026-11-15T08:53:00Z"   # ~73 hours before the run

# Ten surface scenarios. Each is a skin over the same FailLoud document
# shape: claims with evidence, counts reconciled against items, state
# with a freshness timestamp and version, a segmented deliverable, and
# a payload. `n` = the true number of items handled.
SCENARIOS = [
    dict(task="Send the weekly product digest to the subscriber list",
         action_a="email_sent", action_b="card_published",
         target_a="subscriber-list", target_b="community-feed",
         item="reader{:02d}@acme-digest.com", n=9,
         subject="Weekly digest", body="This week: the verification checklist, two reader questions, and the December roadmap."),
    dict(task="Export the resolved support tickets to the helpdesk archive",
         action_a="tickets_exported", action_b="archive_published",
         target_a="helpdesk", target_b="archive",
         item="ticket-{:04d}", n=14,
         subject="Resolved tickets export", body="Fourteen resolved tickets exported with full transcripts and resolution notes attached."),
    dict(task="Run the monthly invoice batch for active accounts",
         action_a="invoices_issued", action_b="ledger_posted",
         target_a="billing", target_b="ledger",
         item="INV-2026-{:03d}", n=7,
         subject="November invoice batch", body="Seven invoices issued; totals reconciled against the ledger before posting."),
    dict(task="Publish the launch announcement to all social channels",
         action_a="post_published", action_b="thread_scheduled",
         target_a="social-feed", target_b="scheduler",
         item="post-{:02d}", n=5,
         subject="Launch announcement", body="The launch post is live with the demo link and the release notes thread scheduled."),
    dict(task="Sync the cleaned contact list into the CRM",
         action_a="contacts_synced", action_b="sync_report_filed",
         target_a="crm", target_b="ops-log",
         item="contact-{:04d}", n=21,
         subject="CRM sync", body="Twenty-one contacts deduplicated, merged, and synced; the sync report is filed."),
    dict(task="Publish the quarterly metrics report to the team wiki",
         action_a="report_published", action_b="charts_embedded",
         target_a="team-wiki", target_b="report",
         item="chart-{:02d}", n=6,
         subject="Quarterly metrics report", body="The report is published with all six charts embedded and the methodology appendix attached."),
    dict(task="Cut the interview recording into publishable segments",
         action_a="segments_cut", action_b="episode_uploaded",
         target_a="editor", target_b="podcast-host",
         item="seg-{:02d}", n=3,
         subject="Interview episode cut", body="Three segments cut clean, loudness matched, and the episode uploaded for review."),
    dict(task="Apply the overnight inventory adjustments to the catalogue",
         action_a="stock_updated", action_b="adjustment_log_written",
         target_a="catalogue", target_b="warehouse-log",
         item="SKU-{:05d}", n=18,
         subject="Inventory adjustment", body="Eighteen SKUs adjusted to the overnight counts; the adjustment log is written."),
    dict(task="Publish the release notes for the new version",
         action_a="notes_published", action_b="changelog_updated",
         target_a="docs-site", target_b="changelog",
         item="note-{:02d}", n=8,
         subject="Release notes", body="Release notes published with the migration guide linked and the changelog updated."),
    dict(task="Distribute the meeting notes to all attendees",
         action_a="notes_sent", action_b="actions_filed",
         target_a="attendees", target_b="tracker",
         item="attendee-{:02d}", n=11,
         subject="Meeting notes", body="Notes sent to all eleven attendees with decisions and action items filed in the tracker."),
]


def base_doc(s: dict) -> dict:
    """A clean, genuinely-done agent output in scenario `s`'s skin."""
    items = [s["item"].format(i + 1) for i in range(s["n"])]
    return {
        "task": s["task"],
        "status": "done",
        "summary": f"{s['task']} — completed for {s['n']} items.",
        "generated_at": GEN_AT,
        "claims": [
            {"action": s["action_a"], "target": s["target_a"],
             "evidence": {"record_id": f"rec-{s['n']}01", "provider": "ops"}},
            {"action": s["action_b"], "target": s["target_b"],
             "evidence": {"record_id": f"rec-{s['n']}02",
                          "url": f"https://ops.acmehq.io/{s['target_b']}/1"}},
        ],
        "counts": {"handled": s["n"]},
        "items": {"handled": items},
        "state": {"context": f"{s['target_a']} snapshot used for the run",
                  "context_updated_at": FRESH_AT, "version": 9},
        "based_on": {"expected_state_version": 9},
        "output": {"body": s["body"], "subject": s["subject"],
                   "archive_url": f"https://ops.acmehq.io/archive/{s['n']}"},
        "segments": [
            {"id": "intro", "start": 0.0, "end": 4.0},
            {"id": "main", "start": 4.0, "end": 9.0},
            {"id": "outro", "start": 9.0, "end": 12.0},
        ],
    }


def rag_doc(variant: int) -> dict:
    """A clean RAG answer: every citation resolves, every number sourced."""
    return {
        "task": "Answer the customer's pricing question from the retrieved help pages",
        "status": "done",
        "answer": "The Pro plan costs 29 dollars a month [1] and includes 10 seats [2].",
        "citations": ["pricing", "seats"],
        "sources": [
            {"id": "pricing", "text": "The Pro plan costs 29 dollars a month."},
            {"id": "seats", "text": "The Pro plan includes 10 seats by default."},
        ],
        "_variant": variant,
    }


# --- defect planters: each takes a clean doc and plants ONE defect ----

def plant_fl001(doc: dict, i: int) -> dict:
    doc["output"]["body"] = (
        "Lorem ipsum dolor sit amet, {{customer_name}}, your update is "
        "coming soon. TODO: replace with the real summary."
    )
    return doc


def plant_fl002(doc: dict, i: int) -> dict:
    # The second claimed action keeps its claim, loses all its evidence.
    doc["claims"][1] = {"action": doc["claims"][1]["action"],
                        "target": doc["claims"][1]["target"]}
    return doc


def plant_fl003(doc: dict, i: int) -> dict:
    mode = i % 3
    if mode == 0:      # stale timestamp
        doc["state"]["context_updated_at"] = STALE_AT
    elif mode == 1:    # no freshness timestamp at all
        del doc["state"]["context_updated_at"]
    else:              # version skew: promised 9, carried 7
        doc["state"]["version"] = 7
    return doc


def plant_fl004(doc: dict, i: int) -> dict:
    # Report more handled than the itemized record contains.
    doc["counts"]["handled"] = doc["counts"]["handled"] + (2 + i % 4)
    return doc


def plant_fl005(doc: dict, i: int) -> dict:
    mode = i % 2
    if mode == 0:      # zero-length middle segment
        doc["segments"][1] = {"id": "main", "start": 4.0, "end": 4.0}
        doc["segments"][2] = {"id": "outro", "start": 9.5, "end": 12.0}
    else:              # dead stretch: a 5.5s silence before the outro
        doc["segments"][2] = {"id": "outro", "start": 14.5, "end": 17.5}
    return doc


def plant_fl006(doc: dict, i: int) -> dict:
    mode = i % 4
    if mode == 0:      # cites a source retrieval never returned
        doc["citations"] = ["pricing", "seats", "refund_policy"]
        doc["answer"] += " Refunds are issued within 3 days [3]."
    elif mode == 1:    # phantom inline citation marker
        doc["answer"] += " See the enterprise addendum [9]."
    elif mode == 2:    # invented number: sources say 10 seats
        doc["answer"] = doc["answer"].replace("10 seats", "25 seats")
    else:              # a cited source that carries no text at all
        doc["sources"].append({"id": "limits", "text": ""})
        doc["citations"] = ["pricing", "seats", "limits"]
        doc["answer"] += " Usage limits are described in the limits page [3]."
    return doc


PLANTERS = {"FL001": plant_fl001, "FL002": plant_fl002, "FL003": plant_fl003,
            "FL004": plant_fl004, "FL005": plant_fl005, "FL006": plant_fl006}
CHECK_FOR_RAG = "FL006"


def build_cases() -> list[dict]:
    cases: list[dict] = []
    for check_id in ["FL001", "FL002", "FL003", "FL004", "FL005"]:
        for i, skin in enumerate(SCENARIOS):
            doc = PLANTERS[check_id](base_doc(skin), i)
            cases.append({"id": f"{check_id.lower()}-{i + 1:02d}",
                          "intended_pattern": check_id,
                          "claimed_status": doc["status"], "doc": doc})
    for i in range(10):
        doc = plant_fl006(rag_doc(i), i)
        doc.pop("_variant", None)
        cases.append({"id": f"fl006-{i + 1:02d}", "intended_pattern": "FL006",
                      "claimed_status": doc["status"], "doc": doc})
    for i, skin in enumerate(SCENARIOS[:8]):
        doc = base_doc(skin)
        cases.append({"id": f"clean-{i + 1:02d}", "intended_pattern": "clean",
                      "claimed_status": doc["status"], "doc": doc})
    for i in range(2):
        doc = rag_doc(i)
        doc.pop("_variant", None)
        cases.append({"id": f"clean-rag-{i + 1:02d}",
                      "intended_pattern": "clean",
                      "claimed_status": doc["status"], "doc": doc})
    return cases


def main() -> None:
    cases = build_cases()
    rows = []
    for case in cases:
        result = check_output(case["doc"])
        fired = sorted({f.check_id for f in result.findings})
        intended = case["intended_pattern"]
        if intended == "clean":
            ok = result.passed and not result.errors
        else:
            ok = any(f.check_id == intended and f.severity.value == "error"
                     for f in result.findings)
        warned = any(f.check_id == intended and f.severity.value == "warning"
                     for f in result.findings)
        rows.append({
            "id": case["id"], "intended_pattern": intended,
            "verdict": result.verdict, "passed": result.passed,
            "caught": ok, "intended_check_warned": warned,
            "checks_fired": fired,
            "error_count": len(result.errors),
            "warning_count": len(result.warnings),
        })

    defective = [r for r in rows if r["intended_pattern"] != "clean"]
    clean = [r for r in rows if r["intended_pattern"] == "clean"]
    per_check = {}
    for check_id in ["FL001", "FL002", "FL003", "FL004", "FL005", "FL006"]:
        group = [r for r in defective if r["intended_pattern"] == check_id]
        per_check[check_id] = {
            "cases": len(group),
            "caught": sum(1 for r in group if r["caught"]),
            "total_errors": sum(r["error_count"] for r in group),
        }
    summary = {
        "failloud_version": __version__,
        "total_cases": len(rows),
        "defective_cases": len(defective),
        "clean_cases": len(clean),
        "defective_caught": sum(1 for r in defective if r["caught"]),
        "defective_missed": [r["id"] for r in defective if not r["caught"]],
        "defective_warned_only": [r["id"] for r in defective
                                  if not r["caught"]
                                  and r["intended_check_warned"]],
        "clean_passed": sum(1 for r in clean if r["caught"]),
        "clean_failed": [r["id"] for r in clean if not r["caught"]],
        "total_errors": sum(r["error_count"] for r in rows),
        "total_warnings": sum(r["warning_count"] for r in rows),
        "per_check": per_check,
    }

    (HERE / "cases.json").write_text(
        json.dumps(cases, indent=2, sort_keys=True) + "\n")
    (HERE / "results.json").write_text(json.dumps(
        {"summary": summary, "cases": rows}, indent=2, sort_keys=True) + "\n")

    pct = 100.0 * summary["defective_caught"] / summary["defective_cases"]
    lines = [
        "# The Silent Failure Audit — results",
        "",
        f"Generated by `run_audit.py` against FailLoud {__version__}. "
        "Do not edit by hand — re-run the script.",
        "",
        f"- **{summary['defective_cases']} outputs claimed `done` while "
        f"shipping a silent failure. FailLoud caught "
        f"{summary['defective_caught']} of them ({pct:.1f}%).**",
        f"- **{summary['clean_cases']} genuinely clean outputs claimed "
        f"`done`. {summary['clean_passed']} passed with no error — "
        f"{summary['clean_cases'] - summary['clean_passed']} false alarms.**",
        f"- Total findings across the dataset: {summary['total_errors']} "
        f"errors, {summary['total_warnings']} warnings.",
        "",
        "| Planted pattern | Cases | Caught | Errors raised |",
        "|---|---|---|---|",
    ]
    names = {"FL001": "placeholder_shipped", "FL002": "unbacked_claim",
             "FL003": "stale_state", "FL004": "count_mismatch",
             "FL005": "missing_components", "FL006": "unsupported_answer"}
    for check_id, stats in per_check.items():
        lines.append(f"| {check_id} `{names[check_id]}` | {stats['cases']} "
                     f"| {stats['caught']} | {stats['total_errors']} |")
    if summary["defective_missed"]:
        lines += ["", f"Missed (no error from the planted pattern's check): "
                      f"{', '.join(summary['defective_missed'])}"]
    if summary["defective_warned_only"]:
        lines += [f"Flagged as warning only: "
                  f"{', '.join(summary['defective_warned_only'])} — the "
                  "no-freshness-timestamp variant of FL003 raises a warning, "
                  "not an error, so those runs still pass overall. Reported "
                  "as found; it is the one gap this audit exposes."]
    if summary["clean_failed"]:
        lines += ["", f"Clean cases that failed: "
                      f"{', '.join(summary['clean_failed'])}"]
    (HERE / "results.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
