"""AlHuda Med — Medical Insurance Claims Platform (Streamlit prototype)."""
import sys
import os
import streamlit as st
import pandas as pd
from pathlib import Path

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AlHuda Med | إدارة مطالبات التأمين",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0f172a !important;
        color: #f1f5f9;
        direction: rtl;
    }
    [data-testid="stSidebar"] { background-color: #1e293b !important; }
    h1,h2,h3,h4 { color: #f1f5f9 !important; }
    [data-testid="stMetricValue"] { color: #f1f5f9 !important; }
    div[data-testid="stDataFrame"] { direction: rtl; }
    .stButton > button {
        background: #6366f1; color: white; border-radius: 8px; border: none;
    }
    .stButton > button:hover { background: #4f46e5; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    csv_path = ROOT / "data" / "claims.csv"
    if not csv_path.exists():
        # Auto-generate demo data
        import subprocess
        subprocess.run([sys.executable, str(ROOT / "data" / "seed.py")], check=True)
    return pd.read_csv(csv_path)


# ── Session state helpers ─────────────────────────────────────────────────────
def is_logged_in():
    return st.session_state.get("user") is not None


def do_logout():
    st.session_state.pop("user", None)
    st.rerun()


# ── Login screen ──────────────────────────────────────────────────────────────
def login_page():
    st.markdown(
        """
        <div style="text-align:center;padding:40px 0 20px">
          <h1 style="color:#6366f1;font-size:2.5rem">🏥 AlHuda Med</h1>
          <p style="color:#94a3b8;font-size:1.1rem">منصة إدارة وتحليل مطالبات التأمين الطبي</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col = st.columns([1, 2, 1])[1]
    with col:
        with st.form("login_form"):
            st.markdown("### تسجيل الدخول")
            username = st.text_input("اسم المستخدم", placeholder="admin / d001 / d002 ...")
            password = st.text_input("كلمة المرور", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("دخول", use_container_width=True)

        if submitted:
            from app.auth import login
            user = login(username.strip(), password.strip())
            if user:
                st.session_state["user"] = user
                st.rerun()
            else:
                st.error("اسم المستخدم أو كلمة المرور غير صحيحة")

        st.markdown(
            """
            <div style="background:#1e293b;border-radius:10px;padding:16px;margin-top:16px;font-size:13px;color:#94a3b8">
            <b>حسابات تجريبية:</b><br>
            🔑 <code>admin</code> / <code>admin123</code> — مدير النظام<br>
            👨‍⚕️ <code>d001</code> / <code>doctor123</code> — د. أحمد الزهراني<br>
            👩‍⚕️ <code>d002</code> / <code>doctor123</code> — د. سارة المطيري<br>
            👨‍⚕️ <code>d003</code> / <code>doctor123</code> — د. خالد العتيبي
            </div>
            """,
            unsafe_allow_html=True,
        )


# ── Main app ──────────────────────────────────────────────────────────────────
def main():
    if not is_logged_in():
        login_page()
        return

    user = st.session_state["user"]
    df   = load_data()

    # Sidebar
    with st.sidebar:
        st.markdown(
            f"""
            <div style="padding:16px 0 8px;text-align:center">
              <div style="font-size:2rem">🏥</div>
              <div style="color:#f1f5f9;font-weight:700;font-size:1.1rem">AlHuda Med</div>
              <div style="color:#6366f1;font-size:.85rem">{user['display_name']}</div>
              <div style="color:#64748b;font-size:.75rem">{'مدير' if user['role']=='admin' else 'طبيب'}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.divider()

        if user["role"] == "admin":
            pages = {
                "📊 لوحة الإدارة":        "admin",
                "🔍 محرك تحليل اليوكاف":  "ucaaf",
            }
        else:
            pages = {
                "📋 لوحتي الشخصية":       "doctor",
                "🔍 محرك تحليل اليوكاف":  "ucaaf",
            }

        page = st.radio("القائمة", list(pages.keys()), label_visibility="collapsed")
        st.divider()
        if st.button("تسجيل الخروج", use_container_width=True):
            do_logout()

    # Render selected page
    selected = pages[page]
    if selected == "admin":
        from app.pages.admin_dashboard import render
        render(df, user)
    elif selected == "doctor":
        from app.pages.doctor_dashboard import render
        render(df, user)
    elif selected == "ucaaf":
        from app.pages.ucaaf_upload import render
        render(df, user)


if __name__ == "__main__":
    main()
