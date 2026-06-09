"""UCAAF Upload & Error Analyzer — live file checker."""
import io
import streamlit as st
import pandas as pd
from app.ucaaf_analyzer import analyze_dataframe
from app.components import alert_box, error_bar_chart, kpi_row

REQUIRED_COLS = [
    "claim_id","patient_id","doctor_id","service_date",
    "icd_code","cpt_code","amount","approval_no",
]

SAMPLE_DATA = {
    "claim_id":    ["CLM-9001","CLM-9002","CLM-9003"],
    "patient_id":  ["P111111","","P333333"],
    "doctor_id":   ["D001","D002","D003"],
    "service_date":["2025-06-01","2025-06-02",""],
    "icd_code":    ["J18.9","E11.9","I10"],
    "cpt_code":    ["99214","99285","99213"],   # 99285 is wrong for E11.9
    "amount":      [1500, 6200, 800],
    "approval_no": ["APP12345","","APP99999"],
}


def render(_df, user):
    st.markdown("## محرك تحليل أخطاء اليوكاف (UCAAF Analyzer)")
    st.markdown("ارفع ملف CSV يحتوي على بيانات المطالبات وسيقوم النظام بفحصها فورياً.")
    st.divider()

    # ── Download sample ───────────────────────────────────────────────
    sample_df  = pd.DataFrame(SAMPLE_DATA)
    sample_csv = sample_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ تحميل نموذج CSV للاختبار", sample_csv, "ucaaf_sample.csv", "text/csv")

    # ── Manual single-claim entry ─────────────────────────────────────
    st.markdown("### فحص مطالبة واحدة يدوياً")
    with st.form("single_claim"):
        c1, c2 = st.columns(2)
        with c1:
            claim_id   = st.text_input("رقم المطالبة", "CLM-XXXX")
            patient_id = st.text_input("الرقم الطبي للمريض")
            icd        = st.selectbox("كود التشخيص ICD", ["J18.9","E11.9","I10","K21.0","M54.5","Z00.00"])
            service_dt = st.date_input("تاريخ الخدمة")
        with c2:
            cpt        = st.text_input("كود الإجراء CPT", "99213")
            amount     = st.number_input("المبلغ (ر.س)", min_value=0.0, value=1000.0, step=50.0)
            approval   = st.text_input("رقم الموافقة (إن وجد)")
            signed     = st.checkbox("المريض وقّع النموذج", value=True)
        submitted = st.form_submit_button("فحص المطالبة")

    if submitted:
        row = {
            "claim_id":     claim_id,
            "patient_id":   patient_id,
            "icd_code":     icd,
            "cpt_code":     cpt,
            "amount":       amount,
            "approval_no":  approval,
            "service_date": str(service_dt),
            "patient_signed": signed,
        }
        from app.ucaaf_analyzer import analyze
        result = analyze(row)
        if result.has_errors:
            st.error(f"⚠️ تم اكتشاف {len(result.errors)} خطأ في هذه المطالبة:")
            for e in result.errors:
                alert_box(f"[{e['code']}] {e['msg']}", e["level"])
        else:
            st.success("✅ المطالبة سليمة — لا توجد أخطاء في اليوكاف")

    # ── Bulk CSV upload ───────────────────────────────────────────────
    st.markdown("### رفع ملف CSV للفحص الجماعي")
    uploaded = st.file_uploader("اختر ملف CSV", type=["csv"])

    if uploaded:
        try:
            udf = pd.read_csv(io.StringIO(uploaded.read().decode("utf-8-sig")))
        except Exception as e:
            st.error(f"تعذّر قراءة الملف: {e}")
            return

        missing = [c for c in REQUIRED_COLS if c not in udf.columns]
        if missing:
            st.error(f"الأعمدة التالية مفقودة من الملف: {', '.join(missing)}")
            return

        udf["patient_signed"] = udf.get("patient_signed", True)
        results = analyze_dataframe(udf)

        total  = len(results)
        errors = [r for r in results if r.has_errors]
        clean  = total - len(errors)

        kpi_row([
            {"label": "إجمالي السجلات",    "value": total,        "color": "#6366f1"},
            {"label": "سليمة",              "value": clean,        "color": "#22c55e"},
            {"label": "تحتوي أخطاء",        "value": len(errors),  "color": "#ef4444",
             "delta": f"{round(len(errors)/total*100,1)}% من الملفات"},
        ])

        # Error details
        all_errors = []
        for r in errors:
            for e in r.errors:
                all_errors.append({"claim_id": r.claim_id, **e})

        if all_errors:
            err_df = pd.DataFrame(all_errors)
            st.plotly_chart(
                error_bar_chart(err_df["msg"], "توزيع الأخطاء المكتشفة"),
                use_container_width=True,
            )
            st.markdown("### تفاصيل الأخطاء")
            st.dataframe(
                err_df.rename(columns={"claim_id":"رقم المطالبة","code":"كود","level":"الخطورة","msg":"وصف الخطأ"}),
                use_container_width=True,
                hide_index=True,
            )
            csv_out = err_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button("⬇️ تصدير الأخطاء (CSV)", csv_out, "ucaaf_errors.csv", "text/csv")
        else:
            st.success("✅ جميع السجلات في الملف سليمة — لا توجد أخطاء")
