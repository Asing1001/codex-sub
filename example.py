from codex_sub import CodexClient

client = CodexClient(model="gpt-5.4-mini")

# simple fact extraction from broker PDF text
pdf_text = """
Apple Inc. reported Q1 2026 earnings with EPS of $2.41, revenue of $124.3B,
and EBITDA of $38.7B. Operating margin came in at 31.2%.
"""

facts = client.extract(
    text=pdf_text,
    instruction=(
        "Extract financial metrics as JSON. "
        "Keys: eps, revenue_b, ebitda_b, operating_margin_pct. "
        "Use null for missing values."
    ),
)

print(facts)
# {"eps": 2.41, "revenue_b": 124.3, "ebitda_b": 38.7, "operating_margin_pct": 31.2}
