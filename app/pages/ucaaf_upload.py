"""UCAAF Entry Form & Error Analyzer — إدخال بيانات اليوكاف وفحص الأخطاء فوراً"""
import json
import streamlit as st
import pandas as pd
from pathlib import Path
from app.ucaaf_analyzer import analyze
from app.components import alert_box

DOCTORS_PATH = Path(__file__).parent.parent.parent / "data" / "doctors.json"

SEVERITY_COLOR = {"عالي": "#ef4444", "متوسط": "#f59e0b", "منخفض": "#22c55e"}
SEVERITY_ICON  = {"عالي": "🔴",       "متوسط": "🟡",       "منخفض": "🟢"}


def _load_doctors():
    if DOCTORS_PATH.exists():
        return json.loads(DOCTORS_PATH.read_text(encoding="utf-8"))
    return []


def render(_df, user):
    st.markdown("## 🔍 فحص مطالبة يوكاف — UCAAF Checker")
    st.caption("أدخل بيانات الحالة لفحص الأخطاء فوراً قبل الإرسال للتأمين")
    st.divider()

    doctors = _load_doctors()
    doc_options = [f"{d['id']} — {d['name']}" for d in doctors]

    # ── Form ──────────────────────────────────────────────────────────
    with st.form("ucaaf_checker", clear_on_submit=False):
        st.markdown("### 👤 بيانات المريض والطبيب")
        r1c1, r1c2, r1c3 = st.columns(3)
        with r1c1:
            patient_name = st.text_input("اسم المريض")
            patient_id   = st.text_input("الرقم الطبي للمريض")
        with r1c2:
            patient_age  = st.number_input("العمر (سنة)", min_value=0, max_value=120, value=30)
            gender       = st.selectbox("الجنس", ["ذكر", "أنثى"])
        with r1c3:
            service_dt   = st.date_input("تاريخ الخدمة")
            if doc_options:
                doc_sel  = st.selectbox("الطبيب المعالج", doc_options)
            else:
                doc_sel  = st.text_input("الطبيب المعالج")

        st.divider()
        st.markdown("### 📋 بيانات اليوكاف")
        r2c1, r2c2, r2c3 = st.columns(3)
        with r2c1:
            ucaf_type    = st.selectbox("نوع اليوكاف", ["UCAF-1 (خارجي)", "UCAF-2 (داخلي)"])
            patient_type = st.selectbox("نوع المريض", ["خارجي (outpatient)", "داخلي (inpatient)"])
        with r2c2:
            icd_primary  = st.text_input("كود التشخيص الرئيسي ICD-10 *", placeholder="مثال: K29.70")
            icd_second   = st.text_input("كود التشخيص الثانوي (اختياري)", placeholder="مثال: R11")
        with r2c3:
            cpt          = st.text_input("كود الإجراء CPT *", placeholder="مثال: 99213")
            amount       = st.number_input("المبلغ المطالب به (ر.س) *", min_value=0.0, step=50.0)

        st.divider()
        st.markdown("### 💊 الأدوية والخدمات")
        drugs_raw = st.text_area(
            "اكتب الأدوية والخدمات (افصل بعلامة |)",
            placeholder="مثال: riack plus|pantozol|paracetamol",
            height=80,
        )
        chief_c = st.text_input(
            "الشكوى الرئيسية (Chief Complaint)",
            placeholder="مثال: ألم شرسوفي | رغبة في الإنجاب | صعوبة التنفس"
        )

        st.divider()
        st.markdown("### ✅ المربعات الإلزامية والموافقات")
        r4c1, r4c2, r4c3 = st.columns(3)
        with r4c1:
            signed    = st.checkbox("✔ المريض وقّع نموذج الموافقة", value=True)
        with r4c2:
            cb_infert = st.checkbox("☑ تفعيل مربع «infertility»", value=False)
            cb_preg   = st.checkbox("☑ تفعيل مربع «pregnancy/indicate»", value=False)
        with r4c3:
            approval  = st.text_input("رقم الموافقة المسبقة (Prior Auth)", placeholder="APP-XXXXX")

        st.divider()
        submitted = st.form_submit_button(
            "⚡ فحص الأخطاء الآن",
            use_container_width=True,
            type="primary",
        )

    # ── Results ───────────────────────────────────────────────────────
    if submitted:
        if not icd_primary.strip():
            st.error("⚠️ يرجى إدخال كود التشخيص الرئيسي ICD-10")
            return
        if not cpt.strip():
            st.error("⚠️ يرجى إدخال كود الإجراء CPT")
            return

        ucaf_val  = "UCAF-1" if "1" in ucaf_type else "UCAF-2"
        ptype_val = "outpatient" if "خارجي" in patient_type else "inpatient"

        row = {
            "claim_id":        f"CHECK-{patient_id or 'XXX'}",
            "patient_id":      patient_id.strip(),
            "patient_name":    patient_name.strip(),
            "age":             int(patient_age),
            "gender":          gender,
            "icd_code":        icd_primary.strip().upper(),
            "icd_code_2":      icd_second.strip().upper(),
            "cpt_code":        cpt.strip(),
            "amount":          float(amount),
            "approval_no":     approval.strip(),
            "service_date":    str(service_dt),
            "patient_signed":  signed,
            "drugs":           drugs_raw.strip().lower(),
            "ucaf_type":       ucaf_val,
            "patient_type":    ptype_val,
            "cb_infertility":  cb_infert,
            "cb_pregnancy":    cb_preg,
            "chief_complaint": chief_c.strip().lower(),
        }

        result = analyze(row)
        st.divider()

        if not result.has_errors:
            st.success("✅ المطالبة سليمة — لا توجد أخطاء، جاهزة للإرسال")
            st.balloons()
        else:
            high = [e for e in result.errors if e["level"] == "عالي"]
            mid  = [e for e in result.errors if e["level"] != "عالي"]

            st.error(
                f"⚠️ تم اكتشاف **{len(result.errors)} خطأ** "
                f"({len(high)} عالي الخطورة، {len(mid)} متوسط)"
            )

            # Summary bar
            st.markdown(
                f"""
                <div style="background:#1e293b;border-radius:10px;padding:14px 20px;
                            margin-bottom:16px;display:flex;gap:24px;flex-wrap:wrap">
                  <div><span style="color:#94a3b8;font-size:12px">المريض</span>
                       <div style="color:#f1f5f9;font-weight:700">{patient_name or '—'}</div></div>
                  <div><span style="color:#94a3b8;font-size:12px">ICD</span>
                       <div style="color:#f1f5f9;font-weight:700">{icd_primary.upper()}</div></div>
                  <div><span style="color:#94a3b8;font-size:12px">CPT</span>
                       <div style="color:#f1f5f9;font-weight:700">{cpt}</div></div>
                  <div><span style="color:#94a3b8;font-size:12px">المبلغ</span>
                       <div style="color:#ef4444;font-weight:700">{amount:,.0f} ر.س</div></div>
                  <div><span style="color:#94a3b8;font-size:12px">الخطورة الإجمالية</span>
                       <div style="color:{'#ef4444' if result.severity=='عالي' else '#f59e0b'};font-weight:700">
                         {result.severity}</div></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Error cards
            st.markdown("### الأخطاء المكتشفة والحلول")
            for e in result.errors:
                color = SEVERITY_COLOR.get(e["level"], "#f59e0b")
                icon  = SEVERITY_ICON.get(e["level"], "🟡")
                st.markdown(
                    f"""
                    <div style="background:#1e293b;border-radius:10px;padding:16px 20px;
                                border-left:4px solid {color};margin:8px 0">
                      <div style="display:flex;justify-content:space-between;align-items:center">
                        <span style="background:{color};color:white;border-radius:4px;
                                     padding:2px 8px;font-size:11px">{icon} {e['level']}</span>
                        <span style="color:#64748b;font-size:12px">{e['code']}</span>
                      </div>
                      <div style="color:#f1f5f9;font-size:14px;font-weight:600;margin-top:8px">
                        {e['msg']}
                      </div>
                      <div style="color:#22c55e;font-size:13px;margin-top:6px">
                        ✅ الحل: {e.get('fix', '')}
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
