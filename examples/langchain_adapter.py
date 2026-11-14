"""LangChain adapter demo — no LangChain install required.

The adapter is duck-typed, so this demo feeds it the dict/object shapes a
real LangChain run produces. In a real project the same calls look like:

    from failloud.adapters.langchain import FailLoudCallbackHandler
    handler = FailLoudCallbackHandler(raise_on_fail=True)
    chain.invoke(inputs, config={"callbacks": [handler]})

Run:  python examples/langchain_adapter.py
"""

from failloud.adapters.langchain import to_failloud_doc, verify

# What a chat chain returns: a transcript whose last AI message is the
# payload that would be shipped downstream.
transcript = {
    "messages": [
        {"type": "human", "content": "Draft the launch note."},
        {"type": "ai", "content": "Coming soon — lorem ipsum dolor sit amet."},
    ]
}

print("Normalized envelope:")
print(" ", to_failloud_doc(transcript))

result = verify(transcript)
print(f"\nVerdict: {result.verdict}")
for finding in result.errors:
    print(f"  [{finding.check_id}] {finding.path} — {finding.message}")

# The corrected twin passes.
fixed = {
    "messages": [
        {"type": "human", "content": "Draft the launch note."},
        {"type": "ai", "content": "Launch note drafted: FailLoud 0.4.0 is live."},
    ]
}
print(f"\nCorrected twin verdict: {verify(fixed).verdict}")
