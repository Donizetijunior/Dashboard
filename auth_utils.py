import json
from pathlib import Path

DATA_DIR = Path("data")
USERS_FILE = DATA_DIR / "usuarios.json"
USERS_DEFAULT = {
    "admin": {"senha": "admin123", "perfil": "admin"},
    "usuario": {"senha": "usuario123", "perfil": "comum"}
}

def load_users():
    if not USERS_FILE.exists():
        with open(USERS_FILE, "w") as f:
            json.dump(USERS_DEFAULT, f, indent=4)
    with open(USERS_FILE) as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def authenticate(username, password):
    users = load_users()
    return username in users and users[username]['senha'] == password

def get_user_profile(username):
    return load_users()[username]['perfil'] 