# codex-sub

A thin Python library that lets your programs call OpenAI models using your existing Codex/openclaw subscription — no API key, no proxy process, no Docker.

Zero dependencies beyond the Python standard library.

## Prerequisites

You must have either **openclaw** or the **Codex CLI** installed and logged in on the machine. Either one writes the credentials this library reads.

If you only have the Codex CLI:

```bash
npx @openai/codex login
```

That's the only authentication step you'll ever need. The library refreshes tokens automatically when they expire (~10 day access token TTL, refresh token lasts months).

## Installation

```bash
pip install codex-sub
```

## Usage

### Fact extraction (primary use case)

```python
from codex_sub import CodexClient

client = CodexClient()

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
# {'eps': 2.41, 'revenue_b': 124.3, 'ebitda_b': 38.7, 'operating_margin_pct': 31.2}
```

`extract()` always returns a parsed `dict`. It handles JSON mode internally.

### General chat

```python
response = client.complete(
    messages=[
        {"role": "system", "content": "You are a concise analyst."},
        {"role": "user", "content": "Summarise this text: ..."},
    ]
)
print(response)  # plain string
```

### JSON mode with `complete()`

```python
response = client.complete(
    messages=[
        {"role": "system", "content": "Extract data as JSON."},
        {"role": "user", "content": "Revenue was $5B, margin 20%."},
    ],
    json_mode=True,
)
import json
data = json.loads(response)
```

## Available models

| Model | Speed | Notes |
|---|---|---|
| `gpt-5.4-mini` | Fastest | Default — good for structured extraction |
| `gpt-5.4` | Balanced | Better reasoning |
| `gpt-5.5` | Slower | Highest quality |
| `gpt-5.5-pro` | Slowest | Maximum context (1M tokens) |

Set a default model at construction time, or override per call:

```python
client = CodexClient(model="gpt-5.4")

# override for a single call
result = client.extract(text, instruction, model="gpt-5.5")
```

## Token refresh

Credentials are read from `~/.codex/auth.json` on every call. If the access token is expired, the library refreshes it silently using the stored refresh token and writes the new token back to the file — so openclaw and the Codex CLI also benefit from the refresh.

No action needed on your part. If the refresh token itself expires (after months of no use), re-run `npx @openai/codex login`.

## Endpoint constraints

These are handled automatically by the library, documented here for reference:

- `stream=True` and `store=False` are required by the endpoint and always set
- System messages are translated to the top-level `instructions` field
- `max_output_tokens` is not supported by this endpoint
- JSON mode requires the word "json" to appear in the user message — the library appends `\n\nRespond in JSON.` if it's absent
- Only Codex-tier models are accepted (`gpt-5.4-mini`, `gpt-5.4`, `gpt-5.5`, `gpt-5.5-pro`)
