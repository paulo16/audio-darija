"""Test ElevenLabs TTS darija"""

import os

import requests
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("EVEN_LAB_KEY")
vid = os.getenv("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")

text = "كيف داير؟ لاباس عليك؟ شنو كدير اليوم؟"
url = f"https://api.elevenlabs.io/v1/text-to-speech/{vid}"
payload = {
    "text": text,
    "model_id": "eleven_v3",
    "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
}
headers = {"xi-api-key": key, "Content-Type": "application/json"}

r = requests.post(url, headers=headers, json=payload, timeout=60)
print(f"Status: {r.status_code}")

if r.status_code == 200:
    with open("test_darija.mp3", "wb") as f:
        f.write(r.content)
    print(f"Audio genere: test_darija.mp3 ({len(r.content)} bytes)")

    user = requests.get(
        "https://api.elevenlabs.io/v1/user", headers={"xi-api-key": key}
    ).json()
    sub = user.get("subscription", {})
    tier = sub.get("tier")
    used = sub.get("character_count")
    limit = sub.get("character_limit")
    print(f"Plan: {tier}")
    print(f"Caracteres: {used}/{limit}")
else:
    print(f"Erreur: {r.text[:300]}")
