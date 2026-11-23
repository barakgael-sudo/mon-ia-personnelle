import os
import base64
import requests
import streamlit as st
from google import genai

FICHIER_CLE = "cle.txt"
FICHIER_MEMOIRE = "memoire.txt"
MODELE = "gemini-2.5-flash-lite"

st.set_page_config(page_title="Mon IA personnelle", page_icon="🧠", layout="wide")

CSS = """

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


def lire_memoire():
    if github_actif():
        try:
            r = requests.get(url_memoire(), headers=entetes_github(), timeout=15)
            if r.status_code == 200:
                return base64.b64decode(r.json()["content"]).decode("utf-8").strip()
            return ""
        except Exception:
            return ""
    if os.path.exists(FICHIER_MEMOIRE):
        with open(FICHIER_MEMOIRE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""


def ajouter_memoire(info):
    if github_actif():
        try:
            r = requests.get(url_memoire(), headers=entetes_github(), timeout=15)
            sha = None
            ancien = ""
            if r.status_code == 200:
                sha = r.json()["sha"]
                ancien = base64.b64decode(r.json()["content"]).decode("utf-8")
            nouveau = (ancien.rstrip("\n") + "\n" if ancien.strip() else "") + info + "\n"
            corps = {
                "message": "Ajout a la memoire",
                "content": base64.b64encode(nouveau.encode("utf-8")).decode("utf-8"),
            }
            if sha:
                corps["sha"] = sha
            r2 = requests.put(url_memoire(), headers=entetes_github(), json=corps, timeout=15)
            return r2.status_code in (200, 201)
        except Exception:
            return False
    with open(FICHIER_MEMOIRE, "a", encoding="utf-8") as f:
        f.write(info + "\n")
    return True


def lire_fichier(nom):
    if os.path.exists(nom):
        with open(nom, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""


def nouvelle_conversation():
    for k in ["chat", "messages", "en_attente", "suggestion"]:
        if k in st.session_state:
            del st.session_state[k]


cle = lire_fichier(FICHIER_CLE)
if not cle and "GEMINI_API_KEY" in st.secrets:
    cle = st.secrets["GEMINI_API_KEY"]
if not cle:
    st.markdown(' Mon IA personnelle', unsafe_allow_html=True)
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
    st.markdown("**⚙️ Réglages**")
    ton = st.selectbox("Ton de l'IA", list(TONS.keys()), key="ton")
    longueur = st.selectbox("Longueur des réponses", list(LONGUEURS.keys()), index=1, key="longueur")
    langue = st.selectbox("Langue des réponses", list(LANGUES.keys()), key="langue")
    st.caption("Après un changement de réglage, clique sur Nouvelle conversation.")
    st.markdown("---")
    st.markdown("**💾 Mémoire" + (" permanente" if github_actif() else "") + "**")
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

st.markdown(' Bonjour Baraka', unsafe_allow_html=True)
st.markdown(' Ton assistant personnel pour toutes tes activités.', unsafe_allow_html=True)

if not st.session_state.messages and not st.session_state.en_attente:
    c1, c2, c3 = st.columns(3)
    c1.markdown(' 🎨 Créer Idées de designs, textes, publications.', unsafe_allow_html=True)
    c2.markdown(' 📊 Calculer Chiffres, budgets, devis, statistiques.', unsafe_allow_html=True)
    c3.markdown(' 🧩 Organiser Projets, clients, tâches du jour.', unsafe_allow_html=True)
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
    message = st.chat_input("Écris ta demande... (retiens : ... pour la mémoire)")
    if message:
        traiter(message)
