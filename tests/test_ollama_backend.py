"""Unit tests for the ollama_backend helpers (pure functions, no network)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills" / "watch" / "scripts"))

import ollama_backend as ob  # noqa: E402


def test_even_indices_keeps_first_and_last():
    idx = ob._even_indices(10, 4)
    assert idx[0] == 0
    assert idx[-1] == 9
    assert len(idx) == 4


def test_even_indices_returns_all_when_n_ge_count():
    assert ob._even_indices(3, 5) == [0, 1, 2]


def test_select_frames_caps_and_samples():
    frames = [f"f{i}.jpg" for i in range(20)]
    sel = ob._select_frames(frames, 5)
    assert len(sel) == 5
    assert sel[0] == "f0.jpg"
    assert sel[-1] == "f19.jpg"


def test_select_frames_passthrough_under_cap():
    frames = ["a.jpg", "b.jpg"]
    assert ob._select_frames(frames, 8) == frames


def test_build_prompt_question_mode_includes_question():
    p = ob.build_prompt("hello world", "what is shown?", 3)
    assert "QUESTION: what is shown?" in p
    assert "3 frame image(s)" in p
    assert "hello world" in p


def test_build_prompt_summary_mode_when_no_question():
    p = ob.build_prompt("some transcript", None, 2)
    assert "Summarize the video" in p
    assert "QUESTION:" not in p


def test_build_prompt_handles_missing_transcript():
    p = ob.build_prompt(None, "q", 1)
    assert "none available" in p
