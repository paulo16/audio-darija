"""
Génération audio des dialogues darija avec Edge TTS
Utilise les voix marocaines ar-MA-JamalNeural (homme) et ar-MA-MounaNeural (femme)
Lit le texte arabe pour la prononciation, affiche le texte en translittération pour l'apprentissage
"""

import asyncio
import json
import re
import time
from pathlib import Path

import edge_tts

BASE_DIR = Path(__file__).parent.parent
LESSON_DIR = BASE_DIR / "data" / "lesson_packs"
AUDIO_DIR = BASE_DIR / "data" / "lesson_audio"

# Voix marocaines Edge TTS
VOICE_MALE = "ar-MA-JamalNeural"  # Voix masculine marocaine
VOICE_FEMALE = "ar-MA-MounaNeural"  # Voix féminine marocaine

AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def parse_dialogue_arabe(dialogue_arabe: str):
    """Parse le dialogue arabe (A:/B:) en parties avec speakers"""
    lines = dialogue_arabe.strip().split("\n")
    parts = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        match = re.match(r"^([A-Z]):\s*(.+)$", line)
        if match:
            speaker = match.group(1)
            text = match.group(2).strip()
            # Ignorer les didascalies comme "... (b3d l-makla) ..."
            text = re.sub(r"\.\.\.\s*\(.*?\)\s*\.\.\.", "", text).strip()
            if text:
                parts.append({"speaker": speaker, "text": text})
    return parts


async def generate_single_audio(text: str, voice: str, output_file: Path):
    """Génère un fichier audio unique"""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_file))


async def generate_dialogue_audio(lesson: dict, output_file: Path):
    """Génère l'audio d'un dialogue complet avec 2 voix alternées"""
    dialogue_arabe = lesson.get("dialogue_arabe", "")
    if not dialogue_arabe:
        print(f"  ⏭️  Pas de dialogue arabe")
        return False

    parts = parse_dialogue_arabe(dialogue_arabe)
    if not parts:
        print(f"  ⏭️  Dialogue arabe vide après parsing")
        return False

    # Assigner les voix: A = homme, B = femme
    voice_map = {"A": VOICE_MALE, "B": VOICE_FEMALE}

    # Générer chaque partie séparément puis combiner
    # Utiliser un dossier temp unique par leçon pour éviter les conflits
    import uuid

    temp_files = []
    temp_dir = output_file.parent / f"_temp_{uuid.uuid4().hex[:8]}"
    temp_dir.mkdir(exist_ok=True)

    for i, part in enumerate(parts):
        voice = voice_map.get(part["speaker"], VOICE_MALE)
        temp_file = temp_dir / f"part_{i:03d}.mp3"
        try:
            await generate_single_audio(part["text"], voice, temp_file)
            temp_files.append(temp_file)
        except Exception as e:
            print(f"  ⚠️  Erreur partie {i}: {e}")

    if not temp_files:
        # Nettoyer le dossier temp vide
        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)
        return False

    # Combiner les fichiers audio
    combine_mp3_files(temp_files, output_file)

    # Nettoyer les fichiers temporaires
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)

    return True


def combine_mp3_files(input_files: list, output_file: Path):
    """Combine plusieurs fichiers MP3 en un seul (concaténation binaire)"""
    with open(output_file, "wb") as outf:
        for f in input_files:
            with open(f, "rb") as inf:
                outf.write(inf.read())


async def generate_vocab_audio(lesson: dict, output_dir: Path):
    """Génère l'audio de chaque mot de vocabulaire"""
    vocabulaire = lesson.get("vocabulaire", [])
    if not vocabulaire:
        return

    lesson_slug = lesson["title"].lower().replace(" ", "_")[:30]
    vocab_dir = output_dir / lesson_slug
    vocab_dir.mkdir(parents=True, exist_ok=True)

    for i, mot in enumerate(vocabulaire):
        arabe = mot.get("arabe", "")
        darija = mot.get("darija", "")
        if not arabe:
            continue

        output_file = vocab_dir / f"vocab_{i:02d}_{darija.replace(' ', '_')[:20]}.mp3"
        if output_file.exists():
            continue

        try:
            await generate_single_audio(arabe, VOICE_MALE, output_file)
        except Exception as e:
            print(f"  ⚠️  Erreur vocab '{darija}': {e}")


async def process_all_lessons():
    """Traite tous les fichiers de leçons"""
    lesson_files = sorted(LESSON_DIR.glob("*.json"))

    if not lesson_files:
        print("❌ Aucun fichier de leçon trouvé!")
        return

    total = 0
    success = 0

    for lesson_file in lesson_files:
        print(f"\n📂 {lesson_file.name}")

        with open(lesson_file, "r", encoding="utf-8") as f:
            lessons = json.load(f)

        for lesson in lessons:
            total += 1
            title = lesson["title"]
            level = lesson.get("cefr_level", "??")
            slug = re.sub(r"[^\w]", "_", title.lower())[:40]

            output_file = AUDIO_DIR / f"{level}_{slug}.mp3"

            if output_file.exists():
                print(f"  ✅ {level} - {title} (déjà généré)")
                success += 1
                continue

            print(f"  🎙️ {level} - {title}...")

            try:
                result = await generate_dialogue_audio(lesson, output_file)
                if result:
                    print(f"  ✅ OK -> {output_file.name}")
                    success += 1

                    # Générer aussi l'audio du vocabulaire
                    await generate_vocab_audio(lesson, AUDIO_DIR / "vocab")
                else:
                    print(f"  ❌ Échec")
            except Exception as e:
                print(f"  ❌ Erreur: {e}")

            # Petite pause entre les appels
            await asyncio.sleep(0.5)

    print(f"\n{'='*50}")
    print(f"✅ {success}/{total} dialogues générés avec succès")


if __name__ == "__main__":
    print("🇲🇦 Génération audio Darija - Edge TTS")
    print(f"   Voix homme: {VOICE_MALE}")
    print(f"   Voix femme: {VOICE_FEMALE}")
    print(f"   Dossier leçons: {LESSON_DIR}")
    print(f"   Dossier audio: {AUDIO_DIR}")
    print()
    asyncio.run(process_all_lessons())
