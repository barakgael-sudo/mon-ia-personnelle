import os
import streamlit as st
from google import genai

FICHIER_CLE = "cle.txt"
FICHIER_MEMOIRE = "memoire.txt"
MODELE = "gemini-2.5-flash-lite"

st.set_page_config(page_title="Mon IA personnelle", page_icon="🧠", layout="wide")

CSS = """
<style>
.stApp {
    background: radial-gradient(circle at 20% 0%, #1b1740 0%, #0b0b14 55%);
    color: #ececf1;
}
header[data-testid="stHeader"] { background: transparent; }
section[data-testid="stSidebar"] {
    background: #0f0f1a;
    border-right: 1px solid #23233a;
}
.titre {
    font-size: 2.1rem;
    font-weight: 700;
    background: linear-gradient(90deg, #a78bfa, #60a5fa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0;
}
.sous-titre { color: #8b8ba7; margin-top: 0; margin-bottom: 1.5rem; }
.carte {
    background: #15152a;
    border: 1px solid #2a2a4a;
    border-radius: 14px;
    padding: 16px;
    color: #cfcfe6;
    min-height: 90px;
}
.carte b { color: #a78bfa; }
div[data-testid="stChatMessage"] {
    background: #14142a;
    border: 1px solid #25254a;
    border-radius: 16px;
    padding: 12px 16px;
    margin-bottom: 10px;
}
.stButton > button {
    border-radius: 12px;
    border: 1px solid #3b3b6b;
    background: #1c1c3a;
    color: #ececf1;
    width: 100%;
}
.stButton > button:hover { border-color: #a78bfa; color: #a78bfa; }
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


def lire_fichier(nom):
    if os.path.exists(nom):
        with open(nom, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""


def ajouter_memoire(info):
    with open(FICHIER_MEMOIRE, "a", encoding="utf-8") as f:
        f.write(info + "\n")


def nouvelle_conversation():
    for k in ["chat", "messages", "en_attente"]:
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
    st.markdown("**Réglages**")
    ton = st.selectbox("Ton de l'IA", list(TONS.keys()), key="ton")
    longueur = st.selectbox("Longueur des réponses", list(LONGUEURS.keys()), index=1, key="longueur")
    st.caption("Après un changement de réglage, clique sur Nouvelle conversation.")
    st.markdown("---")
    st.markdown("**Mémoire**")
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
        "Tu reponds en francais. "
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

for m in st.session_state.messages:
    with st.chat_message(m["role"], avatar="🧑‍🎨" if m["role"] == "user" else "🧠"):
        st.write(m["content"])

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
