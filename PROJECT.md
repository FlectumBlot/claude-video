# PROJECT — claude-video (upstream mirror)

**What it is:** Read-only clone of the third-party repo `bradautomates/claude-video` (MIT) — the "Claude Video" `/watch` skill that lets Claude watch a video (URL or local file) by downloading with `yt-dlp`, extracting frames with `ffmpeg`, and pulling captions or a Whisper transcript. Vendored into `skill-library` as the `watch` skill in the **utility** plugin. This clone exists **only** as the upstream reference for reviewing diffs before updating the vendored copy.

**Status:** active · git · **third-party upstream — no push rights** · origin `https://github.com/bradautomates/claude-video.git` · cloned 2026-08-13 at upstream v0.2.0

**How Claude uses it:** **DO NOT edit or push this repo** — it is someone else's project. The canonical, editable copy of the skill lives at `skill-library/skills/watch/` (per the Canonical Skills Gate). To update `watch`: (1) `git -C claude-video pull`, (2) diff `claude-video/skills/watch/` against `skill-library/skills/watch/`, (3) review the changes as security-relevant code, (4) copy accepted changes into canonical `skill-library/skills/watch/` and rebuild via the skill-library workflow. When porting, re-apply the frontmatter adaptation: the standalone `SKILL.md` puts `version, argument-hint, user-invocable, homepage, repository, author` at top level, but skill-library's validator requires them nested under `metadata:` (only `name, description, allowed-tools, license, compatibility, metadata` are allowed top-level).

**Runtime facts (learned 2026-08-13 during integration):**
- Needs `ffmpeg`/`ffprobe`/`yt-dlp` on PATH; on first run `setup.py` auto-installs the first two via `brew` (no sudo).
- **YouTube requires the nightly `yt-dlp`** — Homebrew's stable (2026.07.04) returned "video unavailable" on every YouTube video; the pipx nightly (2026.08.04) fixed it. `~/.local/bin` (pipx) must win on PATH over `/opt/homebrew/bin` (brew) for the plugin to pick the working binary.
- Per-source support = `yt-dlp`'s current extractor health. Verified working: local files, generic HTTP MP4, YouTube, Vimeo, Loom (Loom serves native captions). **`ted.com` is currently broken upstream in yt-dlp** — use the TED talk's YouTube link instead.
- Whisper fallback (Groq/OpenAI) only fires when a video has no captions; needs a key in `~/.config/watch/.env` (mode 0600). Optional — `--no-whisper` runs frames-only.

**Key files:** `skills/watch/SKILL.md` (skill contract), `skills/watch/scripts/*.py` (watch.py orchestrator, download.py, frames.py, transcribe.py, whisper.py, setup.py, config.py), `hooks/` (standalone SessionStart status hook — **omitted** from the vendored copy), `CHANGELOG.md`

**Tool stack:** pure-stdlib Python 3 orchestrating `yt-dlp` + `ffmpeg`/`ffprobe` + optional Groq/OpenAI Whisper API; pytest suite (`tests/`, ffmpeg-synthesized clips, no network)

**Depends on / used by:** paired with `skill-library` (canonical home of the vendored `watch` skill). Not depended on by anything at runtime — the running skill uses `skill-library/skills/watch/`, not this clone.

**Security review:** full read of every script on 2026-08-13 — no `shell=True`, all subprocess calls list-form, `--` guards before URLs, no eval/exec, no telemetry, keys never logged. Clean. Re-review any upstream diff before porting.

**Last verified:** 2026-08-13 (age & presence only — not a correctness guarantee)
