# Example: gate agent outputs in CI

**Job:** a CI check that fails the build when your agent pipeline
produces a bad output — the exact job in audit prompt P10.

Your pipeline already writes its agent outputs somewhere (a JSON
artifact, a results file, a fixture). This example verifies that file
on every push and pull request with **FailLoud** — a deterministic
verification harness for LLM agent outputs. Exit code is the contract:

| Exit | Meaning | CI result |
|---|---|---|
| 0 | Output passed all six checks | ✅ green |
| 1 | Output failed verification (a silent failure shipped as "done") | ❌ build fails |
| 2 | FailLoud itself could not run (missing file, bad JSON) | ❌ build fails |

## Files

- `agent-output-gate.yml` — the workflow. Copy it to
  `.github/workflows/` in your repo and point `AGENT_OUTPUT` at the
  JSON your pipeline produces.
- `sample_agent_output.json` — a lying output to try it on: it claims
  12 emails sent over a 9-item record (FL004) and a publish action with
  no evidence (FL002). The gate fails on it, as it should.

## Two ways to run the gate

**A. The published GitHub Action** (least code):

```yaml
- uses: Yalakala-Naveen/failloud@v0.6.0
  with:
    path: agent_output.json
```

**B. A plain CLI step** (what `agent-output-gate.yml` does — use this
when you want the flags visible in your own workflow):

```yaml
- run: pip install failloud
- run: failloud check agent_output.json --format md
```

Useful flags: `--only FL002,FL004` to run a subset, `--require
output.url,output.body` to demand fields, `--format json` to feed the
findings into another step.

## Try it locally

```console
$ pip install failloud
$ failloud check sample_agent_output.json
FAIL — 2 errors … (exit 1)
$ failloud check ../../examples/passing_output.json
PASS (exit 0)
```
