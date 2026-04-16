"""Build a Darija text corpus from YouTube subtitles.

This script is intentionally text-only: it does not clone voices or reuse audio.
Use it to collect authentic, source-traceable Darija expressions from captions.

Examples
--------
python scripts/collect_youtube_darija_texts.py \
  --query "darija maroc podcast" \
  --max-results 20

python scripts/collect_youtube_darija_texts.py \
  --query "dariija dialogue maroc" \
  --max-results 30 \
  --allow-auto-captions \
  --append
"""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from typing import Any

import requests
from yt_dlp import YoutubeDL

BASE_DIR = Path(__file__).parent.parent
DEFAULT_OUTPUT = BASE_DIR / "data" / "connected_speech" / "youtube_darija_corpus.jsonl"

_TS_RE = re.compile(r"(?P<h>\d+):(?P<m>\d+):(?P<s>\d+)[\.,](?P<ms>\d+)")
_TAG_RE = re.compile(r"<[^>]+>")
_MULTISPACE_RE = re.compile(r"\s+")
_DARija_LATIN_HINT_RE = re.compile(
    r"\b(ana|nta|nti|ntuma|kif|fin|chnou|chno|wach|wakha|bzaf|safi|"
    r"khouya|khouyti|lhamdullah|bslama|labas|ghadi|3afak|allah)\b",
    re.IGNORECASE,
)
_ARABIC_RE = re.compile(r"[\u0600-\u06FF]")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect Darija lines from YouTube subtitles."
    )
    parser.add_argument("--query", required=True, help="YouTube search query.")
    parser.add_argument(
        "--max-results", type=int, default=20, help="Maximum videos to inspect."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output JSONL path (default: {DEFAULT_OUTPUT}).",
    )
    parser.add_argument(
        "--allow-auto-captions",
        action="store_true",
        help="Allow YouTube automatic captions when manual subtitles are missing.",
    )
    parser.add_argument(
        "--allow-standard-license",
        action="store_true",
        help="Include non-Creative Commons videos (off by default).",
    )
    parser.add_argument(
        "--darija-only",
        action="store_true",
        help="Keep only lines that look like Darija (Arabic script or Darija Latin hints).",
    )
    parser.add_argument("--append", action="store_true", help="Append to output file.")
    return parser.parse_args()


def normalize_text(text: str) -> str:
    text = html.unescape(text)
    text = _TAG_RE.sub("", text)
    text = text.replace("\u200f", " ").replace("\u200e", " ").replace("\xa0", " ")
    text = _MULTISPACE_RE.sub(" ", text).strip()
    return text


def looks_like_darija(text: str) -> bool:
    if _ARABIC_RE.search(text):
        return True
    return _DARija_LATIN_HINT_RE.search(text) is not None


def parse_vtt_timestamp(value: str) -> float | None:
    match = _TS_RE.search(value.strip())
    if not match:
        return None
    hours = int(match.group("h"))
    minutes = int(match.group("m"))
    seconds = int(match.group("s"))
    millis = int(match.group("ms").ljust(3, "0")[:3])
    return float(hours * 3600 + minutes * 60 + seconds + millis / 1000)


def parse_vtt(content: str) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = []
    current_start: float | None = None
    current_end: float | None = None
    text_buffer: list[str] = []

    def flush() -> None:
        nonlocal text_buffer, current_start, current_end
        if not text_buffer:
            return
        text = normalize_text(" ".join(text_buffer))
        text_buffer = []
        if not text:
            return
        segments.append({"start": current_start, "end": current_end, "text": text})

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            flush()
            current_start = None
            current_end = None
            continue
        if line.startswith("WEBVTT") or line.startswith("NOTE"):
            continue
        if "-->" in line:
            flush()
            parts = [p.strip() for p in line.split("-->", 1)]
            current_start = parse_vtt_timestamp(parts[0])
            current_end = parse_vtt_timestamp(parts[1])
            continue
        if line.isdigit():
            continue
        text_buffer.append(line)

    flush()
    return segments


def parse_json3(content: str) -> list[dict[str, Any]]:
    payload = json.loads(content)
    segments: list[dict[str, Any]] = []
    for event in payload.get("events", []):
        segs = event.get("segs")
        if not segs:
            continue
        text = normalize_text("".join(seg.get("utf8", "") for seg in segs))
        if not text:
            continue
        start = event.get("tStartMs")
        duration = event.get("dDurationMs")
        start_s = (start / 1000.0) if isinstance(start, (int, float)) else None
        end_s = None
        if isinstance(start, (int, float)) and isinstance(duration, (int, float)):
            end_s = (start + duration) / 1000.0
        segments.append({"start": start_s, "end": end_s, "text": text})
    return segments


def is_creative_commons(license_text: str) -> bool:
    low = (license_text or "").lower()
    return "creative commons" in low or "cc by" in low


def select_subtitle_track(
    info: dict[str, Any], allow_auto: bool
) -> tuple[str, str, str] | None:
    preferred_langs = ("ar-MA", "ary", "ar", "fr", "en")
    for source_name, source in (
        ("manual", info.get("subtitles") or {}),
        ("auto", info.get("automatic_captions") or {}),
    ):
        if source_name == "auto" and not allow_auto:
            continue
        for lang in preferred_langs:
            tracks = source.get(lang)
            if not tracks:
                continue
            for ext in ("json3", "vtt"):
                track = next(
                    (t for t in tracks if t.get("ext") == ext and t.get("url")), None
                )
                if track:
                    return source_name, lang, track["url"]
            track = next((t for t in tracks if t.get("url")), None)
            if track:
                return source_name, lang, track["url"]
    return None


def download_subtitles(url: str) -> list[dict[str, Any]]:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    content_type = (response.headers.get("Content-Type") or "").lower()
    text = response.text

    if "json" in content_type or text.lstrip().startswith("{"):
        return parse_json3(text)
    return parse_vtt(text)


def iter_videos(query: str, max_results: int) -> list[dict[str, Any]]:
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "extract_flat": False,
        "noplaylist": True,
        "ignoreerrors": True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        search_result = ydl.extract_info(
            f"ytsearch{max_results}:{query}", download=False
        )
        return search_result.get("entries", []) if search_result else []


def main() -> None:
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    mode = "a" if args.append else "w"
    kept_videos = 0
    kept_segments = 0

    videos = iter_videos(args.query, args.max_results)
    with open(args.output, mode, encoding="utf-8") as out:
        for item in videos:
            if not item:
                continue

            video_id = item.get("id")
            if not video_id:
                continue

            license_text = item.get("license") or ""
            if not args.allow_standard_license and not is_creative_commons(
                license_text
            ):
                continue

            track = select_subtitle_track(item, allow_auto=args.allow_auto_captions)
            if not track:
                continue
            caption_source, caption_lang, caption_url = track

            try:
                segments = download_subtitles(caption_url)
            except Exception as exc:
                print(f"[skip] {video_id}: subtitle download failed ({exc})")
                continue

            written_here = 0
            for seg in segments:
                text = normalize_text(seg.get("text", ""))
                if len(text) < 2:
                    continue
                if args.darija_only and not looks_like_darija(text):
                    continue

                payload = {
                    "video_id": video_id,
                    "url": item.get("webpage_url")
                    or f"https://www.youtube.com/watch?v={video_id}",
                    "title": item.get("title") or "",
                    "channel": item.get("uploader") or item.get("channel") or "",
                    "license": license_text,
                    "caption_source": caption_source,
                    "caption_lang": caption_lang,
                    "start": seg.get("start"),
                    "end": seg.get("end"),
                    "text": text,
                }
                out.write(json.dumps(payload, ensure_ascii=False) + "\n")
                written_here += 1

            if written_here:
                kept_videos += 1
                kept_segments += written_here
                print(
                    f"[ok] {video_id} | {caption_source}:{caption_lang} | "
                    f"{written_here} lines | {item.get('title','(no title)')}"
                )

    print("\nDone.")
    print(f"Videos kept: {kept_videos}")
    print(f"Segments kept: {kept_segments}")
    print(f"Output: {args.output}")
    if not args.allow_standard_license:
        print(
            "License policy: Creative Commons only (use --allow-standard-license to relax)."
        )


if __name__ == "__main__":
    main()
