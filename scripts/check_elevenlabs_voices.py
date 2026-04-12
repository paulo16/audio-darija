"""Check available Arabic/Darija voices on ElevenLabs"""

import os

import requests
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("EVEN_LAB_KEY")
r = requests.get("https://api.elevenlabs.io/v1/voices", headers={"xi-api-key": key})
voices = r.json().get("voices", [])

print("=== VOIX ARABES / MAROCAINES ===")
for v in voices:
    labels = v.get("labels", {})
    lang = labels.get("language", "") or ""
    accent = labels.get("accent", "") or ""
    desc = labels.get("description", "") or ""
    name = v.get("name", "")
    all_text = f"{lang} {accent} {desc} {name}".lower()
    if any(w in all_text for w in ["arab", "morocc", "maroc", "darija", "maghreb"]):
        print(f"  ID: {v['voice_id']}")
        print(f"  Name: {name}")
        print(f"  Language: {lang} | Accent: {accent}")
        print(f"  Description: {desc}")
        print(f"  Category: {v.get('category', '')}")
        print()

print(f"\n=== Total voices in account: {len(voices)} ===")
print("\n=== ALL VOICES (first 20) ===")
for v in voices[:20]:
    labels = v.get("labels", {})
    print(
        f"  {v['name']} | lang={labels.get('language','')} | accent={labels.get('accent','')} | cat={v.get('category','')}"
    )
