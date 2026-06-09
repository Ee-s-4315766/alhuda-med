"""Generate realistic demo data for AlHuda Med platform."""
import json
import random
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

DOCTORS = [
    {"id": "D001", "name": "د. أحمد الزهراني", "specialty": "باطنية"},
    {"id": "D002", "name": "د. سارة المطيري",  "specialty": "أطفال"},
    {"id": "D003", "name": "د. خالد العتيبي",  "specialty": "جراحة عامة"},
    {"id": "D004", "name": "د. نورة الغامدي",  "specialty": "نساء وولادة"},
]

ICD_CPT_MAP = {
    "J18.9":  {"name": "التهاب رئوي",          "valid_cpt": ["99213","99214","71046"]},
    "E11.9":  {"name": "سكري النوع الثاني",     "valid_cpt": ["99213","99214","80047","83036"]},
    "I10":    {"name": "ارتفاع ضغط الدم",       "valid_cpt": ["99213","99214","93000"]},
    "K21.0":  {"name": "ارتداد معدي مريئي",     "valid_cpt": ["99213","43239"]},
    "M54.5":  {"name": "ألم أسفل الظهر",        "valid_cpt": ["99213","72148","97110"]},
    "Z00.00": {"name": "فحص دوري",              "valid_cpt": ["99395","99396","99397"]},
}

WRONG_CPT = ["99232", "93010", "71045", "80053", "99285"]

ERROR_TYPES = [
    "عدم تطابق ICD مع CPT",
    "نقص رقم الموافقة",
    "غياب توقيع المريض",
    "تجاوز الحد المالي",
    "خطأ في جرعة الدواء",
    "بيانات ناقصة (رقم طبي)",
    "تاريخ الخدمة مفقود",
]

random.seed(42)

def random_date(days_back=180):
    return (datetime.now() - timedelta(days=random.randint(0, days_back))).strftime("%Y-%m-%d")

def generate_claims(n=200):
    rows = []
    for i in range(n):
        doctor  = random.choice(DOCTORS)
        icd     = random.choice(list(ICD_CPT_MAP.keys()))
        info    = ICD_CPT_MAP[icd]
        wrong   = random.random() < 0.38          # 38% have at least one error

        if wrong:
            cpt = random.choice(WRONG_CPT)
        else:
            cpt = random.choice(info["valid_cpt"])

        errors = []
        if wrong:
            errors.append("عدم تطابق ICD مع CPT")
        if random.random() < 0.18:
            errors.append("نقص رقم الموافقة")
        if random.random() < 0.12:
            errors.append("غياب توقيع المريض")
        if random.random() < 0.08:
            errors.append("تجاوز الحد المالي")
        if random.random() < 0.06:
            errors.append("خطأ في جرعة الدواء")

        has_errors = len(errors) > 0
        if has_errors:
            status = random.choice(["مرفوض", "معلق"])
        else:
            status = random.choices(["مقبول", "معلق"], weights=[85, 15])[0]

        amount = round(random.uniform(200, 8000), 2)
        recovered = amount if status == "مقبول" else (round(amount * random.uniform(0.3, 0.7), 2) if status == "معلق" else 0)

        rows.append({
            "claim_id":      f"CLM-{1000+i}",
            "patient_name":  f"مريض {i+1}",
            "patient_id":    f"P{random.randint(100000,999999)}",
            "doctor_id":     doctor["id"],
            "doctor_name":   doctor["name"],
            "specialty":     doctor["specialty"],
            "service_date":  random_date(),
            "icd_code":      icd,
            "icd_name":      info["name"],
            "cpt_code":      cpt,
            "amount":        amount,
            "recovered":     recovered,
            "status":        status,
            "errors":        "|".join(errors),
            "error_count":   len(errors),
            "approval_no":   "" if "نقص رقم الموافقة" in errors else f"APP{random.randint(10000,99999)}",
        })
    return pd.DataFrame(rows)

if __name__ == "__main__":
    out = Path(__file__).parent
    df = generate_claims(200)
    df.to_csv(out / "claims.csv", index=False)
    with open(out / "doctors.json", "w", encoding="utf-8") as f:
        json.dump(DOCTORS, f, ensure_ascii=False, indent=2)
    print(f"Generated {len(df)} claims → data/claims.csv")
