"""Framework adapters: capture agent outputs where they are produced.

Each adapter normalizes one framework's in-memory output shapes into the
FailLoud envelope so the same five checks verify them — no intermediate
file, no re-serialization step to forget. Adapters are duck-typed and
zero-dependency: the framework does not need to be installed for the
adapter to import or be tested.
"""

from __future__ import annotations

from .langchain import (
    FailLoudCallbackHandler,
    FailLoudVerificationError,
    message_text,
    to_failloud_doc,
    verify,
)

__all__ = [
    "FailLoudCallbackHandler",
    "FailLoudVerificationError",
    "message_text",
    "to_failloud_doc",
    "verify",
]
