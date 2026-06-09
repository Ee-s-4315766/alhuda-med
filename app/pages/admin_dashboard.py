"""Admin & Audit Dashboard — full view, cross-doctor analytics."""
import streamlit as st
import pandas as pd
import plotly.express as px
from app.components import (
    kpi_row, status_pie, error_bar_chart,
    doctor_comparison_bar, monthly_trend, alert_box,
)


def render(df: pd.DataFrame, user: dict):
    st.markdown("## لوحة تحكم الإدارة والتدقيق")
    st.divider()

    # ── Global KPIs ──────────────────────────────────────────────────
    total     = len(df)
    accepted  = (df["status"] == "مقبول").sum()
    rejected  = (df["status"] == "مرفوض").sum()
    pending   = (df["status"] == "معلق").sum()
    recovered = df["recovered"].sum()
    total_billed = df["amount"].sum()
    rej_rate  = round(rejected / total * 100, 1) if total else 0

    kpi_row([
        {"label": "إجمالي المطالبات",  "value": total,                    "color": "#6366f1"},
        {"label": "مقبولة",             "value": accepted,                 "color": "#22c55e"},
        {"label": "مرفوضة",             "value": rejected,                 "color": "#ef4444",
         "delta": f"نسبة الرفض الكلية: {rej_rate}%"},
        {"label": "معلقة",              "value": pending,                  "color": "#f59e0b"},
        {"label": "إجمالي المطالب به",  "value": f"{total_billed:,.0f} ر.س","color": "#8b5cf6"},
        {"label": "المستردة فعلياً",    "value": f"{recovered:,.0f} ر.س",  "color": "#06b6d4"},
    ])

    # ── Doctor comparison ─────────────────────────────────────────────
    st.markdown("### مقارنة الأطباء")
    st.plotly_chart(doctor_comparison_bar(df), use_container_width=True)

    # ── Root cause analysis ──────────────────────────────────────────
    st.markdown("### تحليل الأسباب الجذرية للرفض (Root Cause Analysis)")
    col1, col2 = st.columns(2)
    with col1:
        errors_flat = df[df["errors"] != ""]["errors"].str.split("|").explode()
        st.plotly_chart(error_bar_chart(errors_flat, "أكثر أخطاء اليوكاف تكراراً"), use_container_width=True)
    with col2:
        st.plotly_chart(status_pie(df, "توزيع الحالات الكلي"), use_container_width=True)

    # ── Per-doctor error breakdown ────────────────────────────────────
    st.markdown("### تفصيل أخطاء كل طبيب")
    doc_choice = st.selectbox("اختر طبيباً", df["doctor_name"].unique(), key="admin_doc_select")
    ddf = df[df["doctor_name"] == doc_choice]
    derr = round((ddf["status"] == "مرفوض").mean() * 100, 1)
    st.markdown(f"**نسبة الرفض:** `{derr}%` | **إجمالي الحالات:** `{len(ddf)}`")

    doc_errors = ddf[ddf["errors"] != ""]["errors"].str.split("|").explode()
    if len(doc_errors):
        st.plotly_chart(error_bar_chart(doc_errors, f"أخطاء {doc_choice}"), use_container_width=True)
        # Smart insight
        top = doc_errors.value_counts().idxmax()
        alert_box(f"أبرز خطأ عند {doc_choice}: «{top}» — يستوجب مراجعة فورية", "عالي")
    else:
        st.success(f"لا توجد أخطاء مسجلة لـ {doc_choice}")

    # ── Monthly trend ─────────────────────────────────────────────────
    st.plotly_chart(monthly_trend(df, "الاتجاه الشهري لجميع الحالات"), use_container_width=True)

    # ── Full data table ───────────────────────────────────────────────
    st.markdown("### جدول البيانات الكامل")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        status_f = st.selectbox("تصفية: الحالة", ["الكل","مقبول","مرفوض","معلق"], key="adm_status")
    with col_f2:
        doc_f = st.selectbox("تصفية: الطبيب", ["الكل"] + list(df["doctor_name"].unique()), key="adm_doc")

    view = df.copy()
    if status_f != "الكل":
        view = view[view["status"] == status_f]
    if doc_f != "الكل":
        view = view[view["doctor_name"] == doc_f]

    display = ["claim_id","patient_name","doctor_name","service_date","icd_code","cpt_code",
               "amount","recovered","status","errors","error_count"]
    st.dataframe(
        view[display].rename(columns={
            "claim_id":"رقم المطالبة","patient_name":"المريض","doctor_name":"الطبيب",
            "service_date":"تاريخ الخدمة","icd_code":"ICD","cpt_code":"CPT",
            "amount":"المبلغ","recovered":"المسترد","status":"الحالة",
            "errors":"الأخطاء","error_count":"عدد الأخطاء",
        }),
        use_container_width=True,
        hide_index=True,
    )

    # ── Export ────────────────────────────────────────────────────────
    csv = view.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ تصدير التقرير (CSV)", csv, "taqreer_almatalibat.csv", "text/csv")
