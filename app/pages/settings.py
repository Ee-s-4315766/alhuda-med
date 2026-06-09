"""صفحة إعدادات النظام — Settings Page (Admin only)."""
import json
import streamlit as st
import pandas as pd
from pathlib import Path

SETTINGS_PATH = Path(__file__).parent.parent.parent / "data" / "settings.json"
DOCTORS_PATH  = Path(__file__).parent.parent.parent / "data" / "doctors.json"


def _load_settings() -> dict:
    if SETTINGS_PATH.exists():
        return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    return {
        "clinic_name":      "عيادة الهدى الطبية",
        "clinic_name_en":   "AlHuda Medical Clinic",
        "city":             "الرياض",
        "financial_limit":  5000,
        "rejection_alert_pct": 30,
        "default_ucaf":     "UCAF-1",
        "logo_url":         "",
    }


def _save_settings(s: dict):
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_doctors() -> list:
    if DOCTORS_PATH.exists():
        return json.loads(DOCTORS_PATH.read_text(encoding="utf-8"))
    return []


def _save_doctors(docs: list):
    DOCTORS_PATH.write_text(json.dumps(docs, ensure_ascii=False, indent=2), encoding="utf-8")


def render(_df, user):
    if user.get("role") != "admin":
        st.error("⛔ هذه الصفحة للمدير فقط")
        return

    st.markdown("## ⚙️ إعدادات النظام")
    st.divider()

    settings = _load_settings()
    doctors  = _load_doctors()

    tab1, tab2, tab3, tab4 = st.tabs([
        "🏥 معلومات العيادة",
        "👨‍⚕️ إدارة الأطباء",
        "🔔 حدود التنبيهات",
        "📤 النسخ الاحتياطي",
    ])

    # ════════════════════════════════════════════════════════════════
    with tab1:
        st.markdown("### معلومات العيادة الأساسية")
        with st.form("clinic_form"):
            c1, c2 = st.columns(2)
            with c1:
                clinic_name    = st.text_input("اسم العيادة (عربي)",
                                               settings.get("clinic_name",""))
                city           = st.text_input("المدينة", settings.get("city",""))
            with c2:
                clinic_name_en = st.text_input("اسم العيادة (إنجليزي)",
                                               settings.get("clinic_name_en",""))
                default_ucaf   = st.selectbox("نوع اليوكاف الافتراضي",
                                              ["UCAF-1","UCAF-2","UCAF-3"],
                                              index=["UCAF-1","UCAF-2","UCAF-3"]
                                              .index(settings.get("default_ucaf","UCAF-1")))

            saved = st.form_submit_button("💾 حفظ", use_container_width=True)

        if saved:
            settings.update({
                "clinic_name": clinic_name, "clinic_name_en": clinic_name_en,
                "city": city, "default_ucaf": default_ucaf,
            })
            _save_settings(settings)
            st.success("✅ تم حفظ معلومات العيادة")

        # Preview
        s = _load_settings()
        st.markdown(
            f"""
            <div style="background:#1e293b;border-radius:10px;padding:16px 20px;
                        border-left:4px solid #6366f1;margin-top:12px">
              <div style="color:#f1f5f9;font-size:1.1rem;font-weight:700">{s.get('clinic_name','')}</div>
              <div style="color:#94a3b8;font-size:13px">{s.get('clinic_name_en','')} — {s.get('city','')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ════════════════════════════════════════════════════════════════
    with tab2:
        st.markdown("### قائمة الأطباء المسجلين")

        # Show current doctors
        if doctors:
            doc_df = pd.DataFrame(doctors)
            st.dataframe(doc_df.rename(columns={
                "id":"المعرف","name":"الاسم","specialty":"التخصص"
            }), use_container_width=True, hide_index=True)
        else:
            st.info("لا يوجد أطباء مسجلون بعد")

        st.divider()
        st.markdown("### إضافة طبيب جديد")
        with st.form("add_doctor"):
            c1, c2, c3 = st.columns(3)
            with c1:
                new_id   = st.text_input("المعرف (مثال: D005)")
            with c2:
                new_name = st.text_input("الاسم الكامل (مثال: د. اسم اسم)")
            with c3:
                new_spec = st.selectbox("التخصص", [
                    "باطنية","أطفال","جراحة عامة","نساء وولادة",
                    "عظام","جلدية","أنف وأذن","عيون","قلب",
                    "أعصاب","نفسية","طوارئ","طب أسرة",
                ])
            add_btn = st.form_submit_button("➕ إضافة طبيب", use_container_width=True)

        if add_btn:
            if not new_id.strip() or not new_name.strip():
                st.error("يرجى ملء جميع الحقول")
            elif any(d["id"] == new_id.strip() for d in doctors):
                st.error(f"المعرف {new_id} موجود مسبقاً")
            else:
                doctors.append({
                    "id":        new_id.strip(),
                    "name":      new_name.strip(),
                    "specialty": new_spec,
                })
                _save_doctors(doctors)
                st.success(f"✅ تمت إضافة {new_name}")
                st.rerun()

        st.divider()
        st.markdown("### حذف طبيب")
        if doctors:
            del_choice = st.selectbox(
                "اختر طبيباً للحذف",
                [f"{d['id']} — {d['name']}" for d in doctors],
                key="del_doc",
            )
            if st.button("🗑️ حذف", type="secondary"):
                del_id = del_choice.split(" — ")[0]
                doctors = [d for d in doctors if d["id"] != del_id]
                _save_doctors(doctors)
                st.success(f"✅ تم الحذف")
                st.rerun()

    # ════════════════════════════════════════════════════════════════
    with tab3:
        st.markdown("### حدود التنبيهات والمراجعة")
        with st.form("alerts_form"):
            fin_limit = st.number_input(
                "الحد المالي الذي يستوجب موافقة مسبقة (ر.س)",
                min_value=100, max_value=50000,
                value=int(settings.get("financial_limit", 5000)),
                step=500,
            )
            rej_alert = st.slider(
                "نسبة الرفض التي تُطلق تنبيهاً للمدير (%)",
                min_value=5, max_value=80,
                value=int(settings.get("rejection_alert_pct", 30)),
            )
            saved2 = st.form_submit_button("💾 حفظ الحدود", use_container_width=True)

        if saved2:
            settings.update({
                "financial_limit": fin_limit,
                "rejection_alert_pct": rej_alert,
            })
            _save_settings(settings)
            # Update analyzer limit
            try:
                import app.ucaaf_analyzer as eng
                eng.FINANCIAL_LIMIT = fin_limit
            except Exception:
                pass
            st.success(f"✅ تم الحفظ — الحد المالي: {fin_limit:,} ر.س | تنبيه الرفض: {rej_alert}%")

        # Current rejection rate alert check
        if "status" in _df.columns:
            curr_rej = round((_df["status"] == "مرفوض").mean() * 100, 1)
            alert_pct = settings.get("rejection_alert_pct", 30)
            if curr_rej >= alert_pct:
                st.error(
                    f"🚨 تنبيه: نسبة الرفض الحالية {curr_rej}% تتجاوز الحد المحدد {alert_pct}%"
                )
            else:
                st.success(
                    f"✅ نسبة الرفض الحالية {curr_rej}% — ضمن الحد المقبول ({alert_pct}%)"
                )

    # ════════════════════════════════════════════════════════════════
    with tab4:
        st.markdown("### النسخ الاحتياطي والاستيراد")

        # Export settings
        settings_json = json.dumps(settings, ensure_ascii=False, indent=2).encode("utf-8")
        st.download_button(
            "⬇️ تصدير إعدادات النظام (JSON)",
            settings_json, "settings_backup.json", "application/json",
        )

        doctors_json = json.dumps(doctors, ensure_ascii=False, indent=2).encode("utf-8")
        st.download_button(
            "⬇️ تصدير قائمة الأطباء (JSON)",
            doctors_json, "doctors_backup.json", "application/json",
        )

        # Export all claims
        if len(_df):
            claims_csv = _df.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "⬇️ تصدير جميع الحالات (CSV)",
                claims_csv, "claims_backup.csv", "text/csv",
            )

        st.divider()
        st.markdown("### استيراد إعدادات")
        up_settings = st.file_uploader("ارفع ملف إعدادات JSON", type=["json"], key="up_set")
        if up_settings:
            try:
                new_s = json.loads(up_settings.read().decode("utf-8"))
                _save_settings(new_s)
                st.success("✅ تم استيراد الإعدادات")
                st.rerun()
            except Exception as e:
                st.error(f"خطأ في الملف: {e}")
