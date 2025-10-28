from supabase import create_client, Client
import bcrypt

# Configuration Supabase
url = "https://eyffbmbmwdhrzzcboawu.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiIsInJlZiI6ImV5ZmZibWJtd2Rocnp6Y2JvYXd1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE2Njc2NzksImV4cCI6MjA3NzI0MzY3OX0.iSfIDxTpdnwAdSSzjo6tFOZJs8ZQGY5DE50TIo2_79I"
supabase: Client = create_client(url, key)


def add_user(username, password):
    # Vérifie les champs
    if not username or not password:
        return False

    # Vérifie si l'utilisateur existe déjà
    existing = supabase.table("users").select("id").eq("username", username).execute()
    if existing.data:
        # L'utilisateur existe déjà
        return False

    # Hash le mot de passe avant insertion
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    # Insère le nouvel utilisateur
    res = supabase.table("users").insert({"username": username, "password": hashed}).execute()

    # Si une erreur est retournée, on échoue
    if res.error:
        print("Erreur Supabase :", res.error)
        return False

    return True


def validate_user(username, password):
    # Récupère le hash associé au username
    result = supabase.table("users").select("password").eq("username", username).execute()
    data = result.data
    if data:
        hashed = data[0]["password"].encode()
        return bcrypt.checkpw(password.encode(), hashed)
    return False


def list_users():
    res = supabase.table("users").select("username").execute()
    if res.data:
        return [row["username"] for row in res.data]
    return []




