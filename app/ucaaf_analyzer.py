"""UCAAF Error Analyzer — rule-based engine."""
from dataclasses import dataclass, field
from typing import List

# Valid ICD → CPT mappings
ICD_CPT_VALID = {
    "J18.9":  ["99213","99214","71046"],
    "E11.9":  ["99213","99214","80047","83036"],
    "I10":    ["99213","99214","93000"],
    "K21.0":  ["99213","43239"],
    "M54.5":  ["99213","72148","97110"],
    "Z00.00": ["99395","99396","99397"],
}

FINANCIAL_LIMIT = 5000  # SAR — requires prior auth above this

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
        highs = [e for e in self.errors if e["level"] == "عالي"]
        return "عالي" if highs else "متوسط"


def analyze(row: dict) -> ClaimCheck:
    """Run all UCAAF rules against a single claim dict."""
    result = ClaimCheck(claim_id=row.get("claim_id", "?"))

    # Rule 1 – ICD / CPT mismatch
    icd = str(row.get("icd_code", "")).strip()
    cpt = str(row.get("cpt_code", "")).strip()
    if icd in ICD_CPT_VALID and cpt not in ICD_CPT_VALID[icd]:
        result.errors.append({
            "code":  "ERR-01",
            "level": "عالي",
            "msg":   f"عدم تطابق التشخيص ({icd}) مع الإجراء ({cpt})",
        })

    # Rule 2 – Missing approval number
    amount = float(row.get("amount", 0))
    approval = str(row.get("approval_no", "")).strip()
    if amount > FINANCIAL_LIMIT and not approval:
        result.errors.append({
            "code":  "ERR-02",
            "level": "عالي",
            "msg":   f"تجاوز الحد المالي ({amount:,.0f} ر.س) دون رقم موافقة مسبقة",
        })
    if not approval and amount <= FINANCIAL_LIMIT:
        result.errors.append({
            "code":  "ERR-02B",
            "level": "متوسط",
            "msg":   "رقم الموافقة مفقود",
        })

    # Rule 3 – Missing patient signature flag
    if not row.get("patient_signed", True):
        result.errors.append({
            "code":  "ERR-03",
            "level": "عالي",
            "msg":   "توقيع المريض مفقود في نموذج اليوكاف",
        })

    # Rule 4 – Missing service date
    if not row.get("service_date", "").strip():
        result.errors.append({
            "code":  "ERR-04",
            "level": "متوسط",
            "msg":   "تاريخ الخدمة مفقود",
        })

    # Rule 5 – Missing patient medical ID
    if not str(row.get("patient_id", "")).strip():
        result.errors.append({
            "code":  "ERR-05",
            "level": "عالي",
            "msg":   "الرقم الطبي للمريض مفقود",
        })

    return result


def analyze_dataframe(df):
    """Return list of ClaimCheck for every row in df."""
    return [analyze(row) for row in df.to_dict("records")]
