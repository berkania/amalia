from supabase import create_client, Client
import bcrypt

# Configuration Supabase
url = "https://eyffbmbmwdhrzzcboawu.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiIsInJlZiI6ImV5ZmZibWJtd2Rocnp6Y2JvYXd1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE2Njc2NzksImV4cCI6MjA3NzI0MzY3OX0.iSfIDxTpdnwAdSSzjo6tFOZJs8ZQGY5DE50TIo2_79I"
supabase: Client = create_client(url, key)

def add_user(username, password):
    import streamlit as st

    if not username or not password:
        st.error("Champs vides")
        return False

    try:
        # Vérifie si l'utilisateur existe déjà
        existing = supabase.table("users").select("id").eq("username", username).execute()
        st.write("Résultat de la recherche :", existing.data)

        if existing.data and len(existing.data) > 0:
            st.warning("Nom déjà utilisé")
            return False

        # Hash le mot de passe
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        # Insertion
        res = supabase.table("users").insert({"username": username, "password": hashed}).execute()
        st.write("Résultat insertion :", res.data, res.error)

        if res.error:
            st.error(f"Erreur Supabase : {res.error}")
            return False

        st.success("Utilisateur ajouté avec succès dans la base")
        return True

    except Exception as e:
        st.error(f"Erreur inattendue : {e}")
        return False


def validate_user(username, password):
    try:
        result = supabase.table("users").select("password").eq("username", username).execute()
        data = result.data
        if data and len(data) > 0:
            hashed = data[0]["password"].encode()
            return bcrypt.checkpw(password.encode(), hashed)
    except Exception as e:
        print("Erreur de connexion :", e)
    return False


def list_users():
    try:
        res = supabase.table("users").select("username").execute()
        if res.data:
            return [row["username"] for row in res.data]
    except Exception as e:
        print("Erreur list_users :", e)
    return []







