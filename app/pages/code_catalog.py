"""
كتالوج الأكواد الذكي — بحث ICD/CPT + اقتراح الكود الصحيح + كاشف الأخطاء
"""
import streamlit as st
import pandas as pd
from app.icd_cpt_db import ICD_DATABASE, CPT_DATABASE, CPT_COMMON_MISTAKES
from app.components import alert_box

CATEGORY_ICONS = {
    "تنفسي":                    "🫁",
    "هضمي":                     "🫃",
    "غدد صماء":                 "🩸",
    "قلب وأوعية":               "❤️",
    "عظام ومفاصل":              "🦴",
    "نساء وولادة":              "👶",
    "بولي":                     "💧",
    "أعصاب":                    "🧠",
    "نفسي":                     "🧘",
    "جلدية":                    "🩹",
    "أنف وأذن وحنجرة":          "👂",
    "وقائي":                    "✅",
    "أعراض — لا يُستخدم كتشخيص رئيسي": "⚠️",
}

SPEC_COLOR = {
    "specific":   "#22c55e",
    "unspecified":"#f59e0b",
    "symptom":    "#ef4444",
}
SPEC_LABEL = {
    "specific":   "محدد ✅",
    "unspecified":"غير محدد ⚠️",
    "symptom":    "عَرَض 🚫",
}


def _icd_card(icd: str, info: dict):
    spec_color = SPEC_COLOR.get(info["specificity"], "#6366f1")
    spec_label = SPEC_LABEL.get(info["specificity"], "")
    valid_cpt  = ", ".join(info["valid_cpt"]) if info["valid_cpt"] else "—"
    forbidden  = ", ".join(info["forbidden_cpt"]) if info["forbidden_cpt"] else "—"
    cb_list    = ", ".join(info["requires_cb"]) if info["requires_cb"] else "لا شيء"
    prefer     = info.get("prefer_code") or "—"
    icon       = CATEGORY_ICONS.get(info["category"], "🔹")

    st.markdown(
        f"""
        <div style="background:#1e293b;border-radius:12px;padding:18px 22px;
                    border-left:5px solid {spec_color};margin-bottom:12px">
          <div style="display:flex;justify-content:space-between;align-items:flex-start">
            <div>
              <span style="color:#94a3b8;font-size:12px">{icon} {info['category']}</span>
              <div style="color:#f1f5f9;font-size:1.15rem;font-weight:700;margin:4px 0">
                {icd} — {info['name_ar']}
              </div>
              <div style="color:#64748b;font-size:12px">{info['name_en']}</div>
            </div>
            <span style="background:{spec_color};color:white;border-radius:6px;
                         padding:3px 10px;font-size:12px;white-space:nowrap;margin-right:8px">
              {spec_label}
            </span>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:14px">
            <div style="background:#0f172a;border-radius:8px;padding:10px">
              <div style="color:#6366f1;font-size:11px;margin-bottom:4px">أكواد CPT المقبولة</div>
              <div style="color:#22c55e;font-size:13px;font-weight:600">{valid_cpt}</div>
            </div>
            <div style="background:#0f172a;border-radius:8px;padding:10px">
              <div style="color:#ef4444;font-size:11px;margin-bottom:4px">CPT الخاطئة (شائعة)</div>
              <div style="color:#f87171;font-size:13px">{forbidden}</div>
            </div>
            <div style="background:#0f172a;border-radius:8px;padding:10px">
              <div style="color:#f59e0b;font-size:11px;margin-bottom:4px">المربعات الإلزامية</div>
              <div style="color:#fbbf24;font-size:13px">{cb_list}</div>
            </div>
            <div style="background:#0f172a;border-radius:8px;padding:10px">
              <div style="color:#06b6d4;font-size:11px;margin-bottom:4px">
                {"الكود الأفضل (بدلاً منه)" if info['specificity']!='specific' else "ملاحظة"}
              </div>
              <div style="color:#67e8f9;font-size:13px">{prefer}</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render(_df, user):
    st.markdown("## 🗂️ كتالوج الأكواد الذكي — ICD-10 & CPT")
    st.caption("ابحث عن أي تشخيص أو كود، واحصل على CPT الصحيح وتحذيرات الترميز")
    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs([
        "🔍 بحث عن تشخيص",
        "⚡ فاحص ICD+CPT الفوري",
        "❌ أخطاء CPT الشائعة",
        "📊 إحصائيات الأخطاء",
    ])

    # ════════════════════════════════════════════════════════════════
    with tab1:
        col_s, col_cat = st.columns([3, 1])
        with col_s:
            query = st.text_input(
                "ابحث بالاسم العربي أو الإنجليزي أو كود ICD",
                placeholder="مثال: معدة | gastritis | K29 | ربو | N97",
            )
        with col_cat:
            cats = ["الكل"] + sorted({v["category"] for v in ICD_DATABASE.values()})
            cat_f = st.selectbox("التخصص", cats, label_visibility="collapsed")

        # Filter
        results = {}
        q = query.strip().lower()
        for icd, info in ICD_DATABASE.items():
            if cat_f != "الكل" and info["category"] != cat_f:
                continue
            if q and not any([
                q in icd.lower(),
                q in info["name_ar"].lower(),
                q in info["name_en"].lower(),
                q in info["category"].lower(),
            ]):
                continue
            results[icd] = info

        if not results:
            st.warning("لا توجد نتائج — جرّب كلمة أخرى")
        else:
            st.caption(f"{len(results)} نتيجة")
            # Warn about symptoms first
            symptoms = {k: v for k, v in results.items() if v["specificity"] == "symptom"}
            unspec   = {k: v for k, v in results.items() if v["specificity"] == "unspecified"}
            specific = {k: v for k, v in results.items() if v["specificity"] == "specific"}

            for grp, label in [(symptoms,"⚠️ أكواد أعراض — لا تُستخدم كتشخيص رئيسي"),
                                (unspec,  "🟡 أكواد غير محددة — يُفضَّل استبدالها"),
                                (specific,"✅ أكواد محددة")]:
                if grp:
                    st.markdown(f"#### {label}")
                    for icd, info in grp.items():
                        _icd_card(icd, info)

    # ════════════════════════════════════════════════════════════════
    with tab2:
        st.markdown("### تحقق من تطابق ICD مع CPT فوراً")
        c1, c2 = st.columns(2)
        with c1:
            icd_input = st.text_input("أدخل كود ICD-10", "K29.7",
                                      placeholder="K29.7 / J45.9 / N97.0 ...")
        with c2:
            cpt_input = st.text_input("أدخل كود CPT", "99285",
                                      placeholder="99213 / 99214 / 94640 ...")

        if st.button("⚡ فحص التطابق", use_container_width=True):
            icd_info = ICD_DATABASE.get(icd_input.strip())
            cpt_desc = CPT_DATABASE.get(cpt_input.strip(), "كود CPT غير موجود في قاعدة البيانات")

            if not icd_info:
                st.warning(f"كود ICD **{icd_input}** غير موجود في قاعدة البيانات — تأكد من الكود")
            else:
                # Render ICD info
                _icd_card(icd_input.strip(), icd_info)

                st.markdown(f"**CPT المُدخَل:** `{cpt_input}` — {cpt_desc}")

                # Specificity warning
                if icd_info["specificity"] == "symptom":
                    alert_box(
                        f"🚫 {icd_input} هو كود عَرَض — لا يجوز استخدامه كتشخيص رئيسي. "
                        f"استبدله بـ: {icd_info['prefer_code']}",
                        "عالي",
                    )
                elif icd_info["specificity"] == "unspecified":
                    alert_box(
                        f"⚠️ {icd_input} كود غير محدد — استخدم كوداً أدق: {icd_info['prefer_code']}",
                        "متوسط",
                    )

                # CPT match check
                if not icd_info["valid_cpt"]:
                    alert_box("هذا الكود لا يقبل CPT مباشرة — يُستخدم كتشخيص ثانوي فقط", "عالي")
                elif cpt_input.strip() in icd_info["valid_cpt"]:
                    st.success(f"✅ التطابق صحيح — CPT {cpt_input} مقبول مع {icd_input}")
                elif cpt_input.strip() in icd_info.get("forbidden_cpt", []):
                    alert_box(
                        f"❌ CPT {cpt_input} من الأكواد الخاطئة الشائعة مع {icd_input}",
                        "عالي",
                    )
                    st.markdown(
                        f"**أكواد CPT الصحيحة:** `{'` | `'.join(icd_info['valid_cpt'])}`"
                    )
                else:
                    alert_box(
                        f"❌ CPT {cpt_input} غير مطابق لـ {icd_input}",
                        "عالي",
                    )
                    st.markdown(
                        f"**أكواد CPT الصحيحة:** `{'` | `'.join(icd_info['valid_cpt'])}`"
                    )
                    # Check if it's a common mistake
                    if cpt_input.strip() in CPT_COMMON_MISTAKES:
                        m = CPT_COMMON_MISTAKES[cpt_input.strip()]
                        alert_box(f"تنبيه: {m['description']}", "متوسط")

                # Required checkboxes
                if icd_info["requires_cb"]:
                    st.info(
                        f"📋 هذا الكود يتطلب تفعيل المربعات التالية: "
                        f"**{' + '.join(icd_info['requires_cb'])}**"
                    )

        # Quick CPT lookup
        st.divider()
        st.markdown("### بحث سريع عن كود CPT")
        cpt_q = st.text_input("ابحث عن كود CPT أو وصفه", placeholder="99213 | سونار | تنظير ...")
        cq = cpt_q.strip().lower()
        if cq:
            cpt_results = {
                k: v for k, v in CPT_DATABASE.items()
                if cq in k.lower() or cq in v.lower()
            }
            if cpt_results:
                rows = [{"كود CPT": k, "الوصف": v} for k, v in cpt_results.items()]
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            else:
                st.warning("لا توجد نتائج")

    # ════════════════════════════════════════════════════════════════
    with tab3:
        st.markdown("### أكثر أخطاء CPT شيوعاً في العيادة")
        for cpt, info in CPT_COMMON_MISTAKES.items():
            correct_str = " | ".join([f"`{c}` — {CPT_DATABASE.get(c,'')}" for c in info["correct"]])
            st.markdown(
                f"""
                <div style="background:#1e293b;border-radius:10px;padding:16px 20px;
                            border-left:4px solid #ef4444;margin:8px 0">
                  <div style="display:flex;justify-content:space-between;align-items:center">
                    <span style="color:#f87171;font-size:1.1rem;font-weight:700">❌ CPT {cpt}</span>
                    <span style="background:#ef4444;color:white;border-radius:4px;
                                 padding:2px 8px;font-size:11px">خطأ شائع</span>
                  </div>
                  <div style="color:#f1f5f9;font-size:13px;margin:6px 0">{info['description']}</div>
                  <div style="color:#22c55e;font-size:12px">✅ البديل الصحيح: {correct_str}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Unspecified ICD list
        st.markdown("### أكواد ICD غير محددة يجب تجنبها")
        unspec_rows = [
            {
                "الكود غير المحدد": icd,
                "الوصف": info["name_ar"],
                "الكود الأفضل": info.get("prefer_code","—"),
            }
            for icd, info in ICD_DATABASE.items()
            if info["specificity"] == "unspecified"
        ]
        st.dataframe(
            pd.DataFrame(unspec_rows),
            use_container_width=True,
            hide_index=True,
        )

    # ════════════════════════════════════════════════════════════════
    with tab4:
        st.markdown("### إحصائيات أخطاء الترميز في بيانات العيادة")

        errors_flat = _df[_df["errors"] != ""]["errors"].str.split("|").explode()
        if len(errors_flat) == 0:
            st.info("لا توجد بيانات أخطاء")
            return

        coding_errors = errors_flat[
            errors_flat.str.contains("ICD|CPT|كود|تشخيص|عَرَض|ترميز", na=False)
        ]

        total_claims = len(_df)
        coding_count = len(coding_errors)
        coding_pct   = round(coding_count / total_claims * 100, 1)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("إجمالي أخطاء الترميز", coding_count)
        with col2:
            st.metric("نسبتها من الكل", f"{coding_pct}%")
        with col3:
            st.metric("أكثر خطأ تكراراً",
                      errors_flat.value_counts().idxmax() if len(errors_flat) else "—")

        # Per-doctor coding errors
        st.markdown("#### أخطاء الترميز لكل طبيب")
        doc_coding = []
        for doc in _df["doctor_name"].unique():
            ddf   = _df[_df["doctor_name"] == doc]
            derr  = ddf[ddf["errors"] != ""]["errors"].str.split("|").explode()
            coding = derr[derr.str.contains("ICD|CPT|كود|تشخيص|عَرَض", na=False)]
            doc_coding.append({
                "الطبيب":               doc,
                "أخطاء ترميز":          len(coding),
                "نسبة أخطاء الترميز %": round(len(coding) / len(ddf) * 100, 1),
                "أبرز خطأ":             coding.value_counts().idxmax() if len(coding) else "لا يوجد",
            })

        doc_df = pd.DataFrame(doc_coding).sort_values("أخطاء ترميز", ascending=False)
        st.dataframe(
            doc_df.style.background_gradient(subset=["نسبة أخطاء الترميز %"], cmap="RdYlGn_r"),
            use_container_width=True,
            hide_index=True,
        )

        # ICD error matrix
        st.markdown("#### أي ICD يسبب أكثر الأخطاء")
        icd_err = _df[_df["errors"].str.contains("ICD|CPT|كود", na=False)].groupby(
            "icd_code"
        ).size().reset_index(name="عدد الأخطاء").sort_values("عدد الأخطاء", ascending=False)

        if len(icd_err):
            import plotly.express as px
            fig = px.bar(
                icd_err.head(12),
                x="icd_code", y="عدد الأخطاء",
                color="عدد الأخطاء",
                color_continuous_scale=["#6366f1","#ef4444"],
                title="أكثر أكواد ICD ارتباطاً بأخطاء الترميز",
                labels={"icd_code": "كود ICD"},
                text="عدد الأخطاء",
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#f1f5f9", coloraxis_showscale=False,
                margin=dict(t=50, b=10),
            )
            st.plotly_chart(fig, use_container_width=True)
