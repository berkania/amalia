import speech_recognition as sr
import threading
import time
from gtts import gTTS
import os
import random
import datetime
import re
import webbrowser


import feedparser
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import email
import imaplib



# Nettoyage fichiers audio anciens
def nettoyage_audio():
    for f in os.listdir():
        if f.startswith("reponse_") and f.endswith(".mp3"):
            try:
                os.remove(f)
            except Exception:
                pass

nettoyage_audio()

# Initialisation TTS
listener = sr.Recognizer()

contacts = {
    "lina": "lhamdaoui544@gmail.com",
    "amandine": "rommaniolaya@gmail.com",
    "directeur": "b.ramaekers@sjb-liege.org",
    "personne": "rousden@sjb-liege.org",
    "loris": "porrlor@sjb-liege.org"
}

def ecoute():
    """Fonction pour écouter via reconnaissance vocale (adaptée pour Streamlit avec JS)."""
    try:
        if "voice_input" in st.session_state and st.session_state.voice_input:
            texte = st.session_state.voice_input.lower()
            st.session_state.voice_input = ""  # Reset après utilisation
            return texte
        return ""
    except Exception as e:
        print("Erreur:", e)
        return ""

def parle(text):
    """Synthèse vocale avec gTTS, joue via Streamlit."""
    print("🤖:", text)
    tts = gTTS(text=text, lang='fr')
    nom_fichier = f"reponse_{int(time.time())}.mp3"
    tts.save(nom_fichier)
    st.audio(nom_fichier, format="audio/mp3", autoplay=True)
    threading.Timer(len(text) * 0.06 + 1, lambda: supprimer_fichier_audio(nom_fichier)).start()

def supprimer_fichier_audio(fichier, tentatives=5):
    for _ in range(tentatives):
        try:
            if os.path.exists(fichier):
                os.remove(fichier)
                return
        except PermissionError:
            time.sleep(0.5)

def envoyer_mail(destinataire, sujet, corps):
    expediteur = "kiri22519@gmail.com"
    mot_de_passe = "mmknoxmafvwctxwp"

    message = MIMEMultipart()
    message['From'] = expediteur
    message['To'] = destinataire
    message['Subject'] = sujet
    message.attach(MIMEText(corps, 'plain'))

    print(f"Envoi d'un mail à : {destinataire}")

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as serveur:
            serveur.starttls()
            serveur.login(expediteur, mot_de_passe)
            serveur.send_message(message)
            parle("Le mail a été envoyé.")
    except Exception as e:
        print("Erreur d'envoi :", e)
        parle("Erreur pendant l'envoi du mail.")

def lire_actualites():
    flux = feedparser.parse("https://www.francetvinfo.fr/titres.rss")
    titres = [entry.title for entry in flux.entries[:5]]
    if not titres:
        parle("Désolé, je n'ai trouvé aucune actualité.")
    else:
        for titre in titres:
            parle(titre)

def meteo_ville(ville):
    try:
        url = f"https://wttr.in/{ville}?format=3"
        response = requests.get(url)
        if response.status_code == 200:
            return response.text.strip()
        else:
            return "❌ Impossible de récupérer la météo."
    except Exception as e:
        return f"❌ Erreur : {e}"

def ajouter_contact(nom, email):
    contacts[nom.lower()] = email

def recherche_google():
    parle("Que veux-tu chercher sur Google ?")
    requete = ecoute()
    if requete:
        url = f"https://www.google.com/search?q={requete}"
        webbrowser.open(url)
        parle(f"Voici les résultats de ta recherche pour {requete}.")

def lire_email_specifique(nom):
    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login('kiri22519@gmail.com', 'mmknoxmafvwctxwp')
        mail.select('inbox')

        adresse_recherche = contacts.get(nom.lower(), nom)
        result, data = mail.search(None, f'(FROM "{adresse_recherche}")')
        email_ids = data[0].split()
        if email_ids:
            latest_email_id = email_ids[-1]
            result, msg_data = mail.fetch(latest_email_id, '(RFC822)')
            msg = email.message_from_bytes(msg_data[0][1])

            subject = msg['subject']
            from_email = email.utils.parseaddr(msg['From'])[1]
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode()
            else:
                body = msg.get_payload(decode=True).decode()

            parle(f"Voici le mail de {nom}. Sujet : {subject}. Contenu : {body}")

            parle("Voulez-vous lui répondre ? (oui ou non)")
            reponse = ecoute()
            if "oui" in reponse:
                repondre_email(from_email, subject)
            else:
                parle("D'accord, je ne réponds pas.")
        else:
            parle(f"Aucun e-mail trouvé de {nom}.")
        mail.logout()
    except Exception as e:
        print("Erreur lors de la lecture des e-mails :", e)
        parle("Erreur lors de la lecture des e-mails.")

def repondre_email(adresse, sujet):
    parle("Quel est le contenu de votre réponse ?")
    corps = ecoute()
    parle(f"Vous avez dit : {corps}. Est-ce correct ? (oui ou non)")
    confirmation = ecoute()
    if "oui" in confirmation:
        envoyer_mail(adresse, f"Re: {sujet}", corps)
    else:
        parle("D'accord, je ne vais pas envoyer le mail.")

def traiter_commande(cmd):
    """Traite une commande vocale."""
    if not cmd:
        return
    elif "bonjour" in cmd:
        parle("Bonjour !")
    elif "envoie un mail" in cmd:
        parle("À qui voulez-vous envoyer le mail ?")
        nom = ecoute()
        email_dest = contacts.get(nom.strip().lower())
        if not email_dest:
            parle("Je ne connais pas cette personne.")
            return
        parle("Quel est le sujet du mail ?")
        sujet = ecoute()
        parle("Quel est le message ?")
        corps = ecoute()
        envoyer_mail(email_dest, sujet, corps)
    elif "lire le mail de" in cmd:
        expediteur = cmd.split("lire le mail de")[-1].strip()
        lire_email_specifique(expediteur)
    elif "répondre au mail de" in cmd:
        expediteur = cmd.split("répondre au mail de")[-1].strip()
        lire_email_specifique(expediteur)
    elif "les infos" in cmd or "actualités" in cmd:
        parle("Voici les actualités du jour.")
        lire_actualites()
    elif "météo" in cmd or "temps" in cmd:
        parle("Pour quelle ville veux-tu la météo ?")
        ville = ecoute()
        resultat = meteo_ville(ville)
        parle(resultat)
    elif "cherche" in cmd or "recherche" in cmd:
        recherche_google()
    elif "ça va" in cmd:
        parle("Je vais très bien, merci ! En quoi puis-je vous aider aujourd'hui ?")
    elif "stop" in cmd or "au revoir" in cmd:
        parle("Au revoir !")
    else:
        parle("Je n'ai pas compris la commande.")

