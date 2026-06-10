"""صفحة الإشعارات — Notifications Page."""
import streamlit as st
from app.notifications import get_notifications, mark_all_read, mark_one_read, get_unread_count


def render(_df, user):
    doctor_id = user.get("doctor_id")
    if not doctor_id:
        st.info("الإشعارات متاحة للأطباء فقط")
        return

    unread = get_unread_count(doctor_id)
    st.markdown(f"## 🔔 الإشعارات {'(' + str(unread) + ' غير مقروءة)' if unread else ''}")
    st.divider()

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("✅ تحديد الكل كمقروء", use_container_width=True):
            mark_all_read(doctor_id)
            st.rerun()

    notifs = get_notifications(doctor_id)

    if not notifs:
        st.info("لا توجد إشعارات بعد")
        return

    level_color = {"عالي": "#ef4444", "متوسط": "#f59e0b", "منخفض": "#22c55e"}
    type_icon   = {"new_claim": "📋", "error_found": "⚠️", "claim_rejected": "❌"}

    for n in notifs:
        color   = level_color.get(n.get("level","متوسط"), "#6366f1")
        icon    = type_icon.get(n.get("type",""), "🔔")
        opacity = "1" if not n["read"] else "0.55"
        bg      = "#1e293b" if not n["read"] else "#0f172a"
        badge   = f'<span style="background:{color};color:white;border-radius:4px;padding:2px 7px;font-size:11px">{n.get("level","")}</span>' if not n["read"] else ""

        st.markdown(
            f"""
            <div style="background:{bg};border-radius:10px;padding:14px 18px;
                        border-left:4px solid {color};margin:6px 0;opacity:{opacity}">
              <div style="display:flex;justify-content:space-between;align-items:center">
                <div style="color:#f1f5f9;font-weight:700;font-size:14px">
                  {icon} {n['title']} {badge}
                </div>
                <div style="color:#64748b;font-size:11px">{n['timestamp']}</div>
              </div>
              <div style="color:#94a3b8;font-size:13px;margin-top:5px">{n['message']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if not n["read"]:
            if st.button("تحديد كمقروء", key=f"read_{n['id']}"):
                mark_one_read(doctor_id, n["id"])
                st.rerun()
