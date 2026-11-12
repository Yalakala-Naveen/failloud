"""CLI behaviour: exit codes are the contract (0 pass / 1 fail / 2 tool error)."""

import json

from failloud.cli import main

FAILING = {"status": "done", "output": {"body": "Lorem ipsum."}}
PASSING = {"status": "done", "output": {"body": "Finished, real work."}}


def _write(tmp_path, name, payload):
    path = tmp_path / name
    if isinstance(payload, str):
        path.write_text(payload, encoding="utf-8")
    else:
        path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


def test_failing_output_exits_1(tmp_path, capsys):
    code = main(["check", _write(tmp_path, "out.json", FAILING)])
    assert code == 1
    assert "FAIL" in capsys.readouterr().out


def test_passing_output_exits_0(tmp_path, capsys):
    code = main(["check", _write(tmp_path, "out.json", PASSING)])
    assert code == 0
    assert "PASS" in capsys.readouterr().out


def test_json_format_is_machine_readable(tmp_path, capsys):
    code = main(["check", _write(tmp_path, "out.json", FAILING), "--format", "json"])
    assert code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["verdict"] == "FAIL"


def test_invalid_json_exits_2(tmp_path, capsys):
    code = main(["check", _write(tmp_path, "out.json", "{not json")])
    assert code == 2
    assert "cannot read input" in capsys.readouterr().err


def test_missing_file_exits_2(tmp_path):
    assert main(["check", str(tmp_path / "nope.json")]) == 2


def test_out_writes_report_file(tmp_path, capsys):
    report = tmp_path / "report.md"
    code = main(
        [
            "check",
            _write(tmp_path, "out.json", FAILING),
            "--format",
            "md",
            "--out",
            str(report),
        ]
    )
    assert code == 1
    assert report.read_text(encoding="utf-8").startswith("# FAILURE REPORT")
    assert "report written to" in capsys.readouterr().out


def test_require_flag_enforces_paths(tmp_path):
    doc = {"status": "done", "output": {"body": "Real work, no link."}}
    code = main(["check", _write(tmp_path, "out.json", doc), "--require", "output.url"])
    assert code == 1


def test_checks_subcommand_lists_all_five(capsys):
    assert main(["checks"]) == 0
    out = capsys.readouterr().out
    for check_id in ("FL001", "FL002", "FL003", "FL004", "FL005"):
        assert check_id in out
