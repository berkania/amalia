from supabase import create_client, Client
import bcrypt
import streamlit as st

# Configuration Supabase
url = "https://eyffbmbmwdhrzzcboawu.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV5ZmZibWJtd2Rocnp6Y2JvYXd1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE2Njc2NzksImV4cCI6MjA3NzI0MzY3OX0.iSfIDxTpdnwAdSSzjo6tFOZJs8ZQGY5DE50TIo2_79I"
supabase: Client = create_client(url, key)


def add_user(username, password):
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
    try:
        result = supabase.table("users").select("password").eq("username", username).execute()

        if not result.data or len(result.data) == 0:
            st.warning("Nom d'utilisateur introuvable.")
            return False

        hashed_password = result.data[0]["password"].encode()
        if bcrypt.checkpw(password.encode(), hashed_password):
            return True
        else:
            st.error("Mot de passe incorrect.")
            return False

    except Exception as e:
        st.error(f"Erreur de connexion : {e}")
        return False


def list_users():
    try:
        res = supabase.table("users").select("username").execute()
        if res.data:
            return [row["username"] for row in res.data]
        else:
            return []
    except Exception as e:
        st.error(f"Erreur list_users : {e}")
        return []










