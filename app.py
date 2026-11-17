import os
import streamlit as st
from google import genai

FICHIER_CLE = "cle.txt"
FICHIER_MEMOIRE = "memoire.txt"
MODELE = "gemini-2.5-flash-lite"

st.set_page_config(page_title="Mon IA personnelle", page_icon="🧠")
st.title("🧠 Mon IA personnelle")


def lire_fichier(nom):
    if os.path.exists(nom):
        with open(nom, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""


def ajouter_memoire(info):
    with open(FICHIER_MEMOIRE, "a", encoding="utf-8") as f:
        f.write(info + "\n")


cle = lire_fichier(FICHIER_CLE)
if not cle and "GEMINI_API_KEY" in st.secrets:
    cle = st.secrets["GEMINI_API_KEY"]
if not cle:
    st.warning("Colle ta cle API Gemini pour commencer.")
    nouvelle = st.text_input("Cle API Gemini", type="password")
    if st.button("Enregistrer la cle") and nouvelle.strip():
        with open(FICHIER_CLE, "w", encoding="utf-8") as f:
            f.write(nouvelle.strip())
        st.rerun()
    st.stop()

if "chat" not in st.session_state:
    client = genai.Client(api_key=cle)
    memoire = lire_fichier(FICHIER_MEMOIRE)
    consigne = (
        "Tu es l'assistant personnel de Baraka. "
        "Tu l'aides dans toutes ses activites et toutes ses entreprises. "
        "Tu reponds en francais, simplement. "
        "Tu ne fais jamais d'action importante sans son autorisation."
    )
    if memoire:
        consigne += "\n\nVoici ce que tu sais deja sur Baraka et ses activites :\n" + memoire
    st.session_state.chat = client.chats.create(
        model=MODELE,
        config={"system_instruction": consigne},
    )
    st.session_state.messages = []
    st.session_state.en_attente = None

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])

if st.session_state.en_attente:
    info = st.session_state.en_attente
    st.info("Le noyau veut ajouter a sa memoire : " + info)
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
    message = st.chat_input("Ecris ta demande... (retiens : ... pour la memoire)")
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
                st.session_state.messages.append({"role": "assistant", "content": "Le serveur de Google est surcharge. Reessaie dans un instant."})
        st.rerun()
