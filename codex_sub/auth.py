import base64
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_AUTH_FILE = Path.home() / ".codex" / "auth.json"
REFRESH_URL = "https://auth.openai.com/oauth/token"
CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"


def _decode_jwt_exp(token: str) -> int:
    payload = token.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    return json.loads(base64.urlsafe_b64decode(payload))["exp"]


def load_token(auth_file: Path = DEFAULT_AUTH_FILE) -> str:
    """Return a valid access token, refreshing if expired."""
    data = json.loads(auth_file.read_text())
    tokens = data["tokens"]
    access = tokens["access_token"]

    if time.time() < _decode_jwt_exp(access) - 60:
        return access

    refreshed = _refresh(tokens["refresh_token"])
    tokens["access_token"] = refreshed["access_token"]
    tokens["refresh_token"] = refreshed.get("refresh_token", tokens["refresh_token"])
    data["last_refresh"] = time.strftime("%Y-%m-%dT%H:%M:%S.000000Z", time.gmtime())
    auth_file.write_text(json.dumps(data, indent=2))
    return tokens["access_token"]


def _refresh(refresh_token: str) -> dict:
    body = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
    }).encode()
    req = urllib.request.Request(REFRESH_URL, data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)
