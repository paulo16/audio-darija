"""Recommend Moroccan/Darija-sounding voices from ElevenLabs metadata.

This script does not copy voices from YouTube.
It helps you find candidate voice IDs to set in .env:
  ELEVENLABS_VOICE_ID=...
  ELEVENLABS_VOICE_ID_FEMALE=...
"""

from __future__ import annotations

import argparse
import os
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

KEYWORDS = (
    "morocc",
    "maroc",
    "darija",
    "maghreb",
    "casablanca",
    "rabat",
    "arabic",
    "arab",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Recommend Darija voice candidates.")
    parser.add_argument(
        "--limit", type=int, default=12, help="Max candidates to print."
    )
    parser.add_argument(
        "--include-shared",
        action="store_true",
        help="Include shared-voice library suggestions (metadata only).",
    )
    return parser.parse_args()


def score_voice(record: dict[str, Any]) -> int:
    fields = [
        record.get("name", ""),
        record.get("description", ""),
        record.get("accent", ""),
        record.get("language", ""),
        " ".join(f"{k}:{v}" for k, v in (record.get("labels", {}) or {}).items()),
    ]
    text = " ".join(fields).lower()
    score = 0
    for token in KEYWORDS:
        if token in text:
            score += 2
    if "morocc" in text or "darija" in text:
        score += 4
    if "female" in text or record.get("gender") == "female":
        score += 1
    if "male" in text or record.get("gender") == "male":
        score += 1
    return score


def get_account_voices(api_key: str) -> list[dict[str, Any]]:
    response = requests.get(
        "https://api.elevenlabs.io/v1/voices",
        headers={"xi-api-key": api_key},
        timeout=20,
    )
    response.raise_for_status()
    voices = response.json().get("voices", [])
    normalized = []
    for v in voices:
        labels = v.get("labels", {}) or {}
        normalized.append(
            {
                "voice_id": v.get("voice_id", ""),
                "name": v.get("name", ""),
                "description": labels.get("description", "")
                or v.get("description", ""),
                "language": labels.get("language", ""),
                "accent": labels.get("accent", ""),
                "gender": labels.get("gender", ""),
                "category": v.get("category", ""),
                "labels": labels,
                "source": "account",
            }
        )
    return normalized


def get_shared_voices(api_key: str) -> list[dict[str, Any]]:
    response = requests.get(
        "https://api.elevenlabs.io/v1/shared-voices",
        headers={"xi-api-key": api_key},
        params={"page_size": 100, "language": "ar", "sort": "usage_character_count_7d"},
        timeout=20,
    )
    response.raise_for_status()
    voices = response.json().get("voices", [])
    normalized = []
    for v in voices:
        normalized.append(
            {
                "voice_id": v.get("voice_id", ""),
                "name": v.get("name", ""),
                "description": v.get("description", ""),
                "language": v.get("language", ""),
                "accent": v.get("accent", ""),
                "gender": v.get("gender", ""),
                "category": v.get("category", ""),
                "labels": {},
                "source": "shared",
            }
        )
    return normalized


def print_candidates(candidates: list[dict[str, Any]], limit: int) -> None:
    if not candidates:
        print("No candidates found.")
        return
    print("Top voice candidates:\n")
    for item in candidates[:limit]:
        print(
            f"- score={item['score']} | source={item['source']} | name={item['name']}"
        )
        print(f"  voice_id: {item['voice_id']}")
        print(
            f"  lang={item.get('language','')} | accent={item.get('accent','')} | "
            f"gender={item.get('gender','')} | category={item.get('category','')}"
        )
        if item.get("description"):
            print(f"  desc: {item['description']}")
        print()


def main() -> None:
    args = parse_args()
    api_key = os.getenv("EVEN_LAB_KEY", "")
    if not api_key:
        raise SystemExit("Missing EVEN_LAB_KEY in environment.")

    voices = get_account_voices(api_key)
    if args.include_shared:
        try:
            voices.extend(get_shared_voices(api_key))
        except Exception as exc:
            print(f"Shared voice lookup failed: {exc}")

    for v in voices:
        v["score"] = score_voice(v)

    ranked = [
        v
        for v in sorted(voices, key=lambda x: x["score"], reverse=True)
        if v["score"] > 0
    ]
    print_candidates(ranked, args.limit)

    print("Suggested .env setup after listening tests:")
    print("ELEVENLABS_VOICE_ID=<male_or_main_voice_id>")
    print("ELEVENLABS_VOICE_ID_FEMALE=<female_voice_id>")


if __name__ == "__main__":
    main()
