"""UCAAF Error Analyzer — rule-based engine.

Rules extracted from real clinic cases:
  Case 1 — Gastritis / H. pylori (K29.7, R11, Riack Plus, Daroxime)
  Case 2 — Asthma + Gastritis (J45.9, K29.7, triple corticosteroid, Riack Plus)
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
    "J45.9":  ["99213","99214","94640","94664"],
    "J45.5":  ["99213","99214","94640","94664"],
    "J45.4":  ["99213","99214","94640"],
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
    "R06.2", # Wheezing
    "R07.9", # Chest pain
    "R55",   # Syncope
    "R41.3", # Other amnesia
    "R00.0", # Tachycardia
    "R06.09",# Other forms of dyspnoea
}

# ── Drugs that require a specific ICD justification ──────────────────────────
DRUG_ICD_REQUIRED = {
    "cefuroxime":    ["J","K29.70","A","B96","L","N"],
    "daroxime":      ["J","K29.70","A","B96","L","N"],
    "amoxicillin":   ["J","K29.70","A","B96","L","N","H"],
    "clarithromycin":["J","K29.70","A","B96","L","K29.0"],
    "riack":         ["K29.70","K29.0","B96"],
    "metronidazole": ["K29.70","K29.0","B96","A06","N76"],
}

# ── Corticosteroid keywords (systemic vs inhaled) ─────────────────────────────
SYSTEMIC_STEROIDS = [
    "dexamethasone", "prednisolone", "respred", "prednisone",
    "hydrocortisone", "methylprednisolone", "solumedrol",
]
INHALED_STEROIDS = [
    "pulmicort", "budesonide", "fluticasone", "beclomethasone",
    "symbicort", "seretide", "flixotide",
]

# ── Asthma ICD sub-code → allowed drug severity mapping ──────────────────────
# Systemic corticosteroids (IV/IM/oral) are justified for J45.4 and J45.5 only
SYSTEMIC_STEROID_ASTHMA_CODES = {"J45.4", "J45.5", "J45.41", "J45.51"}

# ── Source codes that require GP referral code ────────────────────────────────
REQUIRES_REFERRAL_SRC = {"MG1002", "MG1003"}

# ── Infertility ICD codes that require the "infertility" checkbox ─────────────
INFERTILITY_ICD_CODES = {
    "N97.0",  # Female infertility — anovulation
    "N97.1",  # Female infertility — tubal origin
    "N97.2",  # Female infertility — uterine origin
    "N97.8",  # Female infertility — other specified
    "N97.9",  # Female infertility — unspecified
    "N46",    # Male infertility
    "N46.0",  # Azoospermia
    "N46.1",  # Oligospermia
    "Z31.0",  # Tuboplasty / sterilization reversal
    "Z31.4",  # Procreative investigation
}

# ── Fertility-related lab/service keywords ────────────────────────────────────
FERTILITY_LAB_KEYWORDS = [
    "fsh", "lh", "prolactin", "amh", "estradiol", "testosterone",
    "progesterone", "semen analysis", "hysteroscopy", "hsg",
    "follicle", "ovulation", "ivf", "iui",
]

# ── UCAF type rules ────────────────────────────────────────────────────────────
# UCAF-2 is for inpatient; UCAF-1 for outpatient
UCAF_PATIENT_RULES = {
    "UCAF-2": "inpatient",
    "UCAF-1": "outpatient",
}

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

    icd           = str(row.get("icd_code", "")).strip()
    icd2          = str(row.get("icd_code_2", "")).strip()
    cpt           = str(row.get("cpt_code", "")).strip()
    amount        = float(row.get("amount", 0))
    approval      = str(row.get("approval_no", "")).strip()
    drugs         = str(row.get("drugs", "")).lower()
    src_code      = str(row.get("source_code", "")).strip().upper()
    ucaf_type     = str(row.get("ucaf_type", "")).strip().upper()      # "UCAF-1" or "UCAF-2"
    patient_type  = str(row.get("patient_type", "")).strip().lower()   # "outpatient" / "inpatient"
    cb_infertility   = bool(row.get("cb_infertility", False))          # checkbox
    cb_pregnancy     = bool(row.get("cb_pregnancy", False))            # pregnancy/indicate checkbox
    chief_complaint  = str(row.get("chief_complaint", "")).lower()
    age           = int(row.get("age", 0))

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

    # ── Rule 9 — ICD code order: symptom before cause ────────────────────────
    if icd in SYMPTOM_CODES and icd2 and icd2 not in SYMPTOM_CODES:
        result.errors.append({
            "code":  "ERR-09",
            "level": "عالي",
            "msg":   f"ترتيب الأكواد مقلوب: العَرَض ({icd}) في الأول والتشخيص ({icd2}) في الثاني",
            "fix":   f"اجعل {icd2} هو الكود الأول و {icd} الكود الثاني",
        })

    # ── Rule 10 — Systemic corticosteroid without severe asthma ICD ──────────
    has_systemic = any(k in drugs for k in SYSTEMIC_STEROIDS)
    has_inhaled  = any(k in drugs for k in INHALED_STEROIDS)
    is_asthma    = icd.startswith("J45") or icd2.startswith("J45")
    asthma_code  = icd if icd.startswith("J45") else icd2

    if has_systemic and is_asthma and asthma_code not in SYSTEMIC_STEROID_ASTHMA_CODES:
        result.errors.append({
            "code":  "ERR-10",
            "level": "عالي",
            "msg":   f"كورتيزون جهازي (حقن/شراب) مع كود ربو ({asthma_code}) لا يبرره — يُقبل فقط مع J45.4 أو J45.5",
            "fix":   f"غيّر الكود إلى J45.5 (Severe persistent) إذا كانت الحالة حادة، أو احذف الكورتيزون الجهازي",
        })

    # ── Rule 11 — Duplicate / triple corticosteroids ─────────────────────────
    systemic_count = sum(1 for k in SYSTEMIC_STEROIDS if k in drugs)
    if has_systemic and has_inhaled and systemic_count >= 1:
        result.errors.append({
            "code":  "ERR-11",
            "level": "عالي",
            "msg":   "مضاعفة الكورتيزون: كورتيزون استنشاقي + كورتيزون جهازي في وصفة واحدة",
            "fix":   "راجع الطبيب — عادةً يُختار إما الاستنشاق أو الجهازي. اذكر المبرر السريري صراحةً في الملف",
        })
    if systemic_count >= 2:
        result.errors.append({
            "code":  "ERR-11B",
            "level": "عالي",
            "msg":   f"وصف {systemic_count} أنواع كورتيزون جهازي في نفس الوصفة (تكرار)",
            "fix":   "احتفظ بنوع واحد فقط وأزل الباقي أو وثّق المبرر الطبي",
        })

    # ── Rule 12 — Asthma drug linked to wrong asthma sub-code ────────────────
    # Dexamethasone / Pulmicort should match same J45.x variant
    drug_icd_col = str(row.get("drug_icd", "")).strip()   # per-line drug ICD if available
    if drug_icd_col and is_asthma and drug_icd_col != asthma_code:
        if drug_icd_col.startswith("J45") and asthma_code.startswith("J45"):
            result.errors.append({
                "code":  "ERR-12",
                "level": "متوسط",
                "msg":   f"كود التشخيص المربوط بالدواء ({drug_icd_col}) يختلف عن التشخيص الرئيسي ({asthma_code})",
                "fix":   f"وحّد الكود إلى {asthma_code} في جميع سطور الوصفة",
            })

    # ── Rule 13 — Infertility diagnosis without "infertility" checkbox ───────
    is_infertility_icd = icd in INFERTILITY_ICD_CODES or any(
        icd.startswith(c) for c in ["N97", "N46", "Z31"]
    )
    if is_infertility_icd and not cb_infertility:
        result.errors.append({
            "code":  "ERR-13",
            "level": "عالي",
            "msg":   f"تشخيص العقم ({icd}) بدون تفعيل مربع «infertility» في النموذج",
            "fix":   "فعّل مربع الاختيار «infertility» في صفحة اليوكاف — هذا شرط إلزامي لشركات التأمين",
        })

    # ── Rule 14 — Fertility labs without infertility checkbox ────────────────
    has_fertility_lab = any(k in drugs for k in FERTILITY_LAB_KEYWORDS)
    if has_fertility_lab and not cb_infertility:
        result.errors.append({
            "code":  "ERR-14",
            "level": "عالي",
            "msg":   "تحاليل خصوبة (FSH/Prolactin/LH/AMH) بدون تفعيل مربع «infertility»",
            "fix":   "فعّل مربع «infertility» وتأكد من وجود تشخيص N97.x أو N46.x",
        })

    # ── Rule 15 — "pregnancy/indicate" missing for conception cases ──────────
    wants_conception = any(k in chief_complaint for k in [
        "conceive", "pregnancy", "ivf", "iui", "infertil", "nullipara",
    ])
    if wants_conception and not cb_pregnancy:
        result.errors.append({
            "code":  "ERR-15",
            "level": "متوسط",
            "msg":   "الشكوى تذكر الرغبة في الحمل لكن مربع «pregnancy/indicate» غير مُفعَّل",
            "fix":   "فعّل مربع «pregnancy/indicate» لتبرير تحاليل الخصوبة",
        })

    # ── Rule 16 — UCAF-2 used for outpatient visit ───────────────────────────
    if ucaf_type == "UCAF-2" and patient_type == "outpatient":
        result.errors.append({
            "code":  "ERR-16",
            "level": "عالي",
            "msg":   "نموذج UCAF-2 مستخدم مع حالة خارجية (Outpatient) — UCAF-2 مخصص للمنوم",
            "fix":   "استخدم UCAF-1 للحالات الخارجية أو تأكد من صحة نوع المريض",
        })

    # ── Rule 17 — Advanced maternal age infertility note ─────────────────────
    if is_infertility_icd and age >= 40:
        result.errors.append({
            "code":  "ERR-17",
            "level": "متوسط",
            "msg":   f"المريضة عمرها {age} سنة — بعض شركات التأمين تشترط موافقة مسبقة لعلاج العقم فوق 40 سنة",
            "fix":   "تأكد من وجود رقم موافقة مسبقة (Prior Auth) خاص بحالات العقم لهذا العمر",
        })

    # ── Rule 19 — H. pylori drug without H. pylori ICD (extended check) ──────
    # Already ERR-07 handles primary ICD; this catches when K29.7 is 2nd code
    pylori_drugs_list = ["riack", "clarithromycin"]
    has_pylori_drug   = any(d in drugs for d in pylori_drugs_list)
    all_icds          = " ".join([icd, icd2, str(row.get("icd_code_3",""))])
    has_pylori_icd    = any(c in all_icds for c in ["K29.70","K29.0","B96"])
    if has_pylori_drug and not has_pylori_icd:
        # Only add if ERR-07 was not already added
        if not any(e["code"] == "ERR-07" for e in result.errors):
            result.errors.append({
                "code":  "ERR-07",
                "level": "عالي",
                "msg":   "وصف دواء علاج H. pylori بدون كود K29.70 أو B96.81 في أي خانة",
                "fix":   "أضف K29.70 في خانة التشخيص الثاني إذا كان التهاب المعدة بسبب H. pylori",
            })

    return result


def analyze_dataframe(df):
    """Return list of ClaimCheck for every row in df."""
    return [analyze(row) for row in df.to_dict("records")]


# ─────────────────────────────────────────────────────────────────────────────
# Quick test
if __name__ == "__main__":
    cases = [
        # Case 1 — Gastritis screenshot (R11 as primary, H.pylori drug, antibiotic)
        {
            "claim_id": "CASE1-GASTRITIS",
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
        # Case 2 — Asthma + Gastritis screenshot (triple corticosteroid, J45.9 + K29.7)
        {
            "claim_id": "CASE2-ASTHMA",
            "patient_id": "P789012",
            "icd_code": "J45.9",
            "icd_code_2": "K29.7",
            "cpt_code": "99213",
            "amount": 200.9,
            "approval_no": "",
            "service_date": "2025-06-02",
            "patient_signed": True,
            "drugs": "pulmicort|dexamethasone|respred|riack plus|gp general practitioner",
            "drug_icd": "J45.5",
        },
        # Case 3 — Infertility screenshot (N97.0, FSH+Prolactin, infertility CB missing)
        {
            "claim_id":       "CASE3-INFERTILITY",
            "patient_id":     "P3918",
            "icd_code":       "N97.0",
            "icd_code_2":     "",
            "cpt_code":       "99213",
            "amount":         450,
            "approval_no":    "2026/2398109",
            "service_date":   "2026-03-08",
            "patient_signed": True,
            "drugs":          "specialist|prolactin h|fsh",
            "ucaf_type":      "UCAF-2",
            "patient_type":   "outpatient",
            "cb_infertility": False,
            "cb_pregnancy":   False,
            "chief_complaint":"nullipara old age 41y irregular cycle wants to conceive",
            "age":            41,
        },
        {
            "claim_id": "CASE4-CLEAN",
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
