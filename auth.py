from supabase import create_client, Client
import bcrypt

# Configure tes clés/fichier secrets ici
url = "https://eyffbmbmwdhrzzcboawu.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV5ZmZibWJtd2Rocnp6Y2JvYXd1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE2Njc2NzksImV4cCI6MjA3NzI0MzY3OX0.iSfIDxTpdnwAdSSzjo6tFOZJs8ZQGY5DE50TIo2_79I"
supabase: Client = create_client(url, key)

def add_user(username, password):
    # Hash le mot de passe avant insertion
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    # Tente d'insérer l'utilisateur
    res = supabase.table('users').insert({"username": username, "password": hashed}).execute()
    # Si erreur car utilisateur déjà existant, renvoie False
    if res.status_code == 409:
        return False
    return res.status_code == 201

def validate_user(username, password):
    # Récupère le hash associé au username
    result = supabase.table('users').select("password").eq("username", username).execute()
    data = result.data
    if data:
        hashed = data[0]["password"].encode()
        return bcrypt.checkpw(password.encode(), hashed)
    return False

def list_users():
    # Liste tous les utilisateurs
    res = supabase.table('users').select("username").execute()
    if res.data:
        return [row["username"] for row in res.data]
    return []



