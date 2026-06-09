"""UCAAF Upload & Error Analyzer — live file checker."""
import io
import streamlit as st
import pandas as pd
from app.ucaaf_analyzer import analyze_dataframe, analyze
from app.components import alert_box, error_bar_chart, kpi_row

REQUIRED_COLS = [
    "claim_id", "patient_id", "doctor_id", "service_date",
    "icd_code", "cpt_code", "amount", "approval_no",
]

SAMPLE_DATA = {
    "claim_id":      ["CLM-9001", "CLM-9002", "CLM-9003", "CLM-9004"],
    "patient_id":    ["P111111",  "",          "P333333",  "P444444"],
    "doctor_id":     ["D001",     "D002",      "D003",     "D001"],
    "service_date":  ["2025-06-01","2025-06-02","",        "2025-06-03"],
    "icd_code":      ["R11",      "E11.9",     "I10",      "K29.7"],
    "icd_code_2":    ["K29.7",    "",          "",         ""],
    "cpt_code":      ["99213",    "99285",     "99213",    "99213"],
    "amount":        [357,        6200,        800,        1100],
    "approval_no":   ["",         "",          "APP99999", "APP12345"],
    "patient_signed":[ True,      True,        True,       True],
    "drugs":         [
        "riack plus|daroxime|paracetamol|pantozol|dansetron",
        "metformin|insulin",
        "amlodipine",
        "riack plus|pantoprazole",
    ],
}

SEVERITY_BADGE = {
    "عالي":  "🔴",
    "متوسط": "🟡",
}

ICD_HINTS = {
    "R11":   "R11 = Nausea & Vomiting — عَرَض، يجب ألا يكون تشخيصاً رئيسياً",
    "K29.7": "K29.7 = Gastritis — استخدم K29.70 إذا كان بسبب H. pylori",
    "K29.70":"K29.70 = Gastritis with H. pylori — الكود الصحيح مع علاج H. pylori",
    "E11.9": "E11.9 = Type 2 Diabetes — أكود CPT المقبولة: 99213, 99214, 80047",
    "I10":   "I10 = Hypertension — أكواد CPT المقبولة: 99213, 99214, 93000",
    "J18.9": "J18.9 = Pneumonia — أكواد CPT المقبولة: 99213, 99214, 71046",
}


def render(_df, user):
    st.markdown("## محرك تحليل أخطاء اليوكاف (UCAAF Analyzer)")
    st.caption("فحص فوري للمطالبات قبل الإرسال — يكشف أخطاء ICD/CPT، الأدوية، الموافقات، وترتيب الأكواد")
    st.divider()

    tab1, tab2, tab3 = st.tabs(["🔍 فحص مطالبة واحدة", "📂 رفع ملف CSV جماعي", "📖 مرجع الأكواد"])

    # ════════════════════════════════════════════════════════════════
    with tab1:
        st.markdown("### أدخل بيانات المطالبة للفحص الفوري")

        with st.form("single_claim"):
            c1, c2 = st.columns(2)
            with c1:
                claim_id    = st.text_input("رقم المطالبة", "CLM-XXXX")
                patient_id  = st.text_input("الرقم الطبي للمريض")
                icd_primary = st.text_input("كود التشخيص الرئيسي (ICD-10)", "K29.70",
                                            help="مثال: K29.70 | J18.9 | E11.9")
                icd_second  = st.text_input("كود التشخيص الثانوي (اختياري)", "R11")
                service_dt  = st.date_input("تاريخ الخدمة")
            with c2:
                cpt         = st.text_input("كود الإجراء CPT", "99213")
                amount      = st.number_input("المبلغ (ر.س)", min_value=0.0, value=357.0, step=50.0)
                approval    = st.text_input("رقم الموافقة المسبقة (إن وجد)")
                signed      = st.checkbox("المريض وقّع نموذج الموافقة", value=True)
                drugs_raw   = st.text_area("الأدوية والخدمات (افصل بـ |)",
                                           "riack plus|daroxime|paracetamol|pantozol|dansetron",
                                           height=90)

            submitted = st.form_submit_button("⚡ فحص الآن", use_container_width=True)

        if submitted:
            row = {
                "claim_id":     claim_id,
                "patient_id":   patient_id,
                "icd_code":     icd_primary.strip(),
                "icd_code_2":   icd_second.strip(),
                "cpt_code":     cpt.strip(),
                "amount":       amount,
                "approval_no":  approval.strip(),
                "service_date": str(service_dt),
                "patient_signed": signed,
                "drugs":        drugs_raw.lower(),
            }
            result = analyze(row)

            if result.has_errors:
                st.error(f"⚠️ تم اكتشاف **{len(result.errors)} خطأ** — الخطورة الإجمالية: {result.severity}")
                for e in result.errors:
                    badge = SEVERITY_BADGE.get(e["level"], "🟡")
                    with st.container():
                        st.markdown(
                            f"""
                            <div style="background:#1e293b;border-radius:10px;padding:14px 18px;
                                        border-left:4px solid {'#ef4444' if e['level']=='عالي' else '#f59e0b'};
                                        margin:6px 0">
                              <div style="color:#f1f5f9;font-size:14px;font-weight:600">
                                {badge} [{e['code']}] {e['msg']}
                              </div>
                              <div style="color:#22c55e;font-size:12px;margin-top:6px">
                                ✅ الحل: {e.get('fix','')}
                              </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
            else:
                st.success("✅ المطالبة سليمة — لا توجد أخطاء في اليوكاف، جاهزة للإرسال")

        # ICD hint box
        if icd_primary in ICD_HINTS:
            st.info(f"💡 {ICD_HINTS[icd_primary]}")

    # ════════════════════════════════════════════════════════════════
    with tab2:
        sample_df  = pd.DataFrame(SAMPLE_DATA)
        sample_csv = sample_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇️ تحميل نموذج CSV للاختبار", sample_csv,
                           "ucaaf_sample.csv", "text/csv")

        uploaded = st.file_uploader("اختر ملف CSV", type=["csv"])

        if uploaded:
            try:
                udf = pd.read_csv(io.StringIO(uploaded.read().decode("utf-8-sig")))
            except Exception as e:
                st.error(f"تعذّر قراءة الملف: {e}")
                return

            missing = [c for c in REQUIRED_COLS if c not in udf.columns]
            if missing:
                st.error(f"الأعمدة التالية مفقودة: {', '.join(missing)}")
                return

            # Fill optional columns if absent
            for col, default in [("icd_code_2",""), ("drugs",""), ("patient_signed",True)]:
                if col not in udf.columns:
                    udf[col] = default

            results = analyze_dataframe(udf)
            total   = len(results)
            errors  = [r for r in results if r.has_errors]
            clean   = total - len(errors)

            kpi_row([
                {"label": "إجمالي السجلات",  "value": total,       "color": "#6366f1"},
                {"label": "سليمة",            "value": clean,       "color": "#22c55e"},
                {"label": "تحتوي أخطاء",      "value": len(errors), "color": "#ef4444",
                 "delta": f"{round(len(errors)/total*100,1)}% من الملفات"},
            ])

            if not errors:
                st.success("✅ جميع السجلات سليمة — لا توجد أخطاء")
                return

            # Build flat error table
            all_errors = []
            for r in errors:
                for e in r.errors:
                    all_errors.append({
                        "رقم المطالبة": r.claim_id,
                        "كود الخطأ":    e["code"],
                        "الخطورة":      e["level"],
                        "وصف الخطأ":   e["msg"],
                        "الحل المقترح": e.get("fix", ""),
                    })
            err_df = pd.DataFrame(all_errors)

            # Chart
            st.plotly_chart(
                error_bar_chart(err_df["وصف الخطأ"], "توزيع الأخطاء المكتشفة"),
                use_container_width=True,
            )

            # Severity breakdown
            col1, col2 = st.columns(2)
            with col1:
                high_cnt = (err_df["الخطورة"] == "عالي").sum()
                st.metric("أخطاء عالية الخطورة 🔴", high_cnt)
            with col2:
                med_cnt = (err_df["الخطورة"] == "متوسط").sum()
                st.metric("أخطاء متوسطة الخطورة 🟡", med_cnt)

            st.markdown("### تفاصيل الأخطاء مع الحلول")
            st.dataframe(err_df, use_container_width=True, hide_index=True)

            csv_out = err_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button("⬇️ تصدير الأخطاء مع الحلول (CSV)",
                               csv_out, "ucaaf_errors_with_fixes.csv", "text/csv")

    # ════════════════════════════════════════════════════════════════
    with tab3:
        st.markdown("### مرجع سريع — أكواد ICD-10 الشائعة في العيادة")
        ref = [
            {"ICD-10": "K29.70", "الوصف": "التهاب المعدة بسبب H. pylori",
             "أكواد CPT المقبولة": "99213, 99214",
             "ملاحظة": "✅ استخدمه مع Riack Plus / Clarithromycin"},
            {"ICD-10": "K29.7",  "الوصف": "التهاب المعدة غير محدد",
             "أكواد CPT المقبولة": "99213, 99214",
             "ملاحظة": "⚠️ لا يبرر وصف Riack Plus أو Daroxime"},
            {"ICD-10": "R11",    "الوصف": "غثيان وقيء",
             "أكواد CPT المقبولة": "—",
             "ملاحظة": "🚫 عَرَض — يجب أن يكون 2nd code وليس Primary"},
            {"ICD-10": "J45.9",  "الوصف": "ربو غير محدد",
             "أكواد CPT المقبولة": "99213, 99214, 94640",
             "ملاحظة": "⚠️ لا يبرر كورتيزون جهازي — استخدم J45.5 للحالات الحادة"},
            {"ICD-10": "J45.5",  "الوصف": "ربو مستمر شديد",
             "أكواد CPT المقبولة": "99213, 99214, 94640",
             "ملاحظة": "✅ يبرر Dexamethasone / Prednisolone"},
            {"ICD-10": "J45.4",  "الوصف": "ربو مستمر متوسط",
             "أكواد CPT المقبولة": "99213, 99214, 94640",
             "ملاحظة": "✅ يبرر الكورتيزون الجهازي"},
            {"ICD-10": "J18.9",  "الوصف": "التهاب رئوي",
             "أكواد CPT المقبولة": "99213, 99214, 71046",
             "ملاحظة": "✅ يبرر المضادات الحيوية"},
            {"ICD-10": "E11.9",  "الوصف": "سكري النوع الثاني",
             "أكواد CPT المقبولة": "99213, 99214, 80047, 83036", "ملاحظة": ""},
            {"ICD-10": "I10",    "الوصف": "ارتفاع ضغط الدم",
             "أكواد CPT المقبولة": "99213, 99214, 93000", "ملاحظة": ""},
            {"ICD-10": "B96.81", "الوصف": "H. pylori كعامل مُسبِّب",
             "أكواد CPT المقبولة": "—",
             "ملاحظة": "✅ يُضاف كـ 2nd code لتبرير العلاج الثلاثي"},
        ]
        st.dataframe(pd.DataFrame(ref), use_container_width=True, hide_index=True)

        st.markdown("### الأخطاء الأكثر شيوعاً في العيادة")
        tips = [
            ("ERR-06", "عالي",  "كود عَرَض (R11, R51...) كتشخيص رئيسي",
             "ضع التشخيص السببي في الأول والعَرَض في الثاني"),
            ("ERR-07", "عالي",  "علاج H. pylori (Riack Plus) بدون كود K29.70",
             "أضف K29.70 أو B96.81 كلما وُصف Riack Plus أو Clarithromycin"),
            ("ERR-08", "عالي",  "مضاد حيوي (Daroxime/Cefuroxime) بدون تشخيص عدوى",
             "تأكد أن التشخيص يبرر المضاد أو أضف الكود الصحيح"),
            ("ERR-10", "عالي",  "كورتيزون جهازي مع J45.9 — يُقبل فقط مع J45.4 أو J45.5",
             "غيّر الكود إلى J45.5 إذا كانت الحالة شديدة أو احذف الكورتيزون الجهازي"),
            ("ERR-11", "عالي",  "ثلاثة كورتيزونات في وصفة واحدة (Pulmicort + Dexamethasone + Respred)",
             "احتفظ بنوع واحد أو اثنين بمبرر سريري موثّق"),
            ("ERR-12", "متوسط", "كود الدواء في السطر يختلف عن التشخيص الرئيسي (J45.5 vs J45.9)",
             "وحّد كود ICD في جميع سطور الوصفة"),
            ("ERR-01", "عالي",  "عدم تطابق ICD مع CPT",
             "راجع جدول الأكواد في هذا التبويب"),
            ("ERR-02", "عالي",  "تجاوز الحد المالي (5000 ر.س) بدون موافقة مسبقة",
             "احصل على Prior Authorization قبل الإرسال"),
        ]
        for code, level, prob, fix in tips:
            badge = "🔴" if level == "عالي" else "🟡"
            st.markdown(
                f"""
                <div style="background:#1e293b;border-radius:8px;padding:12px 16px;
                            border-left:4px solid {'#ef4444' if level=='عالي' else '#f59e0b'};margin:5px 0">
                  <span style="color:#94a3b8;font-size:12px">{badge} {code}</span>
                  <div style="color:#f1f5f9;font-size:14px">{prob}</div>
                  <div style="color:#22c55e;font-size:12px">✅ {fix}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
