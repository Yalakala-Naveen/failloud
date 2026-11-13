"""Watch mode: discovery, change detection, receipt chaining, CLI contract.

The properties under test:

- A first poll checks everything; an unchanged file is never re-checked
  (content hash, not mtime, decides "changed").
- New, changed, and fixed files are picked up; deleted files are
  forgotten; one broken file never hides the others.
- With a receipt file, every check seals into one verifiable chain.
- ``watch --once`` follows the check exit contract over the whole sweep:
  0 all passed, 1 any failed or errored, 2 target missing.
"""

import json

from failloud import Watcher, watch
from failloud.cli import main
from failloud.receipts import read_chain, verify_chain

FAILING = {"status": "done", "output": {"body": "Lorem ipsum."}}
PASSING = {"status": "done", "output": {"body": "Finished, real work."}}


def _write(path, payload):
    if isinstance(payload, str):
        path.write_text(payload, encoding="utf-8")
    else:
        path.write_text(json.dumps(payload), encoding="utf-8")
    return path


# -- discovery ---------------------------------------------------------------


def test_single_file_target_is_checked_on_first_poll(tmp_path):
    target = _write(tmp_path / "out.json", PASSING)
    events = Watcher(target).poll_once()
    assert len(events) == 1
    assert events[0].passed
    assert events[0].error is None


def test_directory_target_checks_every_json_sorted(tmp_path):
    _write(tmp_path / "b.json", FAILING)
    _write(tmp_path / "a.json", PASSING)
    _write(tmp_path / "notes.txt", PASSING)  # not JSON: ignored
    events = Watcher(tmp_path).poll_once()
    assert [e.path.name for e in events] == ["a.json", "b.json"]
    assert events[0].passed and events[1].failed


def test_recursive_flag_reaches_subdirectories(tmp_path):
    sub = tmp_path / "sub"
    sub.mkdir()
    _write(sub / "deep.json", PASSING)
    assert Watcher(tmp_path).poll_once() == []
    assert len(Watcher(tmp_path, recursive=True).poll_once()) == 1


def test_empty_directory_polls_clean(tmp_path):
    assert Watcher(tmp_path).poll_once() == []
    summary = watch(tmp_path, once=True)
    assert summary.ok and summary.checks == 0


# -- change detection ----------------------------------------------------------


def test_unchanged_file_is_not_rechecked(tmp_path):
    target = _write(tmp_path / "out.json", PASSING)
    watcher = Watcher(target)
    assert len(watcher.poll_once()) == 1
    assert watcher.poll_once() == []
    # Rewriting identical bytes (a touch) is not a change.
    _write(target, PASSING)
    assert watcher.poll_once() == []


def test_changed_file_is_rechecked_with_new_verdict(tmp_path):
    target = _write(tmp_path / "out.json", FAILING)
    watcher = Watcher(target)
    assert watcher.poll_once()[0].failed
    _write(target, PASSING)
    events = watcher.poll_once()
    assert len(events) == 1 and events[0].passed


def test_new_file_in_directory_is_picked_up(tmp_path):
    watcher = Watcher(tmp_path)
    assert watcher.poll_once() == []
    _write(tmp_path / "late.json", PASSING)
    events = watcher.poll_once()
    assert len(events) == 1 and events[0].path.name == "late.json"


def test_deleted_file_is_forgotten_and_recreated_as_new(tmp_path):
    target = _write(tmp_path / "out.json", PASSING)
    watcher = Watcher(tmp_path)
    assert len(watcher.poll_once()) == 1
    target.unlink()
    assert watcher.poll_once() == []
    _write(target, PASSING)  # same bytes, but it is a new file again
    assert len(watcher.poll_once()) == 1


# -- errors never kill the watcher ----------------------------------------------


def test_invalid_json_is_an_error_event_not_a_crash(tmp_path):
    _write(tmp_path / "bad.json", "{not json")
    _write(tmp_path / "good.json", PASSING)
    events = Watcher(tmp_path).poll_once()
    by_name = {e.path.name: e for e in events}
    assert by_name["bad.json"].error is not None
    assert by_name["bad.json"].result is None
    assert by_name["good.json"].passed


def test_broken_file_is_not_rereported_until_it_changes(tmp_path):
    target = _write(tmp_path / "bad.json", "{not json")
    watcher = Watcher(target)
    assert len(watcher.poll_once()) == 1
    assert watcher.poll_once() == []  # unchanged broken file: quiet
    _write(target, PASSING)  # fixed: re-checked, now a verdict
    events = watcher.poll_once()
    assert len(events) == 1 and events[0].passed


# -- receipts ---------------------------------------------------------------------


def test_watch_seals_every_check_into_one_chain(tmp_path):
    _write(tmp_path / "a.json", PASSING)
    _write(tmp_path / "b.json", FAILING)
    receipts = tmp_path / "receipts.jsonl"
    summary = watch(tmp_path, once=True, receipt_out=receipts)
    assert summary.checks == 2 and summary.receipts == 2
    chain = read_chain(receipts)
    assert len(chain) == 2
    assert chain[1].prev_hash == chain[0].receipt_hash
    assert verify_chain(chain) == []


def test_watch_does_not_seal_unreadable_files(tmp_path):
    _write(tmp_path / "bad.json", "{not json")
    receipts = tmp_path / "receipts.jsonl"
    summary = watch(tmp_path, once=True, receipt_out=receipts)
    assert summary.errors == 1 and summary.receipts == 0
    assert not receipts.exists()


# -- watch() driver -----------------------------------------------------------------


def test_watch_once_summary_counts_verdicts(tmp_path):
    _write(tmp_path / "a.json", PASSING)
    _write(tmp_path / "b.json", FAILING)
    seen = []
    summary = watch(tmp_path, once=True, on_event=seen.append)
    assert (summary.checks, summary.failures, summary.errors) == (2, 1, 0)
    assert not summary.ok
    assert len(seen) == 2


def test_watch_max_polls_rechecks_across_polls(tmp_path):
    target = _write(tmp_path / "out.json", PASSING)
    state = {"sleeps": 0}

    def fake_sleep(_seconds):
        state["sleeps"] += 1
        if state["sleeps"] == 1:
            _write(target, FAILING)  # the agent retries and fails louder

    summary = watch(tmp_path, max_polls=2, sleep=fake_sleep)
    assert summary.checks == 2 and summary.failures == 1


# -- CLI -----------------------------------------------------------------------------


def test_cli_watch_once_all_passing_exits_0(tmp_path, capsys):
    _write(tmp_path / "a.json", PASSING)
    assert main(["watch", str(tmp_path), "--once"]) == 0
    assert "PASS" in capsys.readouterr().out


def test_cli_watch_once_any_failure_exits_1(tmp_path):
    _write(tmp_path / "a.json", PASSING)
    _write(tmp_path / "b.json", FAILING)
    assert main(["watch", str(tmp_path), "--once"]) == 1


def test_cli_watch_once_error_file_exits_1(tmp_path):
    _write(tmp_path / "bad.json", "{not json")
    assert main(["watch", str(tmp_path), "--once"]) == 1


def test_cli_watch_missing_target_exits_2(tmp_path):
    assert main(["watch", str(tmp_path / "nope"), "--once"]) == 2


def test_cli_watch_single_file_with_receipts(tmp_path, capsys):
    target = _write(tmp_path / "out.json", PASSING)
    receipts = tmp_path / "receipts.jsonl"
    code = main(
        ["watch", str(target), "--once", "--receipt-out", str(receipts)]
    )
    assert code == 0
    assert verify_chain(read_chain(receipts)) == []
    assert "sealed" in capsys.readouterr().err
