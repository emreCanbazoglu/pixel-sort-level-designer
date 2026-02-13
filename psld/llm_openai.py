from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"


@dataclass(frozen=True, slots=True)
class OpenAIConfig:
    api_key: str
    model: str = "gpt-4o-mini"
    timeout_s: float = 60.0
    max_retries: int = 2


def _extract_output_text(resp: dict[str, Any]) -> str:
    # Responses API: output is an array; message items contain content entries with type "output_text".
    out: list[str] = []
    for item in resp.get("output", []) or []:
        for c in item.get("content", []) or []:
            if c.get("type") == "output_text" and isinstance(c.get("text"), str):
                out.append(c["text"])
            # Some SDKs expose "text" content types too; be permissive.
            if c.get("type") == "text" and isinstance(c.get("text"), str):
                out.append(c["text"])
    if out:
        return "\n".join(out).strip()
    # Fallback: sometimes there is a top-level "output_text" (SDK convenience); keep for robustness.
    if isinstance(resp.get("output_text"), str):
        return str(resp["output_text"]).strip()
    raise RuntimeError("Could not find output text in Responses API payload")


def _request_json(url: str, *, headers: dict[str, str], body: dict[str, Any], timeout_s: float) -> dict[str, Any]:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    for k, v in headers.items():
        req.add_header(k, v)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        # Include body to make debugging 400s possible.
        try:
            body_text = e.read().decode("utf-8", errors="replace")
        except Exception:
            body_text = "<unable to read error body>"
        raise RuntimeError(f"HTTP {e.code} {e.reason}: {body_text}") from e


def _schema_for_mask_candidates(w: int, h: int) -> dict[str, Any]:
    # Keep this schema inside the strict-mode supported subset:
    # basic object/array/string/integer, required, additionalProperties=false.
    # Validate shape/characters in code.
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "w": {"type": "integer"},
            "h": {"type": "integer"},
            "candidates": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "mask": {"type": "array", "items": {"type": "string"}},
                        "notes": {"type": "string"},
                    },
                    "required": ["mask", "notes"],
                },
            },
            "notes": {"type": "string"},
        },
        # OpenAI strict schema validation requires required to include every property key.
        "required": ["w", "h", "candidates", "notes"],
    }


def _normalize_mask_rows(mask_rows: list[Any], *, w: int, h: int) -> list[str]:
    """
    Deterministically coerce the model output into exactly h rows of length w.
    - Extra rows are dropped.
    - Missing rows are appended as '.' * w.
    - Long rows are truncated.
    - Short rows are right-padded with '.'.
    """
    rows: list[str] = [r for r in mask_rows if isinstance(r, str)]
    rows = rows[:h]
    if len(rows) < h:
        rows.extend(["." * w for _ in range(h - len(rows))])

    out: list[str] = []
    for r in rows:
        if len(r) > w:
            out.append(r[:w])
        elif len(r) < w:
            out.append(r + ("." * (w - len(r))))
        else:
            out.append(r)
    return out


def _stable_cache_key(payload: dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def generate_mask_candidates_via_openai(
    *,
    prompt: str,
    w: int,
    h: int,
    cfg: OpenAIConfig,
    cache_dir: str | None = ".psld_cache",
    candidates: int = 6,
) -> dict[str, Any]:
    """
    Returns a dict with:
      - w: int
      - h: int
      - candidates: list[ {mask: list[str], notes: str} ]
    """
    schema = _schema_for_mask_candidates(w, h)

    dev = (
        "You generate pixel-art silhouettes as boolean grids.\n"
        "Rules:\n"
        f"- Output JSON matching the schema.\n"
        f"- Must be exactly {w}x{h}.\n"
        "- Use '.' for empty/background, '#' for foreground.\n"
        "- Foreground should be a single dominant connected shape (4-neighborhood).\n"
        "- Avoid tiny specks and avoid thin 1px diagonals.\n"
        "- Make it readable at small size.\n"
        f"- Generate {candidates} DISTINCT candidates.\n"
    )
    usr = (
        f"Create {candidates} distinct clean silhouette icon options of: {prompt!r}\n"
        "Focus on recognizability. Keep the subject centered with margins."
    )

    payload: dict[str, Any] = {
        "model": cfg.model,
        "input": [
            {
                "role": "developer",
                "content": [{"type": "input_text", "text": dev}],
            },
            {
                "role": "user",
                "content": [{"type": "input_text", "text": usr}],
            },
        ],
        # Structured Outputs (JSON schema). See OpenAI docs for supported models.
        "text": {
            "format": {
                "type": "json_schema",
                "name": "silhouette_mask",
                "strict": True,
                "schema": schema,
            }
        },
        # Non-zero temp so we actually get diverse candidates.
        "temperature": 0.7,
    }

    cache_path = None
    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
        cache_path = os.path.join(cache_dir, f"openai_{_stable_cache_key(payload)}.json")
        if os.path.exists(cache_path):
            return json.load(open(cache_path, "r", encoding="utf-8"))

    headers = {"Authorization": f"Bearer {cfg.api_key}"}

    last_err: Exception | None = None
    for attempt in range(cfg.max_retries + 1):
        try:
            resp = _request_json(OPENAI_RESPONSES_URL, headers=headers, body=payload, timeout_s=cfg.timeout_s)
            text = _extract_output_text(resp)
            obj = json.loads(text)
            if obj.get("w") != w or obj.get("h") != h:
                raise RuntimeError(f"Model returned wrong dimensions: {obj.get('w')}x{obj.get('h')}, expected {w}x{h}")
            if not isinstance(obj.get("candidates"), list) or not obj["candidates"]:
                raise RuntimeError("Model returned invalid candidates array")

            # Normalize/validate every candidate mask.
            for cand in obj["candidates"]:
                if not isinstance(cand, dict) or "mask" not in cand:
                    raise RuntimeError("Candidate missing mask")
                if not isinstance(cand.get("mask"), list):
                    raise RuntimeError("Candidate mask not a list")
                cand["mask"] = _normalize_mask_rows(cand["mask"], w=w, h=h)
                for row in cand["mask"]:
                    if len(row) != w:
                        raise RuntimeError("Candidate mask row length invalid after normalization")
                    if any(ch not in ".#" for ch in row):
                        raise RuntimeError("Candidate mask has invalid characters (expected '.' and '#')")
            if cache_path:
                json.dump(obj, open(cache_path, "w", encoding="utf-8"), indent=2, sort_keys=True)
            return obj
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, RuntimeError) as e:
            last_err = e
            if attempt >= cfg.max_retries:
                break
            time.sleep(0.5 * (2**attempt))

    raise RuntimeError(f"OpenAI mask generation failed: {last_err}")
