"""Reusable Streamlit UI helpers."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

STATUS_COLORS = {
    "مقبول":  "#22c55e",
    "مرفوض":  "#ef4444",
    "معلق":   "#f59e0b",
}

SEVERITY_COLORS = {
    "عالي":   "#ef4444",
    "متوسط":  "#f59e0b",
    "سليم":   "#22c55e",
}


def kpi_row(metrics: list[dict]):
    """Render a row of KPI cards. Each dict: {label, value, delta?, color?}."""
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        with col:
            color = m.get("color", "#6366f1")
            delta = m.get("delta", "")
            st.markdown(
                f"""
                <div style="background:#1e293b;border-radius:12px;padding:18px 20px;
                            border-left:4px solid {color};margin-bottom:8px">
                  <div style="color:#94a3b8;font-size:13px">{m['label']}</div>
                  <div style="color:#f1f5f9;font-size:28px;font-weight:700">{m['value']}</div>
                  <div style="color:{color};font-size:12px">{delta}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def status_pie(df: pd.DataFrame, title="توزيع الحالات"):
    counts = df["status"].value_counts().reset_index()
    counts.columns = ["status", "count"]
    colors = [STATUS_COLORS.get(s, "#94a3b8") for s in counts["status"]]
    fig = go.Figure(go.Pie(
        labels=counts["status"],
        values=counts["count"],
        hole=0.55,
        marker_colors=colors,
        textfont_size=14,
    ))
    fig.update_layout(
        title=title,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#f1f5f9",
        margin=dict(t=50, b=10, l=10, r=10),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2),
    )
    return fig


def error_bar_chart(error_series: pd.Series, title="أبرز أسباب الرفض"):
    df = error_series.value_counts().head(8).reset_index()
    df.columns = ["error", "count"]
    fig = px.bar(
        df, x="count", y="error", orientation="h",
        color="count",
        color_continuous_scale=["#6366f1","#ef4444"],
        labels={"count": "عدد الحالات", "error": "نوع الخطأ"},
        title=title,
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#f1f5f9",
        coloraxis_showscale=False,
        yaxis=dict(autorange="reversed"),
        margin=dict(t=50, b=10, l=10, r=10),
    )
    return fig


def doctor_comparison_bar(df: pd.DataFrame):
    g = df.groupby("doctor_name").apply(
        lambda x: pd.Series({
            "rejection_rate": round((x["status"] == "مرفوض").mean() * 100, 1),
            "total": len(x),
        })
    ).reset_index()
    g = g.sort_values("rejection_rate", ascending=False)
    fig = px.bar(
        g, x="doctor_name", y="rejection_rate",
        text="rejection_rate",
        color="rejection_rate",
        color_continuous_scale=["#22c55e","#f59e0b","#ef4444"],
        labels={"doctor_name":"الطبيب","rejection_rate":"نسبة الرفض %"},
        title="مقارنة نسبة الرفض بين الأطباء",
    )
    fig.update_traces(texttemplate="%{text}%", textposition="outside")
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#f1f5f9",
        coloraxis_showscale=False,
        margin=dict(t=50, b=10),
    )
    return fig


def monthly_trend(df: pd.DataFrame, title="الاتجاه الشهري للحالات"):
    df = df.copy()
    df["month"] = pd.to_datetime(df["service_date"]).dt.to_period("M").astype(str)
    g = df.groupby(["month","status"]).size().reset_index(name="count")
    fig = px.line(
        g, x="month", y="count", color="status",
        color_discrete_map=STATUS_COLORS,
        markers=True, title=title,
        labels={"month":"الشهر","count":"عدد الحالات","status":"الحالة"},
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#f1f5f9",
        margin=dict(t=50, b=10),
    )
    return fig


def alert_box(msg: str, level: str = "عالي"):
    color = SEVERITY_COLORS.get(level, "#f59e0b")
    icon  = "🔴" if level == "عالي" else "🟡"
    st.markdown(
        f"""<div style="background:#1e293b;border-radius:8px;padding:12px 16px;
                        border-left:4px solid {color};margin:4px 0;font-size:14px;color:#f1f5f9">
            {icon} {msg}
        </div>""",
        unsafe_allow_html=True,
    )
