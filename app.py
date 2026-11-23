import os
import base64
import requests
import streamlit as st
from google import genai
from google.genai import types

FICHIER_CLE = "cle.txt"
FICHIER_MEMOIRE = "memoire.txt"
MODELE = "gemini-2.5-flash-lite"

st.set_page_config(page_title="Mon IA personnelle", page_icon="🧠", layout="wide")

TAILLES = {"Petite": "0.92rem", "Normale": "1rem", "Grande": "1.12rem"}
ACCENTS = {"Rouge carmin": "#e11d48", "Rouge sombre": "#be123c", "Gris acier": "#9a9aa6", "Blanc cassé": "#dcdce1"}

taille = TAILLES.get(st.session_state.get("taille", "Normale"), "1rem")
accent = ACCENTS.get(st.session_state.get("accent", "Rouge carmin"), "#e11d48")

CSS = """
<style>
:root { color-scheme: dark; }
.stApp {
    background: linear-gradient(160deg, #2b2b33 0%, #1f1f26 45%, #34343d 100%);
    background-attachment: fixed;
}
.stApp, .stApp p, .stApp span, .stApp label, .stApp li, .stApp div,
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stMarkdown {
    color: #e8e8ec !important;
    font-size: __TAILLE__;
}
.stCaption, [data-testid="stCaptionContainer"], .stApp small { color: #a3a3ae !important; }
header[data-testid="stHeader"] { background: transparent; }
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #3a3a44 0%, #2c2c34 100%);
    border-right: 1px solid #4a4a55;
}
.titre {
    font-size: 2.2rem;
    font-weight: 800;
    letter-spacing: -0.5px;
    color: #f2f2f5 !important;
    margin-bottom: 0;
    border-left: 4px solid __ACCENT__;
    padding-left: 14px;
}
.sous-titre { color: #a3a3ae !important; margin: 4px 0 1.6rem 18px; }
.carte {
    background: linear-gradient(145deg, #3c3c46, #30303a);
    border: 1px solid #55555f;
    border-top: 2px solid __ACCENT__;
    border-radius: 4px;
    padding: 18px;
    min-height: 110px;
}
.carte b { color: #f2f2f5 !important; font-size: 1.05rem; letter-spacing: 0.3px; }
.carte span { color: #b4b4be !important; }
div[data-testid="stChatMessage"] {
    background: linear-gradient(145deg, #3a3a44, #2f2f38);
    border: 1px solid #50505a;
    border-radius: 4px;
    padding: 14px 18px;
    margin-bottom: 10px;
}
[data-testid="stBottom"], [data-testid="stBottom"] > div { background: #26262d !important; }
[data-testid="stChatInput"],
[data-testid="stChatInput"] > div,
[data-testid="stChatInputContainer"] {
    background: #34343e !important;
    border: 1px solid __ACCENT__ !important;
    border-radius: 4px !important;
}
[data-testid="stChatInput"] textarea,
[data-testid="stChatInputTextArea"], textarea {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    caret-color: __ACCENT__ !important;
    background-color: transparent !important;
    opacity: 1 !important;
}
[data-testid="stChatInput"] textarea::placeholder, textarea::placeholder {
    color: #a3a3ae !important;
    -webkit-text-fill-color: #a3a3ae !important;
    opacity: 1 !important;
}
[data-testid="stChatInput"] button {
    background: __ACCENT__ !important;
    border-radius: 3px !important;
}
[data-testid="stChatInput"] button svg { fill: #ffffff !important; color: #ffffff !important; }
.stTextInput input, .stTextArea textarea {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    background: #34343e !important;
    border-radius: 4px !important;
}
.stButton > button, .stDownloadButton > button {
    border-radius: 4px;
    border: 1px solid #5a5a66;
    background: #3a3a44;
    color: #f0f0f3 !important;
    width: 100%;
    font-weight: 600;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    border-color: __ACCENT__;
    color: #ffffff !important;
    background: #44444f;
}
.stButton > button p, .stDownloadButton > button p { color: #f0f0f3 !important; }
div[data-baseweb="select"] > div {
    background: #34343e !important;
    border: 1px solid #5a5a66 !important;
    border-radius: 4px !important;
}
div[data-baseweb="select"] * { color: #f0f0f3 !important; }
[data-testid="stExpander"] {
    background: #34343e;
    border: 1px solid #50505a;
    border-radius: 4px;
}
[data-testid="stAlert"] {
    background: #3a2f33 !important;
    border: 1px solid __ACCENT__;
    border-radius: 4px;
}
[data-testid="stFileUploader"] section {
    background: #34343e;
    border: 1px dashed #5a5a66;
    border-radius: 4px;
}
hr { border-color: #4a4a55 !important; }
</style>
"""
st.markdown(CSS.replace("__ACCENT__", accent).replace("__TAILLE__", taille), unsafe_allow_html=True)

TONS = {
    "Amical": "Tu es chaleureux et simple.",
    "Professionnel": "Tu es precis, clair et professionnel.",
    "Creatif": "Tu es inventif, plein d'idees originales.",
    "Direct": "Tu es tres bref et va droit au but.",
}
LONGUEURS = {
    "Courtes": "Tes reponses sont courtes.",
    "Normales": "Tes reponses ont une longueur normale.",
    "Detaillees": "Tes reponses sont detaillees et structurees.",
}
LANGUES = {
    "Français": "Tu reponds en francais.",
    "English": "You answer in English.",
    "Kirundi / Swahili": "Tu reponds en swahili si Baraka ecrit en swahili, sinon en francais.",
}
ROLES = {
    "Assistant général": "Tu es un assistant general pour tout ce dont Baraka a besoin.",
    "Designer": "Tu es un directeur artistique et designer graphique expert.",
    "Marketing": "Tu es un expert en marketing et reseaux sociaux.",
    "Comptable": "Tu es un assistant comptable rigoureux pour petites entreprises.",
    "Développeur": "Tu es un developpeur expert qui explique simplement a un debutant.",
}
SUGGESTIONS = {
    "🎨 Idée de publication": "Donne-moi 3 idées de publications pour mes réseaux sociaux cette semaine.",
    "📊 Faire un devis": "Aide-moi à préparer un devis pour un client en design graphique.",
    "🧩 Organiser ma journée": "Aide-moi à organiser ma journée de travail.",
}


def lire_secret(nom):
    try:
        return st.secrets[nom]
    except Exception:
        return ""


def github_actif():
    return bool(lire_secret("GITHUB_TOKEN") and lire_secret("GITHUB_REPO"))


def entetes_github():
    return {
        "Authorization": "Bearer " + lire_secret("GITHUB_TOKEN"),
        "Accept": "application/vnd.github+json",
    }


def url_memoire():
    return "https://api.github.com/repos/" + lire_secret("GITHUB_REPO") + "/contents/" + FICHIER_MEMOIRE


def lire_fichier(nom):
    if os.path.exists(nom):
        with open(nom, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""


def lire_memoire():
    if github_actif():
        try:
            r = requests.get(url_memoire(), headers=entetes_github(), timeout=15)
            if r.status_code == 200:
                return base64.b64decode(r.json()["content"]).decode("utf-8").strip()
            return ""
        except Exception:
            return ""
    return lire_fichier(FICHIER_MEMOIRE)


def ecrire_memoire(texte):
    if github_actif():
        try:
            r = requests.get(url_memoire(), headers=entetes_github(), timeout=15)
            sha = r.json()["sha"] if r.status_code == 200 else None
            corps = {
                "message": "Mise a jour de la memoire",
                "content": base64.b64encode(texte.encode("utf-8")).decode("utf-8"),
            }
            if sha:
                corps["sha"] = sha
            r2 = requests.put(url_memoire(), headers=entetes_github(), json=corps, timeout=15)
            return r2.status_code in (200, 201)
        except Exception:
            return False
    with open(FICHIER_MEMOIRE, "w", encoding="utf-8") as f:
        f.write(texte)
    return True


def ajouter_memoire(info):
    ancien = lire_memoire()
    nouveau = (ancien.rstrip("\n") + "\n" if ancien.strip() else "") + info + "\n"
    return ecrire_memoire(nouveau)


def nouvelle_conversation():
    for k in ["chat", "messages", "en_attente", "suggestion"]:
        if k in st.session_state:
            del st.session_state[k]


cle = lire_fichier(FICHIER_CLE)
if not cle and "GEMINI_API_KEY" in st.secrets:
    cle = st.secrets["GEMINI_API_KEY"]
if not cle:
    st.markdown('<p class="titre">Mon IA personnelle</p>', unsafe_allow_html=True)
    st.warning("Colle ta cle API Gemini pour commencer.")
    nouvelle = st.text_input("Cle API Gemini", type="password")
    if st.button("Enregistrer la cle") and nouvelle.strip():
        with open(FICHIER_CLE, "w", encoding="utf-8") as f:
            f.write(nouvelle.strip())
        st.rerun()
    st.stop()

memoire_actuelle = lire_memoire()

with st.sidebar:
    st.markdown("### 🧠 Mon IA")
    if st.button("➕ Nouvelle conversation"):
        nouvelle_conversation()
        st.rerun()
    st.markdown("---")
    st.markdown("**⚙️ Paramètres**")
    with st.expander("Intelligence", expanded=True):
        st.selectbox("Rôle", list(ROLES.keys()), key="role")
        st.selectbox("Ton", list(TONS.keys()), key="ton")
        st.selectbox("Longueur des réponses", list(LONGUEURS.keys()), index=1, key="longueur")
        st.selectbox("Langue", list(LANGUES.keys()), key="langue")
        st.slider("Créativité", 0.0, 1.0, 0.5, 0.1, key="creativite")
        st.caption("Après un changement, clique sur Nouvelle conversation.")
    with st.expander("Apparence"):
        st.selectbox("Taille du texte", list(TAILLES.keys()), index=1, key="taille")
        st.selectbox("Couleur d'accent", list(ACCENTS.keys()), key="accent")
    with st.expander("Mémoire" + (" permanente" if github_actif() else "")):
        nb = len([l for l in memoire_actuelle.split("\n") if l.strip()])
        st.caption(str(nb) + " information(s) retenue(s)")
        st.write(memoire_actuelle if memoire_actuelle else "Rien pour l'instant.")
        if memoire_actuelle:
            if st.button("Effacer toute la mémoire"):
                st.session_state.confirmer_effacement = True
            if st.session_state.get("confirmer_effacement"):
                st.warning("Tu es sûr ? Cette action efface tout.")
                if st.button("Oui, effacer"):
                    ecrire_memoire("")
                    st.session_state.confirmer_effacement = False
                    st.rerun()
    with st.expander("Conversation"):
        texte_export = ""
        for m in st.session_state.get("messages", []):
            qui = "Baraka" if m["role"] == "user" else "IA"
            texte_export += qui + " : " + m["content"] + "\n\n"
        st.download_button("Exporter en fichier texte", texte_export or "Conversation vide.", file_name="conversation.txt")
    st.markdown("---")
    st.caption("Écris « retiens : ... » pour lui apprendre quelque chose. Rien n'est retenu sans ton accord.")

if "chat" not in st.session_state:
    client = genai.Client(api_key=cle)
    consigne = (
        "Tu es l'assistant personnel de Baraka. "
        "Tu l'aides dans toutes ses activites et toutes ses entreprises. "
        + ROLES[st.session_state.get("role", "Assistant général")] + " "
        + LANGUES[st.session_state.get("langue", "Français")] + " "
        + TONS[st.session_state.get("ton", "Amical")] + " "
        + LONGUEURS[st.session_state.get("longueur", "Normales")] + " "
        "Tu ne fais jamais d'action importante sans son autorisation."
    )
    if memoire_actuelle:
        consigne += "\n\nVoici ce que tu sais deja sur Baraka et ses activites :\n" + memoire_actuelle
    st.session_state.chat = client.chats.create(
        model=MODELE,
        config=types.GenerateContentConfig(
            system_instruction=consigne,
            temperature=float(st.session_state.get("creativite", 0.5)) * 1.5,
        ),
    )
    st.session_state.messages = []
    st.session_state.en_attente = None

st.markdown('<p class="titre">Bonjour Baraka</p>', unsafe_allow_html=True)
st.markdown('<p class="sous-titre">Ton assistant personnel pour toutes tes activités.</p>', unsafe_allow_html=True)

if not st.session_state.messages and not st.session_state.en_attente:
    c1, c2, c3 = st.columns(3)
    c1.markdown('<div class="carte"><b>CRÉER</b><br><span>Idées de designs, textes, publications.</span></div>', unsafe_allow_html=True)
    c2.markdown('<div class="carte"><b>CALCULER</b><br><span>Chiffres, budgets, devis, statistiques.</span></div>', unsafe_allow_html=True)
    c3.markdown('<div class="carte"><b>ORGANISER</b><br><span>Projets, clients, tâches du jour.</span></div>', unsafe_allow_html=True)
    st.markdown("")
    s1, s2, s3 = st.columns(3)
    cles_sug = list(SUGGESTIONS.keys())
    if s1.button(cles_sug[0]):
        st.session_state.suggestion = SUGGESTIONS[cles_sug[0]]
        st.rerun()
    if s2.button(cles_sug[1]):
        st.session_state.suggestion = SUGGESTIONS[cles_sug[1]]
        st.rerun()
    if s3.button(cles_sug[2]):
        st.session_state.suggestion = SUGGESTIONS[cles_sug[2]]
        st.rerun()

for m in st.session_state.messages:
    with st.chat_message(m["role"], avatar="🧑‍🎨" if m["role"] == "user" else "🧠"):
        st.write(m["content"])


def envoyer(contenu, affichage):
    st.session_state.messages.append({"role": "user", "content": affichage})
    try:
        reponse = st.session_state.chat.send_message(contenu)
        st.session_state.messages.append({"role": "assistant", "content": reponse.text})
    except Exception:
        st.session_state.messages.append({"role": "assistant", "content": "Le serveur de Google est surchargé. Réessaie dans un instant."})
    st.rerun()


def traiter(message):
    if message.lower().startswith("retiens"):
        st.session_state.messages.append({"role": "user", "content": message})
        info = message.split(":", 1)[-1].strip()
        if info:
            st.session_state.en_attente = info
        st.rerun()
    else:
        envoyer(message, message)


if st.session_state.get("suggestion"):
    texte = st.session_state.suggestion
    st.session_state.suggestion = None
    traiter(texte)

if st.session_state.en_attente:
    info = st.session_state.en_attente
    st.info("Le noyau veut ajouter à sa mémoire : " + info)
    col1, col2 = st.columns(2)
    if col1.button("✅ Approuver"):
        if ajouter_memoire(info):
            texte_rep = "C'est retenu."
        else:
            texte_rep = "Je n'ai pas réussi à enregistrer. Vérifie le jeton GitHub dans les Secrets."
        st.session_state.messages.append({"role": "assistant", "content": texte_rep})
        st.session_state.en_attente = None
        st.rerun()
    if col2.button("❌ Refuser"):
        st.session_state.messages.append({"role": "assistant", "content": "D'accord, je n'ajoute rien."})
        st.session_state.en_attente = None
        st.rerun()
else:
    b1, b2 = st.columns(2)
    with b1:
        with st.expander("📎 Joindre un fichier texte"):
            fichier = st.file_uploader("Fichier", type=["txt", "md", "csv", "py", "json"], label_visibility="collapsed")
            question_fichier = st.text_input("Que veux-tu que je fasse avec ce fichier ?", key="question_fichier")
            if fichier is not None and st.button("Envoyer le fichier"):
                contenu_fichier = fichier.read().decode("utf-8", errors="ignore")[:20000]
                demande = (question_fichier or "Résume ce fichier.") + "\n\nContenu du fichier " + fichier.name + " :\n" + contenu_fichier
                envoyer(demande, "📎 " + fichier.name + " : " + (question_fichier or "Résume ce fichier."))
    with b2:
        with st.expander("🎤 Parler (voix)"):
            audio = st.audio_input("Appuie, parle, puis arrête")
            if audio is not None and st.button("Envoyer ma voix"):
                try:
                    client_voix = genai.Client(api_key=cle)
                    resultat = client_voix.models.generate_content(
                        model=MODELE,
                        contents=[
                            "Transcris fidèlement cet audio, sans rien ajouter.",
                            types.Part.from_bytes(data=audio.getvalue(), mime_type="audio/wav"),
                        ],
                    )
                    texte_voix = (resultat.text or "").strip()
                except Exception:
                    texte_voix = ""
                if texte_voix:
                    traiter(texte_voix)
                else:
                    st.warning("Je n'ai pas réussi à comprendre l'audio. Réessaie.")
    message = st.chat_input("Écris ta demande... (retiens : ... pour la mémoire)")
    if message:
        traiter(message)
