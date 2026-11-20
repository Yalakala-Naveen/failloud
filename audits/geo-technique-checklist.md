# GEO technique checklist — every tactic in the playbook, statused

Source: `~/workspace/research_notes/llm-recommendation-geo-playbook-20261120-0523/report.md`
(2026-11-20). Built 2026-11-20 in the timeline-squeeze pass; Phase A
(`d7a8450`) and the AI-discovery tuning (`f496ede`) are the earlier
passes. Statuses: ✅ done · 🔄 in progress elsewhere · 🆕 done in the
squeeze pass · ⛔ cannot be sped up from our side · 🚫 rejected on the
evidence.

## Content features (report §1.1 — GEO-bench, with its replication caveat)
| Technique | Status | Evidence |
|---|---|---|
| Quotation addition (+41%) | ✅ | Maintainer quote, README line 10; quotable one-liners atop every docs page's Short Answer box |
| Statistics addition (+31%) | ✅ 🆕 | README "by the numbers"; Silent Failure Audit original stats (57/60, 95.0%, 10/10 clean) |
| Cite sources (+27%) | ✅ | Every claim on the new pages links a primary artifact: dataset, generator script, shipped examples, real CLI output |
| Fluency / easy-to-understand (+28%/+14%) | ✅ | Plain-language Short Answer first on all 20 docs pages |
| Technical terms (+18%) | ✅ | Check IDs (FL001–FL006) + exact task vocabulary used identically everywhere |
| Authoritative tone (+10% only) | 🚫 | Near-bottom in GEO-bench; not a lever — evidence over tone, per the report |
| Keyword stuffing (−8%) | 🚫 | Actively harmful; never used |
| Comparison tables (highest-citation format) | ✅ | README table + 5 `/compare/` pages + `/alternatives/` + 🆕 `/deterministic-verification-vs-llm-judge/` |
| Primary-research pages (11.3 vs 3.4 citations) | 🆕 | `/silent-failure-audit/` + `audits/silent-failure-audit/` dataset |

## llms.txt (§1.2)
| Technique | Status | Evidence |
|---|---|---|
| Publish llms.txt + llms-full.txt | ✅ | `f496ede`; root + site copies kept in sync; expectation set to ~zero for rankings — its value is coding-agent docs ingestion |

## Per-engine source diets (§1.3 — the engines read different webs)
| Technique | Status | Evidence |
|---|---|---|
| Reddit presence (Perplexity #1 source) | 🔄 | Phase B content pack (separate agent) — drafts; posting is a platform step |
| Wikipedia / encyclopaedic authority (ChatGPT #1) | ⛔ | Notability gate: a 0-user library has no honest route to an article today |
| YouTube mentions (strongest correlate, 0.737) | 🆕 scripts | `docs/videos/` — 3 full scripts, titles/descriptions/transcripts optimised; upload is an owner step |
| GitHub as canonical surface | ✅ | README is the canonical retrievable asset; code + examples in-repo |
| Stack Overflow answers | 🔄 | Phase B pack drafts |
| Hacker News (Show HN) | 🔄 | Phase B pack drafts |
| dev.to series | 🔄 | Phase B pack drafts (extends the live launch post) |
| Third-party listicle inclusion (EvalShift first) | 🔄 | Phase B outreach drafts; inclusion is editors' decision — ⛔ on timing |
| Earned > paid (>84% of citations are earned) | ✅ | Strategy adopted fleet-wide; no paid placements anywhere |

## Fan-out & mentions (§1.4)
| Technique | Status | Evidence |
|---|---|---|
| Fan-out query presence (68.9% vs 2.1%) | 🆕 | `audits/fan-out-map.md` — every P01–P12 sub-query mapped to a page whose title + first lines answer it with FailLoud named; 3 gap pages added |
| Brand mentions over backlinks (~3× correlation) | ✅ | All work targets mentions in context; backlink buying 🚫 (weakest measured signal) |
| Named-in-answer, not merely cited | ✅ | Audit scorecard records named / named-first separately from citations |
| Beat DIY ("agents build, not buy") | ✅ 🆕 | `/deterministic-verification-vs-llm-judge/` + taxonomy/receipts/recheck argument: "the six silent failures your hand-rolled check misses" |

## Retrieval eligibility (§2, Phase A1)
| Technique | Status | Evidence |
|---|---|---|
| robots.txt allows all AI crawlers | ✅ | `docs/robots.txt` (`d7a8450`) — OAI-SearchBot, GPTBot, PerplexityBot, ClaudeBot/SearchBot/User, Google-Extended, Bingbot |
| IndexNow on publish/update | ✅ 🆕 | Submitted + accepted in Phase A; new URLs from this pass submitted with it |
| Bing Webmaster Tools (ChatGPT/Copilot index) | ⛔ | Needs an owner-account verification token — platform step, copy in Phase A report |
| Google Search Console (Gemini gate) | ⛔ | Same owner-token step |
| Brave ranking (Claude search) | ⛔ | Brave has no webmaster/submission channel; only indirect via content |
| Entity resolution for Gemini (sameAs) | 🆕 | JSON-LD `SoftwareApplication` + `sameAs` (GitHub/PyPI/MCP Registry) in `docs/index.html` |

## Playbook phases
| Item | Status | Evidence |
|---|---|---|
| A2 README rebuild | ✅ | `d7a8450` |
| A3 one docs page per prompt + vs pages | ✅ 🆕 | 16 pages in Phase A; +4 in this pass (definition, LangGraph, judge comparison, audit) = 20 |
| A5 MCP registry sweep | ✅ prepared | `registry-submissions.md` — Official Registry LIVE, Glama claimed, Agensi live, awesome-mcp PR #19633 open; remaining forms are platform steps |
| Skills channel (SKILL.md directories) | ✅ | `skill/SKILL.md` + Agensi listing live; agent snippets in `agent/` |
| B1 listicles | 🔄 | Phase B pack |
| B2 SO / HN / Product Hunt | 🔄 | Phase B pack |
| B3 YouTube | 🆕 scripts | `docs/videos/` (upload ⛔ owner step) |
| B4 original-data asset | 🆕 | Silent Failure Audit — dataset + script + page; Hugging Face Datasets posting is a platform step |
| B5 measurement loop | ✅ 🆕 | Weekly audit cron (Mon ~10:17 ET) + ×3-runs protocol and 30-prompt expansion (`audits/prompts-expansion.md`) |
| C1 GitHub Action | ✅ | `action.yml` in-repo + README section; Marketplace listing on a release is an account step |
| C1 example integrations in code corpora | 🆕 | `examples/ci_gate/`, `examples/langgraph_gate/` (both run-verified) + pre-existing LangChain adapter; separate micro-repos remain an option, not a gap |
| C1 third-party tutorials | ⛔ | By definition other people's work; Phase B outreach is the lever |
| C2 entity consistency | 🆕 | Canonical sentence verbatim in README, `llms.txt`, `pyproject.toml`, `server.json`, docs meta + JSON-LD, `registry-submissions.md` (PyPI page itself refreshes at the next release) |
| C3 trained-answer harvest | ⛔ | Realised only at providers' model releases — months, unschedulable |

## Explicitly deprioritised (report's own list)
Buying backlinks 🚫 · keyword-stuffed pages 🚫 · self-published
"best tools" listicles as a substitute for third-party inclusion 🚫 ·
paid/advertorial placements 🚫 · llms.txt as a ranking strategy 🚫 ·
chasing one assistant's current source mix 🚫 (Semrush volatility).
