import json
import urllib.request
from pathlib import Path
from typing import Any

from .auth import DEFAULT_AUTH_FILE, load_token

CODEX_URL = "https://chatgpt.com/backend-api/codex/responses"
DEFAULT_MODEL = "gpt-5.4-mini"


class CodexClient:
    """Thin client that calls the Codex subscription endpoint.

    Reads credentials from ~/.codex/auth.json (written by openclaw or
    `npx @openai/codex login`). Refreshes the access token automatically
    when expired.

    The endpoint requires stream=True and store=False — handled internally.
    System messages are lifted to the top-level `instructions` field.
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        auth_file: Path = DEFAULT_AUTH_FILE,
    ):
        self.model = model
        self._auth_file = Path(auth_file)

    def complete(
        self,
        messages: list[dict],
        *,
        model: str | None = None,
        json_mode: bool = False,
        **kwargs: Any,
    ) -> str:
        """Send a chat-completions-style request, return the full text response."""
        instructions, user_messages = _split_system(messages)

        responses_input = _to_responses_input(user_messages)
        if json_mode:
            _ensure_json_in_input(responses_input)

        payload: dict[str, Any] = {
            "model": model or self.model,
            "instructions": instructions,
            "input": responses_input,
            "store": False,
            "stream": True,
            **kwargs,
        }
        if json_mode:
            payload["text"] = {"format": {"type": "json_object"}}

        token = load_token(self._auth_file)
        data = json.dumps(payload).encode()
        req = urllib.request.Request(CODEX_URL, data=data, method="POST")
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("Content-Type", "application/json")

        with urllib.request.urlopen(req) as resp:
            return _collect_sse_text(resp)

    def extract(
        self,
        text: str,
        instruction: str,
        *,
        model: str | None = None,
    ) -> dict:
        """Extract structured facts from text. Returns a parsed dict."""
        raw = self.complete(
            messages=[
                {"role": "system", "content": instruction},
                {"role": "user", "content": text},
            ],
            model=model,
            json_mode=True,
        )
        return json.loads(raw)


def _split_system(messages: list[dict]) -> tuple[str, list[dict]]:
    """Pull system message out as instructions; return the rest."""
    instructions = "You are a helpful assistant."
    rest = []
    for m in messages:
        if m["role"] == "system":
            instructions = m["content"]
        else:
            rest.append(m)
    return instructions, rest


def _ensure_json_in_input(responses_input: list[dict]) -> None:
    """Append 'Respond in JSON.' to the last user message if 'json' isn't present.

    The Codex endpoint requires the word 'json' somewhere in the input
    when using json_object format.
    """
    for msg in reversed(responses_input):
        if msg["role"] == "user":
            for part in msg["content"]:
                if part.get("type") == "input_text":
                    if "json" not in part["text"].lower():
                        part["text"] += "\n\nRespond in JSON."
                    return


def _to_responses_input(messages: list[dict]) -> list[dict]:
    out = []
    for m in messages:
        content = m["content"]
        if isinstance(content, str):
            content = [{"type": "input_text", "text": content}]
        out.append({"role": m["role"], "content": content})
    return out


def _collect_sse_text(resp) -> str:
    """Read SSE stream and return the assembled output text."""
    chunks: list[str] = []
    for raw_line in resp:
        line = raw_line.decode().strip()
        if not line.startswith("data:"):
            continue
        event = json.loads(line[5:])
        if event.get("type") == "response.output_text.delta":
            chunks.append(event["delta"])
    return "".join(chunks)
