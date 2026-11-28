import os
import re
import json
import time
import base64
import requests
import streamlit as st
from bs4 import BeautifulSoup
from pypdf import PdfReader
from google import genai
from google.genai import types

FICHIER_CLE = "cle.txt"
FICHIER_MEMOIRE = "memoire.txt"
FICHIER_CONVERSATIONS = "conversations.json"
DOSSIER_MODULES = "modules"
MODELES_GEMINI = ["gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]
MODELES_GROQ = ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]

st.set_page_config(page_title="Mon IA personnelle", page_icon="🧠", layout="wide")

TAILLES = {"Petite": "0.92rem", "Normale": "1rem", "Grande": "1.12rem"}
ACCENTS = {"Rouge carmin": "#e11d48", "Rouge sombre": "#be123c", "Gris acier": "#9a9aa6", "Blanc cassé": "#dcdce1"}

taille = TAILLES.get(st.session_state.get("taille", "Normale"), "1rem")
accent = ACCENTS.get(st.session_state.get("accent", "Rouge carmin"), "#e11d48")

CSS = """
<style>
:root { color-scheme: dark; }
.stApp {
    background-color: #0c0c0f;
    background-image:
        conic-gradient(from 210deg at 100% 0%, rgba(120,120,135,0.16) 0deg, transparent 60deg),
        conic-gradient(from 30deg at 0% 100%, rgba(120,120,135,0.12) 0deg, transparent 55deg);
    background-attachment: fixed;
}
.stApp, .stApp p, .stApp span, .stApp label, .stApp li, .stApp div,
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stMarkdown {
    color: #e6e6ea !important;
    font-size: __TAILLE__;
}
.stCaption, [data-testid="stCaptionContainer"], .stApp small { color: #9a9aa6 !important; }
header[data-testid="stHeader"] { background: transparent; }
section[data-testid="stSidebar"] { background: #131317; border-right: 1px solid #26262d; }
.block-container { padding-bottom: 11rem !important; max-width: 900px; }
.titre {
    font-size: 2rem; font-weight: 700; letter-spacing: -0.4px;
    color: #f2f2f5 !important; margin-bottom: 0;
    border-left: 4px solid __ACCENT__; padding-left: 14px;
}
.sous-titre { color: #9a9aa6 !important; margin: 4px 0 1.2rem 18px; }
.carte {
    background: #1a1a1f; border: 1px solid #2c2c34; border-top: 2px solid __ACCENT__;
    border-radius: 8px; padding: 18px; min-height: 105px;
}
.carte b { color: #f2f2f5 !important; font-size: 1.02rem; letter-spacing: 0.3px; }
.carte span { color: #a8a8b3 !important; }
.ligne { display: flex; margin: 10px 0; width: 100%; }
.ligne.moi { justify-content: flex-end; }
.ligne.ia { justify-content: flex-start; }
.bulle {
    max-width: 62%; min-width: 60px; padding: 10px 14px; border-radius: 14px;
    line-height: 1.55; white-space: pre-wrap; word-wrap: break-word; font-size: 0.97rem;
}
.bulle.moi { background: #34343c; border: 1px solid #44444e; border-bottom-right-radius: 4px; }
.bulle.ia { background: #1d1d23; border: 1px solid #2c2c34; border-bottom-left-radius: 4px; }
.points { display: inline-flex; gap: 5px; padding: 4px 2px; }
.points span {
    width: 8px; height: 8px; border-radius: 50%; background: #9a9aa6;
    animation: saut 1.2s infinite ease-in-out;
}
.points span:nth-child(2) { animation-delay: 0.2s; }
.points span:nth-child(3) { animation-delay: 0.4s; }
@keyframes saut { 0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; } 40% { transform: scale(1); opacity: 1; } }
.souvenir {
    background: #1d1d23; border: 1px solid #2c2c34; border-left: 3px solid __ACCENT__;
    border-radius: 4px; padding: 7px 9px; margin: 5px 0; font-size: 0.82rem; line-height: 1.4;
}
[data-testid="stBottom"] { background: transparent !important; padding-bottom: 12px !important; }
[data-testid="stBottom"] > div { background: transparent !important; }
[data-testid="stChatInput"] {
    background: #1a1a1f !important; border: 1px solid #3a3a43 !important;
    border-radius: 12px !important; min-height: 72px !important;
}
[data-testid="stChatInput"] > div, [data-testid="stChatInputContainer"] {
    background: transparent !important; border: none !important; min-height: 62px !important;
}
[data-testid="stChatInput"] textarea, [data-testid="stChatInputTextArea"] {
    color: #ffffff !important; -webkit-text-fill-color: #ffffff !important;
    caret-color: __ACCENT__ !important; background-color: transparent !important;
    opacity: 1 !important; min-height: 52px !important; font-size: 1.02rem !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: #8a8a96 !important; -webkit-text-fill-color: #8a8a96 !important; opacity: 1 !important;
}
[data-testid="stChatInput"] button { background: #44444e !important; border-radius: 8px !important; }
[data-testid="stChatInput"] button svg { fill: #ffffff !important; color: #ffffff !important; }
.stTextInput input, .stTextArea textarea {
    color: #ffffff !important; -webkit-text-fill-color: #ffffff !important;
    background: #1a1a1f !important; border-radius: 6px !important;
}
.stButton > button, .stDownloadButton > button {
    border-radius: 6px; border: 1px solid #36363f; background: #1d1d23;
    color: #eeeef1 !important; width: 100%; font-weight: 600;
}
.stButton > button:hover, .stDownloadButton > button:hover { border-color: #6a6a76; color: #ffffff !important; background: #26262d; }
.stButton > button p, .stDownloadButton > button p { color: #eeeef1 !important; }
.sugg .stButton > button {
    background: linear-gradient(135deg, #fca5a5 0%, #dc2626 50%, #7f1d1d 100%);
    border: 1px solid rgba(255,255,255,0.2);
}
.sugg .stButton > button p { color: #ffffff !important; }
div[data-baseweb="select"] > div { background: #1a1a1f !important; border: 1px solid #36363f !important; border-radius: 6px !important; }
div[data-baseweb="select"] * { color: #eeeef1 !important; }
[data-testid="stExpander"], [data-testid="stPopover"] { background: #16161b; border: 1px solid #2a2a31; border-radius: 6px; }
[data-testid="stAlert"] { background: #1d1a1c !important; border: 1px solid #6a6a76; border-radius: 6px; }
[data-testid="stFileUploader"] section { background: #16161b; border: 1px dashed #3a3a43; border-radius: 6px; }
button[role="tab"] p { font-size: 0.85rem !important; }
hr { border-color: #26262d !important; }
@media (max-width: 900px) {
    .titre { font-size: 1.5rem; }
    .carte { min-height: 80px; padding: 12px; }
    .bulle { max-width: 86%; }
    .block-container { padding-left: 0.8rem !important; padding-right: 0.8rem !important; }
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
    return {"Authorization": "Bearer " + lire_secret("GITHUB_TOKEN"), "Accept": "application/vnd.github+json"}


def url_fichier(chemin):
    return "https://api.github.com/repos/" + lire_secret("GITHUB_REPO") + "/contents/" + chemin


def github_lire(chemin):
    try:
        r = requests.get(url_fichier(chemin), headers=entetes_github(), timeout=15)
        if r.status_code == 200:
            return base64.b64decode(r.json()["content"]).decode("utf-8")
    except Exception:
        pass
    return ""


def github_ecrire(chemin, texte, message):
    try:
        r = requests.get(url_fichier(chemin), headers=entetes_github(), timeout=15)
        sha = r.json()["sha"] if r.status_code == 200 else None
        corps = {"message": message, "content": base64.b64encode(texte.encode("utf-8")).decode("utf-8")}
        if sha:
            corps["sha"] = sha
        r2 = requests.put(url_fichier(chemin), headers=entetes_github(), json=corps, timeout=20)
        return r2.status_code in (200, 201)
    except Exception:
        return False


def github_lister(dossier):
    try:
        r = requests.get(url_fichier(dossier), headers=entetes_github(), timeout=15)
        if r.status_code == 200:
            return [f["name"] for f in r.json() if f.get("type") == "file"]
    except Exception:
        pass
    return []


def lire_fichier(nom):
    if os.path.exists(nom):
        with open(nom, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""


def lire_memoire():
    if github_actif():
        return github_lire(FICHIER_MEMOIRE).strip()
    return lire_fichier(FICHIER_MEMOIRE)


def ecrire_memoire(texte):
    if github_actif():
        return github_ecrire(FICHIER_MEMOIRE, texte, "Mise a jour de la memoire")
    with open(FICHIER_MEMOIRE, "w", encoding="utf-8") as f:
        f.write(texte)
    return True


def ajouter_memoire(info):
    ancien = lire_memoire()
    nouveau = (ancien.rstrip("\n") + "\n" if ancien.strip() else "") + info.strip() + "\n"
    return ecrire_memoire(nouveau)


def charger_conversations():
    if github_actif():
        brut = github_lire(FICHIER_CONVERSATIONS)
    else:
        brut = lire_fichier(FICHIER_CONVERSATIONS)
    try:
        donnees = json.loads(brut) if brut.strip() else {}
    except Exception:
        donnees = {}
    return donnees


def sauver_conversations():
    donnees = {
        "courante": st.session_state.get("messages", []),
        "archives": st.session_state.get("archives", []),
    }
    texte = json.dumps(donnees, ensure_ascii=False)
    if github_actif():
        github_ecrire(FICHIER_CONVERSATIONS, texte, "Sauvegarde des conversations")
    else:
        with open(FICHIER_CONVERSATIONS, "w", encoding="utf-8") as f:
            f.write(texte)


def lire_page_web(adresse):
    try:
        r = requests.get(adresse, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        soupe = BeautifulSoup(r.text, "html.parser")
        for balise in soupe(["script", "style", "nav", "footer"]):
            balise.decompose()
        return " ".join(soupe.get_text(separator=" ").split())[:15000]
    except Exception:
        return ""


def lire_fichier_envoye(fichier):
    nom = fichier.name.lower()
    try:
        if nom.endswith(".pdf"):
            lecteur = PdfReader(fichier)
            return " ".join((p.extract_text() or "") for p in lecteur.pages[:40])[:25000]
        return fichier.read().decode("utf-8", errors="ignore")[:25000]
    except Exception:
        return ""


def construire_consigne(memoire):
    consigne = (
        "Tu es l'assistant personnel de Baraka. "
        "Tu l'aides dans toutes ses activites et toutes ses entreprises. "
        + ROLES[st.session_state.get("role", "Assistant général")] + " "
        + LANGUES[st.session_state.get("langue", "Français")] + " "
        + TONS[st.session_state.get("ton", "Amical")] + " "
        + LONGUEURS[st.session_state.get("longueur", "Normales")] + " "
        "Tu ne fais jamais d'action importante sans son autorisation."
    )
    if memoire:
        consigne += "\n\nVoici ce que tu sais deja sur Baraka et ses activites :\n" + memoire
    return consigne


def appeler_gemini(historique, consigne, erreurs):
    client = genai.Client(api_key=cle)
    contenus = []
    for m in historique:
        role = "user" if m["role"] == "user" else "model"
        contenus.append(types.Content(role=role, parts=[types.Part.from_text(text=m["content"])]))
    avec_recherche = st.session_state.get("recherche_web", True)
    for modele in MODELES_GEMINI:
        for essai in range(2):
            for recherche in ([True, False] if avec_recherche else [False]):
                try:
                    outils = [types.Tool(google_search=types.GoogleSearch())] if recherche else None
                    res = client.models.generate_content(
                        model=modele,
                        contents=contenus,
                        config=types.GenerateContentConfig(
                            system_instruction=consigne,
                            temperature=float(st.session_state.get("creativite", 0.5)) * 1.5,
                            tools=outils,
                        ),
                    )
                    if res.text:
                        return res.text
                except Exception as e:
                    erreurs.append("Gemini " + modele + " : " + str(e)[:140])
            time.sleep(1.2 * (essai + 1))
    return ""


def appeler_groq(historique, consigne, erreurs):
    cle_groq = lire_secret("GROQ_API_KEY")
    if not cle_groq:
        erreurs.append("Groq : la clé GROQ_API_KEY est absente des Secrets.")
        return ""
    messages = [{"role": "system", "content": consigne}]
    for m in historique:
        messages.append({"role": "user" if m["role"] == "user" else "assistant", "content": m["content"]})
    for modele in MODELES_GROQ:
        try:
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": "Bearer " + cle_groq, "Content-Type": "application/json"},
                json={"model": modele, "messages": messages, "temperature": float(st.session_state.get("creativite", 0.5)) * 1.2},
                timeout=60,
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
            erreurs.append("Groq " + modele + " code " + str(r.status_code) + " : " + r.text[:140])
        except Exception as e:
            erreurs.append("Groq " + modele + " : " + str(e)[:140])
    return ""


def repondre(historique, memoire):
    consigne = construire_consigne(memoire)
    erreurs = []
    texte = appeler_gemini(historique, consigne, erreurs)
    if not texte:
        texte = appeler_groq(historique, consigne, erreurs)
    if not texte:
        detail = "\n".join(erreurs[-4:]) if erreurs else "Aucun détail."
        texte = "Je n'ai pas réussi à joindre l'IA. Voici ce que disent les connexions :\n" + detail
    return texte


def resumer_pour_memoire(texte, source, memoire):
    demande = [{"role": "user", "content": "Resume en 8 points courts maximum les informations utiles et durables de ce texte (source : "
               + source + "). Reponds en francais, un point par ligne, sans titre.\n\n" + texte}]
    return repondre(demande, memoire).strip()


def apprendre_auto(question, reponse, memoire):
    consigne = (
        "Tu notes pour toi-meme, en silence, ce qui merite d'etre retenu sur Baraka (ses entreprises, ses projets, "
        "ses preferences, ses decisions, ses faits durables) a partir de cet echange. "
        "Ecris au maximum 2 lignes courtes, une information par ligne, sans puce ni numero. "
        "Ne note jamais de mot de passe, de cle, de numero de compte ou d'information de sante. "
        "S'il n'y a rien de durable a retenir, reponds exactement : RIEN."
    )
    echange = "Baraka : " + question[:1200] + "\n\nIA : " + reponse[:1200]
    try:
        client_a = genai.Client(api_key=cle)
        for modele in MODELES_GEMINI[:2]:
            try:
                res = client_a.models.generate_content(
                    model=modele,
                    contents=echange,
                    config=types.GenerateContentConfig(system_instruction=consigne, temperature=0.2),
                )
                note = (res.text or "").strip()
                if note and not note.upper().startswith("RIEN"):
                    existantes = memoire.lower()
                    lignes = [l.strip(" -•\t") for l in note.split("\n") if l.strip()]
                    nouvelles = [l for l in lignes if l.lower() not in existantes][:2]
                    if nouvelles:
                        ajouter_memoire("\n".join(nouvelles))
                return
            except Exception:
                continue
    except Exception:
        pass


def proposer_module(besoin, memoire):
    demande = [{"role": "user", "content":
        "Ecris un module Python simple et complet pour ce besoin : " + besoin +
        ". Le module doit definir une fonction principale nommee executer(entree) qui recoit un texte et renvoie un texte. "
        "Utilise uniquement la bibliotheque standard et requests. Ajoute des commentaires en francais. "
        "Reponds avec le code seul, sans explication, sans balises de code."}]
    code = repondre(demande, memoire).strip()
    code = re.sub(r"^```(?:python)?", "", code).strip()
    code = re.sub(r"```$", "", code).strip()
    return code


def nom_module_valide(texte):
    base = re.sub(r"[^a-z0-9_]+", "_", texte.lower()).strip("_")[:30]
    return (base or "module") + ".py"


def titre_conversation(messages):
    for m in messages:
        if m["role"] == "user":
            return m["content"][:30]
    return "Conversation"


def archiver_conversation():
    msgs = st.session_state.get("messages", [])
    if msgs:
        archives = st.session_state.get("archives", [])
        archives.insert(0, {"titre": titre_conversation(msgs), "messages": msgs})
        st.session_state.archives = archives[:30]


def nouvelle_conversation():
    archiver_conversation()
    for k in ["en_attente", "suggestion", "a_repondre", "module_propose"]:
        if k in st.session_state:
            del st.session_state[k]
    st.session_state.messages = []
    sauver_conversations()


def ouvrir_archive(index):
    archiver_conversation()
    archives = st.session_state.get("archives", [])
    if index < len(archives):
        choisie = archives.pop(index)
        st.session_state.messages = choisie["messages"]
        st.session_state.en_attente = None
        sauver_conversations()


def envoyer(contenu, affichage):
    st.session_state.messages.append({"role": "user", "content": affichage, "envoi": contenu})
    st.session_state.a_repondre = True
    st.rerun()


def traiter(message, memoire):
    if message.lower().startswith("retiens"):
        st.session_state.messages.append({"role": "user", "content": message})
        info = message.split(":", 1)[-1].strip()
        if info:
            if ajouter_memoire(info):
                st.session_state.messages.append({"role": "assistant", "content": "C'est retenu."})
            else:
                st.session_state.messages.append({"role": "assistant", "content": "Je n'ai pas réussi à enregistrer. Vérifie le jeton GitHub dans les Secrets."})
        sauver_conversations()
        st.rerun()
        return
    if message.lower().startswith("module"):
        besoin = message.split(":", 1)[-1].strip() if ":" in message else message[6:].strip()
        st.session_state.messages.append({"role": "user", "content": message})
        if besoin:
            code = proposer_module(besoin, memoire)
            st.session_state.module_propose = {"nom": nom_module_valide(besoin), "code": code, "besoin": besoin}
            st.session_state.messages.append({"role": "assistant", "content": "J'ai écrit un module pour : " + besoin + ". Regarde le code dans l'onglet Ajouter à gauche, puis approuve ou refuse. Rien n'est ajouté sans ton accord."})
        sauver_conversations()
        st.rerun()
        return
    adresses = re.findall(r"https?://[^\s]+", message)
    contenu = message
    for adr in adresses[:2]:
        page = lire_page_web(adr)
        if page:
            contenu += "\n\nContenu de la page " + adr + " :\n" + page
    envoyer(contenu, message)


def afficher_bulle(role, texte):
    classe = "moi" if role == "user" else "ia"
    propre = texte.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    st.markdown('<div class="ligne ' + classe + '"><div class="bulle ' + classe + '">' + propre + '</div></div>', unsafe_allow_html=True)


def application():
    global cle
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

    if "charge" not in st.session_state:
        donnees = charger_conversations()
        st.session_state.messages = donnees.get("courante", [])
        st.session_state.archives = donnees.get("archives", [])
        st.session_state.en_attente = None
        st.session_state.charge = True

    with st.sidebar:
        st.markdown("### 🧠 Mon IA")
        if st.button("➕ Nouvelle conversation"):
            nouvelle_conversation()
            st.rerun()

        onglet_conv, onglet_mem, onglet_ajout = st.tabs(["Conversations", "Mémoire", "Ajouter"])

        with onglet_conv:
            archives = st.session_state.get("archives", [])
            if archives:
                for i, a in enumerate(archives):
                    if st.button("💬 " + a["titre"], key="arch_" + str(i)):
                        ouvrir_archive(i)
                        st.rerun()
            else:
                st.caption("Aucune conversation passée pour l'instant.")

        with onglet_mem:
            lignes_mem = [l for l in memoire_actuelle.split("\n") if l.strip()]
            if lignes_mem:
                for l in lignes_mem[-12:][::-1]:
                    propre = l.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    st.markdown('<div class="souvenir">' + propre[:200] + '</div>', unsafe_allow_html=True)
                st.caption(str(len(lignes_mem)) + " information(s) au total")
            else:
                st.caption("Rien pour l'instant. Elle apprend toute seule de vos discussions.")
            if st.button("🧠 Retenir la dernière réponse"):
                dernieres = [m for m in st.session_state.messages if m["role"] == "assistant"]
                if dernieres:
                    ajouter_memoire(dernieres[-1]["content"][:600])
                    st.rerun()

        with onglet_ajout:
            st.markdown("**📎 Pièce jointe**")
            fichier = st.file_uploader("Fichier (texte, PDF, livre)", type=["txt", "md", "csv", "py", "json", "pdf"])
            question_fichier = st.text_input("Que veux-tu faire avec ?", key="question_fichier")
            c_a, c_b = st.columns(2)
            if fichier is not None and c_a.button("Envoyer", key="env_fichier"):
                contenu_fichier = lire_fichier_envoye(fichier)
                if contenu_fichier:
                    demande = (question_fichier or "Résume ce fichier.") + "\n\nContenu de " + fichier.name + " :\n" + contenu_fichier
                    envoyer(demande, "📎 " + fichier.name + " : " + (question_fichier or "Résume ce fichier."))
                else:
                    st.warning("Impossible de lire ce fichier.")
            if fichier is not None and c_b.button("Apprendre", key="app_fichier"):
                contenu_fichier = lire_fichier_envoye(fichier)
                resume = resumer_pour_memoire(contenu_fichier, fichier.name, memoire_actuelle) if contenu_fichier else ""
                if resume:
                    ajouter_memoire(resume)
                    st.rerun()
                else:
                    st.warning("Impossible de résumer ce fichier.")
            st.markdown("**🎤 Message vocal**")
            audio = st.audio_input("Appuie, parle, puis arrête")
            if audio is not None and st.button("Envoyer ma voix", key="env_voix"):
                try:
                    client_voix = genai.Client(api_key=cle)
                    resultat = client_voix.models.generate_content(
                        model=MODELES_GEMINI[0],
                        contents=[
                            "Transcris fidèlement cet audio, sans rien ajouter.",
                            types.Part.from_bytes(data=audio.getvalue(), mime_type="audio/wav"),
                        ],
                    )
                    texte_voix = (resultat.text or "").strip()
                except Exception:
                    texte_voix = ""
                if texte_voix:
                    traiter(texte_voix, memoire_actuelle)
                else:
                    st.warning("Je n'ai pas réussi à comprendre l'audio. Réessaie.")
            st.markdown("**🧩 Modules du noyau**")
            existants = [f for f in github_lister(DOSSIER_MODULES) if f.endswith(".py")] if github_actif() else []
            if existants:
                for nom in existants:
                    st.caption("• " + nom)
            else:
                st.caption("Aucun module pour l'instant. Écris dans la conversation : module : ce que tu veux qu'il fasse.")
            proposition = st.session_state.get("module_propose")
            if proposition:
                st.markdown("**Module proposé : " + proposition["nom"] + "**")
                st.code(proposition["code"][:3000], language="python")
                m1, m2 = st.columns(2)
                if m1.button("✅ Approuver", key="ok_module"):
                    if github_actif() and github_ecrire(DOSSIER_MODULES + "/" + proposition["nom"], proposition["code"], "Ajout du module " + proposition["nom"]):
                        st.session_state.messages.append({"role": "assistant", "content": "Module ajouté : " + proposition["nom"] + "."})
                    else:
                        st.session_state.messages.append({"role": "assistant", "content": "Je n'ai pas réussi à ajouter le module. Vérifie le jeton GitHub."})
                    st.session_state.module_propose = None
                    sauver_conversations()
                    st.rerun()
                if m2.button("❌ Refuser", key="non_module"):
                    st.session_state.module_propose = None
                    st.rerun()

        st.markdown("---")
        st.markdown("**⚙️ Paramètres**")
        with st.expander("Intelligence"):
            st.selectbox("Rôle", list(ROLES.keys()), key="role")
            st.selectbox("Ton", list(TONS.keys()), key="ton")
            st.selectbox("Longueur des réponses", list(LONGUEURS.keys()), index=1, key="longueur")
            st.selectbox("Langue", list(LANGUES.keys()), key="langue")
            st.slider("Créativité", 0.0, 1.0, 0.5, 0.1, key="creativite")
            st.toggle("Recherche internet", value=True, key="recherche_web")
            st.toggle("Apprentissage automatique", value=True, key="apprentissage_auto")
        with st.expander("Apparence"):
            st.selectbox("Taille du texte", list(TAILLES.keys()), index=1, key="taille")
            st.selectbox("Couleur d'accent", list(ACCENTS.keys()), key="accent")
        with st.expander("Données"):
            if memoire_actuelle:
                if st.button("Effacer toute la mémoire"):
                    st.session_state.confirmer_effacement = True
                if st.session_state.get("confirmer_effacement"):
                    st.warning("Tu es sûr ? Cette action efface tout.")
                    if st.button("Oui, effacer"):
                        ecrire_memoire("")
                        st.session_state.confirmer_effacement = False
                        st.rerun()
            texte_export = ""
            for m in st.session_state.get("messages", []):
                qui = "Baraka" if m["role"] == "user" else "IA"
                texte_export += qui + " : " + m["content"] + "\n\n"
            st.download_button("Exporter la conversation", texte_export or "Conversation vide.", file_name="conversation.txt")
        st.caption("Colle une adresse web dans ta question pour que je la lise. « retiens : ... » pour lui apprendre quelque chose. « module : ... » pour lui ajouter une fonction, avec ton accord.")

    st.markdown('<p class="titre">Bonjour Baraka</p>', unsafe_allow_html=True)
    st.markdown('<p class="sous-titre">Ton assistant personnel pour toutes tes activités.</p>', unsafe_allow_html=True)

    if not st.session_state.messages:
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
        afficher_bulle(m["role"], m["content"])

    if st.session_state.get("a_repondre"):
        place = st.empty()
        place.markdown('<div class="ligne ia"><div class="bulle ia"><div class="points"><span></span><span></span><span></span></div></div></div>', unsafe_allow_html=True)
        historique = []
        for m in st.session_state.messages:
            historique.append({"role": m["role"], "content": m.get("envoi", m["content"])})
        texte = repondre(historique, memoire_actuelle)
        place.empty()
        st.session_state.messages.append({"role": "assistant", "content": texte})
        st.session_state.a_repondre = False
        if st.session_state.get("apprentissage_auto", True) and not texte.startswith("Je n'ai pas réussi"):
            derniere_question = ""
            for m in reversed(st.session_state.messages[:-1]):
                if m["role"] == "user":
                    derniere_question = m["content"]
                    break
            apprendre_auto(derniere_question, texte, memoire_actuelle)
        sauver_conversations()
        st.rerun()

    if st.session_state.get("suggestion"):
        texte_s = st.session_state.suggestion
        st.session_state.suggestion = None
        traiter(texte_s, memoire_actuelle)

    message = st.chat_input("Écris ta demande... Colle une adresse web pour que je la lise.")
    if message:
        traiter(message, memoire_actuelle)


try:
    application()
except Exception as erreur:
    if type(erreur).__name__ in ("RerunException", "StopException"):
        raise
    st.error("Une erreur est survenue : " + str(erreur)[:400])
    st.caption("Recharge la page avec Ctrl et F5. Si l'erreur revient, envoie-moi ce message exact.")
