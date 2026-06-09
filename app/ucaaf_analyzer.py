"""UCAAF Error Analyzer — rule-based engine.

Rules extracted from real clinic cases (including H. pylori / Gastritis scenario).
"""
from dataclasses import dataclass, field
from typing import List

# ── ICD-10 → valid CPT codes ──────────────────────────────────────────────────
ICD_CPT_VALID = {
    "J18.9":  ["99213","99214","71046"],
    "E11.9":  ["99213","99214","80047","83036"],
    "I10":    ["99213","99214","93000"],
    "K21.0":  ["99213","43239"],
    "M54.5":  ["99213","72148","97110"],
    "Z00.00": ["99395","99396","99397"],
    "K29.7":  ["99213","99214"],
    "K29.70": ["99213","99214"],
    "K29.0":  ["99213","99214","43239"],
    "R11":    ["99213","99214"],
    "R10.9":  ["99213","99214"],
}

# ── Symptom codes that must NOT appear as primary diagnosis ───────────────────
SYMPTOM_CODES = {
    "R11",   # Nausea and vomiting
    "R10.9", # Unspecified abdominal pain
    "R10.0", # Acute abdomen
    "R51",   # Headache
    "R50.9", # Fever, unspecified
    "R05",   # Cough
    "R06.0", # Dyspnoea
    "R07.9", # Chest pain
    "R55",   # Syncope
    "R41.3", # Other amnesia
    "R00.0", # Tachycardia
}

# ── Drugs that require a specific ICD justification ──────────────────────────
# drug_keyword (lowercase) → list of acceptable primary ICD prefixes
DRUG_ICD_REQUIRED = {
    "cefuroxime":    ["J","K29.70","A","B96","L","N"],
    "daroxime":      ["J","K29.70","A","B96","L","N"],
    "amoxicillin":   ["J","K29.70","A","B96","L","N","H"],
    "clarithromycin":["J","K29.70","A","B96","L","K29.0"],
    "riack":         ["K29.70","K29.0","B96"],   # H.pylori triple therapy
    "metronidazole": ["K29.70","K29.0","B96","A06","N76"],
}

# ── Source codes that require GP referral code ────────────────────────────────
REQUIRES_REFERRAL_SRC = {"MG1002", "MG1003"}

FINANCIAL_LIMIT = 5000  # SAR — prior auth required above this


# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class ClaimCheck:
    claim_id: str
    errors: List[dict] = field(default_factory=list)

    @property
    def has_errors(self):
        return len(self.errors) > 0

    @property
    def severity(self):
        if not self.errors:
            return "سليم"
        return "عالي" if any(e["level"] == "عالي" for e in self.errors) else "متوسط"


# ─────────────────────────────────────────────────────────────────────────────
def analyze(row: dict) -> ClaimCheck:
    """Run all UCAAF rules against a single claim dict."""
    result = ClaimCheck(claim_id=row.get("claim_id", "?"))

    icd      = str(row.get("icd_code", "")).strip()
    icd2     = str(row.get("icd_code_2", "")).strip()   # second ICD code
    cpt      = str(row.get("cpt_code", "")).strip()
    amount   = float(row.get("amount", 0))
    approval = str(row.get("approval_no", "")).strip()
    drugs    = str(row.get("drugs", "")).lower()         # pipe-separated drug names
    src_code = str(row.get("source_code", "")).strip().upper()

    # ── Rule 1 — ICD / CPT mismatch ──────────────────────────────────────────
    if icd in ICD_CPT_VALID and cpt and cpt not in ICD_CPT_VALID[icd]:
        result.errors.append({
            "code":  "ERR-01",
            "level": "عالي",
            "msg":   f"عدم تطابق التشخيص ({icd}) مع الإجراء ({cpt})",
            "fix":   f"تأكد أن كود CPT {cpt} متوافق مع {icd} أو غيّر التشخيص",
        })

    # ── Rule 2 — Symptom code used as primary diagnosis ──────────────────────
    primary_prefix = icd.split(".")[0] if icd else ""
    if icd in SYMPTOM_CODES or primary_prefix in SYMPTOM_CODES:
        result.errors.append({
            "code":  "ERR-06",
            "level": "عالي",
            "msg":   f"كود العَرَض ({icd}) مستخدم كتشخيص رئيسي — يجب أن يكون ثانوياً",
            "fix":   "انقل كود العَرَض إلى الخانة الثانية (2nd code) وضع التشخيص السببي أولاً",
        })

    # ── Rule 3 — H. pylori drug without H. pylori diagnosis ──────────────────
    pylori_drugs = ["riack", "clarithromycin", "metronidazole", "amoxicillin"]
    has_pylori_drug = any(d in drugs for d in pylori_drugs)
    has_pylori_icd  = any(icd.startswith(p) for p in ["K29.70","K29.0","B96"])
    if has_pylori_drug and not has_pylori_icd:
        result.errors.append({
            "code":  "ERR-07",
            "level": "عالي",
            "msg":   "وصف دواء علاج H. pylori بدون كود تشخيصي مناسب (K29.70 / B96.81)",
            "fix":   "أضف K29.70 كتشخيص رئيسي أو B96.81 كتشخيص ثانوي",
        })

    # ── Rule 4 — Antibiotic without infection diagnosis ──────────────────────
    antibiotic_keywords = ["cefuroxime","daroxime","augmentin","azithromycin","ciprofloxacin"]
    has_antibiotic = any(k in drugs for k in antibiotic_keywords)
    if has_antibiotic:
        infection_prefixes = ["J","A","B","K29.70","K29.0","L","N","H66","H60"]
        justified = any(icd.startswith(p) for p in infection_prefixes)
        if not justified:
            result.errors.append({
                "code":  "ERR-08",
                "level": "عالي",
                "msg":   "وصف مضاد حيوي بدون تشخيص عدوى مبرر (التشخيص الحالي لا يستدعيه)",
                "fix":   "أضف كود التشخيص الذي يبرر المضاد الحيوي أو احذف الدواء",
            })

    # ── Rule 5 — Missing approval number ─────────────────────────────────────
    if amount > FINANCIAL_LIMIT and not approval:
        result.errors.append({
            "code":  "ERR-02",
            "level": "عالي",
            "msg":   f"تجاوز الحد المالي ({amount:,.0f} ر.س) دون رقم موافقة مسبقة",
            "fix":   "احصل على رقم موافقة مسبقة من شركة التأمين قبل الإرسال",
        })
    elif not approval:
        result.errors.append({
            "code":  "ERR-02B",
            "level": "متوسط",
            "msg":   "رقم الموافقة مفقود",
            "fix":   "أدخل رقم الموافقة أو تأكد من الإعفاء",
        })

    # ── Rule 6 — Missing patient signature ───────────────────────────────────
    if not row.get("patient_signed", True):
        result.errors.append({
            "code":  "ERR-03",
            "level": "عالي",
            "msg":   "توقيع المريض مفقود في نموذج اليوكاف",
            "fix":   "أحضر نموذج الموافقة الموقّع قبل إرسال المطالبة",
        })

    # ── Rule 7 — Missing service date ────────────────────────────────────────
    if not str(row.get("service_date", "")).strip():
        result.errors.append({
            "code":  "ERR-04",
            "level": "متوسط",
            "msg":   "تاريخ الخدمة مفقود",
            "fix":   "أدخل تاريخ تقديم الخدمة بصيغة YYYY-MM-DD",
        })

    # ── Rule 8 — Missing patient medical ID ──────────────────────────────────
    if not str(row.get("patient_id", "")).strip():
        result.errors.append({
            "code":  "ERR-05",
            "level": "عالي",
            "msg":   "الرقم الطبي للمريض مفقود",
            "fix":   "أدخل الرقم الطبي (MRN) للمريض",
        })

    # ── Rule 9 — R11 paired with K29.7 order check ───────────────────────────
    # If primary=K29.7 and second=R11 that's correct; reverse is wrong
    if icd in SYMPTOM_CODES and icd2.startswith("K"):
        result.errors.append({
            "code":  "ERR-09",
            "level": "عالي",
            "msg":   f"ترتيب الأكواد مقلوب: العَرَض ({icd}) في الأول والتشخيص ({icd2}) في الثاني",
            "fix":   f"اجعل {icd2} هو الكود الأول و {icd} الكود الثاني",
        })

    return result


def analyze_dataframe(df):
    """Return list of ClaimCheck for every row in df."""
    return [analyze(row) for row in df.to_dict("records")]


# ─────────────────────────────────────────────────────────────────────────────
# Quick test
if __name__ == "__main__":
    cases = [
        # Gastritis case from screenshot — R11 as primary, H.pylori drug, antibiotic
        {
            "claim_id": "CLM-SCREENSHOT",
            "patient_id": "P123456",
            "icd_code": "R11",
            "icd_code_2": "K29.7",
            "cpt_code": "99213",
            "amount": 357.15,
            "approval_no": "",
            "service_date": "2025-06-01",
            "patient_signed": True,
            "drugs": "riack plus|daroxime|paracetamol|pantozol|dansetron|normal saline",
        },
        # Clean claim
        {
            "claim_id": "CLM-CLEAN",
            "patient_id": "P999",
            "icd_code": "K29.70",
            "icd_code_2": "R11",
            "cpt_code": "99213",
            "amount": 400,
            "approval_no": "APP12345",
            "service_date": "2025-06-01",
            "patient_signed": True,
            "drugs": "riack plus|paracetamol|pantozol",
        },
    ]
    for c in cases:
        r = analyze(c)
        print(f"\n{'='*55}")
        print(f"المطالبة: {r.claim_id} — الخطورة: {r.severity}")
        if r.errors:
            for e in r.errors:
                print(f"  [{e['code']}] {e['msg']}")
                print(f"         الحل: {e['fix']}")
        else:
            print("  ✅ سليمة")
