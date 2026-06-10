"""UCAAF & DCAF Entry Forms — إدخال بيانات اليوكاف/ديكاف وفحص الأخطاء فوراً"""
import json
import base64
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


DCAF_PROCEDURES = {
    "D0120": "فحص دوري",
    "D0140": "فحص محدود",
    "D0210": "أشعة بانورامية كاملة",
    "D0220": "أشعة فردية (Periapical)",
    "D0230": "أشعة إضافية (Bitewing)",
    "D1110": "تنظيف الأسنان (Prophylaxis) — بالغ",
    "D1120": "تنظيف الأسنان — طفل",
    "D1206": "فلورايد موضعي",
    "D2140": "حشو أمالغم — سطح واحد",
    "D2150": "حشو أمالغم — سطحان",
    "D2160": "حشو أمالغم — ثلاثة أسطح",
    "D2330": "حشو كمبوزيت — سطح أمامي",
    "D2391": "حشو كمبوزيت — خلفي سطح واحد",
    "D2392": "حشو كمبوزيت — خلفي سطحان",
    "D2393": "حشو كمبوزيت — خلفي ثلاثة أسطح",
    "D2750": "تاج خزفي على معدن",
    "D2930": "تاج جاهز — أمامي",
    "D2931": "تاج جاهز — خلفي (ستانلس)",
    "D3310": "علاج عصب أحادي القناة — أمامي",
    "D3320": "علاج عصب ثنائي القناة — ضاحك",
    "D3330": "علاج عصب ثلاثي القناة — طاحن",
    "D4341": "كحت وتجريف — ربع الفم",
    "D4910": "صيانة دورية بعد علاج اللثة",
    "D5110": "طقم كامل — فك علوي",
    "D5120": "طقم كامل — فك سفلي",
    "D6010": "غرسة سنية (Implant)",
    "D7140": "قلع بسيط",
    "D7210": "قلع جراحي",
    "D7240": "قلع ضرس العقل الجراحي",
    "D9910": "تطبيق فلورايد علاجي",
}

TOOTH_NUMBERS = (
    ["FMX","PANO","BW"] +
    [f"UR{i}" for i in range(1,9)] +
    [f"UL{i}" for i in range(1,9)] +
    [f"LR{i}" for i in range(1,9)] +
    [f"LL{i}" for i in range(1,9)] +
    [f"55","54","53","52","51","61","62","63","64","65",
     "85","84","83","82","81","71","72","73","74","75"]
)


def _dcaf_tab(doctors):
    st.markdown("### 🦷 إدخال مطالبة DCAF — أسنان")
    st.caption("نموذج خاص بطبيب الأسنان — يفحص الإجراء ورقم السن والموافقات")

    doc_options = [f"{d['id']} — {d['name']}" for d in doctors
                   if "أسنان" in d.get("specialty", "")]
    if not doc_options:
        doc_options = [f"{d['id']} — {d['name']}" for d in doctors]

    with st.form("dcaf_form", clear_on_submit=False):
        st.markdown("#### بيانات المريض")
        c1, c2, c3 = st.columns(3)
        with c1:
            patient_name = st.text_input("اسم المريض")
            patient_id   = st.text_input("الرقم الطبي")
        with c2:
            patient_age  = st.number_input("العمر", min_value=0, max_value=120, value=25)
            gender       = st.selectbox("الجنس", ["ذكر", "أنثى"])
        with c3:
            service_dt   = st.date_input("تاريخ الخدمة")
            doc_sel      = st.selectbox("طبيب الأسنان", doc_options) if doc_options else st.text_input("الطبيب")

        st.divider()
        st.markdown("#### إجراءات الأسنان")
        st.caption("يمكن إضافة حتى 4 إجراءات في نفس الجلسة")

        proc_rows = []
        for i in range(1, 5):
            ca, cb, cc, cd = st.columns([2, 2, 1, 1])
            with ca:
                code = st.selectbox(
                    f"الإجراء {i}",
                    ["—"] + list(DCAF_PROCEDURES.keys()),
                    format_func=lambda x: f"{x} — {DCAF_PROCEDURES.get(x,'')}" if x != "—" else "—",
                    key=f"proc_{i}",
                )
            with cb:
                tooth = st.selectbox(f"رقم/موقع السن {i}", ["—"] + TOOTH_NUMBERS, key=f"tooth_{i}")
            with cc:
                qty   = st.number_input(f"الكمية {i}", min_value=0, max_value=10, value=0 if i > 1 else 1, key=f"qty_{i}")
            with cd:
                fee   = st.number_input(f"الرسوم {i} ر.س", min_value=0.0, step=10.0, key=f"fee_{i}")
            if code != "—" and qty > 0:
                proc_rows.append({"code": code, "tooth": tooth, "qty": qty, "fee": fee})

        st.divider()
        st.markdown("#### الموافقة والدفع")
        d1, d2, d3 = st.columns(3)
        with d1:
            insurance_co = st.selectbox("شركة التأمين", [
                "بوبا العربية", "أكسا التعاونية", "ملاذ للتأمين",
                "الشركة العربية السعودية للتأمين", "أخرى"
            ])
            approval_no  = st.text_input("رقم الموافقة المسبقة")
        with d2:
            total_amount = sum(r["fee"] for r in proc_rows) if proc_rows else st.number_input("المبلغ الإجمالي ر.س", min_value=0.0, step=10.0)
            signed       = st.checkbox("المريض وقّع الموافقة", value=True)
        with d3:
            xray_taken   = st.checkbox("تم أخذ أشعة سينية", value=False)
            notes        = st.text_area("ملاحظات سريرية", height=68)

        st.divider()
        submitted = st.form_submit_button("⚡ فحص المطالبة الآن", use_container_width=True, type="primary")

    if submitted:
        errors = []

        # Rule D1: No procedures selected
        if not proc_rows:
            st.error("⚠️ يرجى اختيار إجراء واحد على الأقل")
            return

        total_fee = sum(r["fee"] for r in proc_rows)

        # Rule D2: Procedures needing X-ray
        xray_needed = {"D2750","D3310","D3320","D3330","D6010","D7210","D7240"}
        for p in proc_rows:
            if p["code"] in xray_needed and not xray_taken:
                errors.append({
                    "level": "عالي",
                    "code":  "DCAF-01",
                    "msg":   f"الإجراء {p['code']} ({DCAF_PROCEDURES[p['code']]}) يستلزم أشعة سينية موثّقة",
                    "fix":   "فعّل خانة «تم أخذ أشعة سينية» أو أضف كود الأشعة (D0220/D0210)",
                })

        # Rule D3: Crown needs prior auth
        crown_codes = {"D2750","D2930","D2931","D5110","D5120","D6010"}
        for p in proc_rows:
            if p["code"] in crown_codes and not approval_no.strip():
                errors.append({
                    "level": "عالي",
                    "code":  "DCAF-02",
                    "msg":   f"الإجراء {p['code']} ({DCAF_PROCEDURES[p['code']]}) يتطلب موافقة مسبقة",
                    "fix":   "احصل على Prior Authorization من شركة التأمين قبل تنفيذ الإجراء",
                })

        # Rule D4: Implant not covered by most plans
        for p in proc_rows:
            if p["code"] == "D6010":
                errors.append({
                    "level": "متوسط",
                    "code":  "DCAF-03",
                    "msg":   "الغرسة السنية (D6010) غير مشمولة في أغلب خطط التأمين الأساسية",
                    "fix":   "تحقق من بوليصة المريض — قد تكون ملحق إضافي أو دفع ذاتي",
                })

        # Rule D5: Tooth number missing for restorative
        restorative = {"D2140","D2150","D2160","D2330","D2391","D2392","D2393","D2750","D3310","D3320","D3330","D7140","D7210","D7240"}
        for p in proc_rows:
            if p["code"] in restorative and p["tooth"] == "—":
                errors.append({
                    "level": "عالي",
                    "code":  "DCAF-04",
                    "msg":   f"الإجراء {p['code']} يتطلب تحديد رقم السن",
                    "fix":   "اختر رقم السن أو منطقة الفم المعالجة",
                })

        # Rule D6: Amount > 1000 SAR without approval (BUPA)
        if total_fee > 1000 and not approval_no.strip() and "بوبا" in insurance_co:
            errors.append({
                "level": "عالي",
                "code":  "DCAF-05",
                "msg":   f"المبلغ {total_fee:,.0f} ر.س يتجاوز حد بوبا العربية (1000 ر.س) بدون موافقة",
                "fix":   "احصل على Prior Auth من بوبا قبل الإرسال",
            })

        # Rule D7: Patient signature
        if not signed:
            errors.append({
                "level": "متوسط",
                "code":  "DCAF-06",
                "msg":   "المريض لم يوقّع نموذج الموافقة",
                "fix":   "احصل على توقيع المريض قبل إرسال المطالبة",
            })

        st.divider()

        # Summary box
        st.markdown(
            f"""
            <div style="background:#1e293b;border-radius:10px;padding:14px 20px;margin-bottom:16px">
              <div style="color:#6366f1;font-size:1rem;font-weight:700;margin-bottom:8px">
                🦷 ملخص المطالبة — {patient_name or 'مريض'}
              </div>
              <div style="display:flex;gap:20px;flex-wrap:wrap;color:#94a3b8;font-size:13px">
                <span>📅 {service_dt}</span>
                <span>👤 العمر: {patient_age}</span>
                <span>🏢 {insurance_co}</span>
                <span>💰 المبلغ الإجمالي: <b style="color:#f1f5f9">{total_fee:,.0f} ر.س</b></span>
              </div>
              <div style="margin-top:10px;color:#f1f5f9;font-size:13px">
                {"".join(f"<div>• {DCAF_PROCEDURES.get(p['code'],'')} ({p['code']}) — سن {p['tooth']} — {p['fee']:,.0f} ر.س</div>" for p in proc_rows)}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if not errors:
            st.success("✅ مطالبة الأسنان سليمة — لا توجد أخطاء، جاهزة للإرسال")
            st.balloons()
        else:
            st.error(f"⚠️ تم اكتشاف {len(errors)} ملاحظة")
            for e in errors:
                color = "#ef4444" if e["level"] == "عالي" else "#f59e0b"
                icon  = "🔴" if e["level"] == "عالي" else "🟡"
                st.markdown(
                    f"""
                    <div style="background:#1e293b;border-radius:10px;padding:14px 18px;
                                border-left:4px solid {color};margin:6px 0">
                      <div style="display:flex;justify-content:space-between">
                        <span style="background:{color};color:white;border-radius:4px;
                                     padding:2px 7px;font-size:11px">{icon} {e['level']}</span>
                        <span style="color:#64748b;font-size:12px">{e['code']}</span>
                      </div>
                      <div style="color:#f1f5f9;font-size:14px;font-weight:600;margin-top:8px">{e['msg']}</div>
                      <div style="color:#22c55e;font-size:13px;margin-top:5px">✅ الحل: {e['fix']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def _ucaaf_pdf_html(row: dict, errors: list, clinic_name: str = "عيادة الهدى الطبية") -> str:
    err_rows = "".join(
        f"<tr><td>{e['code']}</td><td>{e['level']}</td><td>{e['msg']}</td><td>{e.get('fix','')}</td></tr>"
        for e in errors
    )
    status_color = "#dc2626" if errors else "#16a34a"
    status_text  = f"⚠️ {len(errors)} خطأ مكتشف" if errors else "✅ سليمة — جاهزة للإرسال"
    return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<style>
  body {{ font-family: Arial, sans-serif; margin: 20px; color: #111; font-size: 13px; }}
  h1 {{ text-align: center; font-size: 18px; border-bottom: 2px solid #6366f1; padding-bottom: 8px; }}
  .clinic {{ text-align: center; color: #555; margin-bottom: 16px; }}
  .status {{ background: {status_color}; color: white; padding: 8px 16px;
             border-radius: 6px; text-align: center; font-weight: bold; margin: 12px 0; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
  th {{ background: #6366f1; color: white; padding: 7px; text-align: right; }}
  td {{ padding: 6px; border: 1px solid #ddd; }}
  tr:nth-child(even) {{ background: #f8f8f8; }}
  .section {{ background: #f1f5f9; padding: 10px; border-radius: 6px; margin: 10px 0; }}
  .section h3 {{ margin: 0 0 8px 0; color: #6366f1; font-size: 14px; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }}
  .field {{ display: flex; gap: 8px; }}
  .label {{ color: #555; min-width: 140px; }}
  .value {{ font-weight: bold; }}
  @media print {{ button {{ display: none; }} }}
</style>
</head>
<body>
<h1>🏥 تقرير فحص مطالبة اليوكاف</h1>
<div class="clinic">{clinic_name}</div>
<div class="status">{status_text}</div>

<div class="section">
  <h3>👤 بيانات المريض</h3>
  <div class="grid">
    <div class="field"><span class="label">الاسم:</span> <span class="value">{row.get('patient_name','—')}</span></div>
    <div class="field"><span class="label">الرقم الطبي:</span> <span class="value">{row.get('patient_id','—')}</span></div>
    <div class="field"><span class="label">العمر:</span> <span class="value">{row.get('age','—')} سنة</span></div>
    <div class="field"><span class="label">الجنس:</span> <span class="value">{row.get('gender','—')}</span></div>
    <div class="field"><span class="label">تاريخ الخدمة:</span> <span class="value">{row.get('service_date','—')}</span></div>
    <div class="field"><span class="label">نوع اليوكاف:</span> <span class="value">{row.get('ucaf_type','—')}</span></div>
  </div>
</div>

<div class="section">
  <h3>📋 بيانات الترميز</h3>
  <div class="grid">
    <div class="field"><span class="label">ICD الرئيسي:</span> <span class="value">{row.get('icd_code','—')}</span></div>
    <div class="field"><span class="label">ICD الثانوي:</span> <span class="value">{row.get('icd_code_2','—') or '—'}</span></div>
    <div class="field"><span class="label">كود CPT:</span> <span class="value">{row.get('cpt_code','—')}</span></div>
    <div class="field"><span class="label">المبلغ:</span> <span class="value">{float(row.get('amount',0)):,.0f} ر.س</span></div>
    <div class="field"><span class="label">رقم الموافقة:</span> <span class="value">{row.get('approval_no','—') or '—'}</span></div>
    <div class="field"><span class="label">الأدوية:</span> <span class="value">{row.get('drugs','—')}</span></div>
  </div>
</div>

{"<div class='section'><h3>⚠️ الأخطاء المكتشفة</h3><table><tr><th>الكود</th><th>الخطورة</th><th>الخطأ</th><th>الحل</th></tr>" + err_rows + "</table></div>" if errors else "<div class='section' style='background:#dcfce7'><h3>✅ لا توجد أخطاء</h3><p>المطالبة جاهزة للإرسال</p></div>"}

<div style="text-align:center;margin-top:20px;color:#888;font-size:11px">
  تم الفحص بواسطة منصة AlHuda Med — {row.get('service_date','')}
</div>
<br>
<button onclick="window.print()" style="background:#6366f1;color:white;padding:10px 24px;
  border:none;border-radius:6px;cursor:pointer;font-size:14px;display:block;margin:0 auto">
  🖨️ طباعة / حفظ PDF
</button>
</body></html>"""


def _ucaaf_tab(doctors):
    st.markdown("### 🏥 إدخال مطالبة UCAAF — عامة")
    doc_options = [f"{d['id']} — {d['name']}" for d in doctors]

    with st.form("ucaaf_checker", clear_on_submit=False):
        st.markdown("#### 👤 بيانات المريض والطبيب")
        r1c1, r1c2, r1c3 = st.columns(3)
        with r1c1:
            patient_name = st.text_input("اسم المريض")
            patient_id   = st.text_input("الرقم الطبي للمريض")
        with r1c2:
            patient_age  = st.number_input("العمر (سنة)", min_value=0, max_value=120, value=30)
            gender       = st.selectbox("الجنس", ["ذكر", "أنثى"])
        with r1c3:
            service_dt = st.date_input("تاريخ الخدمة")
            if doc_options:
                doc_sel = st.selectbox("الطبيب المعالج", doc_options)
            else:
                doc_sel = st.text_input("الطبيب المعالج")

        st.divider()
        st.markdown("#### 📋 بيانات اليوكاف")
        r2c1, r2c2, r2c3 = st.columns(3)
        with r2c1:
            ucaf_type    = st.selectbox("نوع اليوكاف", ["UCAF-1 (خارجي)", "UCAF-2 (داخلي)"])
            patient_type = st.selectbox("نوع المريض", ["خارجي (outpatient)", "داخلي (inpatient)"])
        with r2c2:
            icd_primary = st.text_input("كود التشخيص الرئيسي ICD-10 *", placeholder="مثال: K29.70")
            icd_second  = st.text_input("كود التشخيص الثانوي (اختياري)", placeholder="مثال: R11")
        with r2c3:
            cpt    = st.text_input("كود الإجراء CPT *", placeholder="مثال: 99213")
            amount = st.number_input("المبلغ المطالب به (ر.س) *", min_value=0.0, step=50.0)

        st.divider()
        st.markdown("#### 💊 الأدوية والشكوى")
        drugs_raw = st.text_area(
            "الأدوية (افصل بـ |)",
            placeholder="مثال: riack plus|pantozol|paracetamol",
            height=70,
        )
        chief_c = st.text_input(
            "الشكوى الرئيسية",
            placeholder="مثال: ألم شرسوفي | رغبة في الإنجاب | صعوبة التنفس"
        )

        st.divider()
        st.markdown("#### ✅ المربعات والموافقات")
        r4c1, r4c2, r4c3 = st.columns(3)
        with r4c1:
            signed    = st.checkbox("✔ المريض وقّع نموذج الموافقة", value=True)
        with r4c2:
            cb_infert = st.checkbox("☑ مربع «infertility» مُفعَّل", value=False)
            cb_preg   = st.checkbox("☑ مربع «pregnancy/indicate» مُفعَّل", value=False)
        with r4c3:
            approval = st.text_input("رقم الموافقة المسبقة", placeholder="APP-XXXXX")

        st.divider()
        submitted = st.form_submit_button("⚡ فحص الأخطاء الآن", use_container_width=True, type="primary")

    if submitted:
        if not icd_primary.strip():
            st.error("⚠️ يرجى إدخال كود ICD-10")
            return
        if not cpt.strip():
            st.error("⚠️ يرجى إدخال كود CPT")
            return

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
            "ucaf_type":       "UCAF-1" if "1" in ucaf_type else "UCAF-2",
            "patient_type":    "outpatient" if "خارجي" in patient_type else "inpatient",
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
            st.error(f"⚠️ تم اكتشاف **{len(result.errors)} خطأ** ({len(high)} عالي، {len(mid)} متوسط)")

            st.markdown(
                f"""<div style="background:#1e293b;border-radius:10px;padding:14px 20px;
                    margin-bottom:16px;display:flex;gap:20px;flex-wrap:wrap">
                  <div><span style="color:#94a3b8;font-size:12px">المريض</span>
                       <div style="color:#f1f5f9;font-weight:700">{patient_name or '—'}</div></div>
                  <div><span style="color:#94a3b8;font-size:12px">ICD</span>
                       <div style="color:#f1f5f9;font-weight:700">{icd_primary.upper()}</div></div>
                  <div><span style="color:#94a3b8;font-size:12px">CPT</span>
                       <div style="color:#f1f5f9;font-weight:700">{cpt}</div></div>
                  <div><span style="color:#94a3b8;font-size:12px">المبلغ</span>
                       <div style="color:#ef4444;font-weight:700">{amount:,.0f} ر.س</div></div>
                </div>""",
                unsafe_allow_html=True,
            )

            st.markdown("### الأخطاء المكتشفة والحلول")
            for e in result.errors:
                color = SEVERITY_COLOR.get(e["level"], "#f59e0b")
                icon  = SEVERITY_ICON.get(e["level"], "🟡")
                st.markdown(
                    f"""<div style="background:#1e293b;border-radius:10px;padding:14px 18px;
                                border-left:4px solid {color};margin:7px 0">
                      <div style="display:flex;justify-content:space-between">
                        <span style="background:{color};color:white;border-radius:4px;
                                     padding:2px 7px;font-size:11px">{icon} {e['level']}</span>
                        <span style="color:#64748b;font-size:12px">{e['code']}</span>
                      </div>
                      <div style="color:#f1f5f9;font-size:14px;font-weight:600;margin-top:7px">{e['msg']}</div>
                      <div style="color:#22c55e;font-size:12px;margin-top:5px">✅ الحل: {e.get('fix','')}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )

        # ── PDF export ────────────────────────────────────────────────
        st.divider()
        st.markdown("### 📄 تصدير تقرير PDF")
        html_content = _ucaaf_pdf_html(row, result.errors if result.has_errors else [])
        b64 = base64.b64encode(html_content.encode("utf-8")).decode()
        st.markdown(
            f'<a href="data:text/html;base64,{b64}" download="ucaaf_report_{patient_id or "claim"}.html" '
            f'style="background:#6366f1;color:white;padding:10px 20px;border-radius:8px;'
            f'text-decoration:none;font-size:14px;display:inline-block">⬇️ تحميل التقرير</a>'
            f'<span style="color:#94a3b8;font-size:12px;margin-right:12px"> — افتح الملف ثم اضغط Ctrl+P للطباعة أو الحفظ كـ PDF</span>',
            unsafe_allow_html=True,
        )


def render(_df, user):
    st.markdown("## 🔍 فحص مطالبات اليوكاف والديكاف")
    st.caption("أدخل بيانات الحالة لفحص الأخطاء فوراً قبل الإرسال للتأمين")
    st.divider()

    tab_ucaaf, tab_dcaf = st.tabs(["🏥 يوكاف — UCAAF (عام)", "🦷 ديكاف — DCAF (أسنان)"])

    with tab_dcaf:
        doctors = _load_doctors()
        _dcaf_tab(doctors)

    with tab_ucaaf:
        _ucaaf_tab(_load_doctors())
