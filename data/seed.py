"""Generate realistic demo data — aligned with real UCAAF fields."""
import json
import random
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

DOCTORS = [
    {"id": "D001", "name": "د. أحمد الزهراني",  "specialty": "باطنية"},
    {"id": "D002", "name": "د. سارة المطيري",   "specialty": "أطفال"},
    {"id": "D003", "name": "د. خالد العتيبي",   "specialty": "جراحة عامة"},
    {"id": "D004", "name": "د. نورة الغامدي",   "specialty": "نساء وولادة"},
]

# ICD → {name, valid_cpt, typical_drugs, specialty}
ICD_PROFILES = {
    "J18.9":  {
        "name": "التهاب رئوي",
        "valid_cpt": ["99213","99214","71046"],
        "drugs": "azithromycin|paracetamol|normal saline",
        "specialty": ["D001","D002"],
        "ucaf": "UCAF-1", "patient_type": "outpatient",
    },
    "E11.9":  {
        "name": "سكري النوع الثاني",
        "valid_cpt": ["99213","99214","80047","83036"],
        "drugs": "metformin|insulin|glucometer",
        "specialty": ["D001"],
        "ucaf": "UCAF-1", "patient_type": "outpatient",
    },
    "I10":    {
        "name": "ارتفاع ضغط الدم",
        "valid_cpt": ["99213","99214","93000"],
        "drugs": "amlodipine|losartan",
        "specialty": ["D001"],
        "ucaf": "UCAF-1", "patient_type": "outpatient",
    },
    "K29.7":  {
        "name": "التهاب المعدة",
        "valid_cpt": ["99213","99214"],
        "drugs": "pantozol|dansetron|paracetamol|normal saline",
        "specialty": ["D001","D003"],
        "ucaf": "UCAF-1", "patient_type": "outpatient",
    },
    "K29.70": {
        "name": "التهاب المعدة (H. pylori)",
        "valid_cpt": ["99213","99214"],
        "drugs": "riack plus|pantozol|paracetamol",
        "specialty": ["D001","D003"],
        "ucaf": "UCAF-1", "patient_type": "outpatient",
    },
    "J45.9":  {
        "name": "ربو غير محدد",
        "valid_cpt": ["99213","99214","94640"],
        "drugs": "pulmicort|salbutamol|montelukast",
        "specialty": ["D001","D002"],
        "ucaf": "UCAF-1", "patient_type": "outpatient",
    },
    "N97.0":  {
        "name": "عقم أنثوي — عدم إباضة",
        "valid_cpt": ["99213","99214"],
        "drugs": "specialist|fsh|prolactin h|lh",
        "specialty": ["D004"],
        "ucaf": "UCAF-1", "patient_type": "outpatient",
    },
    "M54.5":  {
        "name": "ألم أسفل الظهر",
        "valid_cpt": ["99213","72148","97110"],
        "drugs": "diclofenac|muscle relaxant|paracetamol",
        "specialty": ["D001","D003"],
        "ucaf": "UCAF-1", "patient_type": "outpatient",
    },
    "Z00.00": {
        "name": "فحص دوري",
        "valid_cpt": ["99395","99396","99397"],
        "drugs": "cbc|lipid profile|fasting glucose",
        "specialty": ["D001","D002","D004"],
        "ucaf": "UCAF-1", "patient_type": "outpatient",
    },
}

WRONG_CPT    = ["99232","93010","71045","80053","99285","99231"]
SYMPTOM_ICD  = ["R11","R51","R50.9","R10.9","R06.0"]  # symptom codes used wrongly as primary

random.seed(42)

def random_date(days_back=180):
    return (datetime.now() - timedelta(days=random.randint(1, days_back))).strftime("%Y-%m-%d")

def random_name():
    first = ["محمد","أحمد","خالد","عبدالله","سارة","نورة","فاطمة","ريم","عمر","يوسف"]
    last  = ["العتيبي","الزهراني","الغامدي","المطيري","القحطاني","الشهري","الدوسري"]
    return f"{random.choice(first)} {random.choice(last)}"

def generate_claims(n=300):
    rows = []
    for i in range(n):
        doctor  = random.choice(DOCTORS)
        icd     = random.choice(list(ICD_PROFILES.keys()))
        profile = ICD_PROFILES[icd]

        # pick a doctor from specialty if possible
        if doctor["id"] not in profile["specialty"]:
            doctor = random.choice([d for d in DOCTORS if d["id"] in profile["specialty"]]
                                   or DOCTORS)

        # --- Error injection ---
        error_roll = random.random()
        errors = []

        # Wrong CPT
        if error_roll < 0.32:
            cpt = random.choice(WRONG_CPT)
            errors.append("عدم تطابق ICD مع CPT")
        else:
            cpt = random.choice(profile["valid_cpt"])

        # Symptom code as primary (ERR-06)
        primary_icd = icd
        if random.random() < 0.12:
            primary_icd = random.choice(SYMPTOM_ICD)
            errors.append("كود عَرَض كتشخيص رئيسي")

        # Missing approval
        if random.random() < 0.20:
            errors.append("نقص رقم الموافقة")

        # H.pylori drug without K29.70 (ERR-07)
        drugs = profile["drugs"]
        if icd == "K29.7" and random.random() < 0.45:
            drugs = "riack plus|pantozol|dansetron"
            if "عدم تطابق ICD مع CPT" not in errors:
                errors.append("دواء H.pylori بدون كود K29.70")

        # Infertility checkbox missing (ERR-13)
        cb_infertility = True
        cb_pregnancy   = True
        if icd == "N97.0" and random.random() < 0.55:
            cb_infertility = False
            errors.append("مربع infertility غير مُفعَّل")
        if icd == "N97.0" and random.random() < 0.40:
            cb_pregnancy = False
            if "مربع infertility غير مُفعَّل" not in errors:
                errors.append("مربع pregnancy/indicate غير مُفعَّل")

        # Triple corticosteroid (ERR-11)
        if icd == "J45.9" and random.random() < 0.35:
            drugs = "pulmicort|dexamethasone|respred|salbutamol"
            errors.append("مضاعفة الكورتيزون")

        # Missing patient signature
        patient_signed = True
        if random.random() < 0.10:
            patient_signed = False
            errors.append("غياب توقيع المريض")

        # UCAF-2 for outpatient (ERR-16)
        ucaf_type = profile["ucaf"]
        if random.random() < 0.08:
            ucaf_type = "UCAF-2"
            errors.append("UCAF-2 مع حالة خارجية")

        # Status
        has_errors = len(errors) > 0
        if has_errors:
            status = random.choices(["مرفوض","معلق"], weights=[65,35])[0]
        else:
            status = random.choices(["مقبول","معلق"], weights=[88,12])[0]

        amount    = round(random.uniform(150, 7500), 2)
        recovered = (amount if status == "مقبول"
                     else round(amount * random.uniform(0.3, 0.65), 2) if status == "معلق"
                     else 0)
        age = random.randint(18, 72)

        rows.append({
            "claim_id":       f"CLM-{1000+i}",
            "patient_name":   random_name(),
            "patient_id":     f"P{random.randint(100000,999999)}",
            "age":            age,
            "gender":         random.choice(["ذكر","أنثى"]),
            "doctor_id":      doctor["id"],
            "doctor_name":    doctor["name"],
            "specialty":      doctor["specialty"],
            "service_date":   random_date(),
            "icd_code":       primary_icd,
            "icd_name":       profile["name"],
            "icd_code_2":     "" if primary_icd == icd else icd,
            "cpt_code":       cpt,
            "drugs":          drugs,
            "ucaf_type":      ucaf_type,
            "patient_type":   profile["patient_type"],
            "cb_infertility": cb_infertility,
            "cb_pregnancy":   cb_pregnancy,
            "patient_signed": patient_signed,
            "amount":         amount,
            "recovered":      recovered,
            "status":         status,
            "errors":         "|".join(errors),
            "error_count":    len(errors),
            "approval_no":    ("" if "نقص رقم الموافقة" in errors
                               else f"APP{random.randint(10000,99999)}"),
            "chief_complaint": ("irregular cycle wants to conceive"
                                if icd == "N97.0" else ""),
        })

    return pd.DataFrame(rows)


if __name__ == "__main__":
    out = Path(__file__).parent
    df  = generate_claims(300)
    df.to_csv(out / "claims.csv", index=False)
    with open(out / "doctors.json", "w", encoding="utf-8") as f:
        json.dump(DOCTORS, f, ensure_ascii=False, indent=2)
    rej = round((df["status"] == "مرفوض").mean() * 100, 1)
    print(f"Generated {len(df)} claims → data/claims.csv  (rejection rate: {rej}%)")
