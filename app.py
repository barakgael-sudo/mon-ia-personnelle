import os
import streamlit as st
from google import genai

FICHIER_CLE = "cle.txt"
FICHIER_MEMOIRE = "memoire.txt"
MODELE = "gemini-2.5-flash-lite"

st.set_page_config(page_title="Mon IA personnelle", page_icon="🧠", layout="wide")

CSS = """
<style>
:root { color-scheme: dark; }
.stApp {
    background:
        radial-gradient(circle at 15% 0%, rgba(124,58,237,0.35) 0%, transparent 45%),
        radial-gradient(circle at 90% 10%, rgba(37,99,235,0.28) 0%, transparent 40%),
        radial-gradient(circle at 50% 100%, rgba(236,72,153,0.15) 0%, transparent 45%),
        #0a0a12;
}
.stApp, .stApp p, .stApp span, .stApp label, .stApp li, .stApp div,
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stMarkdown, .stCaption {
    color: #f1f1f8 !important;
}
.stApp small, .stCaption, [data-testid="stCaptionContainer"] { color: #a9a9c8 !important; }
header[data-testid="stHeader"] { background: transparent; }
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #12122a 0%, #0c0c1a 100%);
    border-right: 1px solid rgba(167,139,250,0.25);
}
.titre {
    font-size: 2.4rem;
    font-weight: 800;
    letter-spacing: -0.5px;
    background: linear-gradient(90deg, #c4b5fd, #7dd3fc, #f9a8d4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent !important;
    margin-bottom: 0;
}
.sous-titre { color: #a9a9c8 !important; margin-top: 0; margin-bottom: 1.6rem; font-size: 1.05rem; }
.carte {
    background: linear-gradient(145deg, rgba(255,255,255,0.07), rgba(255,255,255,0.02));
    border: 1px solid rgba(167,139,250,0.35);
    border-radius: 18px;
    padding: 18px;
    min-height: 105px;
    box-shadow: 0 8px 30px rgba(124,58,237,0.15);
    backdrop-filter: blur(8px);
}
.carte b { color: #c4b5fd !important; font-size: 1.05rem; }
div[data-testid="stChatMessage"] {
    background: linear-gradient(145deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
    border: 1px solid rgba(125,211,252,0.25);
    border-radius: 18px;
    padding: 14px 18px;
    margin-bottom: 12px;
    box-shadow: 0 6px 24px rgba(0,0,0,0.35);
}
div[data-testid="stChatInput"] {
    background: rgba(20,20,45,0.9) !important;
    border: 1px solid rgba(167,139,250,0.6) !important;
    border-radius: 22px !important;
    box-shadow: 0 0 25px rgba(124,58,237,0.35);
}
div[data-testid="stChatInput"] textarea {
    color: #f1f1f8 !important;
    background: transparent !important;
}
div[data-testid="stChatInput"] textarea::placeholder { color: #8b8bb0 !important; }
[data-testid="stBottom"] > div { background: transparent !important; }
.stButton > button {
    border-radius: 14px;
    border: 1px solid rgba(167,139,250,0.5);
    background: linear-gradient(135deg, rgba(124,58,237,0.55), rgba(37,99,235,0.45));
    color: #ffffff !important;
    width: 100%;
    font-weight: 600;
    transition: all 0.2s ease;
}
.stButton > button:hover {
    border-color: #f9a8d4;
    box-shadow: 0 0 18px rgba(249,168,212,0.45);
    transform: translateY(-1px);
}
.stButton > button p { color: #ffffff !important; }
div[data-baseweb="select"] > div {
    background: rgba(25,25,55,0.95) !important;
    border: 1px solid rgba(167,139,250,0.4) !important;
    border-radius: 12px !important;
}
div[data-baseweb="select"] * { color: #f1f1f8 !important; }
[data-testid="stExpander"] {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(167,139,250,0.3);
    border-radius: 14px;
}
[data-testid="stAlert"] {
    background: rgba(37,99,235,0.18) !important;
    border: 1px solid rgba(125,211,252,0.4);
    border-radius: 14px;
}
hr { border-color: rgba(167,139,250,0.25) !important; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

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
SUGGESTIONS = {
    "🎨 Idée de publication": "Donne-moi 3 idées de publications pour mes réseaux sociaux cette semaine.",
    "📊 Faire un devis": "Aide-moi à préparer un devis pour un client en design graphique.",
    "🧩 Organiser ma journée": "Aide-moi à organiser ma journée de travail.",
}


def lire_fichier(nom):
    if os.path.exists(nom):
        with open(nom, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""


def ajouter_memoire(info):
    with open(FICHIER_MEMOIRE, "a", encoding="utf-8") as f:
        f.write(info + "\n")


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

with st.sidebar:
    st.markdown("### 🧠 Mon IA")
    if st.button("➕ Nouvelle conversation"):
        nouvelle_conversation()
        st.rerun()
    st.markdown("---")
    st.markdown("**⚙️ Réglages**")
    ton = st.selectbox("Ton de l'IA", list(TONS.keys()), key="ton")
    longueur = st.selectbox("Longueur des réponses", list(LONGUEURS.keys()), index=1, key="longueur")
    langue = st.selectbox("Langue des réponses", list(LANGUES.keys()), key="langue")
    st.caption("Après un changement de réglage, clique sur Nouvelle conversation.")
    st.markdown("---")
    st.markdown("**💾 Mémoire**")
    memoire_actuelle = lire_fichier(FICHIER_MEMOIRE)
    nb = len([l for l in memoire_actuelle.split("\n") if l.strip()])
    st.caption(str(nb) + " information(s) retenue(s)")
    with st.expander("Voir la mémoire"):
        st.write(memoire_actuelle if memoire_actuelle else "Rien pour l'instant.")
    st.markdown("---")
    st.caption("Écris « retiens : ... » pour lui apprendre quelque chose. Rien n'est retenu sans ton accord.")

if "chat" not in st.session_state:
    client = genai.Client(api_key=cle)
    consigne = (
        "Tu es l'assistant personnel de Baraka. "
        "Tu l'aides dans toutes ses activites et toutes ses entreprises. "
        + LANGUES[st.session_state.get("langue", "Français")] + " "
        + TONS[st.session_state.get("ton", "Amical")] + " "
        + LONGUEURS[st.session_state.get("longueur", "Normales")] + " "
        "Tu ne fais jamais d'action importante sans son autorisation."
    )
    if memoire_actuelle:
        consigne += "\n\nVoici ce que tu sais deja sur Baraka et ses activites :\n" + memoire_actuelle
    st.session_state.chat = client.chats.create(
        model=MODELE,
        config={"system_instruction": consigne},
    )
    st.session_state.messages = []
    st.session_state.en_attente = None

st.markdown('<p class="titre">Bonjour Baraka</p>', unsafe_allow_html=True)
st.markdown('<p class="sous-titre">Ton assistant personnel pour toutes tes activités.</p>', unsafe_allow_html=True)

if not st.session_state.messages and not st.session_state.en_attente:
    c1, c2, c3 = st.columns(3)
    c1.markdown('<div class="carte"><b>🎨 Créer</b><br>Idées de designs, textes, publications.</div>', unsafe_allow_html=True)
    c2.markdown('<div class="carte"><b>📊 Calculer</b><br>Chiffres, budgets, devis, statistiques.</div>', unsafe_allow_html=True)
    c3.markdown('<div class="carte"><b>🧩 Organiser</b><br>Projets, clients, tâches du jour.</div>', unsafe_allow_html=True)
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
    with st.chat_message(m["role"], avatar="🧑\u200d🎨" if m["role"] == "user" else "🧠"):
        st.write(m["content"])


def traiter(message):
    st.session_state.messages.append({"role": "user", "content": message})
    if message.lower().startswith("retiens"):
        info = message.split(":", 1)[-1].strip()
        if info:
            st.session_state.en_attente = info
    else:
        try:
            reponse = st.session_state.chat.send_message(message)
            st.session_state.messages.append({"role": "assistant", "content": reponse.text})
        except Exception:
            st.session_state.messages.append({"role": "assistant", "content": "Le serveur de Google est surchargé. Réessaie dans un instant."})
    st.rerun()


if st.session_state.get("suggestion"):
    texte = st.session_state.suggestion
    st.session_state.suggestion = None
    traiter(texte)

if st.session_state.en_attente:
    info = st.session_state.en_attente
    st.info("Le noyau veut ajouter à sa mémoire : " + info)
    col1, col2 = st.columns(2)
    if col1.button("✅ Approuver"):
        ajouter_memoire(info)
        st.session_state.messages.append({"role": "assistant", "content": "C'est retenu."})
        st.session_state.en_attente = None
        st.rerun()
    if col2.button("❌ Refuser"):
        st.session_state.messages.append({"role": "assistant", "content": "D'accord, je n'ajoute rien."})
        st.session_state.en_attente = None
        st.rerun()
else:
    message = st.chat_input("Écris ta demande... (retiens : ... pour la mémoire)")
    if message:
        traiter(message)
