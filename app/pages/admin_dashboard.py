"""Admin & Audit Dashboard — full analytics with financial reporting."""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from app.components import (
    kpi_row, status_pie, error_bar_chart,
    doctor_comparison_bar, monthly_trend, alert_box,
)


def _lost_revenue_chart(df: pd.DataFrame):
    """Bar chart: money lost per doctor from rejections."""
    g = df[df["status"] == "مرفوض"].groupby("doctor_name")["amount"].sum().reset_index()
    g.columns = ["doctor_name", "lost"]
    g = g.sort_values("lost", ascending=False)
    fig = px.bar(
        g, x="doctor_name", y="lost",
        text=g["lost"].apply(lambda v: f"{v:,.0f}"),
        color="lost", color_continuous_scale=["#f59e0b","#ef4444"],
        labels={"doctor_name":"الطبيب","lost":"المبلغ المفقود (ر.س)"},
        title="المبالغ المفقودة بالرفض — لكل طبيب",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#f1f5f9", coloraxis_showscale=False,
        margin=dict(t=50,b=10),
    )
    return fig


def _specialty_heatmap(df: pd.DataFrame):
    """Heatmap: error type × specialty."""
    rows = []
    for _, row in df[df["errors"] != ""].iterrows():
        for e in row["errors"].split("|"):
            rows.append({"specialty": row["specialty"], "error": e})
    if not rows:
        return None
    tmp = pd.DataFrame(rows)
    pivot = tmp.groupby(["specialty","error"]).size().unstack(fill_value=0)
    fig = px.imshow(
        pivot,
        color_continuous_scale=["#0f172a","#6366f1","#ef4444"],
        labels=dict(x="نوع الخطأ", y="التخصص", color="التكرار"),
        title="خريطة الأخطاء حسب التخصص",
        aspect="auto",
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", font_color="#f1f5f9",
        margin=dict(t=50,b=10,l=10,r=10),
        xaxis=dict(tickangle=-30),
    )
    return fig


def _monthly_financial(df: pd.DataFrame):
    df = df.copy()
    df["month"] = pd.to_datetime(df["service_date"], errors="coerce").dt.to_period("M").astype(str)
    g = df.groupby("month").agg(
        billed   =("amount","sum"),
        recovered=("recovered","sum"),
    ).reset_index()
    g["lost"] = g["billed"] - g["recovered"]

    fig = go.Figure()
    fig.add_trace(go.Bar(name="مُطالَب به", x=g["month"], y=g["billed"],
                         marker_color="#6366f1", opacity=0.8))
    fig.add_trace(go.Bar(name="مُسترَد",    x=g["month"], y=g["recovered"],
                         marker_color="#22c55e", opacity=0.9))
    fig.add_trace(go.Scatter(name="خسارة", x=g["month"], y=g["lost"],
                             mode="lines+markers", line=dict(color="#ef4444",width=2)))
    fig.update_layout(
        barmode="group", title="التحليل المالي الشهري",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#f1f5f9", margin=dict(t=50,b=10),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25),
    )
    return fig


def render(df: pd.DataFrame, user: dict):
    st.markdown("## لوحة تحكم الإدارة والتدقيق")
    st.divider()

    # Ensure required columns exist
    for col in ["status","amount","recovered","errors","error_count","doctor_name",
                "specialty","icd_code","cpt_code","service_date","claim_id",
                "patient_name"]:
        if col not in df.columns:
            df[col] = "" if col not in ["amount","recovered","error_count"] else 0

    df["amount"]      = pd.to_numeric(df["amount"],      errors="coerce").fillna(0)
    df["recovered"]   = pd.to_numeric(df["recovered"],   errors="coerce").fillna(0)
    df["error_count"] = pd.to_numeric(df["error_count"], errors="coerce").fillna(0)
    df["errors"]      = df["errors"].fillna("")
    df["status"]      = df["status"].fillna("")

    if len(df) == 0:
        st.info("📭 لا توجد حالات مسجلة بعد. أضف حالات من صفحة **📦 معالجة جماعية**.")
        return

    # ── Global KPIs ───────────────────────────────────────────────────
    total        = len(df)
    accepted     = (df["status"] == "مقبول").sum()
    rejected     = (df["status"] == "مرفوض").sum()
    pending      = (df["status"] == "معلق").sum()
    recovered    = df["recovered"].sum()
    total_billed = df["amount"].sum()
    total_lost   = df[df["status"] == "مرفوض"]["amount"].sum()
    rej_rate     = round(rejected / total * 100, 1) if total else 0
    recovery_pct = round(recovered / total_billed * 100, 1) if total_billed else 0

    kpi_row([
        {"label": "إجمالي المطالبات",    "value": total,
         "color": "#6366f1"},
        {"label": "مقبولة",               "value": accepted,
         "color": "#22c55e", "delta": f"{round(accepted/total*100,1)}%" if total else ""},
        {"label": "مرفوضة",               "value": rejected,
         "color": "#ef4444", "delta": f"نسبة الرفض: {rej_rate}%"},
        {"label": "معلقة",                "value": pending,
         "color": "#f59e0b"},
        {"label": "إجمالي المطالب به",    "value": f"{total_billed:,.0f} ر.س",
         "color": "#8b5cf6"},
        {"label": "المستردة",             "value": f"{recovered:,.0f} ر.س",
         "color": "#06b6d4", "delta": f"نسبة الاسترداد: {recovery_pct}%"},
        {"label": "خسائر الرفض",          "value": f"{total_lost:,.0f} ر.س",
         "color": "#ef4444"},
    ])

    # ── Tabs ──────────────────────────────────────────────────────────
    t1, t2, t3, t4 = st.tabs([
        "📊 نظرة عامة",
        "👨‍⚕️ تحليل الأطباء",
        "💰 التقرير المالي",
        "📋 الجدول الكامل",
    ])

    # ════════════════════════════════════════════════════════════════
    with t1:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(status_pie(df), use_container_width=True)
        with col2:
            errors_flat = df[df["errors"] != ""]["errors"].str.split("|").explode()
            if len(errors_flat):
                st.plotly_chart(
                    error_bar_chart(errors_flat, "أكثر أخطاء اليوكاف تكراراً"),
                    use_container_width=True,
                )

        st.plotly_chart(monthly_trend(df, "الاتجاه الشهري للمطالبات"), use_container_width=True)

        hm = _specialty_heatmap(df)
        if hm:
            st.plotly_chart(hm, use_container_width=True)

    # ════════════════════════════════════════════════════════════════
    with t2:
        st.markdown("### مقارنة نسب الرفض بين الأطباء")
        st.plotly_chart(doctor_comparison_bar(df), use_container_width=True)

        st.markdown("### تفاصيل أخطاء طبيب بعينه")
        doc_choice = st.selectbox(
            "اختر طبيباً", df["doctor_name"].unique(), key="adm_doc_select"
        )
        ddf   = df[df["doctor_name"] == doc_choice]
        derr  = round((ddf["status"] == "مرفوض").mean() * 100, 1)
        dlost = ddf[ddf["status"] == "مرفوض"]["amount"].sum()

        kpi_row([
            {"label": "إجمالي حالاته",   "value": len(ddf),             "color": "#6366f1"},
            {"label": "نسبة الرفض",       "value": f"{derr}%",            "color": "#ef4444"},
            {"label": "خسائر الرفض",      "value": f"{dlost:,.0f} ر.س",  "color": "#f59e0b"},
        ])

        doc_errors = ddf[ddf["errors"] != ""]["errors"].str.split("|").explode()
        if len(doc_errors):
            st.plotly_chart(
                error_bar_chart(doc_errors, f"أخطاء {doc_choice}"),
                use_container_width=True,
            )
            top3 = doc_errors.value_counts().head(3)
            st.markdown("**🔔 أبرز التنبيهات:**")
            for err, cnt in top3.items():
                pct = round(cnt / len(ddf) * 100, 1)
                alert_box(
                    f"«{err}» — تكررت {cnt} مرة ({pct}% من حالاته)",
                    "عالي" if pct > 15 else "متوسط",
                )
        else:
            st.success(f"✅ لا توجد أخطاء مسجلة لـ {doc_choice}")

    # ════════════════════════════════════════════════════════════════
    with t3:
        st.markdown("### التحليل المالي الشهري")
        st.plotly_chart(_monthly_financial(df), use_container_width=True)

        st.markdown("### خسائر الرفض لكل طبيب")
        st.plotly_chart(_lost_revenue_chart(df), use_container_width=True)

        # Financial summary table per doctor
        st.markdown("### ملخص مالي — لكل طبيب")
        fin = df.groupby("doctor_name").apply(lambda x: pd.Series({
            "إجمالي الحالات":    len(x),
            "مجموع المطالب به":  round(x["amount"].sum(), 2),
            "مجموع المسترد":     round(x["recovered"].sum(), 2),
            "خسائر الرفض":      round(x[x["status"]=="مرفوض"]["amount"].sum(), 2),
            "نسبة الرفض %":     round((x["status"]=="مرفوض").mean()*100, 1),
            "نسبة الاسترداد %": round(
                x["recovered"].sum() / x["amount"].sum() * 100, 1
            ) if x["amount"].sum() else 0,
        })).reset_index().rename(columns={"doctor_name":"الطبيب"})

        st.dataframe(
            fin.style.background_gradient(
                subset=["نسبة الرفض %"], cmap="RdYlGn_r"
            ).background_gradient(
                subset=["نسبة الاسترداد %"], cmap="RdYlGn"
            ),
            use_container_width=True,
            hide_index=True,
        )

        csv_fin = fin.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇️ تصدير الملخص المالي", csv_fin,
                           "maliy_summary.csv", "text/csv")

    # ════════════════════════════════════════════════════════════════
    with t4:
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            status_f = st.selectbox("الحالة", ["الكل","مقبول","مرفوض","معلق"], key="adm_st")
        with col_f2:
            doc_f = st.selectbox(
                "الطبيب", ["الكل"] + list(df["doctor_name"].unique()), key="adm_doc_t"
            )
        with col_f3:
            icd_f = st.selectbox(
                "ICD", ["الكل"] + sorted(df["icd_code"].unique()), key="adm_icd"
            )

        view = df.copy()
        if status_f != "الكل":
            view = view[view["status"] == status_f]
        if doc_f != "الكل":
            view = view[view["doctor_name"] == doc_f]
        if icd_f != "الكل":
            view = view[view["icd_code"] == icd_f]

        st.caption(f"عدد السجلات: {len(view)}")

        cols = ["claim_id","patient_name","doctor_name","specialty","service_date",
                "icd_code","cpt_code","amount","recovered","status","errors","error_count"]
        st.dataframe(
            view[cols].rename(columns={
                "claim_id":"رقم المطالبة","patient_name":"المريض","doctor_name":"الطبيب",
                "specialty":"التخصص","service_date":"تاريخ الخدمة","icd_code":"ICD",
                "cpt_code":"CPT","amount":"المبلغ","recovered":"المسترد",
                "status":"الحالة","errors":"الأخطاء","error_count":"عدد الأخطاء",
            }),
            use_container_width=True,
            hide_index=True,
        )
        csv = view.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇️ تصدير (CSV)", csv, "taqreer.csv", "text/csv")
