from supabase import create_client, Client
import bcrypt
import streamlit as st
import json

# Configuration Supabase
url = "https://eyffbmbmwdhrzzcboawu.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV5ZmZibWJtd2Rocnp6Y2JvYXd1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE2Njc2NzksImV4cCI6MjA3NzI0MzY3OX0.iSfIDxTpdnwAdSSzjo6tFOZJs8ZQGY5DE50TIo2_79I"
supabase: Client = create_client(url, key)

def add_user(username, password):
    # (Ton code existant reste inchangé)
    if not username or not password:
        st.error("Veuillez remplir tous les champs.")
        return False

    try:
        # Vérifier si l'utilisateur existe déjà
        existing = supabase.table("users").select("id").eq("username", username).execute()

        if existing.data and len(existing.data) > 0:
            st.warning("Nom d'utilisateur déjà utilisé.")
            return False

        # Hashage du mot de passe
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        # Insertion de l'utilisateur
        response = supabase.table("users").insert({
            "username": username,
            "password": hashed
        }).execute()

        # Vérification de l'insertion
        if not response.data:
            st.error("Erreur : impossible d’enregistrer l’utilisateur dans la base.")
            return False

        st.success("Compte créé avec succès 🎉")
        return True

    except Exception as e:
        st.error(f"Erreur lors de la création du compte : {e}")
        return False

def validate_user(username, password):
    # (Ton code existant reste inchangé)
    import streamlit as st
    try:
        st.write(f"🔍 Vérification de l'utilisateur : {username}")

        result = supabase.table("users").select("password").eq("username", username).execute()
        st.write("Résultat Supabase :", result.data)

        data = result.data
        if data and len(data) > 0:
            hashed = data[0]["password"].encode()
            st.write("Mot de passe chiffré trouvé :", hashed)

            if bcrypt.checkpw(password.encode(), hashed):
                st.success("✅ Connexion réussie !")
                return True
            else:
                st.error("❌ Mot de passe incorrect.")
                return False
        else:
            st.error("❌ Nom d’utilisateur introuvable.")
            return False
    except Exception as e:
        st.error(f"Erreur de connexion : {e}")
        return False

def list_users():
    # (Ton code existant reste inchangé)
    try:
        res = supabase.table("users").select("username").execute()
        if res.data:
            return [row["username"] for row in res.data]
        else:
            return []
    except Exception as e:
        st.error(f"Erreur list_users : {e}")
        return []

# Nouvelles fonctions pour les carnets secrets

def has_secret_journal(username):
    """Vérifie si l'utilisateur a déjà un carnet secret."""
    try:
        result = supabase.table("secret_journals").select("id").eq("username", username).execute()
        return len(result.data) > 0
    except Exception as e:
        st.error(f"Erreur vérification carnet : {e}")
        return False

def create_secret_journal(username, journal_name, color, code):
    """Crée un nouveau carnet secret."""
    if not journal_name or not color or not code:
        st.error("Tous les champs sont requis.")
        return False
    try:
        # Vérifier si déjà un carnet
        if has_secret_journal(username):
            st.warning("Vous avez déjà un carnet secret.")
            return False
        # Hash du code
        code_hash = bcrypt.hashpw(code.encode(), bcrypt.gensalt()).decode()
        # Contenu initial : JSON avec une page vide
        content = json.dumps({"pages": [{"title": "Page 1", "content": ""}]})
        response = supabase.table("secret_journals").insert({
            "username": username,
            "journal_name": journal_name,
            "color": color,
            "code_hash": code_hash,
            "content": content
        }).execute()
        if response.data:
            st.success("Carnet secret créé avec succès !")
            return True
        else:
            st.error("Erreur lors de la création du carnet.")
            return False
    except Exception as e:
        st.error(f"Erreur création carnet : {e}")
        return False

def validate_journal_code(username, code):
    """Valide le code du carnet secret."""
    try:
        result = supabase.table("secret_journals").select("code_hash").eq("username", username).execute()
        if result.data and len(result.data) > 0:
            hashed = result.data[0]["code_hash"].encode()
            return bcrypt.checkpw(code.encode(), hashed)
        return False
    except Exception as e:
        st.error(f"Erreur validation code : {e}")
        return False

def load_journal_content(username):
    """Charge le contenu du carnet secret."""
    try:
        result = supabase.table("secret_journals").select("journal_name, color, content").eq("username", username).execute()
        if result.data and len(result.data) > 0:
            data = result.data[0]
            return {
                "name": data["journal_name"],
                "color": data["color"],
                "content": json.loads(data["content"])
            }
        return None
    except Exception as e:
        st.error(f"Erreur chargement contenu : {e}")
        return None

def save_journal_content(username, content):
    """Sauvegarde le contenu du carnet secret."""
    try:
        content_json = json.dumps(content)
        supabase.table("secret_journals").update({"content": content_json}).eq("username", username).execute()
    except Exception as e:
        st.error(f"Erreur sauvegarde contenu : {e}")


















