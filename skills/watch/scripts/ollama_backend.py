#!/usr/bin/env python3
"""Local vision-model backend for /watch — answer from frames + transcript via Ollama.

The default /watch flow hands frame paths to the *agent* (Claude) to Read and reason
over. This backend instead sends the frames + transcript to a local Ollama vision model
and returns its answer as text — for batch / offline / private runs (e.g. summarizing
many videos into a corpus) where a hosted model is unnecessary or undesirable.

Ollama does NOT transcribe audio — captions (or the Whisper fallback) still produce the
transcript upstream; this module only does the comprehension step. Pure stdlib.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


DEFAULT_MODEL = "mistral-small3.2:24b"
DEFAULT_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
# Cap images per request: local vision models degrade and slow sharply with many images,
# and multi-image support varies by model. Frames are evenly sampled down to this many.
DEFAULT_MAX_IMAGES = 8
REQUEST_TIMEOUT = 600  # local generation on a big model can be slow


def _even_indices(count: int, n: int) -> list[int]:
    """Indices of n evenly-spaced items out of count (first + last kept)."""
    if n >= count:
        return list(range(count))
    if n <= 1:
        return [0]
    return [round(i * (count - 1) / (n - 1)) for i in range(n)]


def _select_frames(frame_paths: list[str], max_images: int) -> list[str]:
    if max_images is None or len(frame_paths) <= max_images:
        return list(frame_paths)
    return [frame_paths[i] for i in _even_indices(len(frame_paths), max_images)]


def _encode(path: str) -> str:
    return base64.b64encode(Path(path).read_bytes()).decode("ascii")


def build_prompt(transcript: str | None, question: str | None, n_frames: int) -> str:
    """Assemble the instruction sent alongside the frame images."""
    parts = [
        "You are analyzing a video. You are given its transcript and "
        f"{n_frames} frame image(s) sampled in chronological order.",
    ]
    if transcript:
        parts.append("\nTRANSCRIPT:\n" + transcript.strip())
    else:
        parts.append("\nTRANSCRIPT: (none available — rely on the frames.)")
    if question and question.strip():
        parts.append("\nQUESTION: " + question.strip())
        parts.append(
            "\nAnswer the question using BOTH the transcript and what is visible in the "
            "frames. Cite what you see on screen where relevant. Be concise and specific."
        )
    else:
        parts.append(
            "\nSummarize the video: its topic, structure, key moments, and notable on-screen "
            "visuals. Ground the summary in BOTH the transcript and the frames. Be concise."
        )
    return "\n".join(parts)


def answer_with_ollama(
    frame_paths: list[str],
    transcript: str | None,
    question: str | None = None,
    model: str = DEFAULT_MODEL,
    host: str = DEFAULT_HOST,
    max_images: int = DEFAULT_MAX_IMAGES,
    temperature: float = 0.2,
) -> str:
    """Send frames + transcript to a local Ollama vision model; return its answer text.

    Raises SystemExit with an actionable message on connection failure or an Ollama error
    (fail loud — never silently return an empty answer).
    """
    selected = _select_frames(frame_paths, max_images)
    images = [_encode(p) for p in selected]
    prompt = build_prompt(transcript, question, len(images))

    body = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "images": images,
            "stream": False,
            "options": {"temperature": temperature},
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        f"{host}/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            payload = json.loads(response.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = " — " + exc.read().decode("utf-8", errors="replace")[:300]
        except Exception:
            pass
        if exc.code == 404:
            raise SystemExit(
                f"Ollama model '{model}' not found at {host}{detail}. "
                f"Pull it first: `ollama pull {model}` (or pass --ollama-model)."
            )
        raise SystemExit(f"Ollama request failed (HTTP {exc.code}){detail}")
    except (urllib.error.URLError, ConnectionError, TimeoutError, OSError) as exc:
        raise SystemExit(
            f"Cannot reach Ollama at {host} ({exc}). Is it running? "
            "Start it with `ollama serve`, or set OLLAMA_HOST."
        )

    answer = (payload.get("response") or "").strip()
    if not answer:
        raise SystemExit("Ollama returned an empty response.")
    return answer


if __name__ == "__main__":
    # Standalone: ollama_backend.py <frame.jpg>[,<frame2.jpg>...] [question...]
    if len(sys.argv) < 2:
        print("usage: ollama_backend.py <frame.jpg[,frame2.jpg...]> [question]", file=sys.stderr)
        raise SystemExit(2)
    frames = sys.argv[1].split(",")
    q = " ".join(sys.argv[2:]) or None
    print(answer_with_ollama(frames, transcript=None, question=q))
