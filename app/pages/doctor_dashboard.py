"""Doctor-specific dashboard — shows only the logged-in doctor's claims."""
import streamlit as st
import pandas as pd
from app.components import kpi_row, status_pie, error_bar_chart, monthly_trend, alert_box


def render(df: pd.DataFrame, user: dict):
    doctor_id = user["doctor_id"]
    ddf = df[df["doctor_id"] == doctor_id].copy()

    st.markdown(f"## لوحة تحكم الطبيب — {user['display_name']}")
    st.markdown(f"**التخصص:** {ddf['specialty'].iloc[0] if len(ddf) else '-'}")
    st.divider()

    # ── KPIs ─────────────────────────────────────────────────────────
    total     = len(ddf)
    accepted  = (ddf["status"] == "مقبول").sum()
    rejected  = (ddf["status"] == "مرفوض").sum()
    pending   = (ddf["status"] == "معلق").sum()
    recovered = ddf["recovered"].sum()
    rej_rate  = round(rejected / total * 100, 1) if total else 0

    kpi_row([
        {"label": "إجمالي الحالات",    "value": total,              "color": "#6366f1"},
        {"label": "مقبولة",             "value": accepted,           "color": "#22c55e",
         "delta": f"{round(accepted/total*100,1)}%" if total else ""},
        {"label": "مرفوضة",             "value": rejected,           "color": "#ef4444",
         "delta": f"نسبة الرفض {rej_rate}%"},
        {"label": "معلقة",              "value": pending,            "color": "#f59e0b"},
        {"label": "المبالغ المستردة",   "value": f"{recovered:,.0f} ر.س", "color": "#06b6d4"},
    ])

    # ── Smart alerts ─────────────────────────────────────────────────
    if rejected > 0:
        st.markdown("### 🔔 تنبيهات ذكية")
        errors_flat = ddf[ddf["errors"] != ""]["errors"].str.split("|").explode()
        top_errors  = errors_flat.value_counts().head(3)
        for err, cnt in top_errors.items():
            pct = round(cnt / total * 100, 1)
            alert_box(f"{err} — تكررت {cnt} مرة ({pct}% من ملفاتك)", "عالي" if pct > 15 else "متوسط")

    # ── Charts ───────────────────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(status_pie(ddf), use_container_width=True)
    with col2:
        errors_series = ddf[ddf["errors"] != ""]["errors"].str.split("|").explode()
        if len(errors_series):
            st.plotly_chart(error_bar_chart(errors_series, "أخطاء ملفاتك"), use_container_width=True)
        else:
            st.success("لا توجد أخطاء مسجلة في ملفاتك")

    st.plotly_chart(monthly_trend(ddf), use_container_width=True)

    # ── Claims table ─────────────────────────────────────────────────
    st.markdown("### جميع الحالات")
    status_filter = st.selectbox("تصفية حسب الحالة", ["الكل", "مقبول", "مرفوض", "معلق"], key="doc_filter")
    view = ddf if status_filter == "الكل" else ddf[ddf["status"] == status_filter]

    display_cols = ["claim_id","patient_name","service_date","icd_code","cpt_code",
                    "amount","status","errors"]
    st.dataframe(
        view[display_cols].rename(columns={
            "claim_id":"رقم المطالبة","patient_name":"المريض","service_date":"تاريخ الخدمة",
            "icd_code":"ICD","cpt_code":"CPT","amount":"المبلغ","status":"الحالة","errors":"الأخطاء",
        }),
        use_container_width=True,
        hide_index=True,
    )
