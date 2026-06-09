"""Pre-Submission Checklist — قائمة التحقق قبل إرسال اليوكاف."""
import streamlit as st
import pandas as pd
from app.components import alert_box

# ── Checklist definition ──────────────────────────────────────────────────────
SECTIONS = [
    {
        "title": "📋 بيانات المريض الأساسية",
        "color": "#6366f1",
        "items": [
            ("الرقم الطبي للمريض (MRN) مُدخَل",                        "عالي"),
            ("رقم الهوية / الإقامة مُدخَل",                            "عالي"),
            ("تاريخ الميلاد صحيح ومتطابق مع الهوية",                  "متوسط"),
            ("فئة التأمين (Class) صحيحة",                              "متوسط"),
            ("رقم بوليصة التأمين مُدخَل",                              "عالي"),
            ("تاريخ انتهاء البوليصة لم يتجاوز تاريخ الخدمة",          "عالي"),
        ],
    },
    {
        "title": "🩺 بيانات الزيارة",
        "color": "#06b6d4",
        "items": [
            ("تاريخ الخدمة مُدخَل بصيغة صحيحة",                       "عالي"),
            ("نوع المريض (Outpatient/Inpatient) صحيح",                 "عالي"),
            ("نوع اليوكاف (UCAF-1 / UCAF-2) متوافق مع نوع المريض",    "عالي"),
            ("الزيارة الجديدة أو المتابعة محددة بشكل صحيح",           "متوسط"),
            ("مستوى الطوارئ محدد إن وُجد",                            "متوسط"),
            ("توقيع المريض / ولي الأمر على نموذج الموافقة",           "عالي"),
        ],
    },
    {
        "title": "🔬 التشخيص والترميز",
        "color": "#f59e0b",
        "items": [
            ("التشخيص الرئيسي (Primary ICD-10) مُدخَل",               "عالي"),
            ("كود ICD ليس كود عَرَض فقط (R11, R51, R50.9...)",        "عالي"),
            ("كود CPT متوافق مع التشخيص الرئيسي",                     "عالي"),
            ("الأكواد الثانوية (2nd/3rd code) مُرتَّبة من الأهم للأقل","متوسط"),
            ("ICD-10 وليس ICD-9",                                      "عالي"),
            ("كود H. pylori (K29.70) مدخَل عند وصف Riack Plus",       "عالي"),
        ],
    },
    {
        "title": "💊 الأدوية والخدمات",
        "color": "#22c55e",
        "items": [
            ("كل دواء مربوط بالتشخيص الصحيح في سطره",                 "عالي"),
            ("لا يوجد كورتيزونان جهازيان في وصفة واحدة",              "عالي"),
            ("الكورتيزون الجهازي مع ربو شديد (J45.4 أو J45.5) فقط",   "عالي"),
            ("المضاد الحيوي مبرَّر بتشخيص عدوى واضح",                "عالي"),
            ("الجرعة متوافقة مع عمر وجنس المريض",                    "متوسط"),
            ("لا تكرار في الأدوية (نفس المادة الفعالة مرتين)",        "متوسط"),
        ],
    },
    {
        "title": "✅ المربعات الإلزامية",
        "color": "#8b5cf6",
        "items": [
            ("مربع «infertility» مُفعَّل لحالات N97.x و N46.x",       "عالي"),
            ("مربع «pregnancy/indicate» مُفعَّل عند طلب الحمل",       "عالي"),
            ("مربع «chronic» مُفعَّل للأمراض المزمنة",               "متوسط"),
            ("مربع «Work Related» مُفعَّل لإصابات العمل",            "متوسط"),
            ("مربع «congenital» مُفعَّل للحالات الخِلقية",           "متوسط"),
        ],
    },
    {
        "title": "💰 الموافقة المالية",
        "color": "#ef4444",
        "items": [
            ("رقم الموافقة المسبقة (Prior Auth) مُدخَل",               "عالي"),
            ("المبلغ لا يتجاوز سقف الموافقة",                        "عالي"),
            ("لا يتجاوز حد الزيارة المالي (Approval Limit per Visit)", "عالي"),
            ("موافقة إضافية للخدمات فوق 5000 ر.س",                   "عالي"),
            ("تاريخ الموافقة يسبق تاريخ الخدمة",                     "عالي"),
        ],
    },
    {
        "title": "📎 المستندات المرفقة",
        "color": "#0ea5e9",
        "items": [
            ("تقرير الطبيب مرفق للحالات التي تستدعيه",               "متوسط"),
            ("نتائج التحاليل المرفقة لتبرير الإجراءات",              "متوسط"),
            ("صورة بطاقة التأمين مرفقة",                             "متوسط"),
            ("تقرير الإحالة (Referral) مرفق عند وجوده",              "متوسط"),
        ],
    },
]

LEVEL_COLOR = {"عالي": "#ef4444", "متوسط": "#f59e0b"}
LEVEL_ICON  = {"عالي": "🔴",       "متوسط": "🟡"}


def render(_df, user):
    st.markdown("## ✅ قائمة التحقق قبل إرسال اليوكاف")
    st.caption("راجع كل بند قبل الإرسال لتفادي الرفض. البنود الحمراء سبب مباشر للرفض.")
    st.divider()

    # ── Progress tracking ─────────────────────────────────────────────
    if "checklist_state" not in st.session_state:
        st.session_state["checklist_state"] = {}

    all_items, checked_items = 0, 0
    for sec in SECTIONS:
        for item, level in sec["items"]:
            key = f"chk_{item[:30]}"
            all_items += 1
            if st.session_state["checklist_state"].get(key, False):
                checked_items += 1

    pct = round(checked_items / all_items * 100) if all_items else 0
    color = "#22c55e" if pct == 100 else "#f59e0b" if pct >= 70 else "#ef4444"

    st.markdown(
        f"""
        <div style="background:#1e293b;border-radius:12px;padding:20px 24px;margin-bottom:20px;
                    border:2px solid {color}">
          <div style="display:flex;justify-content:space-between;align-items:center">
            <div>
              <div style="color:#94a3b8;font-size:13px">نسبة الاكتمال</div>
              <div style="color:{color};font-size:2rem;font-weight:700">{pct}%</div>
              <div style="color:#f1f5f9;font-size:13px">{checked_items} من {all_items} بنداً</div>
            </div>
            <div style="font-size:3rem">{"✅" if pct==100 else "⚠️" if pct>=70 else "🚫"}</div>
          </div>
          <div style="background:#0f172a;border-radius:6px;height:8px;margin-top:12px">
            <div style="background:{color};width:{pct}%;height:8px;border-radius:6px;transition:width .3s"></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Reset button ──────────────────────────────────────────────────
    col1, col2, col3 = st.columns([1,1,4])
    with col1:
        if st.button("🔄 إعادة تعيين", use_container_width=True):
            st.session_state["checklist_state"] = {}
            st.rerun()
    with col2:
        if st.button("☑️ تحديد الكل", use_container_width=True):
            for sec in SECTIONS:
                for item, _ in sec["items"]:
                    st.session_state["checklist_state"][f"chk_{item[:30]}"] = True
            st.rerun()

    st.divider()

    # ── Sections ──────────────────────────────────────────────────────
    for sec in SECTIONS:
        sec_done = sum(
            1 for item, _ in sec["items"]
            if st.session_state["checklist_state"].get(f"chk_{item[:30]}", False)
        )
        sec_total = len(sec["items"])

        with st.expander(
            f"{sec['title']}  —  {sec_done}/{sec_total}",
            expanded=(sec_done < sec_total),
        ):
            for item, level in sec["items"]:
                key = f"chk_{item[:30]}"
                current = st.session_state["checklist_state"].get(key, False)
                col_cb, col_lbl = st.columns([1, 16])
                with col_cb:
                    new_val = st.checkbox("", value=current, key=key + "_widget",
                                          label_visibility="collapsed")
                    st.session_state["checklist_state"][key] = new_val
                with col_lbl:
                    done    = st.session_state["checklist_state"].get(key, False)
                    icon    = "✅" if done else LEVEL_ICON[level]
                    c_text  = "#64748b" if done else "#f1f5f9"
                    c_badge = LEVEL_COLOR[level]
                    st.markdown(
                        f"""<div style="display:flex;align-items:center;gap:10px;padding:4px 0">
                            <span style="font-size:14px;color:{c_text};
                                  text-decoration:{'line-through' if done else 'none'}">
                              {icon} {item}
                            </span>
                            <span style="background:{c_badge};color:white;border-radius:4px;
                                         padding:1px 7px;font-size:11px">{level}</span>
                        </div>""",
                        unsafe_allow_html=True,
                    )

    # ── Final send readiness ──────────────────────────────────────────
    st.divider()
    if pct == 100:
        st.success("🎉 جميع البنود مكتملة — المطالبة جاهزة للإرسال")
    else:
        remaining_high = []
        for sec in SECTIONS:
            for item, level in sec["items"]:
                key = f"chk_{item[:30]}"
                if level == "عالي" and not st.session_state["checklist_state"].get(key, False):
                    remaining_high.append(item)
        if remaining_high:
            st.error(f"⛔ يوجد {len(remaining_high)} بند عالي الأولوية لم يُكتمل — لا تُرسل المطالبة")
            for item in remaining_high[:5]:
                alert_box(item, "عالي")
        else:
            st.warning("⚠️ بعض البنود المتوسطة لم تُكتمل — مقبول للإرسال لكن يُستحسن المراجعة")

    # ── Printable summary ─────────────────────────────────────────────
    rows = []
    for sec in SECTIONS:
        for item, level in sec["items"]:
            key  = f"chk_{item[:30]}"
            done = st.session_state["checklist_state"].get(key, False)
            rows.append({
                "القسم":   sec["title"],
                "البند":   item,
                "الأولوية": level,
                "الحالة":  "✅ مكتمل" if done else "❌ ناقص",
            })
    csv = pd.DataFrame(rows).to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ تصدير قائمة التحقق (CSV)", csv,
                       "checklist_ucaaf.csv", "text/csv")
