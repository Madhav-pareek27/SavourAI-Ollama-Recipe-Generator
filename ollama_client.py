"""Local Ollama REST client for SavourAI.

Uses only Python's standard library. Never requires an API key or cloud service.
Works with Ollama's http://127.0.0.1:11434/api/chat endpoint.
"""
from __future__ import annotations

import json
import os
import socket
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")


class RecipeAIError(RuntimeError):
    """User-readable problem communicating with the locally running model."""


def ollama_url() -> str:
    return (os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").strip().rstrip("/"))


def model_name() -> str:
    return os.getenv("OLLAMA_MODEL", "llama3.2").strip() or "llama3.2"


def _request(path: str, payload: dict | None = None, timeout: int = 15) -> dict:
    url = f"{ollama_url()}{path}"
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    req = Request(url, data=data, headers={"Content-Type": "application/json"} if data else {}, method="POST" if data else "GET")
    try:
        with urlopen(req, timeout=timeout) as res:
            return json.loads(res.read().decode("utf-8"))
    except HTTPError as exc:
        try:
            reason = json.loads(exc.read().decode("utf-8")).get("error", "")
        except (ValueError, OSError, UnicodeError):
            reason = ""
        short_reason = str(reason)[:350]
        if exc.code == 404:
            raise RecipeAIError(f"Ollama could not find the model. Run 'ollama list' and check the model selector. {short_reason}") from exc
        raise RecipeAIError(f"Ollama returned HTTP {exc.code}. {short_reason or 'Check the Ollama terminal for details.'}") from exc
    except (URLError, TimeoutError, ConnectionError, socket.timeout) as exc:
        raise RecipeAIError(
            f"Cannot reach Ollama at {ollama_url()}. Open the Ollama desktop app, or run 'ollama serve' in a separate PowerShell window."
        ) from exc
    except (ValueError, UnicodeError) as exc:
        raise RecipeAIError("Ollama returned an unreadable response. Restart Ollama and try again.") from exc


def list_local_models() -> list[str]:
    """Get installed local model names; does not download or run them."""
    data = _request("/api/tags", timeout=6)
    if not isinstance(data.get("models"), list):
        raise RecipeAIError("Ollama answered but did not provide a model list.")
    return sorted({str(it.get("name", "")).strip() for it in data["models"] if isinstance(it, dict) and it.get("name")}, key=str.lower)


def _resolve_model(requested: str, installed: list[str]) -> str | None:
    if requested in installed:
        return requested
    base = requested.split(":", 1)[0]
    for name in installed:
        if name == base + ":latest":
            return name
    return None


def check_ollama_connection(model: str | None = None) -> str:
    chosen = model or model_name()
    installed = list_local_models()
    if not installed:
        raise RecipeAIError("Ollama is running, but no models are installed. Run: ollama pull llama3.2")
    resolved = _resolve_model(chosen, installed)
    if not resolved:
        raise RecipeAIError(f"'{chosen}' is not installed. Available: {', '.join(installed)}. Run: ollama pull llama3.2")
    return f"Connected to local Ollama. '{resolved}' is installed and ready. No API key is needed."


def _parse_model_json(content: str) -> dict:
    """Parse JSON mode output, with a defensive fallback for fenced JSON."""
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        parsed = json.loads(cleaned)
    except (ValueError, TypeError):
        left = cleaned.find("{")
        right = cleaned.rfind("}")
        if left < 0 or right <= left:
            raise RecipeAIError("The local model answered without valid JSON. Please click Generate again.")
        try:
            parsed = json.loads(cleaned[left:right+1])
        except ValueError as exc:
            raise RecipeAIError("The local model produced invalid JSON. Please try again.") from exc
    if not isinstance(parsed, dict):
        raise RecipeAIError("The local model returned JSON but not a JSON object. Please try again.")
    return parsed


def ask_ollama_json(system: str, payload: dict, *, max_tokens: int = 1000, model: str | None = None) -> dict:
    """Ask a local model to return one JSON object; retry malformed output once."""
    chosen = model or model_name()
    user_prompt = (
        "Return ONLY one valid JSON object, with exactly the keys requested in the system instructions. "
        "Do not include markdown, commentary, or text outside JSON.\n\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )
    messages = [
        {"role": "system", "content": system + "\nYou MUST respond with a complete valid JSON object."},
        {"role": "user", "content": user_prompt},
    ]
    num_predict = max(256, min(int(max_tokens), 3000))
    last_error = None
    for attempt in range(2):
        request = {
            "model": chosen,
            "messages": messages,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.25, "num_predict": num_predict},
            "keep_alive": "10m",
        }
        reply = _request("/api/chat", payload=request, timeout=300)
        content = (reply.get("message") or {}).get("content", "")
        if not isinstance(content, str) or not content.strip():
            last_error = RecipeAIError("Ollama returned an empty response. Check available RAM and the model logs.")
        else:
            try:
                return _parse_model_json(content)
            except RecipeAIError as exc:
                last_error = exc
        # In case a smaller model gives invalid JSON, request a simpler format next time.
        messages[-1] = {"role": "user", "content": user_prompt + "\nIMPORTANT: JSON ONLY. Start with { and end with }. Use short field values."}
    raise last_error or RecipeAIError("Ollama could not provide a valid recipe response.")
