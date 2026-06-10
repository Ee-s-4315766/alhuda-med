"""Doctor-specific dashboard — personal KPIs, smart alerts, claim list."""
import streamlit as st
import pandas as pd
from app.components import kpi_row, status_pie, error_bar_chart, monthly_trend, alert_box
from app.ucaaf_analyzer import analyze_dataframe
from app.notifications import get_notifications, get_unread_count, mark_all_read


def _smart_alerts(ddf: pd.DataFrame) -> list[dict]:
    """Run live analyzer on doctor's claims and return top insights."""
    results  = analyze_dataframe(ddf)
    all_errs = []
    for r in results:
        for e in r.errors:
            all_errs.append({"code": e["code"], "msg": e["msg"], "fix": e["fix"],
                              "level": e["level"]})
    if not all_errs:
        return []
    tmp    = pd.DataFrame(all_errs)
    top    = tmp.groupby(["code","msg","fix","level"]).size().reset_index(name="count")
    top    = top.sort_values("count", ascending=False).head(5)
    return top.to_dict("records")


def render(df: pd.DataFrame, user: dict):
    doctor_id = user["doctor_id"]
    ddf       = df[df["doctor_id"] == doctor_id].copy()

    st.markdown(f"## لوحة تحكم — {user['display_name']}")
    if len(ddf):
        st.caption(f"التخصص: **{ddf['specialty'].iloc[0]}**")
    st.divider()

    # ── Notification banner ───────────────────────────────────────────
    unread_notifs = get_notifications(doctor_id, unread_only=True)
    if unread_notifs:
        n_count = len(unread_notifs)
        err_notifs = [n for n in unread_notifs if n["type"] == "error_found"]
        new_notifs = [n for n in unread_notifs if n["type"] == "new_claim"]
        banner_parts = []
        if new_notifs:
            banner_parts.append(f"📋 {len(new_notifs)} حالة جديدة أُضيفت")
        if err_notifs:
            banner_parts.append(f"⚠️ {len(err_notifs)} خطأ يحتاج تصحيح")
        st.warning(
            f"🔔 لديك {n_count} إشعار جديد — " + " | ".join(banner_parts)
            + " — اضغط على **🔔 إشعاراتي** من القائمة لعرض التفاصيل"
        )
        if st.button("تحديد الكل كمقروء", key="dismiss_notifs"):
            mark_all_read(doctor_id)
            st.rerun()
        st.divider()

    if len(ddf) == 0:
        st.info("لا توجد حالات مسجلة لهذا الطبيب بعد.")
        return

    # ── KPIs ──────────────────────────────────────────────────────────
    total        = len(ddf)
    accepted     = (ddf["status"] == "مقبول").sum()
    rejected     = (ddf["status"] == "مرفوض").sum()
    pending      = (ddf["status"] == "معلق").sum()
    recovered    = ddf["recovered"].sum()
    total_billed = ddf["amount"].sum()
    rej_rate     = round(rejected / total * 100, 1) if total else 0
    rec_pct      = round(recovered / total_billed * 100, 1) if total_billed else 0
    lost         = ddf[ddf["status"] == "مرفوض"]["amount"].sum()

    kpi_row([
        {"label": "إجمالي حالاتي",        "value": total,                  "color": "#6366f1"},
        {"label": "مقبولة",                "value": accepted,               "color": "#22c55e",
         "delta": f"{round(accepted/total*100,1)}%"},
        {"label": "مرفوضة",                "value": rejected,               "color": "#ef4444",
         "delta": f"نسبة الرفض: {rej_rate}%"},
        {"label": "معلقة",                 "value": pending,                "color": "#f59e0b"},
        {"label": "المبالغ المستردة",      "value": f"{recovered:,.0f} ر.س","color": "#06b6d4",
         "delta": f"نسبة الاسترداد: {rec_pct}%"},
        {"label": "خسائر الرفض",           "value": f"{lost:,.0f} ر.س",    "color": "#ef4444"},
    ])

    # ── Smart alerts (live from analyzer) ────────────────────────────
    insights = _smart_alerts(ddf)
    if insights:
        st.markdown("### 🔔 تنبيهات ذكية — أبرز الأخطاء في ملفاتك")
        for ins in insights:
            alert_box(
                f"[{ins['code']}] {ins['msg']}  ·  "
                f"تكرار: {ins['count']} مرة  ·  ✅ {ins['fix']}",
                ins["level"],
            )
    else:
        st.success("✅ لا توجد أخطاء متكررة في ملفاتك — أداء ممتاز!")

    # ── Charts ────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(status_pie(ddf), use_container_width=True)
    with col2:
        errs = ddf[ddf["errors"] != ""]["errors"].str.split("|").explode()
        if len(errs):
            st.plotly_chart(error_bar_chart(errs, "أخطاء ملفاتك"), use_container_width=True)
        else:
            st.success("لا توجد أخطاء مسجلة في بياناتك")

    st.plotly_chart(monthly_trend(ddf), use_container_width=True)

    # ── Claims table ──────────────────────────────────────────────────
    st.markdown("### حالاتي")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        status_f = st.selectbox("تصفية: الحالة",
                                ["الكل","مقبول","مرفوض","معلق"], key="doc_sf")
    with col_s2:
        err_only = st.checkbox("عرض الحالات ذات الأخطاء فقط", key="doc_err_only")

    view = ddf.copy()
    if status_f != "الكل":
        view = view[view["status"] == status_f]
    if err_only:
        view = view[view["errors"] != ""]

    st.caption(f"{len(view)} حالة")

    display = ["claim_id","patient_name","service_date","icd_code","cpt_code",
               "amount","recovered","status","errors"]
    st.dataframe(
        view[display].rename(columns={
            "claim_id":"رقم المطالبة","patient_name":"المريض",
            "service_date":"تاريخ الخدمة","icd_code":"ICD","cpt_code":"CPT",
            "amount":"المبلغ","recovered":"المسترد","status":"الحالة","errors":"الأخطاء",
        }),
        use_container_width=True,
        hide_index=True,
    )

    csv = view.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ تصدير حالاتي", csv,
                       f"halati_{doctor_id}.csv", "text/csv")
