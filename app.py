"""
🇲🇦 Apprendre le Darija Marocain — Application Audio
Interface en français, audio en darija marocain
De A1 (débutant) à C2 (maîtrise)
"""

import asyncio
import base64
import hashlib
import json
import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st

# ============================================================
# CONFIGURATION
# ============================================================
APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
LESSON_DIR = DATA_DIR / "lesson_packs"
AUDIO_DIR = DATA_DIR / "lesson_audio"
VOCAB_DIR = DATA_DIR / "vocabulary"
VOCAB_AUDIO_DIR = DATA_DIR / "vocab_audio"
STORY_DIR = DATA_DIR / "stories"
STORY_AUDIO_DIR = DATA_DIR / "story_audio"
PODCAST_DIR = DATA_DIR / "podcasts"
PODCAST_AUDIO_DIR = DATA_DIR / "podcast_audio"
PROFILE_DIR = APP_DIR / "user_conversations" / "profiles"
SHADOWING_DIR = APP_DIR / "user_conversations" / "shadowing"

# Créer les dossiers nécessaires
for d in [
    AUDIO_DIR,
    VOCAB_DIR,
    VOCAB_AUDIO_DIR,
    STORY_DIR,
    STORY_AUDIO_DIR,
    PODCAST_DIR,
    PODCAST_AUDIO_DIR,
    PROFILE_DIR,
    SHADOWING_DIR,
    AUDIO_DIR / "vocab",
]:
    d.mkdir(parents=True, exist_ok=True)

# Voix Edge TTS marocaines
VOICE_MALE = "ar-MA-JamalNeural"
VOICE_FEMALE = "ar-MA-MounaNeural"

# Configuration de la page
st.set_page_config(
    page_title="🇲🇦 Darija Marocain",
    page_icon="🇲🇦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# STYLES CSS
# ============================================================
st.markdown(
    """
<style>
    /* Thème marocain */
    .main .block-container { max-width: 1200px; padding-top: 1rem; }

    .darija-card {
        background: linear-gradient(135deg, #1a472a 0%, #2d5016 100%);
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        color: white;
        border-left: 5px solid #c1272d;
    }

    .vocab-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        margin: 8px 0;
        border-left: 4px solid #c1272d;
    }

    .darija-text {
        font-size: 1.3em;
        font-weight: bold;
        color: #2d5016;
        font-family: 'Segoe UI', sans-serif;
    }

    .french-text {
        font-size: 1.1em;
        color: #555;
        font-style: italic;
    }

    .level-badge {
        display: inline-block;
        padding: 3px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.85em;
        margin: 2px;
    }
    .level-a1 { background: #e8f5e9; color: #2e7d32; }
    .level-a2 { background: #e3f2fd; color: #1565c0; }
    .level-b1 { background: #fff3e0; color: #e65100; }
    .level-b2 { background: #fce4ec; color: #c62828; }
    .level-c1 { background: #f3e5f5; color: #6a1b9a; }
    .level-c2 { background: #efebe9; color: #3e2723; }

    .stat-box {
        background: linear-gradient(135deg, #c1272d, #8b0000);
        color: white;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
    }

    .proverb-box {
        background: linear-gradient(135deg, #f5e6d0, #e8d5b7);
        border: 2px solid #c1272d;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        font-size: 1.15em;
        margin: 15px 0;
    }

    .dialogue-line {
        padding: 8px 12px;
        margin: 4px 0;
        border-radius: 8px;
    }
    .speaker-a { background: #e3f2fd; border-left: 3px solid #1565c0; }
    .speaker-b { background: #f3e5f5; border-left: 3px solid #7b1fa2; }
</style>
""",
    unsafe_allow_html=True,
)

# ============================================================
# DONNÉES ET UTILITAIRES
# ============================================================

# Thèmes disponibles avec descriptions
THEMES = {
    "salutations-presentations": {
        "nom": "🤝 Salutations & Présentations",
        "description": "Se présenter, saluer, formules de politesse",
        "niveaux": ["A1", "A2"],
    },
    "nourriture-boissons": {
        "nom": "🍵 Nourriture & Boissons",
        "description": "Au café, restaurant, souk alimentaire",
        "niveaux": ["A1", "A2", "B1"],
    },
    "deplacements-directions": {
        "nom": "🚕 Déplacements & Directions",
        "description": "Taxi, bus, demander son chemin",
        "niveaux": ["A1", "A2"],
    },
    "sante-corps": {
        "nom": "🏥 Santé & Corps",
        "description": "Chez le médecin, pharmacie, urgences",
        "niveaux": ["A2", "B1"],
    },
    "vie-sociale-loisirs": {
        "nom": "🎉 Vie sociale & Loisirs",
        "description": "Amis, week-end, fêtes, sorties",
        "niveaux": ["A2", "B1", "B2"],
    },
    "famille-maison": {
        "nom": "👨‍👩‍👧‍👦 Famille & Maison",
        "description": "Relations familiales, vie domestique",
        "niveaux": ["A1", "A2", "B1"],
    },
    "voyages-tourisme": {
        "nom": "✈️ Voyages & Tourisme",
        "description": "Planifier, réserver, visiter le Maroc",
        "niveaux": ["A2", "B1", "B2"],
    },
    "travail-professionnel": {
        "nom": "💼 Travail & Professionnel",
        "description": "Bureau, entretien, projets, collègues",
        "niveaux": ["B1", "B2", "C1"],
    },
    "societe-opinions": {
        "nom": "💬 Société & Opinions",
        "description": "Débats, éducation, politique, culture",
        "niveaux": ["B2", "C1"],
    },
    "politique-medias": {
        "nom": "📰 Politique & Médias",
        "description": "Analyse, argumentation, médias",
        "niveaux": ["C1", "C2"],
    },
    "culture-expressions": {
        "nom": "🏛️ Culture & Expressions",
        "description": "Proverbes, humour, sagesse populaire",
        "niveaux": ["B2", "C1", "C2"],
    },
    "achats-negociation": {
        "nom": "🛍️ Achats & Négociation",
        "description": "Souk, marchandage, shopping",
        "niveaux": ["A1", "A2", "B1"],
    },
    "faire-connaissance": {
        "nom": "🤝 Faire connaissance",
        "description": "Comment vas-tu, d'où tu viens, que fais-tu",
        "niveaux": ["A1", "A2"],
    },
    "transport-deplacements": {
        "nom": "🚕 Transport & Déplacements",
        "description": "Taxi, tram, Hay Riad, Salé, prix trajet",
        "niveaux": ["A1", "A2"],
    },
    "nourriture-repas": {
        "nom": "🍽️ Nourriture & Repas",
        "description": "Petit déjeuner, déjeuner, dîner, café",
        "niveaux": ["A1", "A2"],
    },
    "argent-prix": {
        "nom": "💰 Argent & Prix",
        "description": "Dirhams, combien ça coûte, payer, changer",
        "niveaux": ["A1", "A2"],
    },
    "journee-routine": {
        "nom": "📅 Journée & Routine",
        "description": "Routine, j'ai mal dormi, week-end",
        "niveaux": ["A2"],
    },
    "en-classe-comprendre": {
        "nom": "🏫 En classe & Comprendre",
        "description": "Est-ce que tu comprends, répéter, expliquer",
        "niveaux": ["A1", "A2"],
    },
}

# Niveaux CECRL avec descriptions darija
CEFR_LEVELS = {
    "A1": {
        "nom": "A1 — Découverte",
        "couleur": "#2e7d32",
        "description": "Formules de base : saluer, se présenter, commander, nombres",
        "objectifs": [
            "Dire salam et se présenter",
            "Commander au café ou au souk",
            "Les nombres et l'argent (dryal)",
            "Comprendre les directions basiques",
        ],
    },
    "A2": {
        "nom": "A2 — Survie",
        "couleur": "#1565c0",
        "description": "Conversations simples du quotidien, décrire, raconter au passé simple",
        "objectifs": [
            "Raconter sa journée",
            "Aller chez le médecin",
            "Prendre un taxi et s'orienter",
            "Faire des achats au souk",
        ],
    },
    "B1": {
        "nom": "B1 — Intermédiaire",
        "couleur": "#e65100",
        "description": "Discussions entre amis, projets, narration au passé, futur",
        "objectifs": [
            "Raconter son week-end en détail",
            "Planifier un voyage",
            "Exprimer ses goûts et préférences",
            "Participer à une conversation de groupe",
        ],
    },
    "B2": {
        "nom": "B2 — Avancé",
        "couleur": "#c62828",
        "description": "Débats, opinions nuancées, discours professionnel",
        "objectifs": [
            "Exprimer des opinions complexes",
            "Argumenter et convaincre",
            "Parler de sujets abstraits",
            "Utiliser le conditionnel et l'hypothétique",
        ],
    },
    "C1": {
        "nom": "C1 — Expert",
        "couleur": "#6a1b9a",
        "description": "Discours élaboré, analyse, registres variés",
        "objectifs": [
            "Analyser l'actualité marocaine",
            "Maîtriser les registres formel/informel",
            "Comprendre les sous-entendus culturels",
            "S'exprimer avec fluidité et précision",
        ],
    },
    "C2": {
        "nom": "C2 — Maîtrise",
        "couleur": "#3e2723",
        "description": "Proverbes, humour, nuances culturelles, expression native",
        "objectifs": [
            "Utiliser les proverbes marocains",
            "Comprendre l'humour et l'ironie",
            "Maîtriser le code-switching darija/français",
            "S'exprimer comme un natif",
        ],
    },
}

# Proverbes marocains pour la page d'accueil
PROVERBES = [
    {
        "darija": "Lli bgha l-3ssl, yssber l-9rss d n-n7l",
        "francais": "Qui veut le miel supporte les piqûres d'abeilles",
        "sens": "Pas de gain sans effort",
    },
    {
        "darija": "Lli fat mat",
        "francais": "Ce qui est passé est mort",
        "sens": "Il faut avancer, pas ressasser",
    },
    {
        "darija": "Dreb l-7did w huwa s-khoun",
        "francais": "Bats le fer tant qu'il est chaud",
        "sens": "Agis au bon moment",
    },
    {
        "darija": "3la 9dd l-7af mdd rjlik",
        "francais": "Étends tes pieds selon la couverture",
        "sens": "Vis selon tes moyens",
    },
    {
        "darija": "Koll chi b wqtou zwin",
        "francais": "Chaque chose en son temps est belle",
        "sens": "La patience paie",
    },
    {
        "darija": "L-jar 9bel d-dar",
        "francais": "Le voisin avant la maison",
        "sens": "Choisis bien ton entourage",
    },
    {
        "darija": "Lli ma 3ndou l-flous, klamou msous",
        "francais": "Celui qui n'a pas d'argent, sa parole est fade",
        "sens": "L'argent donne du poids social",
    },
    {
        "darija": "Lli daz 3lih l-bhar, ma ykhaf mn l-wad",
        "francais": "Qui a traversé la mer ne craint pas la rivière",
        "sens": "L'expérience rend courageux",
    },
]

# Translittération guide
TRANSLIT_GUIDE = {
    "3": "ع (ain) — son guttural, comme un 'a' profond de la gorge",
    "7": "ح (ha) — 'h' aspiré fort",
    "9": "ق (qaf) — 'k' du fond de la gorge",
    "kh": "خ (kha) — comme le 'ch' allemand de 'Buch'",
    "gh": "غ (ghain) — 'r' grasseyé parisien",
    "sh": "ش (shin) — 'ch' français",
    "ch": "ش (shin) — 'ch' français (variante)",
    "ss": "ص (sad) — 's' emphatique",
    "dd": "ض (dad) — 'd' emphatique",
    "tt": "ط (ta) — 't' emphatique",
}


def load_all_lessons() -> list:
    """Charge toutes les leçons depuis les fichiers JSON"""
    all_lessons = []
    for f in sorted(LESSON_DIR.glob("*.json")):
        try:
            with open(f, "r", encoding="utf-8") as fh:
                lessons = json.load(fh)
                for lesson in lessons:
                    lesson["_source_file"] = f.name
                all_lessons.extend(lessons)
        except Exception as e:
            st.error(f"Erreur chargement {f.name}: {e}")
    return all_lessons


def get_lessons_by_level(lessons: list, level: str) -> list:
    """Filtre les leçons par niveau"""
    return [l for l in lessons if l.get("cefr_level") == level]


def get_lessons_by_theme(lessons: list, theme: str) -> list:
    """Filtre les leçons par thème"""
    return [l for l in lessons if l.get("theme") == theme]


def get_audio_path(lesson: dict) -> Path:
    """Retourne le chemin du fichier audio d'une leçon"""
    level = lesson.get("cefr_level", "??")
    title = lesson.get("title", "unknown")
    slug = re.sub(r"[^\w]", "_", title.lower())[:40]
    return AUDIO_DIR / f"{level}_{slug}.mp3"


def audio_exists(lesson: dict) -> bool:
    """Vérifie si l'audio existe pour une leçon"""
    return get_audio_path(lesson).exists()


def display_audio_player(audio_path: Path):
    """Affiche un lecteur audio si le fichier existe"""
    if audio_path.exists():
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()
        st.audio(audio_bytes, format="audio/mp3")
        return True
    return False


async def generate_audio_for_lesson(lesson: dict) -> bool:
    """Génère l'audio pour une leçon (appel Edge TTS)"""
    try:
        import edge_tts
    except ImportError:
        st.error("❌ edge_tts non installé. Lancez: pip install edge-tts")
        return False

    output_file = get_audio_path(lesson)
    dialogue_arabe = lesson.get("dialogue_arabe", "")
    if not dialogue_arabe:
        return False

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
            text = re.sub(r"\.\.\.\s*\(.*?\)\s*\.\.\.", "", text).strip()
            if text:
                parts.append({"speaker": speaker, "text": text})

    if not parts:
        return False

    voice_map = {"A": VOICE_MALE, "B": VOICE_FEMALE}
    temp_dir = output_file.parent / "_temp"
    temp_dir.mkdir(exist_ok=True)
    temp_files = []

    for i, part in enumerate(parts):
        voice = voice_map.get(part["speaker"], VOICE_MALE)
        temp_file = temp_dir / f"part_{i:03d}.mp3"
        communicate = edge_tts.Communicate(part["text"], voice)
        await communicate.save(str(temp_file))
        temp_files.append(temp_file)

    # Combiner
    with open(output_file, "wb") as outf:
        for f in temp_files:
            with open(f, "rb") as inf:
                outf.write(inf.read())

    # Nettoyer
    for f in temp_files:
        f.unlink(missing_ok=True)
    try:
        temp_dir.rmdir()
    except OSError:
        pass

    return True


def load_profiles() -> list:
    """Charge les profils utilisateur"""
    profiles_file = PROFILE_DIR / "profiles.json"
    if profiles_file.exists():
        with open(profiles_file, "r", encoding="utf-8") as f:
            return json.load(f)
    default = [
        {
            "id": "default",
            "name": "Profil principal",
            "target_cefr": "A1",
            "created_at": datetime.now().isoformat(),
            "lessons_completed": [],
            "vocab_mastered": 0,
            "total_listen_minutes": 0,
        }
    ]
    save_profiles(default)
    return default


def save_profiles(profiles: list):
    """Sauvegarde les profils"""
    with open(PROFILE_DIR / "profiles.json", "w", encoding="utf-8") as f:
        json.dump(profiles, f, ensure_ascii=False, indent=2)


def load_vocab() -> list:
    """Charge le vocabulaire"""
    vocab_file = VOCAB_DIR / "vocab.json"
    if vocab_file.exists():
        with open(vocab_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_vocab(vocab: list):
    """Sauvegarde le vocabulaire"""
    with open(VOCAB_DIR / "vocab.json", "w", encoding="utf-8") as f:
        json.dump(vocab, f, ensure_ascii=False, indent=2)


def add_vocab_from_lesson(lesson: dict):
    """Ajoute le vocabulaire d'une leçon aux flashcards"""
    vocab = load_vocab()
    existing_terms = {v["darija"] for v in vocab}

    added = 0
    for mot in lesson.get("vocabulaire", []):
        if mot["darija"] not in existing_terms:
            vocab.append(
                {
                    "id": hashlib.md5(mot["darija"].encode()).hexdigest()[:8],
                    "darija": mot["darija"],
                    "arabe": mot.get("arabe", ""),
                    "francais": mot["francais"],
                    "level": lesson.get("cefr_level", "A1"),
                    "created_at": datetime.now().isoformat(),
                    "srs": {
                        "next_review": datetime.now().isoformat(),
                        "interval": 1,
                        "ease": 2.5,
                        "repetitions": 0,
                    },
                    "review_history": [],
                }
            )
            existing_terms.add(mot["darija"])
            added += 1

    if added > 0:
        save_vocab(vocab)
    return added


def format_dialogue_html(
    dialogue_darija: str, dialogue_francais: str, show_french: bool = True
) -> str:
    """Formate le dialogue en HTML avec couleurs par speaker"""
    darija_lines = dialogue_darija.strip().split("\n")
    french_lines = dialogue_francais.strip().split("\n") if dialogue_francais else []

    html = ""
    for i, line in enumerate(darija_lines):
        line = line.strip()
        if not line:
            continue

        match = re.match(r"^([A-Z]):\s*(.+)$", line)
        if match:
            speaker = match.group(1)
            text = match.group(2)
            css_class = "speaker-a" if speaker == "A" else "speaker-b"
            speaker_icon = "👨" if speaker == "A" else "👩"

            html += f'<div class="dialogue-line {css_class}">'
            html += f"<strong>{speaker_icon} {speaker}:</strong> "
            html += f'<span class="darija-text">{text}</span>'

            # Ajouter la traduction française en dessous
            if show_french and i < len(french_lines):
                fr_match = re.match(r"^[A-Z]:\s*(.+)$", french_lines[i].strip())
                if fr_match:
                    html += (
                        f'<br><span class="french-text">→ {fr_match.group(1)}</span>'
                    )

            html += "</div>"

    return html


# ============================================================
# PAGES DE L'APPLICATION
# ============================================================


def page_accueil():
    """Page d'accueil"""
    st.markdown("# 🇲🇦 Apprendre le Darija Marocain")
    st.markdown("### *Ktchuf l-darija — Découvre le darija*")

    # Proverbe du jour
    import random

    proverbe = random.choice(PROVERBES)
    st.markdown(
        f"""
    <div class="proverb-box">
        <div style="font-size: 1.4em; font-weight: bold; color: #c1272d;">🏮 Proverbe du jour</div>
        <div style="font-size: 1.3em; margin: 10px 0; color: #2d5016; font-weight: bold;">{proverbe['darija']}</div>
        <div style="font-size: 1.1em; color: #555; font-style: italic;">« {proverbe['francais']} »</div>
        <div style="font-size: 0.9em; color: #888; margin-top: 5px;">💡 {proverbe['sens']}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Stats rapides
    all_lessons = load_all_lessons()
    profiles = load_profiles()
    current_profile = profiles[0] if profiles else None
    vocab = load_vocab()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f"""<div class="stat-box">
            <div style="font-size: 2em;">📚</div>
            <div style="font-size: 1.8em; font-weight: bold;">{len(all_lessons)}</div>
            <div>Leçons disponibles</div>
        </div>""",
            unsafe_allow_html=True,
        )
    with col2:
        completed = (
            len(current_profile.get("lessons_completed", [])) if current_profile else 0
        )
        st.markdown(
            f"""<div class="stat-box">
            <div style="font-size: 2em;">✅</div>
            <div style="font-size: 1.8em; font-weight: bold;">{completed}</div>
            <div>Leçons terminées</div>
        </div>""",
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""<div class="stat-box">
            <div style="font-size: 2em;">📝</div>
            <div style="font-size: 1.8em; font-weight: bold;">{len(vocab)}</div>
            <div>Mots appris</div>
        </div>""",
            unsafe_allow_html=True,
        )
    with col4:
        level = current_profile.get("target_cefr", "A1") if current_profile else "A1"
        st.markdown(
            f"""<div class="stat-box">
            <div style="font-size: 2em;">🎯</div>
            <div style="font-size: 1.8em; font-weight: bold;">{level}</div>
            <div>Niveau actuel</div>
        </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Parcours recommandé
    st.markdown("## 🗺️ Ton parcours d'apprentissage")
    for level_key, level_data in CEFR_LEVELS.items():
        level_lessons = get_lessons_by_level(all_lessons, level_key)
        count = len(level_lessons)
        audio_count = sum(1 for l in level_lessons if audio_exists(l))

        with st.expander(
            f"{level_data['nom']} — {count} leçons ({audio_count} 🔊)",
            expanded=(level_key == level),
        ):
            st.markdown(f"*{level_data['description']}*")
            st.markdown("**Objectifs :**")
            for obj in level_data["objectifs"]:
                st.markdown(f"- {obj}")
            if count > 0:
                st.markdown(
                    f"**Leçons :** {', '.join(l['title'] for l in level_lessons)}"
                )

    st.markdown("---")

    # Guide de translittération
    with st.expander(
        "📖 Guide de translittération — Comment lire le darija en lettres latines"
    ):
        st.markdown(
            """
        Le darija n'a pas d'écriture standardisée. On utilise des **lettres latines + chiffres** pour représenter
        les sons arabes qui n'existent pas en français :
        """
        )
        for code, explanation in TRANSLIT_GUIDE.items():
            st.markdown(f"- **{code}** → {explanation}")
        st.markdown(
            """
        **Exemples :**
        - **3afak** = عافاك (s'il te plaît) — le 3 = son 'ain'
        - **7rira** = حريرة (harira) — le 7 = 'h' aspiré
        - **9hwa** = قهوة (café) — le 9 = 'q' guttural
        """
        )


def page_lecons():
    """Page des leçons avec écoute audio"""
    st.markdown("# 🎧 Leçons — Écoute & Apprends")

    all_lessons = load_all_lessons()

    # Filtres
    col1, col2 = st.columns(2)
    with col1:
        selected_level = st.selectbox(
            "📊 Niveau", ["Tous"] + list(CEFR_LEVELS.keys()), key="lesson_level"
        )
    with col2:
        theme_options = ["Tous"] + [f"{v['nom']}" for v in THEMES.values()]
        theme_keys = ["Tous"] + list(THEMES.keys())
        selected_theme_idx = st.selectbox(
            "📂 Thème",
            range(len(theme_options)),
            format_func=lambda i: theme_options[i],
            key="lesson_theme",
        )

    # Filtrer
    filtered = all_lessons
    if selected_level != "Tous":
        filtered = get_lessons_by_level(filtered, selected_level)
    if selected_theme_idx > 0:
        theme_key = theme_keys[selected_theme_idx]
        filtered = get_lessons_by_theme(filtered, theme_key)

    if not filtered:
        st.warning("Aucune leçon trouvée pour ces filtres.")
        return

    st.markdown(f"**{len(filtered)} leçon(s) trouvée(s)**")

    # Options d'affichage
    show_french = st.checkbox(
        "🇫🇷 Afficher la traduction française", value=True, key="show_fr"
    )
    show_arabe = st.checkbox(
        "🔤 Afficher le texte arabe (pour référence)", value=False, key="show_ar"
    )

    for i, lesson in enumerate(filtered):
        level = lesson.get("cefr_level", "?")
        level_class = f"level-{level.lower()}"
        has_audio = audio_exists(lesson)

        with st.expander(
            f"{'🔊' if has_audio else '📝'} {lesson['title']} "
            f"— {level} | {lesson.get('estimated_minutes', 5)} min",
            expanded=(i == 0),
        ):
            # En-tête
            st.markdown(
                f"""
            <span class="level-badge {level_class}">{level}</span>
            <strong>{lesson['title']}</strong>
            """,
                unsafe_allow_html=True,
            )

            st.markdown(f"**🎯 Objectif :** {lesson['objective']}")
            st.markdown(f"**📐 Grammaire :** {lesson['grammar_focus']}")

            if lesson.get("chunk_focus"):
                chunks = " | ".join(lesson["chunk_focus"])
                st.markdown(f"**🔑 Expressions clés :** {chunks}")

            st.markdown("---")

            # Audio
            if has_audio:
                st.markdown("### 🔊 Écouter le dialogue")
                display_audio_player(get_audio_path(lesson))
            else:
                if st.button(f"🎙️ Générer l'audio", key=f"gen_audio_{i}"):
                    with st.spinner("Génération en cours avec Edge TTS..."):
                        try:
                            result = asyncio.run(generate_audio_for_lesson(lesson))
                            if result:
                                st.success("✅ Audio généré !")
                                st.rerun()
                            else:
                                st.error("❌ Échec de la génération")
                        except Exception as e:
                            st.error(f"❌ Erreur : {e}")

            # Dialogue en darija (translittération)
            st.markdown("### 💬 Dialogue en Darija")
            dialogue_darija = lesson.get("dialogue_darija", "")
            dialogue_francais = lesson.get("dialogue_francais", "")
            html = format_dialogue_html(dialogue_darija, dialogue_francais, show_french)
            st.markdown(html, unsafe_allow_html=True)

            # Texte arabe (optionnel)
            if show_arabe:
                st.markdown("### 🔤 Texte arabe")
                st.markdown(
                    f"<div dir='rtl' style='font-size: 1.2em; line-height: 2;'>{lesson.get('dialogue_arabe', '').replace(chr(10), '<br>')}</div>",
                    unsafe_allow_html=True,
                )

            # Vocabulaire
            st.markdown("### 📚 Vocabulaire")
            for mot in lesson.get("vocabulaire", []):
                st.markdown(
                    f"""<div class="vocab-card">
                    <strong class="darija-text">{mot['darija']}</strong>
                    <span style="color: #888; margin: 0 10px;">→</span>
                    <span class="french-text">{mot['francais']}</span>
                </div>""",
                    unsafe_allow_html=True,
                )

            # Bouton ajouter au vocabulaire
            if st.button(
                f"➕ Ajouter ce vocabulaire à mes flashcards", key=f"add_vocab_{i}"
            ):
                added = add_vocab_from_lesson(lesson)
                if added > 0:
                    st.success(f"✅ {added} mot(s) ajouté(s) aux flashcards !")
                else:
                    st.info("Tous les mots sont déjà dans tes flashcards.")

            # Marquer comme terminé
            profiles = load_profiles()
            if profiles:
                profile = profiles[0]
                lesson_id = f"{lesson['_source_file']}:{lesson['title']}"
                completed = profile.get("lessons_completed", [])
                if lesson_id not in completed:
                    if st.button(f"✅ Marquer comme terminée", key=f"complete_{i}"):
                        completed.append(lesson_id)
                        profile["lessons_completed"] = completed
                        save_profiles(profiles)
                        st.success("Leçon marquée comme terminée ! 🎉")
                        st.rerun()
                else:
                    st.success("✅ Leçon déjà terminée")


def page_vocabulaire():
    """Page vocabulaire & flashcards avec SRS"""
    st.markdown("# 📚 Vocabulaire & Flashcards")

    vocab = load_vocab()

    if not vocab:
        st.info("Aucun mot dans ton vocabulaire. Ajoute-en depuis les leçons ! 📖")
        return

    # Stats
    total = len(vocab)
    due = sum(
        1
        for v in vocab
        if v.get("srs", {}).get("next_review", "") <= datetime.now().isoformat()
    )
    mastered = sum(1 for v in vocab if v.get("srs", {}).get("repetitions", 0) >= 5)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total mots", total)
    with col2:
        st.metric("À réviser", due)
    with col3:
        st.metric("Maîtrisés", mastered)

    # Mode de révision
    mode = st.radio(
        "Mode",
        ["📋 Liste complète", "🎯 Révision SRS", "🔍 Recherche"],
        horizontal=True,
    )

    if mode == "📋 Liste complète":
        # Filtrer par niveau
        levels = sorted(set(v.get("level", "A1") for v in vocab))
        selected = st.multiselect("Filtrer par niveau", levels, default=levels)
        filtered = [v for v in vocab if v.get("level", "A1") in selected]

        for v in filtered:
            st.markdown(
                f"""<div class="vocab-card">
                <strong class="darija-text">{v['darija']}</strong>
                <span style="color: #888; margin: 0 10px;">→</span>
                <span class="french-text">{v['francais']}</span>
                <span class="level-badge level-{v.get('level', 'a1').lower()}" style="float: right;">{v.get('level', 'A1')}</span>
            </div>""",
                unsafe_allow_html=True,
            )

    elif mode == "🎯 Révision SRS":
        due_cards = [
            v
            for v in vocab
            if v.get("srs", {}).get("next_review", "") <= datetime.now().isoformat()
        ]

        if not due_cards:
            st.success("🎉 Pas de mots à réviser ! Reviens plus tard.")
            return

        st.markdown(f"**{len(due_cards)} mot(s) à réviser**")

        if "current_card_idx" not in st.session_state:
            st.session_state.current_card_idx = 0
        if "show_answer" not in st.session_state:
            st.session_state.show_answer = False

        idx = st.session_state.current_card_idx
        if idx >= len(due_cards):
            st.success("🎉 Révision terminée !")
            st.session_state.current_card_idx = 0
            return

        card = due_cards[idx]

        st.markdown(f"### Carte {idx + 1} / {len(due_cards)}")

        # Afficher la question (darija)
        st.markdown(
            f"""
        <div style="background: #1a472a; color: white; padding: 30px; border-radius: 15px; text-align: center; font-size: 2em;">
            {card['darija']}
        </div>
        """,
            unsafe_allow_html=True,
        )

        if not st.session_state.show_answer:
            if st.button("👁️ Voir la réponse", use_container_width=True):
                st.session_state.show_answer = True
                st.rerun()
        else:
            st.markdown(
                f"""
            <div style="background: #f5f5f5; padding: 20px; border-radius: 10px; text-align: center; font-size: 1.5em; margin: 10px 0;">
                {card['francais']}
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Boutons de rating
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("❌ Difficile", use_container_width=True, key="srs_hard"):
                    update_srs(card, 1)
                    st.session_state.current_card_idx += 1
                    st.session_state.show_answer = False
                    st.rerun()
            with col2:
                if st.button("👍 Bien", use_container_width=True, key="srs_ok"):
                    update_srs(card, 2)
                    st.session_state.current_card_idx += 1
                    st.session_state.show_answer = False
                    st.rerun()
            with col3:
                if st.button("⭐ Facile", use_container_width=True, key="srs_easy"):
                    update_srs(card, 3)
                    st.session_state.current_card_idx += 1
                    st.session_state.show_answer = False
                    st.rerun()

    elif mode == "🔍 Recherche":
        query = st.text_input("🔍 Chercher un mot (darija ou français)")
        if query:
            results = [
                v
                for v in vocab
                if query.lower() in v["darija"].lower()
                or query.lower() in v["francais"].lower()
            ]
            if results:
                for v in results:
                    st.markdown(
                        f"""<div class="vocab-card">
                        <strong class="darija-text">{v['darija']}</strong>
                        <span style="color: #888; margin: 0 10px;">→</span>
                        <span class="french-text">{v['francais']}</span>
                    </div>""",
                        unsafe_allow_html=True,
                    )
            else:
                st.info("Aucun résultat.")


def update_srs(card: dict, rating: int):
    """Met à jour le SRS d'une carte (algorithme SM-2 simplifié)"""
    vocab = load_vocab()
    for v in vocab:
        if v["id"] == card["id"]:
            srs = v.get("srs", {"interval": 1, "ease": 2.5, "repetitions": 0})

            if rating == 1:  # Difficile
                srs["interval"] = 1
                srs["ease"] = max(1.3, srs["ease"] - 0.2)
            elif rating == 2:  # Bien
                srs["interval"] = max(1, int(srs["interval"] * srs["ease"]))
                srs["repetitions"] = srs.get("repetitions", 0) + 1
            elif rating == 3:  # Facile
                srs["interval"] = max(1, int(srs["interval"] * srs["ease"] * 1.3))
                srs["ease"] = min(3.0, srs["ease"] + 0.15)
                srs["repetitions"] = srs.get("repetitions", 0) + 1

            next_review = datetime.now() + timedelta(days=srs["interval"])
            srs["next_review"] = next_review.isoformat()
            v["srs"] = srs

            v.setdefault("review_history", []).append(
                {
                    "date": datetime.now().isoformat(),
                    "rating": rating,
                    "rating_label": ["", "Difficile", "Bien", "Facile"][rating],
                }
            )
            break
    save_vocab(vocab)


def page_shadowing():
    """Page de shadowing interactif"""
    st.markdown("# 🎯 Shadowing Interactif")
    st.markdown(
        """
    Le **shadowing** consiste à écouter une phrase en darija et la **répéter immédiatement**.
    C'est la technique la plus efficace pour améliorer ta prononciation !

    **Comment ça marche :**
    1. 🎧 Écoute la phrase en darija
    2. 📖 Lis la translittération
    3. 🗣️ Répète à voix haute
    4. 🔁 Réécoute et compare
    """
    )

    all_lessons = load_all_lessons()
    if not all_lessons:
        st.info("Aucune leçon disponible.")
        return

    # Sélection de la leçon
    lesson_titles = [f"[{l['cefr_level']}] {l['title']}" for l in all_lessons]
    selected_idx = st.selectbox(
        "Choisis une leçon",
        range(len(lesson_titles)),
        format_func=lambda i: lesson_titles[i],
    )
    lesson = all_lessons[selected_idx]

    # Extraire les phrases du dialogue darija
    dialogue = lesson.get("dialogue_darija", "")
    dialogue_fr = lesson.get("dialogue_francais", "")
    darija_lines = [
        l.strip()
        for l in dialogue.split("\n")
        if l.strip() and re.match(r"^[A-Z]:", l.strip())
    ]
    french_lines = [
        l.strip()
        for l in dialogue_fr.split("\n")
        if l.strip() and re.match(r"^[A-Z]:", l.strip())
    ]

    st.markdown(f"### {lesson['title']} ({lesson['cefr_level']})")
    st.markdown(f"**{len(darija_lines)} phrases à pratiquer**")

    show_fr = st.checkbox("Afficher la traduction", value=True, key="shad_fr")

    for i, line in enumerate(darija_lines):
        match = re.match(r"^([A-Z]):\s*(.+)$", line)
        if not match:
            continue

        speaker = match.group(1)
        text = match.group(2)
        speaker_icon = "👨" if speaker == "A" else "👩"
        css_class = "speaker-a" if speaker == "A" else "speaker-b"

        st.markdown(
            f"""<div class="dialogue-line {css_class}">
            <strong>{speaker_icon} Phrase {i + 1}</strong>
        </div>""",
            unsafe_allow_html=True,
        )

        # Darija en translittération
        st.markdown(f"**Darija :** {text}")

        # Traduction
        if show_fr and i < len(french_lines):
            fr_match = re.match(r"^[A-Z]:\s*(.+)$", french_lines[i])
            if fr_match:
                st.markdown(f"*🇫🇷 {fr_match.group(1)}*")

        # Audio individuel si disponible
        arabe_lines = lesson.get("dialogue_arabe", "").strip().split("\n")
        if i < len(arabe_lines):
            arabe_match = re.match(r"^[A-Z]:\s*(.+)$", arabe_lines[i].strip())
            if arabe_match:
                arabe_text = arabe_match.group(1)
                if st.button(f"🔊 Écouter", key=f"shad_listen_{i}"):
                    try:
                        import edge_tts

                        voice = VOICE_MALE if speaker == "A" else VOICE_FEMALE
                        temp_file = AUDIO_DIR / f"_shad_temp_{i}.mp3"
                        asyncio.run(
                            edge_tts.Communicate(arabe_text, voice).save(str(temp_file))
                        )
                        display_audio_player(temp_file)
                        temp_file.unlink(missing_ok=True)
                    except Exception as e:
                        st.error(f"Erreur: {e}")

        st.markdown("---")


def page_expressions():
    """Page des expressions & proverbes essentiels"""
    st.markdown("# 🏛️ Expressions & Proverbes Marocains")

    tab1, tab2, tab3 = st.tabs(
        ["🗣️ Expressions du quotidien", "🏮 Proverbes", "📖 Guide de prononciation"]
    )

    with tab1:
        st.markdown("### Expressions essentielles")
        expressions = [
            {
                "cat": "Salutations",
                "items": [
                    ("Salam 3likom", "السلام عليكم", "Bonjour (formel)"),
                    ("Salam", "السلام", "Salut"),
                    ("Sbah l-khir", "صباح الخير", "Bonjour (matin)"),
                    ("Msa l-khir", "مساء الخير", "Bonsoir"),
                    ("Bslama", "بسلامة", "Au revoir"),
                    ("Tssba7 3la khir", "تصبح على خير", "Bonne nuit"),
                ],
            },
            {
                "cat": "Formules de politesse",
                "items": [
                    ("3afak / 3afak", "عافاك", "S'il te/vous plaît"),
                    (
                        "Chokran / Chokran bzzaf",
                        "شكرا / شكرا بزاف",
                        "Merci / Merci beaucoup",
                    ),
                    ("Bla jmil", "بلا جميل", "De rien"),
                    ("Smh liya", "سمح ليا", "Excuse-moi / Pardon"),
                    ("Mcharfin", "مشرفين", "Enchanté(e)"),
                    ("Allah y3awnk", "الله يعاونك", "Que Dieu t'aide (encouragement)"),
                ],
            },
            {
                "cat": "Réactions & émotions",
                "items": [
                    ("Wa3r! / Waer!", "واعر", "Super ! Génial !"),
                    ("Zwin!", "زوين", "Beau / Joli !"),
                    ("Hchoma!", "حشومة", "Honte ! C'est la honte !"),
                    ("Ya latif!", "يا لطيف", "Oh mon Dieu ! (surprise)"),
                    ("Ma3lich", "معليش", "C'est pas grave / Tant pis"),
                    ("Nchallah", "إن شاء الله", "Si Dieu le veut"),
                    ("Tbark llah", "تبارك الله", "Bravo ! (admiration)"),
                ],
            },
            {
                "cat": "Questions utiles",
                "items": [
                    ("Bchhal?", "بشحال؟", "Combien ?"),
                    ("Fin?", "فين؟", "Où ?"),
                    ("Imta?", "إمتى؟", "Quand ?"),
                    ("3lach?", "علاش؟", "Pourquoi ?"),
                    ("Chnou? / Achnou?", "شنو؟ / أشنو؟", "Quoi ?"),
                    ("Chkoun?", "شكون؟", "Qui ?"),
                    ("Kif? / Kifach?", "كيف؟ / كيفاش؟", "Comment ?"),
                    ("Wach...?", "واش...؟", "Est-ce que... ?"),
                ],
            },
        ]

        for group in expressions:
            st.markdown(f"#### {group['cat']}")
            for darija, arabe, francais in group["items"]:
                st.markdown(
                    f"""<div class="vocab-card">
                    <strong class="darija-text">{darija}</strong>
                    <span style="color: #888; margin: 0 10px;">→</span>
                    <span class="french-text">{francais}</span>
                </div>""",
                    unsafe_allow_html=True,
                )

    with tab2:
        st.markdown("### 🏮 Proverbes & Sagesse populaire marocaine")
        for p in PROVERBES:
            st.markdown(
                f"""<div class="proverb-box">
                <div style="font-size: 1.2em; font-weight: bold; color: #2d5016;">{p['darija']}</div>
                <div style="color: #555; font-style: italic; margin: 5px 0;">« {p['francais']} »</div>
                <div style="color: #888; font-size: 0.9em;">💡 {p['sens']}</div>
            </div>""",
                unsafe_allow_html=True,
            )

    with tab3:
        st.markdown("### 📖 Guide de prononciation du Darija")
        st.markdown(
            """
        Le darija marocain contient des sons qui n'existent pas en français.
        Voici comment les prononcer :
        """
        )

        for code, expl in TRANSLIT_GUIDE.items():
            st.markdown(f"**`{code}`** — {expl}")

        st.markdown(
            """
        ---
        ### 🎵 Particularités du darija marocain

        **1. Les voyelles sont souvent supprimées :**
        - "ktab" au lieu de "kitab" (livre)
        - "bnt" au lieu de "bint" (fille)

        **2. Emprunts massifs au français :**
        - "tomobil" (automobile), "tléfon" (téléphone), "portabl" (portable)
        - "la croisement", "l-boulice", "ssimana" (semaine)

        **3. Emprunts à l'espagnol (surtout au Nord) :**
        - "simana" (semana), "cocina" (cuisine), "bixo" (voisin)

        **4. Le code-switching :**
        - Les Marocains mélangent naturellement darija et français dans la même phrase
        - Ex: "Ghadi nmchi l-la gare bach nakhd l-train" (Je vais à la gare pour prendre le train)
        """
        )


def page_nombres_temps():
    """Page des nombres, temps et jours"""
    st.markdown("# 🔢 Nombres, Temps & Jours")

    tab1, tab2, tab3 = st.tabs(["🔢 Nombres", "📅 Jours & Mois", "⏰ L'heure"])

    with tab1:
        st.markdown("### Les nombres en darija")
        nombres = [
            (0, "sfr", "صفر"),
            (1, "wa7d", "واحد"),
            (2, "jouj", "جوج"),
            (3, "tlata", "تلاتا"),
            (4, "rb3a", "ربعا"),
            (5, "khmsa", "خمسة"),
            (6, "stta", "ستة"),
            (7, "sb3a", "سبعة"),
            (8, "tmnya", "تمنية"),
            (9, "ts3oud", "تسعود"),
            (10, "3chra", "عشرة"),
            (11, "7dach", "حداش"),
            (12, "tnach", "طناش"),
            (13, "tlttach", "تلطاش"),
            (14, "rb3tach", "ربعطاش"),
            (15, "khmstach", "خمسطاش"),
            (20, "3chrin", "عشرين"),
            (30, "tlatin", "تلاتين"),
            (40, "rb3in", "ربعين"),
            (50, "khmsin", "خمسين"),
            (100, "mia", "مية"),
            (1000, "alf", "ألف"),
        ]

        cols = st.columns(3)
        for i, (num, darija, arabe) in enumerate(nombres):
            with cols[i % 3]:
                st.markdown(
                    f"""<div class="vocab-card">
                    <strong>{num}</strong> →
                    <span class="darija-text">{darija}</span>
                </div>""",
                    unsafe_allow_html=True,
                )

        st.markdown(
            """
        ### 💰 L'argent
        - **Dryal / Dirham** — Monnaie marocaine
        - **Ryal** — Unité populaire (1 dirham = 20 ryals)
        - "Bchhal?" → Combien ça coûte ?
        - "3chrin d dryal" → 20 dirhams
        """
        )

    with tab2:
        st.markdown("### Les jours de la semaine")
        jours = [
            ("Nhar l-tnin", "الاثنين", "Lundi"),
            ("Nhar t-tlat", "الثلاثاء", "Mardi"),
            ("Nhar l-arb3a", "الأربعاء", "Mercredi"),
            ("Nhar l-khmis", "الخميس", "Jeudi"),
            ("Nhar j-jm3a", "الجمعة", "Vendredi"),
            ("Nhar s-sbt", "السبت", "Samedi"),
            ("Nhar l-7dd", "الأحد", "Dimanche"),
        ]
        for darija, arabe, francais in jours:
            st.markdown(
                f"""<div class="vocab-card">
                <strong>{francais}</strong> →
                <span class="darija-text">{darija}</span>
            </div>""",
                unsafe_allow_html=True,
            )

    with tab3:
        st.markdown("### Dire l'heure")
        heures = [
            ("Chal f sa3a?", "Il est quelle heure ?"),
            ("Sa3a wa7da", "1 heure"),
            ("Sa3a jouj", "2 heures"),
            ("Sa3a tlata w noss", "3 heures et demie"),
            ("Sa3a rb3a lla rb3", "4 heures moins le quart"),
            ("Sa3a khmsa w rb3", "5 heures et quart"),
            ("F ssba7", "Le matin"),
            ("F l-3chiya", "Le soir"),
            ("F l-lil", "La nuit"),
        ]
        for darija, francais in heures:
            st.markdown(
                f"""<div class="vocab-card">
                <span class="french-text">{francais}</span> →
                <strong class="darija-text">{darija}</strong>
            </div>""",
                unsafe_allow_html=True,
            )


def page_grammaire():
    """Page de grammaire essentielle du darija"""
    st.markdown("# 📐 Grammaire Essentielle du Darija")

    st.markdown(
        """
    La grammaire du darija est **beaucoup plus simple** que celle de l'arabe classique.
    Voici les règles essentielles :
    """
    )

    tab1, tab2, tab3, tab4 = st.tabs(
        ["👤 Pronoms", "🔄 Verbes", "❓ Questions", "🔗 Connecteurs"]
    )

    with tab1:
        st.markdown("### Pronoms personnels")
        pronoms = [
            ("Ana", "أنا", "Je / Moi"),
            ("Nta", "نتا", "Tu / Toi (masculin)"),
            ("Nti", "نتي", "Tu / Toi (féminin)"),
            ("Huwa", "هوا", "Il / Lui"),
            ("Hiya", "هيا", "Elle"),
            ("7na", "حنا", "Nous"),
            ("Ntouma", "نتوما", "Vous"),
            ("Houma", "هوما", "Ils / Elles"),
        ]
        for darija, arabe, francais in pronoms:
            st.markdown(
                f"""<div class="vocab-card">
                <strong class="darija-text">{darija}</strong> →
                <span class="french-text">{francais}</span>
            </div>""",
                unsafe_allow_html=True,
            )

        st.markdown(
            """
        ### Possessifs
        On ajoute un suffixe au nom :
        - **-i** → mon/ma (ktab**i** = mon livre)
        - **-k** → ton/ta (ktab**k** = ton livre)
        - **-ou** → son/sa (ktab**ou** = son livre)
        - **-na** → notre (ktab**na** = notre livre)
        - **-kom** → votre (ktab**kom** = votre livre)
        - **-hom** → leur (ktab**hom** = leur livre)
        """
        )

    with tab2:
        st.markdown("### Conjugaison simplifiée")
        st.markdown(
            """
        Le darija a **3 temps principaux** :

        #### 🔵 Présent : **ka-** + verbe
        | Pronom | Manger (kla) | Parler (hdr) |
        |--------|-------------|--------------|
        | Ana | ka-**nakol** | ka-**nhdr** |
        | Nta | ka-**takol** | ka-**thdr** |
        | Nti | ka-**takli** | ka-**thdri** |
        | Huwa | ka-**yakol** | ka-**yhdr** |
        | Hiya | ka-**takol** | ka-**thdr** |
        | 7na | ka-**naklo** | ka-**nhdro** |

        #### 🟢 Passé : verbe conjugué directement
        | Pronom | Manger | Aller (mcha) |
        |--------|--------|-------------|
        | Ana | **klit** | **mchit** |
        | Nta | **kliti** | **mchiti** |
        | Huwa | **kla** | **mcha** |
        | Hiya | **klat** | **mchat** |
        | 7na | **klina** | **mchina** |

        #### 🟡 Futur : **ghadi** + verbe au présent (sans ka-)
        - Ana **ghadi nakol** → Je vais manger
        - Huwa **ghadi ymchi** → Il va aller
        - 7na **ghadi nmchiw** → On va aller
        """
        )

    with tab3:
        st.markdown("### Former des questions")
        st.markdown(
            """
        #### Méthode 1 : Wach + phrase
        - **Wach** nta mn l-Maghrib? → **Est-ce que** tu es du Maroc ?
        - **Wach** bghiti atay? → **Est-ce que** tu veux du thé ?

        #### Méthode 2 : Mot interrogatif
        - **Chnou** bghiti? → **Que** veux-tu ?
        - **Fin** ka-tskon? → **Où** habites-tu ?
        - **Imta** ghadi tmchi? → **Quand** tu vas partir ?
        - **3lach** ma jitich? → **Pourquoi** tu n'es pas venu ?
        - **Kifach** drti? → **Comment** t'as fait ?
        - **Chkoun** hada? → **Qui** est-ce ?
        - **Bchhal** had chi? → **Combien** ça coûte ?

        #### Négation
        - **Ma** + verbe + **ch** (encadre le verbe)
        - Ma bghit**ch** → Je ne veux pas
        - Ma mchit**ch** → Je ne suis pas allé
        - Ma ka-nfhm**ch** → Je ne comprends pas
        """
        )

    with tab4:
        st.markdown("### Connecteurs & mots de liaison")
        connecteurs = [
            ("W", "Et"),
            ("Wla", "Ou"),
            ("Walakin", "Mais"),
            ("7it / Hit", "Parce que"),
            ("Bach", "Pour / Afin de"),
            ("Ila", "Si (condition)"),
            ("Mn b3d", "Après / Ensuite"),
            ("L-awwl", "D'abord"),
            ("F l-akher", "À la fin"),
            ("Daba", "Maintenant"),
            ("Mn 9bl", "Avant"),
            ("B7al", "Comme"),
        ]
        cols = st.columns(2)
        for i, (darija, francais) in enumerate(connecteurs):
            with cols[i % 2]:
                st.markdown(f"- **{darija}** → {francais}")


def page_progression():
    """Page de suivi de progression"""
    st.markdown("# 📊 Ma Progression")

    profiles = load_profiles()
    profile = profiles[0] if profiles else None
    if not profile:
        st.error("Aucun profil trouvé.")
        return

    all_lessons = load_all_lessons()
    vocab = load_vocab()
    completed = profile.get("lessons_completed", [])

    # Vue d'ensemble
    st.markdown("### 📈 Vue d'ensemble")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        pct = (len(completed) / len(all_lessons) * 100) if all_lessons else 0
        st.metric(
            "Progression leçons", f"{pct:.0f}%", f"{len(completed)}/{len(all_lessons)}"
        )
    with col2:
        st.metric("Vocabulaire total", len(vocab))
    with col3:
        mastered = sum(1 for v in vocab if v.get("srs", {}).get("repetitions", 0) >= 5)
        st.metric("Mots maîtrisés", mastered)
    with col4:
        st.metric("Niveau cible", profile.get("target_cefr", "A1"))

    # Progression par niveau
    st.markdown("### 📊 Par niveau")
    for level_key in CEFR_LEVELS:
        level_lessons = get_lessons_by_level(all_lessons, level_key)
        if not level_lessons:
            continue
        level_completed = sum(
            1 for l in level_lessons if f"{l['_source_file']}:{l['title']}" in completed
        )
        total = len(level_lessons)
        pct = (level_completed / total * 100) if total else 0

        st.markdown(f"**{level_key}** — {level_completed}/{total} leçons")
        st.progress(pct / 100)

    # Changer le niveau cible
    st.markdown("---")
    st.markdown("### ⚙️ Paramètres")
    new_level = st.selectbox(
        "Modifier mon niveau cible",
        list(CEFR_LEVELS.keys()),
        index=list(CEFR_LEVELS.keys()).index(profile.get("target_cefr", "A1")),
    )
    if new_level != profile.get("target_cefr"):
        if st.button("💾 Sauvegarder"):
            profile["target_cefr"] = new_level
            save_profiles(profiles)
            st.success(f"Niveau cible mis à jour : {new_level}")
            st.rerun()


# ============================================================
# PAGE HISTOIRES
# ============================================================
def page_histoires():
    """Page histoires progressives adaptées au niveau"""
    st.markdown("# 📖 Histoires en Darija")
    st.markdown(
        "Des histoires courtes adaptées à ton niveau pour pratiquer la compréhension."
    )

    # Charger les histoires
    stories_file = STORY_DIR / "stories.json"
    if not stories_file.exists():
        st.warning("Aucune histoire disponible pour le moment.")
        return

    try:
        with open(stories_file, "r", encoding="utf-8") as f:
            stories = json.load(f)
    except Exception as e:
        st.error(f"Erreur chargement histoires: {e}")
        return

    if not stories:
        st.warning("Aucune histoire disponible.")
        return

    # Filtre par niveau
    levels_available = sorted(set(s.get("cefr_level", "A1") for s in stories))
    selected_level = st.selectbox(
        "📊 Filtrer par niveau", ["Tous"] + levels_available, key="story_level"
    )

    filtered = stories
    if selected_level != "Tous":
        filtered = [s for s in stories if s.get("cefr_level") == selected_level]

    st.markdown(f"**{len(filtered)} histoire(s) disponible(s)**")

    show_french = st.checkbox(
        "🇫🇷 Afficher la traduction française", value=False, key="story_show_fr"
    )

    for i, story in enumerate(filtered):
        level = story.get("cefr_level", "?")
        level_class = f"level-{level.lower()}"

        # Audio path
        slug = re.sub(r"[^\w]", "_", story["title"].lower())[:40]
        audio_path = STORY_AUDIO_DIR / f"{level}_{slug}.mp3"

        with st.expander(
            f"{'🔊' if audio_path.exists() else '📖'} {story['title']} "
            f"— {level} | ~{story.get('estimated_minutes', 5)} min",
            expanded=(i == 0),
        ):
            st.markdown(
                f'<span class="level-badge {level_class}">{level}</span> '
                f'<strong>{story["title"]}</strong>',
                unsafe_allow_html=True,
            )
            st.markdown(f"*{story.get('description', '')}*")
            st.markdown("---")

            # Audio
            if audio_path.exists():
                st.markdown("### 🔊 Écouter l'histoire")
                with open(audio_path, "rb") as af:
                    st.audio(af.read(), format="audio/mp3")
            else:
                if st.button(f"🎙️ Générer l'audio", key=f"gen_story_audio_{i}"):
                    with st.spinner("Génération audio en cours..."):
                        try:
                            import edge_tts

                            text_arabe = story.get("story_arabe", "")
                            if text_arabe:
                                STORY_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
                                communicate = edge_tts.Communicate(
                                    text_arabe, "ar-MA-JamalNeural"
                                )
                                asyncio.run(communicate.save(str(audio_path)))
                                st.success("✅ Audio généré !")
                                st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erreur : {e}")

            # Histoire en darija
            st.markdown("### 💬 Histoire en Darija")
            st.markdown(
                f"<div style='font-size: 1.1em; line-height: 1.8; background: #f0f8ff; "
                f"padding: 15px; border-radius: 10px; border-left: 4px solid #1976d2;'>"
                f"{story.get('story_darija', '').replace(chr(10), '<br>')}</div>",
                unsafe_allow_html=True,
            )

            # Traduction française
            if show_french:
                st.markdown("### 🇫🇷 Traduction française")
                st.markdown(
                    f"<div style='font-size: 1.05em; line-height: 1.8; background: #fff3e0; "
                    f"padding: 15px; border-radius: 10px; border-left: 4px solid #ff9800;'>"
                    f"{story.get('story_francais', '').replace(chr(10), '<br>')}</div>",
                    unsafe_allow_html=True,
                )

            # Vocabulaire clé
            if story.get("vocabulaire_cle"):
                st.markdown("### 📚 Vocabulaire clé")
                for mot in story["vocabulaire_cle"]:
                    st.markdown(
                        f"""<div class="vocab-card">
                        <strong class="darija-text">{mot['darija']}</strong>
                        <span style="color: #888; margin: 0 10px;">→</span>
                        <span class="french-text">{mot['francais']}</span>
                    </div>""",
                        unsafe_allow_html=True,
                    )

            # Marquer comme terminée
            profiles = load_profiles()
            if profiles:
                profile = profiles[0]
                story_id = f"story:{story['title']}"
                completed = profile.get("lessons_completed", [])
                if story_id not in completed:
                    if st.button(
                        f"✅ Marquer cette histoire comme lue",
                        key=f"complete_story_{i}",
                    ):
                        completed.append(story_id)
                        profile["lessons_completed"] = completed
                        save_profiles(profiles)
                        st.success("Histoire marquée comme lue ! 🎉")
                        st.rerun()
                else:
                    st.success("✅ Histoire déjà lue")


# ============================================================
# NAVIGATION
# ============================================================
def main():
    # Sidebar
    with st.sidebar:
        st.markdown("## 🇲🇦 Darija Marocain")
        st.markdown("*Apprends le dialecte marocain*")
        st.markdown("---")

        page = st.radio(
            "Navigation",
            [
                "🏠 Accueil",
                "🎧 Leçons (Écoute)",
                "📖 Histoires",
                "🎯 Shadowing",
                "📚 Vocabulaire & Flashcards",
                "🏛️ Expressions & Proverbes",
                "🔢 Nombres, Temps & Jours",
                "📐 Grammaire essentielle",
                "📊 Ma Progression",
            ],
            key="nav",
        )

        st.markdown("---")

        # Profil
        profiles = load_profiles()
        if profiles:
            profile = profiles[0]
            st.markdown(f"**👤 {profile['name']}**")
            st.markdown(f"**🎯 Niveau : {profile.get('target_cefr', 'A1')}**")

        st.markdown("---")
        st.markdown(
            """
        **🔊 Voix TTS :**
        - 👨 Jamal (homme)
        - 👩 Mouna (femme)

        *Edge TTS — Gratuit*
        """
        )

    # Router
    if page == "🏠 Accueil":
        page_accueil()
    elif page == "🎧 Leçons (Écoute)":
        page_lecons()
    elif page == "📖 Histoires":
        page_histoires()
    elif page == "🎯 Shadowing":
        page_shadowing()
    elif page == "📚 Vocabulaire & Flashcards":
        page_vocabulaire()
    elif page == "🏛️ Expressions & Proverbes":
        page_expressions()
    elif page == "🔢 Nombres, Temps & Jours":
        page_nombres_temps()
    elif page == "📐 Grammaire essentielle":
        page_grammaire()
    elif page == "📊 Ma Progression":
        page_progression()


if __name__ == "__main__":
    main()
