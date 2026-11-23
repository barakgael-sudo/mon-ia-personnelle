import os
import re
import base64
import requests
import streamlit as st
from bs4 import BeautifulSoup
from pypdf import PdfReader
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
    background-color: #08080a;
    background-image:
        conic-gradient(from 210deg at 100% 0%, rgba(120,120,135,0.22) 0deg, transparent 60deg),
        conic-gradient(from 30deg at 0% 100%, rgba(120,120,135,0.18) 0deg, transparent 55deg),
        radial-gradient(circle at 92% 18%, rgba(110,110,125,0.20) 0%, transparent 22%),
        radial-gradient(circle at 8% 82%, rgba(110,110,125,0.16) 0%, transparent 24%);
    background-attachment: fixed;
}
.stApp::before {
    content: "";
    position: fixed;
    top: 8%;
    right: 4%;
    width: 200px;
    height: 200px;
    border: 1px solid rgba(160,160,175,0.18);
    transform: rotate(45deg);
    background: linear-gradient(145deg, rgba(90,90,105,0.18), rgba(30,30,38,0.05));
    pointer-events: none;
    z-index: 0;
}
.stApp::after {
    content: "";
    position: fixed;
    bottom: 24%;
    right: 12%;
    width: 120px;
    height: 120px;
    border-radius: 50%;
    border: 1px solid rgba(160,160,175,0.15);
    background: linear-gradient(145deg, rgba(100,100,115,0.16), rgba(20,20,26,0.02));
    pointer-events: none;
    z-index: 0;
}
.stApp, .stApp p, .stApp span, .stApp label, .stApp li, .stApp div,
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stMarkdown {
    color: #e8e8ec !important;
    font-size: __TAILLE__;
}
.stCaption, [data-testid="stCaptionContainer"], .stApp small { color: #a3a3ae !important; }
header[data-testid="stHeader"] { background: transparent; }
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #17171c 0%, #0e0e12 100%);
    border-right: 1px solid #2a2a32;
}
.block-container { padding-bottom: 13rem !important; max-width: 1100px; }
.titre {
    font-size: 2.3rem;
    font-weight: 800;
    letter-spacing: -0.5px;
    color: #f2f2f5 !important;
    margin-bottom: 0;
    border-left: 4px solid __ACCENT__;
    padding-left: 14px;
}
.sous-titre { color: #a3a3ae !important; margin: 4px 0 1.6rem 18px; }
.carte {
    background: linear-gradient(145deg, #2a2a32, #1b1b21);
    border: 1px solid #3a3a44;
    border-top: 2px solid __ACCENT__;
    border-radius: 6px;
    padding: 18px;
    min-height: 110px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.5);
}
.carte b { color: #f2f2f5 !important; font-size: 1.05rem; letter-spacing: 0.3px; }
.carte span { color: #b4b4be !important; }
div[data-testid="stChatMessage"] {
    background: linear-gradient(145deg, #25252c, #18181d);
    border: 1px solid #34343d;
    border-radius: 6px;
    padding: 14px 18px;
    margin-bottom: 10px;
}
[data-testid="stBottom"] {
    background: transparent !important;
    padding-bottom: 64px !important;
}
[data-testid="stBottom"] > div { background: transparent !important; }
[data-testid="stChatInput"] {
    background: #1b1b21 !important;
    border: 1px solid #44444f !important;
    border-radius: 8px !important;
    min-height: 110px !important;
    box-shadow: 0 10px 30px rgba(0,0,0,0.6) !important;
}
[data-testid="stChatInput"] > div,
[data-testid="stChatInputContainer"] {
    background: transparent !important;
    border: none !important;
    border-radius: 8px !important;
    min-height: 100px !important;
}
[data-testid="stChatInput"] textarea,
[data-testid="stChatInputTextArea"] {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    caret-color: __ACCENT__ !important;
    background-color: transparent !important;
    opacity: 1 !important;
    min-height: 90px !important;
    font-size: 1.05rem !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: #8e8e9a !important;
    -webkit-text-fill-color: #8e8e9a !important;
    opacity: 1 !important;
}
[data-testid="stChatInput"] button {
    background: linear-gradient(135deg, #f87171, #991b1b) !important;
    border-radius: 6px !important;
}
[data-testid="stChatInput"] button svg { fill: #ffffff !important; color: #ffffff !important; }
.stTextInput input, .stTextArea textarea {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    background: #1b1b21 !important;
    border-radius: 6px !important;
}
.stButton > button, .stDownloadButton > button {
    border-radius: 6px;
    border: 1px solid #3f3f4a;
    background: #202027;
    color: #f0f0f3 !important;
    width: 100%;
    font-weight: 600;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    border-color: #f87171;
    color: #ffffff !important;
    background: #2a2a33;
}
.stButton > button p, .stDownloadButton > button p { color: #f0f0f3 !important; }
.sugg .stButton > button {
    background: linear-gradient(135deg, #fca5a5 0%, #dc2626 50%, #7f1d1d 100%);
    border: 1px solid rgba(255,255,255,0.2);
    color: #ffffff !important;
}
.sugg .stButton > button p { color: #ffffff !important; }
.sugg .stButton > button:hover { box-shadow: 0 0 18px rgba(248,113,113,0.5); }
.icones .stButton > button, .icones [data-testid="stPopover"] > div > button {
    width: 38px !important;
    min-width: 38px !important;
    height: 34px !important;
    padding: 0 !important;
    font-size: 1rem !important;
    border-radius: 6px !important;
    background: #1b1b21 !important;
    border: 1px solid #3f3f4a !important;
}
div[data-baseweb="select"] > div {
    background: #1b1b21 !important;
    border: 1px solid #3f3f4a !important;
    border-radius: 6px !important;
}
div[data-baseweb="select"] * { color: #f0f0f3 !important; }
[data-testid="stExpander"], [data-testid="stPopover"] {
    background: #17171c;
    border: 1px solid #2f2f38;
    border-radius: 6px;
}
[data-testid="stAlert"] {
    background: #1d1a1c !important;
    border: 1px solid #dc2626;
    border-radius: 6px;
}
[data-testid="stFileUploader"] section {
    background: #17171c;
    border: 1px dashed #3f3f4a;
    border-radius: 6px;
}
hr { border-color: #2a2a32 !important; }
@media (max-width: 900px) {
    .titre { font-size: 1.7rem; }
    .carte { min-height: 80px; padding: 12px; }
    .block-container { padding-left: 0.8rem !important; padding-right: 0.8rem !important; }
    .stApp::before, .stApp::after { display: none; }
    [data-testid="stChatInput"] { min-height: 90px !important; }
}
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
    "Développeur": "Tu es un developpeur expert qui explique simplement a un debutant, et qui ecrit du code complet, commente et pret a copier-coller.",
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


def lire_page_web(adresse):
    try:
        r = requests.get(adresse, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        soupe = BeautifulSoup(r.text, "html.parser")
        for balise in soupe(["script", "style", "nav", "footer"]):
            balise.decompose()
        texte = " ".join(soupe.get_text(separator=" ").split())
        return texte[:15000]
    except Exception:
        return ""


def lire_fichier_envoye(fichier):
    nom = fichier.name.lower()
    try:
        if nom.endswith(".pdf"):
            lecteur = PdfReader(fichier)
            morceaux = []
            for page in lecteur.pages[:40]:
                morceaux.append(page.extract_text() or "")
            return " ".join(morceaux)[:25000]
        return fichier.read().decode("utf-8", errors="ignore")[:25000]
    except Exception:
        return ""


def resumer_pour_memoire(texte, source):
    try:
        client_r = genai.Client(api_key=cle)
        res = client_r.models.generate_content(
            model=MODELE,
            contents="Resume en 8 points courts maximum les informations utiles et durables de ce texte (source : "
            + source + "). Reponds en francais, un point par ligne, sans titre.\n\n" + texte,
        )
        return (res.text or "").strip()
    except Exception:
        return ""


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
        st.toggle("Recherche internet", value=True, key="recherche_web")
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
    st.caption("Colle une adresse web dans ta question pour que je la lise. Écris « retiens : ... » pour lui apprendre quelque chose. Rien n'est retenu sans ton accord.")

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
    outils = []
    if st.session_state.get("recherche_web", True):
        outils = [types.Tool(google_search=types.GoogleSearch())]
    st.session_state.chat = client.chats.create(
        model=MODELE,
        config=types.GenerateContentConfig(
            system_instruction=consigne,
            temperature=float(st.session_state.get("creativite", 0.5)) * 1.5,
            tools=outils,
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
    st.markdown('<div class="sugg">', unsafe_allow_html=True)
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
    st.markdown('</div>', unsafe_allow_html=True)

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
        return
    adresses = re.findall(r"https?://[^\s]+", message)
    contenu = message
    if adresses:
        for adr in adresses[:2]:
            page = lire_page_web(adr)
            if page:
                contenu += "\n\nContenu de la page " + adr + " :\n" + page
    envoyer(contenu, message)


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
    message = st.chat_input("Écris ta demande... Colle une adresse web pour que je la lise.")
    if message:
        traiter(message)

    st.markdown('<div class="icones">', unsafe_allow_html=True)
    i1, i2, i3, _vide = st.columns([1, 1, 1, 9])
    with i1:
        with st.popover("📎"):
            st.caption("Joindre un fichier ou un livre (texte, PDF)")
            fichier = st.file_uploader("Fichier", type=["txt", "md", "csv", "py", "json", "pdf"], label_visibility="collapsed")
            question_fichier = st.text_input("Que veux-tu faire avec ?", key="question_fichier")
            c_a, c_b = st.columns(2)
            if fichier is not None and c_a.button("Envoyer"):
                contenu_fichier = lire_fichier_envoye(fichier)
                if contenu_fichier:
                    demande = (question_fichier or "Résume ce fichier.") + "\n\nContenu de " + fichier.name + " :\n" + contenu_fichier
                    envoyer(demande, "📎 " + fichier.name + " : " + (question_fichier or "Résume ce fichier."))
                else:
                    st.warning("Impossible de lire ce fichier.")
            if fichier is not None and c_b.button("Apprendre"):
                contenu_fichier = lire_fichier_envoye(fichier)
                resume = resumer_pour_memoire(contenu_fichier, fichier.name) if contenu_fichier else ""
                if resume:
                    st.session_state.en_attente = resume
                    st.rerun()
                else:
                    st.warning("Impossible de résumer ce fichier.")
    with i2:
        with st.popover("🎤"):
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
    with i3:
        if st.button("🧠", help="Retenir la dernière réponse en mémoire"):
            dernieres = [m for m in st.session_state.messages if m["role"] == "assistant"]
            if dernieres:
                st.session_state.en_attente = dernieres[-1]["content"][:1500]
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
