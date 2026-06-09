"""التقرير الشهري الآلي — Auto Monthly Performance Report."""
import io
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from app.components import kpi_row, alert_box


def _month_label(period_str: str) -> str:
    """Convert '2026-05' to 'مايو 2026'."""
    MONTHS_AR = {
        "01":"يناير","02":"فبراير","03":"مارس","04":"أبريل",
        "05":"مايو","06":"يونيو","07":"يوليو","08":"أغسطس",
        "09":"سبتمبر","10":"أكتوبر","11":"نوفمبر","12":"ديسمبر",
    }
    try:
        y, m = period_str.split("-")
        return f"{MONTHS_AR.get(m, m)} {y}"
    except Exception:
        return period_str


def _build_monthly_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["service_date"] = pd.to_datetime(df["service_date"], errors="coerce")
    df = df.dropna(subset=["service_date"])
    df["month"] = df["service_date"].dt.to_period("M").astype(str)
    return df


def _monthly_kpis(mdf: pd.DataFrame) -> pd.DataFrame:
    g = mdf.groupby("month").apply(lambda x: pd.Series({
        "total":      len(x),
        "accepted":   (x["status"] == "مقبول").sum() if "status" in x else 0,
        "rejected":   (x["status"] == "مرفوض").sum() if "status" in x else 0,
        "pending":    (x["status"] == "معلق").sum()  if "status" in x else 0,
        "billed":     x["amount"].sum() if "amount" in x else 0,
        "recovered":  x["recovered"].sum() if "recovered" in x else 0,
        "rej_rate":   round((x["status"]=="مرفوض").mean()*100,1) if "status" in x else 0,
        "rec_rate":   round(x["recovered"].sum()/x["amount"].sum()*100,1)
                      if "amount" in x and x["amount"].sum() > 0 else 0,
    })).reset_index()
    g["month_label"] = g["month"].apply(_month_label)
    g["lost"] = g["billed"] - g["recovered"]
    return g


def _doctor_monthly(mdf: pd.DataFrame, month: str) -> pd.DataFrame:
    sub = mdf[mdf["month"] == month]
    if "doctor_name" not in sub.columns or len(sub) == 0:
        return pd.DataFrame()
    g = sub.groupby("doctor_name").apply(lambda x: pd.Series({
        "حالات":          len(x),
        "مقبول":          (x["status"]=="مقبول").sum(),
        "مرفوض":          (x["status"]=="مرفوض").sum(),
        "نسبة الرفض %":  round((x["status"]=="مرفوض").mean()*100,1),
        "مطالب به ر.س":  round(x["amount"].sum(),0),
        "مسترد ر.س":     round(x["recovered"].sum(),0),
        "خسائر ر.س":     round(x[x["status"]=="مرفوض"]["amount"].sum(),0),
    })).reset_index().rename(columns={"doctor_name":"الطبيب"})
    return g.sort_values("نسبة الرفض %", ascending=False)


def render(df: pd.DataFrame, user: dict):
    st.markdown("## 📅 التقرير الشهري الآلي")
    st.caption("تقرير أداء شامل لكل شهر — قابل للتصدير بضغطة واحدة")
    st.divider()

    mdf = _build_monthly_df(df)
    if len(mdf) == 0:
        st.warning("لا توجد بيانات تاريخية كافية لإنشاء تقرير شهري")
        return

    monthly = _monthly_kpis(mdf)
    months   = sorted(monthly["month"].unique(), reverse=True)

    # ── Month selector ────────────────────────────────────────────────
    selected_month = st.selectbox(
        "اختر الشهر",
        months,
        format_func=_month_label,
    )
    cur  = monthly[monthly["month"] == selected_month].iloc[0]
    prev_months = [m for m in months if m < selected_month]
    prev = monthly[monthly["month"] == prev_months[0]].iloc[0] if prev_months else None

    st.markdown(f"## تقرير {_month_label(selected_month)}")
    st.divider()

    # ── KPIs with month-over-month delta ─────────────────────────────
    def delta(field, fmt="{:.0f}", suffix=""):
        if prev is None:
            return ""
        diff = cur[field] - prev[field]
        sign = "▲" if diff > 0 else "▼"
        color_up = "#ef4444" if field in ("rejected","rej_rate","lost") else "#22c55e"
        color_dn = "#22c55e" if field in ("rejected","rej_rate","lost") else "#ef4444"
        c = color_up if diff > 0 else color_dn
        return f'<span style="color:{c}">{sign} {fmt.format(abs(diff))}{suffix} عن الشهر السابق</span>'

    kpi_row([
        {"label":"إجمالي المطالبات", "value":int(cur["total"]),
         "color":"#6366f1"},
        {"label":"مقبولة",           "value":int(cur["accepted"]),
         "color":"#22c55e",
         "delta":f"{round(cur['accepted']/cur['total']*100,1)}%" if cur["total"] else ""},
        {"label":"مرفوضة",           "value":int(cur["rejected"]),
         "color":"#ef4444",
         "delta":f"نسبة الرفض: {cur['rej_rate']}%"},
        {"label":"معلقة",            "value":int(cur["pending"]),   "color":"#f59e0b"},
        {"label":"إجمالي المطالب",   "value":f"{cur['billed']:,.0f} ر.س",
         "color":"#8b5cf6"},
        {"label":"المسترد فعلياً",   "value":f"{cur['recovered']:,.0f} ر.س",
         "color":"#06b6d4",
         "delta":f"نسبة الاسترداد: {cur['rec_rate']}%"},
        {"label":"الخسائر",          "value":f"{cur['lost']:,.0f} ر.س",
         "color":"#ef4444"},
    ])

    # Month vs previous comparison banners
    if prev is not None:
        rej_diff = round(cur["rej_rate"] - prev["rej_rate"], 1)
        rec_diff = round(cur["rec_rate"] - prev["rec_rate"], 1)
        if rej_diff > 0:
            alert_box(
                f"نسبة الرفض ارتفعت {rej_diff}% مقارنةً بـ {_month_label(prev_months[0])} "
                f"({prev['rej_rate']}% → {cur['rej_rate']}%)",
                "عالي",
            )
        else:
            st.success(
                f"✅ نسبة الرفض انخفضت {abs(rej_diff)}% مقارنةً بالشهر السابق "
                f"({prev['rej_rate']}% → {cur['rej_rate']}%)"
            )

    st.divider()

    # ── Charts: current month ─────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        # Pie
        status_counts = mdf[mdf["month"]==selected_month]["status"].value_counts().reset_index()
        status_counts.columns = ["status","count"]
        colors = {"مقبول":"#22c55e","مرفوض":"#ef4444","معلق":"#f59e0b"}
        fig_pie = go.Figure(go.Pie(
            labels=status_counts["status"],
            values=status_counts["count"],
            hole=0.55,
            marker_colors=[colors.get(s,"#94a3b8") for s in status_counts["status"]],
        ))
        fig_pie.update_layout(
            title=f"توزيع الحالات — {_month_label(selected_month)}",
            paper_bgcolor="rgba(0,0,0,0)", font_color="#f1f5f9",
            margin=dict(t=50,b=10),
            legend=dict(orientation="h",yanchor="bottom",y=-0.2),
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        # Errors bar for this month
        month_errs = mdf[
            (mdf["month"]==selected_month) & (mdf["errors"].notna()) & (mdf["errors"]!="")
        ]["errors"].str.split("|").explode()
        if len(month_errs):
            top_errs = month_errs.value_counts().head(8).reset_index()
            top_errs.columns = ["خطأ","عدد"]
            fig_err = px.bar(
                top_errs, x="عدد", y="خطأ", orientation="h",
                color="عدد", color_continuous_scale=["#6366f1","#ef4444"],
                title="أبرز أخطاء الشهر",
            )
            fig_err.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#f1f5f9", coloraxis_showscale=False,
                yaxis=dict(autorange="reversed"),
                margin=dict(t=50,b=10,l=10,r=10),
            )
            st.plotly_chart(fig_err, use_container_width=True)
        else:
            st.success("لا أخطاء في هذا الشهر ✅")

    # ── Doctor performance this month ─────────────────────────────────
    st.markdown("### أداء الأطباء هذا الشهر")
    doc_table = _doctor_monthly(mdf, selected_month)
    if len(doc_table):
        st.dataframe(
            doc_table.style.background_gradient(subset=["نسبة الرفض %"], cmap="RdYlGn_r"),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("لا بيانات")

    # ── 6-month trend ─────────────────────────────────────────────────
    st.markdown("### الاتجاه خلال آخر 6 أشهر")
    last6 = monthly.tail(6)

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Bar(
        name="مقبول", x=last6["month_label"], y=last6["accepted"],
        marker_color="#22c55e", opacity=0.85,
    ))
    fig_trend.add_trace(go.Bar(
        name="مرفوض", x=last6["month_label"], y=last6["rejected"],
        marker_color="#ef4444", opacity=0.85,
    ))
    fig_trend.add_trace(go.Scatter(
        name="نسبة الرفض %", x=last6["month_label"], y=last6["rej_rate"],
        mode="lines+markers+text",
        text=[f"{v}%" for v in last6["rej_rate"]],
        textposition="top center",
        line=dict(color="#f59e0b", width=2),
        yaxis="y2",
    ))
    fig_trend.update_layout(
        barmode="stack",
        title="المطالبات ونسبة الرفض — آخر 6 أشهر",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#f1f5f9",
        yaxis=dict(title="عدد الحالات"),
        yaxis2=dict(title="نسبة الرفض %", overlaying="y", side="right",
                    range=[0,100], showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25),
        margin=dict(t=50, b=10),
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    # Financial trend
    fig_fin = go.Figure()
    fig_fin.add_trace(go.Bar(
        name="مطالب به", x=last6["month_label"], y=last6["billed"],
        marker_color="#6366f1", opacity=0.8,
    ))
    fig_fin.add_trace(go.Bar(
        name="مسترد", x=last6["month_label"], y=last6["recovered"],
        marker_color="#22c55e", opacity=0.9,
    ))
    fig_fin.add_trace(go.Scatter(
        name="خسائر الرفض", x=last6["month_label"], y=last6["lost"],
        mode="lines+markers", line=dict(color="#ef4444", width=2),
    ))
    fig_fin.update_layout(
        barmode="group", title="الأداء المالي — آخر 6 أشهر",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#f1f5f9",
        legend=dict(orientation="h", yanchor="bottom", y=-0.25),
        margin=dict(t=50, b=10),
    )
    st.plotly_chart(fig_fin, use_container_width=True)

    # ── Export ────────────────────────────────────────────────────────
    st.divider()
    st.markdown("### 📥 تصدير التقرير الشهري")

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        # Summary
        summary = pd.DataFrame([
            ["الشهر",               _month_label(selected_month)],
            ["إجمالي المطالبات",    int(cur["total"])],
            ["مقبولة",              int(cur["accepted"])],
            ["مرفوضة",              int(cur["rejected"])],
            ["نسبة الرفض %",        f"{cur['rej_rate']}%"],
            ["إجمالي المطالب به",   f"{cur['billed']:,.0f} ر.س"],
            ["المسترد",             f"{cur['recovered']:,.0f} ر.س"],
            ["نسبة الاسترداد %",    f"{cur['rec_rate']}%"],
            ["الخسائر",             f"{cur['lost']:,.0f} ر.س"],
        ], columns=["البيان","القيمة"])
        summary.to_excel(writer, index=False, sheet_name="الملخص")

        # Doctor table
        if len(doc_table):
            doc_table.to_excel(writer, index=False, sheet_name="أداء الأطباء")

        # Monthly trend
        trend_export = monthly[["month_label","total","accepted","rejected","rej_rate",
                                 "billed","recovered","lost","rec_rate"]]
        trend_export.to_excel(writer, index=False, sheet_name="الاتجاه الشهري")

        # Raw data for this month
        month_raw = mdf[mdf["month"]==selected_month]
        month_raw.to_excel(writer, index=False, sheet_name="تفاصيل الحالات")

    buf.seek(0)
    st.download_button(
        f"⬇️ تصدير تقرير {_month_label(selected_month)} — Excel",
        buf.read(),
        f"monthly_report_{selected_month}.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    # Printable HTML summary
    html_report = f"""
    <div style="font-family:Arial;direction:rtl;padding:20px;background:#fff;color:#000">
      <h2 style="color:#4f46e5">تقرير مطالبات التأمين — {_month_label(selected_month)}</h2>
      <hr>
      <table style="width:100%;border-collapse:collapse">
        <tr style="background:#f0f0f0">
          <th style="padding:8px;text-align:right;border:1px solid #ccc">البيان</th>
          <th style="padding:8px;text-align:right;border:1px solid #ccc">القيمة</th>
        </tr>
        {"".join(f'<tr><td style="padding:8px;border:1px solid #ccc">{r[0]}</td>'
                  f'<td style="padding:8px;border:1px solid #ccc;font-weight:bold">{r[1]}</td></tr>'
                 for r in [
                     ("إجمالي المطالبات", int(cur['total'])),
                     ("مقبولة",           f"{int(cur['accepted'])} ({round(cur['accepted']/cur['total']*100,1) if cur['total'] else 0}%)"),
                     ("مرفوضة",           f"{int(cur['rejected'])} ({cur['rej_rate']}%)"),
                     ("إجمالي المطالب به",f"{cur['billed']:,.0f} ر.س"),
                     ("المسترد",          f"{cur['recovered']:,.0f} ر.س ({cur['rec_rate']}%)"),
                     ("الخسائر",          f"{cur['lost']:,.0f} ر.س"),
                 ])}
      </table>
    </div>
    """
    st.download_button(
        "⬇️ ملخص HTML للطباعة",
        html_report.encode("utf-8"),
        f"report_{selected_month}.html",
        "text/html",
    )
