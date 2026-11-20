#!/usr/bin/env python3
"""Runnable demo: a two-step agent flow with a FailLoud guard between steps.

Step 1 (worker) produces an output that *claims* success. The guard
verifies it before step 2 (publisher) may act on it.

Run 1: the worker lies — it reports 12 emails over a 9-item record and
claims a publish action with no evidence. The guard blocks the run.
Run 2: the worker tells the truth. The guard passes it and the
publisher proceeds.

    PYTHONPATH=../../src python demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_step import BlockedStep, verify_step  # noqa: E402


def worker_output(sent_claim: int, items: int, with_evidence: bool) -> dict:
    doc = {
        "task": "Send the weekly digest and publish the summary card",
        "status": "done",
        "summary": f"Sent the digest to {sent_claim} subscribers.",
        "generated_at": "2026-11-18T10:00:00Z",
        "claims": [
            {"action": "email_sent", "target": "subscriber-list",
             "evidence": {"message_id": "msg_8f42", "provider": "mail"}},
            {"action": "card_published", "target": "community-feed"},
        ],
        "counts": {"sent": sent_claim},
        "items": {"sent": [f"reader{i:02d}@acme-digest.com"
                           for i in range(1, items + 1)]},
        "state": {"context": "subscriber snapshot",
                  "context_updated_at": "2026-11-18T09:35:00Z", "version": 9},
        "based_on": {"expected_state_version": 9},
        "output": {"body": "This week: the verification checklist.",
                   "subject": "Weekly digest",
                   "archive_url": "https://ops.acmehq.io/archive/9"},
        "segments": [{"id": "intro", "start": 0.0, "end": 4.0},
                     {"id": "main", "start": 4.0, "end": 9.0},
                     {"id": "outro", "start": 9.0, "end": 12.0}],
    }
    if with_evidence:
        doc["claims"][1]["evidence"] = {
            "post_id": "post_2481",
            "url": "https://community.acmehq.io/posts/2481",
        }
    return doc


def run(label: str, doc: dict) -> None:
    print(f"--- {label} ---")
    state = {"last_output": doc}
    try:
        update = verify_step(state)
    except BlockedStep as blocked:
        print(blocked)
        print("→ publisher node never ran. The lie stopped at the gate.\n")
        return
    print(f"guard: {update['verification']}")
    print("→ publisher node ran on a verified output.\n")


if __name__ == "__main__":
    run("Run 1: worker claims 12 sent, lists 9, publish has no evidence",
        worker_output(sent_claim=12, items=9, with_evidence=False))
    run("Run 2: worker reports exactly what it did",
        worker_output(sent_claim=9, items=9, with_evidence=True))
