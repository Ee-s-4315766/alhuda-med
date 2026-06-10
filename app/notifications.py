"""نظام الإشعارات — Notification System."""
import json
import uuid
from datetime import datetime
from pathlib import Path

NOTIF_PATH = Path(__file__).parent.parent / "data" / "notifications.json"


def _load() -> dict:
    if NOTIF_PATH.exists():
        try:
            return json.loads(NOTIF_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save(data: dict):
    NOTIF_PATH.parent.mkdir(parents=True, exist_ok=True)
    NOTIF_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def create_notification(doctor_id: str, notif_type: str, title: str,
                        message: str, claim_id: str = "", level: str = "متوسط"):
    """أضف إشعاراً لطبيب معين."""
    data = _load()
    if doctor_id not in data:
        data[doctor_id] = []
    data[doctor_id].append({
        "id":        str(uuid.uuid4())[:8],
        "type":      notif_type,   # new_claim | error_found | claim_rejected
        "title":     title,
        "message":   message,
        "claim_id":  claim_id,
        "level":     level,        # عالي | متوسط | منخفض
        "read":      False,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    # Keep only last 100 notifications per doctor
    data[doctor_id] = data[doctor_id][-100:]
    _save(data)


def get_notifications(doctor_id: str, unread_only: bool = False) -> list:
    data = _load()
    notifs = data.get(doctor_id, [])
    if unread_only:
        notifs = [n for n in notifs if not n["read"]]
    return list(reversed(notifs))  # newest first


def get_unread_count(doctor_id: str) -> int:
    return len(get_notifications(doctor_id, unread_only=True))


def mark_all_read(doctor_id: str):
    data = _load()
    for n in data.get(doctor_id, []):
        n["read"] = True
    _save(data)


def mark_one_read(doctor_id: str, notif_id: str):
    data = _load()
    for n in data.get(doctor_id, []):
        if n["id"] == notif_id:
            n["read"] = True
    _save(data)


def notify_claims_batch(df_new_claims, doctor_lookup: dict):
    """
    يُطلق إشعارات لكل طبيب بعد إضافة حالات من المعالجة الجماعية.
    doctor_lookup: {doctor_id: doctor_name}
    """
    from app.ucaaf_analyzer import analyze_dataframe
    results = analyze_dataframe(df_new_claims)

    # Group by doctor
    from collections import defaultdict
    doctor_claims = defaultdict(list)
    doctor_errors = defaultdict(list)

    for i, (_, row) in enumerate(df_new_claims.iterrows()):
        did = str(row.get("doctor_id", "")).strip()
        if not did:
            continue
        doctor_claims[did].append(str(row.get("claim_id", f"#{i+1}")))
        if i < len(results) and results[i].errors:
            for err in results[i].errors:
                doctor_errors[did].append({
                    "claim_id": str(row.get("claim_id", f"#{i+1}")),
                    "msg":      err["msg"],
                    "fix":      err["fix"],
                    "level":    err["level"],
                })

    for did, claims in doctor_claims.items():
        n = len(claims)
        # New claims notification
        create_notification(
            doctor_id=did,
            notif_type="new_claim",
            title=f"تمت إضافة {n} حالة جديدة",
            message=f"الحالات: {', '.join(claims[:5])}{'...' if n > 5 else ''}",
            level="منخفض",
        )
        # Error notifications (one per error, max 10)
        for err in doctor_errors[did][:10]:
            create_notification(
                doctor_id=did,
                notif_type="error_found",
                title=f"خطأ في الحالة {err['claim_id']}",
                message=f"{err['msg']} ← {err['fix']}",
                claim_id=err["claim_id"],
                level=err["level"],
            )
