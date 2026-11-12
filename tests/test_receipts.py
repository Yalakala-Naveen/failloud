"""Hash-chained receipts: sealing, tamper detection, chain verification,
and the CLI contract around them.

The security property under test is narrow and total: after a receipt is
sealed, ANY change to the result it embeds, to the receipt's own fields, or
to the chain's membership or order must be detected by verification.
"""

import json
from datetime import datetime, timezone

from failloud import check_output, create_receipt, verify_chain, verify_receipt
from failloud.cli import main
from failloud.receipts import read_chain, seal_to_chain

FAILING = {"status": "done", "output": {"body": "Lorem ipsum."}}
PASSING = {"status": "done", "output": {"body": "Finished, real work."}}
WHEN = datetime(2026, 11, 12, 14, 5, tzinfo=timezone.utc)


def _receipt(doc=PASSING, **kwargs):
    kwargs.setdefault("created_at", WHEN)
    return create_receipt(check_output(doc), source="test", **kwargs)


def _chain_of_three():
    first = _receipt(PASSING)
    second = _receipt(FAILING, prev_hash=first.receipt_hash)
    third = _receipt(PASSING, prev_hash=second.receipt_hash)
    return [first, second, third]


# -- sealing ---------------------------------------------------------------


def test_receipt_carries_verdict_and_sha256_hashes():
    receipt = _receipt(FAILING)
    assert receipt.verdict == "FAIL"
    assert receipt.passed is False
    assert receipt.error_count >= 1
    assert len(receipt.result_hash) == 64
    assert len(receipt.receipt_hash) == 64
    assert receipt.prev_hash is None
    assert receipt.created_at == "2026-11-12T14:05:00Z"


def test_sealing_is_deterministic_for_same_inputs():
    assert _receipt().receipt_hash == _receipt().receipt_hash


def test_different_results_seal_differently():
    assert _receipt(PASSING).result_hash != _receipt(FAILING).result_hash


def test_same_result_from_different_source_seals_differently():
    result = check_output(PASSING)
    a = create_receipt(result, source="run-a", created_at=WHEN)
    b = create_receipt(result, source="run-b", created_at=WHEN)
    assert a.result_hash != b.result_hash


# -- single-receipt verification -------------------------------------------


def test_fresh_receipt_verifies():
    assert verify_receipt(_receipt()) == []
    assert verify_receipt(_receipt().to_dict()) == []


def test_tampered_verdict_is_detected():
    payload = _receipt(PASSING).to_dict()
    payload["verdict"] = "FAIL"  # rewrite history: the run "really" failed
    problems = verify_receipt(payload)
    assert problems  # verdict now disagrees with result and breaks the seal


def test_tampered_finding_is_detected():
    payload = _receipt(FAILING).to_dict()
    payload["result"]["checks"][0]["findings"] = []  # erase the evidence
    problems = verify_receipt(payload)
    assert any("result_hash" in p for p in problems)


def test_tampered_timestamp_is_detected():
    payload = _receipt().to_dict()
    payload["created_at"] = "2026-11-12T09:05:00Z"  # backdate the run
    assert verify_receipt(payload)


def test_missing_field_is_reported_not_raised():
    payload = _receipt().to_dict()
    del payload["result_hash"]
    assert verify_receipt(payload)


# -- chain verification ------------------------------------------------------


def test_chain_of_three_verifies():
    assert verify_chain(_chain_of_three()) == []
    assert verify_chain([r.to_dict() for r in _chain_of_three()]) == []


def test_dropped_middle_receipt_breaks_chain():
    chain = _chain_of_three()
    assert verify_chain([chain[0], chain[2]])


def test_reordered_chain_breaks():
    chain = _chain_of_three()
    assert verify_chain([chain[1], chain[0], chain[2]])


def test_edited_middle_receipt_breaks_chain():
    chain = [r.to_dict() for r in _chain_of_three()]
    chain[1]["source"] = "someone-else"
    assert verify_chain(chain)


def test_chain_must_start_unlinked():
    chain = _chain_of_three()
    assert verify_chain(chain[1:])  # second receipt expects a predecessor


def test_empty_chain_is_a_problem():
    assert verify_chain([])


# -- chain files -------------------------------------------------------------


def test_seal_to_chain_appends_and_links(tmp_path):
    path = tmp_path / "receipts.jsonl"
    first = seal_to_chain(path, check_output(PASSING), source="a", created_at=WHEN)
    second = seal_to_chain(path, check_output(FAILING), source="b", created_at=WHEN)
    assert second.prev_hash == first.receipt_hash
    loaded = read_chain(path)
    assert [r.receipt_hash for r in loaded] == [first.receipt_hash, second.receipt_hash]
    assert verify_chain(loaded) == []


def test_read_chain_accepts_single_pretty_receipt(tmp_path):
    path = tmp_path / "one.json"
    path.write_text(json.dumps(_receipt().to_dict(), indent=2), encoding="utf-8")
    loaded = read_chain(path)
    assert len(loaded) == 1
    assert verify_chain(loaded) == []


# -- CLI ---------------------------------------------------------------------


def _write_doc(tmp_path, payload):
    path = tmp_path / "out.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


def test_cli_receipt_out_preserves_exit_code_and_chains(tmp_path, capsys):
    receipts = tmp_path / "receipts.jsonl"
    doc = _write_doc(tmp_path, FAILING)
    assert main(["check", doc, "--receipt-out", str(receipts)]) == 1  # verdict rules
    assert main(["check", doc, "--receipt-out", str(receipts)]) == 1
    chain = read_chain(receipts)
    assert len(chain) == 2
    assert chain[1].prev_hash == chain[0].receipt_hash
    assert "sealed to" in capsys.readouterr().err


def test_cli_receipt_keeps_json_stdout_clean(tmp_path, capsys):
    receipts = tmp_path / "receipts.jsonl"
    code = main(
        ["check", _write_doc(tmp_path, PASSING), "--format", "json",
         "--receipt-out", str(receipts)]
    )
    assert code == 0
    assert json.loads(capsys.readouterr().out)["verdict"] == "PASS"


def test_cli_verify_receipts_roundtrip(tmp_path, capsys):
    receipts = tmp_path / "receipts.jsonl"
    main(["check", _write_doc(tmp_path, PASSING), "--receipt-out", str(receipts)])
    capsys.readouterr()
    assert main(["verify-receipts", str(receipts)]) == 0
    assert "OK" in capsys.readouterr().out


def test_cli_verify_receipts_rejects_tampered_file(tmp_path, capsys):
    receipts = tmp_path / "receipts.jsonl"
    main(["check", _write_doc(tmp_path, PASSING), "--receipt-out", str(receipts)])
    capsys.readouterr()
    payload = json.loads(receipts.read_text(encoding="utf-8"))
    payload["verdict"] = "FAIL"
    receipts.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    assert main(["verify-receipts", str(receipts)]) == 1
    assert "INVALID" in capsys.readouterr().out


def test_cli_verify_receipts_missing_file_exits_2(tmp_path):
    assert main(["verify-receipts", str(tmp_path / "nope.jsonl")]) == 2
