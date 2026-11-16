"""FL006 — unsupported_answer.

Catches RAG answers whose citations and numbers the retrieved sources do
not support: the answer *looks* grounded — it cites, it quotes figures —
while the sources it was given say no such thing, or were never retrieved
at all.

Origin: the recurring production complaint (10 independent public posts
by Nov 15, 2026, logged in the Career Company's Problem Watch) that a RAG
system "retrieves, cites, and the answer is still wrong". Retrieval is
checked by every dashboard; whether the answer is actually backed by what
was retrieved is checked by nobody. This check is that nobody.

What is verified — deterministically, like every FailLoud check:

1. Citation integrity: every citation — an entry in a ``citations`` list
   or an inline marker like ``[2]`` / ``[doc_a]`` in the answer — must
   resolve to a source that was actually retrieved. A citation pointing
   at nothing is fabricated, however confident it looks.
2. Cited-source emptiness: a cited source whose text is empty backs
   nothing.
3. Numeric support: every number stated in the answer must appear in
   the cited sources (or in all retrieved sources when the answer cites
   none specifically). Numbers are the part of an answer a reader
   repeats; they are also the part that can be checked exactly.

What is NOT claimed: semantic entailment. FailLoud does not judge
whether prose *follows* from a source — no model sits in the verdict
path. An answer can pass FL006 and still misread its sources; it cannot
pass while inventing citations or figures.

Shape tolerance: the check activates only on RAG-shaped documents — an
answer string (``answer`` / ``final_answer`` / ``response``) together
with retrieved sources (``sources`` / ``retrieved`` / ``chunks`` /
``documents`` / ``context_documents`` / ``passages`` …), explicit
citations, or inline citation markers. Any other document is out of
scope and produces no findings.
"""

from __future__ import annotations

import re
from typing import Any

from ..models import CheckConfig, Finding, Severity
from ..util import iter_nodes, normalize_key

CHECK_ID = "FL006"
NAME = "unsupported_answer"
DESCRIPTION = (
    "A RAG answer whose citations do not resolve to retrieved sources, "
    "whose cited sources are empty, or whose numbers appear in no source."
)

SOURCE_KEYS = {
    "sources",
    "retrieved",
    "retrievedsources",
    "retrievedchunks",
    "retrieveddocs",
    "retrieveddocuments",
    "chunks",
    "documents",
    "contextdocuments",
    "passages",
}
ANSWER_KEYS = {"answer", "finalanswer", "response"}
CITATION_KEYS = {"citations", "citation"}
SOURCE_ID_KEYS = ("id", "source_id", "doc_id", "ref", "key")
SOURCE_TEXT_KEYS = ("text", "content", "passage", "snippet", "body", "chunk")

# Inline citation marker: [2], [doc_a], [src-1] — a bracketed token with
# no spaces. Markdown links ([text](url)) are excluded by the caller.
_MARKER_RE = re.compile(r"\[([A-Za-z0-9][A-Za-z0-9_\-.]{0,31})\]")
# Numbers: 12 / 1,200 / 12.5 / 12.5% / $1,200 — commas and a leading
# currency sign are presentation, not value.
_NUMBER_RE = re.compile(r"\$?\d[\d,]*(?:\.\d+)?%?")


def _canonical_number(token: str) -> str | None:
    """Canonical form of a number token, so 1,200 / 1200 / 1200.0 match."""
    text = token.strip().lstrip("$").rstrip("%").replace(",", "")
    try:
        value = float(text)
    except ValueError:
        return None
    if value == int(value):
        return str(int(value))
    return str(value)


def _numbers_in(text: str) -> set[str]:
    found: set[str] = set()
    for match in _NUMBER_RE.finditer(text):
        canonical = _canonical_number(match.group(0))
        if canonical is not None:
            found.add(canonical)
    return found


def _source_text(entry: Any) -> str:
    """All text a source carries: its text fields, or the entry itself."""
    if isinstance(entry, str):
        return entry
    if isinstance(entry, dict):
        parts: list[str] = []
        for key in SOURCE_TEXT_KEYS:
            value = entry.get(key)
            if isinstance(value, str):
                parts.append(value)
        if parts:
            return "\n".join(parts)
        # No named text field: every string leaf is potential support.
        return "\n".join(
            str(value) for _path, value in iter_nodes(entry) if isinstance(value, str)
        )
    return ""


def _source_id(entry: Any, index: int) -> str:
    """A source's citable id: its explicit id, else its 1-based position."""
    if isinstance(entry, dict):
        lowered = {normalize_key(k): v for k, v in entry.items()}
        for key in SOURCE_ID_KEYS:
            value = lowered.get(normalize_key(key))
            if isinstance(value, (str, int)) and str(value).strip():
                return str(value).strip()
    return str(index + 1)


class _Source:
    def __init__(self, path: str, index: int, entry: Any) -> None:
        self.path = f"{path}[{index}]"
        self.ref = _source_id(entry, index)
        self.index_ref = str(index + 1)
        self.text = _source_text(entry)

    @property
    def refs(self) -> set[str]:
        return {self.ref, self.index_ref}


def _collect(doc: Any) -> tuple[list[_Source], list[tuple[str, str]], list[tuple[str, Any]]]:
    """(sources, answers, explicit citations) found anywhere in *doc*.

    Answers are ``(path, text)``; citations are ``(path, entries)``.
    """
    sources: list[_Source] = []
    answers: list[tuple[str, str]] = []
    citations: list[tuple[str, Any]] = []
    for path, value in iter_nodes(doc):
        key = normalize_key(path.rsplit(".", 1)[-1]) if path != "$" else ""
        if key in SOURCE_KEYS and isinstance(value, list):
            for index, entry in enumerate(value):
                sources.append(_Source(path, index, entry))
        elif key in ANSWER_KEYS and isinstance(value, str) and value.strip():
            answers.append((path, value))
        elif key in CITATION_KEYS and isinstance(value, list):
            citations.append((path, value))
    return sources, answers, citations


def _citation_ref(entry: Any) -> str | None:
    """The reference a citation entry points at, as a string."""
    if isinstance(entry, (str, int)) and str(entry).strip():
        return str(entry).strip()
    if isinstance(entry, dict):
        lowered = {normalize_key(k): v for k, v in entry.items()}
        for key in ("source_id", "id", "ref", "source", "index", "doc_id"):
            value = lowered.get(normalize_key(key))
            if isinstance(value, (str, int)) and str(value).strip():
                return str(value).strip()
    return None


def _inline_refs(answer: str) -> list[str]:
    refs: list[str] = []
    for match in _MARKER_RE.finditer(answer):
        # [text](url) is a Markdown link, not a citation.
        if answer[match.end() : match.end() + 1] == "(":
            continue
        refs.append(match.group(1))
    return refs


def check(doc: Any, config: CheckConfig) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(doc, (dict, list)):
        return findings

    sources, answers, citation_blocks = _collect(doc)
    if not answers:
        return findings

    by_ref: dict[str, _Source] = {}
    for source in sources:
        for ref in source.refs:
            by_ref.setdefault(ref, source)
            by_ref.setdefault(ref.lower(), source)

    # Explicit citations resolve once, globally — they belong to the doc.
    explicit_refs: list[tuple[str, str]] = []  # (citations path, ref)
    for path, entries in citation_blocks:
        for entry in entries:
            ref = _citation_ref(entry)
            if ref is not None:
                explicit_refs.append((path, ref))

    for path, ref in explicit_refs:
        if ref not in by_ref and ref.lower() not in by_ref:
            findings.append(
                Finding(
                    check_id=CHECK_ID,
                    code="fabricated_citation",
                    severity=Severity.ERROR,
                    path=path,
                    message=(
                        f"Citation {ref!r} does not resolve to any retrieved "
                        "source — the answer cites a source that was never "
                        "retrieved."
                    ),
                    detail={"citation": ref},
                )
            )

    for answer_path, answer in answers:
        markers = _inline_refs(answer)
        cited: list[_Source] = []
        seen_cited: set[int] = set()

        def _cite(source: _Source | None) -> None:
            if source is not None and id(source) not in seen_cited:
                seen_cited.add(id(source))
                cited.append(source)

        unresolved: list[str] = []
        for ref in markers:
            source = by_ref.get(ref) or by_ref.get(ref.lower())
            if source is None:
                unresolved.append(ref)
            else:
                _cite(source)
        for _path, ref in explicit_refs:
            _cite(by_ref.get(ref) or by_ref.get(ref.lower()))

        for ref in dict.fromkeys(unresolved):
            findings.append(
                Finding(
                    check_id=CHECK_ID,
                    code="fabricated_citation",
                    severity=Severity.ERROR,
                    path=answer_path,
                    message=(
                        f"Citation [{ref}] does not resolve to any retrieved "
                        "source — the answer cites a source that was never "
                        "retrieved."
                    ),
                    detail={"citation": ref},
                )
            )

        for source in cited:
            if not source.text.strip():
                findings.append(
                    Finding(
                        check_id=CHECK_ID,
                        code="empty_cited_source",
                        severity=Severity.ERROR,
                        path=source.path,
                        message=(
                            f"Cited source {source.ref!r} carries no text — "
                            "a citation to an empty source backs nothing."
                        ),
                        detail={"citation": source.ref},
                    )
                )

        # Numeric support: numbers in the answer must appear in the
        # cited sources — or in every retrieved source pool when the
        # answer cites nothing specifically.
        support_pool = cited if cited else sources
        if support_pool:
            supported: set[str] = set()
            for source in support_pool:
                supported |= _numbers_in(source.text)
            answer_text = _MARKER_RE.sub("", answer)
            for number in sorted(_numbers_in(answer_text) - supported, key=float):
                findings.append(
                    Finding(
                        check_id=CHECK_ID,
                        code="unsupported_number",
                        severity=Severity.ERROR,
                        path=answer_path,
                        message=(
                            f"Answer states the number {number} but it "
                            "appears in no "
                            + ("cited source" if cited else "retrieved source")
                            + " — a figure the sources do not support."
                        ),
                        detail={"number": number},
                    )
                )
        elif markers or explicit_refs:
            # Citations exist but no source was retrieved at all: the
            # unresolved findings above already name them; numbers have
            # no pool to check against.
            pass

        if sources and not markers and not explicit_refs:
            findings.append(
                Finding(
                    check_id=CHECK_ID,
                    code="no_citations",
                    severity=Severity.WARNING,
                    path=answer_path,
                    message=(
                        "Answer cites none of the retrieved sources — its "
                        "claims cannot be traced to what was retrieved."
                    ),
                    detail={"sources_available": len(sources)},
                )
            )

    return findings
