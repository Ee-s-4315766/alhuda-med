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
    "d1": {
        "password": hashlib.sha256("doctor123".encode()).hexdigest(),
        "role": "doctor",
        "doctor_id": "1",
        "display_name": "د . سعد عبدالفتاح",
    },
    "d3": {
        "password": hashlib.sha256("doctor123".encode()).hexdigest(),
        "role": "doctor",
        "doctor_id": "3",
        "display_name": "د. منه الله صدقي",
    },
    "d4": {
        "password": hashlib.sha256("doctor123".encode()).hexdigest(),
        "role": "doctor",
        "doctor_id": "4",
        "display_name": "د . محمد الجعبري",
    },
    "d5": {
        "password": hashlib.sha256("doctor123".encode()).hexdigest(),
        "role": "doctor",
        "doctor_id": "5",
        "display_name": "د . محمد عبدالعزيز",
    },
    "d8": {
        "password": hashlib.sha256("doctor123".encode()).hexdigest(),
        "role": "doctor",
        "doctor_id": "8",
        "display_name": "د . فريد الخولي",
    },
    "d11": {
        "password": hashlib.sha256("doctor123".encode()).hexdigest(),
        "role": "doctor",
        "doctor_id": "11",
        "display_name": "د . محمد عثمان",
    },
    "d12": {
        "password": hashlib.sha256("doctor123".encode()).hexdigest(),
        "role": "doctor",
        "doctor_id": "12",
        "display_name": "د. محمد عبده",
    },
    "d13": {
        "password": hashlib.sha256("doctor123".encode()).hexdigest(),
        "role": "doctor",
        "doctor_id": "13",
        "display_name": "د . سمر أبو شعيشع",
    },
    "d18": {
        "password": hashlib.sha256("doctor123".encode()).hexdigest(),
        "role": "doctor",
        "doctor_id": "18",
        "display_name": "د.اماني ابو الخير",
    },
    "d19": {
        "password": hashlib.sha256("doctor123".encode()).hexdigest(),
        "role": "doctor",
        "doctor_id": "19",
        "display_name": "د.نداء مدين",
    },
    "d20": {
        "password": hashlib.sha256("doctor123".encode()).hexdigest(),
        "role": "doctor",
        "doctor_id": "20",
        "display_name": "د. عمرو العمري",
    },
    "d24": {
        "password": hashlib.sha256("doctor123".encode()).hexdigest(),
        "role": "doctor",
        "doctor_id": "24",
        "display_name": "د. ممدوح سيد محمد",
    },
    "d26": {
        "password": hashlib.sha256("doctor123".encode()).hexdigest(),
        "role": "doctor",
        "doctor_id": "26",
        "display_name": "د. اسلام فريد",
    },
    "d28": {
        "password": hashlib.sha256("doctor123".encode()).hexdigest(),
        "role": "doctor",
        "doctor_id": "28",
        "display_name": "د. رنا الهلالي",
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
