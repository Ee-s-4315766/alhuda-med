"""
قواعد شركات التأمين السعودية — Insurance Company Rules Engine
كل شركة لها حدود وشروط مختلفة يجب مراعاتها.
"""

# ─────────────────────────────────────────────────────────────────────────────
# Per-company configuration
# ─────────────────────────────────────────────────────────────────────────────
INSURANCE_COMPANIES = {
    "MEDGULF": {
        "name_ar":            "ميدغلف",
        "approval_limit":     1000,    # SAR per visit before needing prior auth
        "max_per_visit":      5000,
        "copay_pct":          20,
        "infertility_covered": True,
        "infertility_age_limit": 45,
        "chronic_requires_cb": True,
        "requires_referral_for_specialist": True,
        "excluded_icd": [],
        "excluded_cpt": ["99397"],     # no preventive for 65+ in some plans
        "extra_rules": [
            "موافقة مسبقة لكل جراحة بغض النظر عن المبلغ",
            "تقرير طبي مطلوب للإجراءات فوق 2000 ر.س",
        ],
    },
    "BUPA": {
        "name_ar":            "بوبا العربية",
        "approval_limit":     2000,
        "max_per_visit":      8000,
        "copay_pct":          15,
        "infertility_covered": True,
        "infertility_age_limit": 40,
        "chronic_requires_cb": True,
        "requires_referral_for_specialist": False,
        "excluded_icd": ["Z00.00","Z00.01"],  # no routine check-up in some plans
        "excluded_cpt": [],
        "extra_rules": [
            "مركز الخصوبة معتمد مطلوب لحالات N97.x",
            "موافقة مسبقة للعمليات والمناظير",
            "تاريخ انتهاء الصلاحية يُتحقق تلقائياً",
        ],
    },
    "TAWUNIYA": {
        "name_ar":            "التعاونية",
        "approval_limit":     1500,
        "max_per_visit":      6000,
        "copay_pct":          20,
        "infertility_covered": False,   # not covered in standard plan
        "infertility_age_limit": None,
        "chronic_requires_cb": True,
        "requires_referral_for_specialist": True,
        "excluded_icd": ["N97.0","N97.1","N46","Z31.4"],  # infertility excluded
        "excluded_cpt": ["58150","90837","90834"],
        "extra_rules": [
            "العقم غير مشمول في الخطة الأساسية — تحقق من الملحق",
            "موافقة مسبقة لكل تحليل فوق 500 ر.س",
            "الأمراض النفسية تشترط إحالة من طبيب الأسرة",
        ],
    },
    "AXA": {
        "name_ar":            "أكسا التعاونية",
        "approval_limit":     2000,
        "max_per_visit":      7000,
        "copay_pct":          10,
        "infertility_covered": True,
        "infertility_age_limit": 42,
        "chronic_requires_cb": True,
        "requires_referral_for_specialist": False,
        "excluded_icd": [],
        "excluded_cpt": [],
        "extra_rules": [
            "نسبة التحمل 10% لكل زيارة",
            "الرعاية المنزلية مشمولة بموافقة مسبقة",
        ],
    },
    "MALATH": {
        "name_ar":            "ملاذ للتأمين",
        "approval_limit":     1000,
        "max_per_visit":      4000,
        "copay_pct":          25,
        "infertility_covered": False,
        "infertility_age_limit": None,
        "chronic_requires_cb": True,
        "requires_referral_for_specialist": True,
        "excluded_icd": ["N97.0","N97.1","N46","F32.9","F41.1"],
        "excluded_cpt": ["90837","90834","58150"],
        "extra_rules": [
            "موافقة مسبقة لكل إجراء فوق 1000 ر.س",
            "الأمراض النفسية غير مشمولة في الخطة الأساسية",
            "تقرير مرفق إلزامي لحالات الطوارئ",
        ],
    },
    "SAICO": {
        "name_ar":            "الشركة العربية السعودية للتأمين",
        "approval_limit":     800,
        "max_per_visit":      3000,
        "copay_pct":          20,
        "infertility_covered": True,
        "infertility_age_limit": 43,
        "chronic_requires_cb": True,
        "requires_referral_for_specialist": True,
        "excluded_icd": [],
        "excluded_cpt": [],
        "extra_rules": [
            "موافقة مسبقة للأشعة المقطعية والرنين المغناطيسي",
        ],
    },
}

# ─────────────────────────────────────────────────────────────────────────────
def check_company_rules(row: dict, company_key: str) -> list[dict]:
    """
    Return list of company-specific errors for a claim row.
    Each error: {code, level, msg, fix}
    """
    company = INSURANCE_COMPANIES.get(company_key)
    if not company:
        return []

    errors = []
    icd     = str(row.get("icd_code","")).strip()
    cpt     = str(row.get("cpt_code","")).strip()
    amount  = float(row.get("amount", 0))
    approval= str(row.get("approval_no","")).strip()
    age     = int(row.get("age", 0))
    cb_infertility = bool(row.get("cb_infertility", False))

    # Rule C1 — Amount exceeds company approval limit
    if amount > company["approval_limit"] and not approval:
        errors.append({
            "code":  "ERR-C01",
            "level": "عالي",
            "msg":   f"[{company['name_ar']}] المبلغ {amount:,.0f} ر.س يتجاوز حد الموافقة "
                     f"({company['approval_limit']:,} ر.س) — مطلوب Prior Auth",
            "fix":   f"أحضر رقم موافقة من {company['name_ar']} قبل الإرسال",
        })

    # Rule C2 — Amount exceeds max per visit
    if amount > company["max_per_visit"]:
        errors.append({
            "code":  "ERR-C02",
            "level": "عالي",
            "msg":   f"[{company['name_ar']}] المبلغ {amount:,.0f} ر.س يتجاوز الحد الأقصى "
                     f"للزيارة ({company['max_per_visit']:,} ر.س)",
            "fix":   "تقسيم الفاتورة أو الحصول على موافقة استثنائية مسبقاً",
        })

    # Rule C3 — Excluded ICD
    if icd in company["excluded_icd"]:
        errors.append({
            "code":  "ERR-C03",
            "level": "عالي",
            "msg":   f"[{company['name_ar']}] كود {icd} غير مشمول في هذه الخطة التأمينية",
            "fix":   f"راجع بوليصة المريض — قد يحتاج خطة مختلفة أو دفع ذاتي",
        })

    # Rule C4 — Excluded CPT
    if cpt in company["excluded_cpt"]:
        errors.append({
            "code":  "ERR-C04",
            "level": "عالي",
            "msg":   f"[{company['name_ar']}] خدمة CPT {cpt} مستثناة من التغطية",
            "fix":   "أبلغ المريض بعدم التغطية قبل تقديم الخدمة",
        })

    # Rule C5 — Infertility age limit
    if icd.startswith("N97") and cb_infertility:
        if not company["infertility_covered"]:
            errors.append({
                "code":  "ERR-C05",
                "level": "عالي",
                "msg":   f"[{company['name_ar']}] العقم غير مشمول في هذه الخطة",
                "fix":   "أبلغ المريض — قد تكون هناك إضافة اختيارية لتغطية الخصوبة",
            })
        elif company["infertility_age_limit"] and age > company["infertility_age_limit"]:
            errors.append({
                "code":  "ERR-C06",
                "level": "عالي",
                "msg":   f"[{company['name_ar']}] المريضة ({age} سنة) تجاوزت الحد العمري "
                         f"لتغطية العقم ({company['infertility_age_limit']} سنة)",
                "fix":   "التغطية محدودة — تحقق من الملحق أو اطلب موافقة استثنائية",
            })

    return errors


def get_company_summary(company_key: str) -> dict:
    return INSURANCE_COMPANIES.get(company_key, {})


def all_company_names() -> list[str]:
    return list(INSURANCE_COMPANIES.keys())
