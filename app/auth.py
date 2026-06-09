"""Simple session-based auth — no external DB needed for prototype."""
import hashlib

# Demo users: {username: {password_hash, role, doctor_id, display_name}}
USERS = {
    "admin": {
        "password": hashlib.sha256("admin123".encode()).hexdigest(),
        "role": "admin",
        "doctor_id": None,
        "display_name": "مدير النظام",
    },
    "d001": {
        "password": hashlib.sha256("doctor123".encode()).hexdigest(),
        "role": "doctor",
        "doctor_id": "D001",
        "display_name": "د. أحمد الزهراني",
    },
    "d002": {
        "password": hashlib.sha256("doctor123".encode()).hexdigest(),
        "role": "doctor",
        "doctor_id": "D002",
        "display_name": "د. سارة المطيري",
    },
    "d003": {
        "password": hashlib.sha256("doctor123".encode()).hexdigest(),
        "role": "doctor",
        "doctor_id": "D003",
        "display_name": "د. خالد العتيبي",
    },
    "d004": {
        "password": hashlib.sha256("doctor123".encode()).hexdigest(),
        "role": "doctor",
        "doctor_id": "D004",
        "display_name": "د. نورة الغامدي",
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
