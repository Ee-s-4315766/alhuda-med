"""Simple session-based auth — no external DB needed for prototype."""
import hashlib

# Users: {username: {password_hash, role, doctor_id, display_name}}
USERS = {
    "admin": {
        "password": hashlib.sha256("admin123".encode()).hexdigest(),
        "role": "admin",
        "doctor_id": None,
        "display_name": "مدير النظام",
    },
}


def login(username: str, password: str):
    user = USERS.get(username.lower())
    if not user:
        return None
    h = hashlib.sha256(password.encode()).hexdigest()
    if h == user["password"]:
        return {**user, "username": username}
    return None
