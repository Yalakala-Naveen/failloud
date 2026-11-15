"""Second-pass verification: provisional verdicts re-judged against a
system-of-record snapshot.

The case under test is the one that motivated the feature (LinkedIn
launch thread, Nov 12, 2026): an output that is internally consistent —
"9 sent", 9 items, every claim carrying an id — and still wrong, because
one message bounced after the run reported success. The first pass can
only call that a provisional PASS; the second pass is where the world
gets its say.
"""

import json

from failloud import check_output, provisional_label, recheck_output
from failloud.cli import main

ORIGINAL = {
    "status": "done",
    "generated_at": "2026-11-14T09:00:00Z",
    "claims": [
        {"action": "email_sent", "target": "a@x.com", "evidence": {"message_id": "m1"}},
        {"action": "email_sent", "target": "b@x.com", "evidence": {"message_id": "m2"}},
        {"action": "email_sent", "target": "c@x.com", "evidence": {"message_id": "m3"}},
    ],
    "counts": {"sent": 3, "delivered": 3},
    "items": {"sent": ["a@x.com", "b@x.com", "c@x.com"],
              "delivered": ["a@x.com", "b@x.com", "c@x.com"]},
    "output": {"body": "Real deliverable body."},
}

CONFIRMING_RECORD = {
    "delivered": [{"message_id": "m1"}, {"message_id": "m2"}, {"message_id": "m3"}],
    "counts": {"sent": 3, "delivered": 3},
}

BOUNCE_RECORD = {
    "delivered": [{"message_id": "m1"}, {"message_id": "m2"}],
    "bounced": [{"message_id": "m3", "reason": "mailbox not found"}],
    "counts": {"delivered": 2, "bounced": 1},
}


# -- provisional labels --------------------------------------------------------


def test_passing_verdict_is_provisional():
    assert provisional_label(check_output(ORIGINAL)) == "PROVISIONAL PASS"


def test_failing_verdict_is_final_not_provisional():
    failing = {"status": "done", "output": {"body": "Lorem ipsum."}}
    assert provisional_label(check_output(failing)) == "FAIL"
    result = recheck_output(failing, CONFIRMING_RECORD)
    assert result.provisional is False
    assert result.verdict == "FAIL"  # a record cannot resurrect a FAIL


# -- claim outcomes --------------------------------------------------------------


def test_record_confirms_every_claim_and_count():
    result = recheck_output(ORIGINAL, CONFIRMING_RECORD)
    assert result.verdict == "CONFIRMED"
    assert result.confirmed is True
    assert [c.status for c in result.claims] == ["confirmed"] * 3
    assert [c.status for c in result.counts] == ["confirmed"] * 2


def test_bounced_message_contradicts_its_claim():
    result = recheck_output(ORIGINAL, BOUNCE_RECORD)
    assert result.verdict == "CONTRADICTED"
    by_target = {c.target: c.status for c in result.claims}
    assert by_target == {"a@x.com": "confirmed", "b@x.com": "confirmed",
                         "c@x.com": "contradicted"}


def test_status_field_marks_failure_even_under_a_neutral_key():
    record = {"events": [{"message_id": "m1", "status": "bounced"},
                         {"message_id": "m2", "status": "delivered"},
                         {"message_id": "m3", "status": "delivered"}],
              "counts": {"sent": 3, "delivered": 3}}
    result = recheck_output(ORIGINAL, record)
    assert result.claims[0].status == "contradicted"
    assert result.verdict == "CONTRADICTED"


def test_silence_in_the_record_is_unverifiable_never_confirmed():
    result = recheck_output(ORIGINAL, {"unrelated": "export", "rows": []})
    assert result.verdict == "UNVERIFIABLE"
    assert result.confirmed is False
    assert all(c.status == "unverifiable" for c in result.claims)


def test_claim_without_evidence_is_unverifiable():
    # FL002 already fails this output at the first pass (a claim with no
    # evidence), so the verdict stays FAIL — final, not provisional. The
    # claim's own second-pass status is still reported honestly: with no
    # evidence identifiers there is nothing for the record to confirm.
    original = {"status": "done",
                "claims": [{"action": "email_sent", "target": "a@x.com"}],
                "output": {"body": "Real deliverable body."}}
    result = recheck_output(original, CONFIRMING_RECORD)
    assert result.claims[0].status == "unverifiable"
    assert result.verdict == "FAIL"


def test_planned_and_failed_claims_are_not_rechecked():
    original = {"status": "done",
                "claims": [
                    {"action": "email_sent", "status": "planned"},
                    {"action": "email_sent", "status": "failed"},
                ],
                "output": {"body": "Real deliverable body."}}
    assert recheck_output(original, CONFIRMING_RECORD).claims == []


# -- count outcomes ---------------------------------------------------------------


def test_count_contradicted_by_record_list_length():
    result = recheck_output(ORIGINAL, BOUNCE_RECORD)
    delivered = next(c for c in result.counts if c.metric == "delivered")
    assert delivered.status == "contradicted"
    assert delivered.claimed == 3
    assert delivered.record_value == 2  # the record's list, not its claim


def test_count_missing_from_record_is_unverifiable():
    result = recheck_output(ORIGINAL, BOUNCE_RECORD)
    sent = next(c for c in result.counts if c.metric == "sent")
    assert sent.status == "unverifiable"
    assert sent.record_value is None


def test_nothing_to_check_is_unverifiable_not_confirmed():
    original = {"status": "done", "output": {"body": "Real deliverable body."}}
    result = recheck_output(original, CONFIRMING_RECORD)
    assert result.claims == [] and result.counts == []
    assert result.verdict == "UNVERIFIABLE"


def test_result_dict_shape():
    payload = recheck_output(ORIGINAL, BOUNCE_RECORD).to_dict()
    assert payload["first_verdict"] == "PASS"
    assert payload["provisional"] is True
    assert payload["verdict"] == "CONTRADICTED"
    assert payload["confirmed"] is False
    assert payload["claims"][2]["evidence"] == ["m3"]


# -- shipped examples ---------------------------------------------------------------


def test_shipped_example_pair_tells_the_bounce_story():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "examples"
    original = json.loads((root / "second_pass_original.json").read_text())
    record = json.loads((root / "second_pass_record.json").read_text())
    assert check_output(original).verdict == "PASS"  # provisional…
    result = recheck_output(original, record)
    assert result.verdict == "CONTRADICTED"  # …until the record speaks
    contradicted = [c for c in result.claims if c.status == "contradicted"]
    assert [c.evidence for c in contradicted] == [["msg_8f09"]]


# -- CLI ----------------------------------------------------------------------------


def _write(tmp_path, name, payload):
    path = tmp_path / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


def test_cli_confirmed_exits_0(tmp_path, capsys):
    code = main(["recheck", _write(tmp_path, "o.json", ORIGINAL),
                 _write(tmp_path, "r.json", CONFIRMING_RECORD)])
    assert code == 0
    out = capsys.readouterr().out
    assert "Second pass: CONFIRMED" in out
    assert "First pass: PASS (provisional)" in out


def test_cli_contradicted_exits_1(tmp_path, capsys):
    code = main(["recheck", _write(tmp_path, "o.json", ORIGINAL),
                 _write(tmp_path, "r.json", BOUNCE_RECORD)])
    assert code == 1
    assert "CONTRADICTED" in capsys.readouterr().out


def test_cli_unverifiable_exits_1_because_not_confirmed_is_not_a_pass(tmp_path):
    code = main(["recheck", _write(tmp_path, "o.json", ORIGINAL),
                 _write(tmp_path, "r.json", {"rows": []})])
    assert code == 1


def test_cli_json_format_is_machine_clean(tmp_path, capsys):
    code = main(["recheck", _write(tmp_path, "o.json", ORIGINAL),
                 _write(tmp_path, "r.json", BOUNCE_RECORD), "--format", "json"])
    assert code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["verdict"] == "CONTRADICTED"
    assert payload["first_pass_label"] == "PROVISIONAL PASS"


def test_cli_missing_record_file_exits_2(tmp_path):
    code = main(["recheck", _write(tmp_path, "o.json", ORIGINAL),
                 str(tmp_path / "nope.json")])
    assert code == 2
