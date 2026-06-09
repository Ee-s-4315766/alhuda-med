"""
معالجة جماعية للحالات الكثيرة — Bulk Processing Engine
رفع Excel/CSV، تحليل فوري، قائمة الأولويات، تصدير تقرير شامل
"""
import io
import streamlit as st
import pandas as pd
import plotly.express as px
from app.ucaaf_analyzer import analyze_dataframe
from app.icd_cpt_db import ICD_DATABASE, CPT_DATABASE
from app.components import kpi_row, alert_box

# ─── Excel template columns ──────────────────────────────────────────────────
TEMPLATE_COLS = [
    "claim_id", "patient_name", "patient_id", "age", "gender",
    "doctor_name", "service_date",
    "icd_code", "icd_code_2", "cpt_code",
    "amount", "approval_no",
    "patient_type",          # outpatient / inpatient
    "ucaf_type",             # UCAF-1 / UCAF-2
    "patient_signed",        # TRUE / FALSE
    "cb_infertility",        # TRUE / FALSE
    "cb_pregnancy",          # TRUE / FALSE
    "chief_complaint",
    "drugs",                 # pipe-separated: riack plus|paracetamol
]

REQUIRED_COLS = [
    "claim_id", "patient_id", "icd_code", "cpt_code",
    "amount", "service_date",
]

# ─── Build Excel template with sample rows ───────────────────────────────────
SAMPLE_ROWS = [
    ["CLM-001","أحمد محمد","P111111",35,"ذكر","د. أحمد الزهراني","2026-05-01",
     "K29.7","R11","99285",800,"","outpatient","UCAF-1",True,False,False,"epigastric pain",
     "pantozol|dansetron|paracetamol"],
    ["CLM-002","نورة سالم","P222222",41,"أنثى","د. نورة الغامدي","2026-05-02",
     "N97.0","","99213",450,"2026/1234","outpatient","UCAF-2",True,False,False,
     "wants to conceive irregular cycle","specialist|prolactin h|fsh"],
    ["CLM-003","خالد عبدالله","P333333",28,"ذكر","د. خالد العتيبي","2026-05-03",
     "J45.9","","94640",600,"APP55555","outpatient","UCAF-1",True,True,True,"",
     "pulmicort|dexamethasone|respred"],
    ["CLM-004","فاطمة علي","P444444",55,"أنثى","د. أحمد الزهراني","2026-05-04",
     "I10","","99213",350,"APP77777","outpatient","UCAF-1",True,True,True,"",
     "amlodipine|losartan"],
    ["CLM-005","محمد الشهري","P555555",30,"ذكر","د. سارة المطيري","2026-05-05",
     "J18.9","","99213",1200,"APP88888","outpatient","UCAF-1",True,True,True,"",
     "azithromycin|paracetamol"],
]


def _build_template() -> bytes:
    df = pd.DataFrame(SAMPLE_ROWS, columns=TEMPLATE_COLS)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="المطالبات")
        # Instructions sheet
        instructions = pd.DataFrame([
            ["claim_id",        "رقم المطالبة",                  "نصي",   "إلزامي", "CLM-001"],
            ["patient_name",    "اسم المريض",                    "نصي",   "اختياري","أحمد محمد"],
            ["patient_id",      "الرقم الطبي",                   "نصي",   "إلزامي", "P123456"],
            ["age",             "العمر بالسنوات",                "رقم",   "اختياري","35"],
            ["gender",          "الجنس",                         "نصي",   "اختياري","ذكر / أنثى"],
            ["doctor_name",     "اسم الطبيب",                    "نصي",   "اختياري","د. أحمد"],
            ["service_date",    "تاريخ الخدمة (YYYY-MM-DD)",     "تاريخ", "إلزامي", "2026-05-01"],
            ["icd_code",        "كود التشخيص الرئيسي",           "نصي",   "إلزامي", "K29.70"],
            ["icd_code_2",      "كود التشخيص الثانوي",           "نصي",   "اختياري","R11"],
            ["cpt_code",        "كود الإجراء CPT",               "نصي",   "إلزامي", "99213"],
            ["amount",          "المبلغ بالريال",                "رقم",   "إلزامي", "500"],
            ["approval_no",     "رقم الموافقة المسبقة",          "نصي",   "اختياري","APP12345"],
            ["patient_type",    "نوع المريض",                    "نصي",   "اختياري","outpatient"],
            ["ucaf_type",       "نوع اليوكاف",                   "نصي",   "اختياري","UCAF-1"],
            ["patient_signed",  "وقّع المريض (TRUE/FALSE)",      "منطقي", "اختياري","TRUE"],
            ["cb_infertility",  "مربع infertility (TRUE/FALSE)", "منطقي", "اختياري","FALSE"],
            ["cb_pregnancy",    "مربع pregnancy (TRUE/FALSE)",   "منطقي", "اختياري","FALSE"],
            ["chief_complaint", "الشكوى الرئيسية",              "نصي",   "اختياري","epigastric pain"],
            ["drugs",           "الأدوية (افصل بـ |)",           "نصي",   "اختياري","riack plus|pantozol"],
        ], columns=["العمود","الوصف","النوع","الإلزامية","مثال"])
        instructions.to_excel(writer, index=False, sheet_name="تعليمات")
    return buf.getvalue()


def _prepare_df(raw: pd.DataFrame) -> pd.DataFrame:
    """Fill missing optional columns with safe defaults."""
    defaults = {
        "icd_code_2": "", "drugs": "", "ucaf_type": "UCAF-1",
        "patient_type": "outpatient", "patient_signed": True,
        "cb_infertility": True, "cb_pregnancy": True,
        "chief_complaint": "", "age": 0, "doctor_name": "",
        "patient_name": "", "gender": "", "approval_no": "",
    }
    for col, val in defaults.items():
        if col not in raw.columns:
            raw[col] = val
        else:
            raw[col] = raw[col].fillna(val)

    for col in ["cb_infertility","cb_pregnancy","patient_signed"]:
        raw[col] = raw[col].astype(str).str.upper().map(
            {"TRUE": True, "FALSE": False, "1": True, "0": False}
        ).fillna(True).astype(bool)

    raw["amount"]  = pd.to_numeric(raw["amount"], errors="coerce").fillna(0)
    raw["service_date"] = raw["service_date"].astype(str).str.strip()
    return raw


def _priority_score(err_count: int, amount: float, level_high: int) -> float:
    """Higher = fix first. Weighs amount lost + number of high-severity errors."""
    return (amount * 0.001) + (level_high * 30) + (err_count * 10)


def render(_df_existing, user):
    st.markdown("## 📦 معالجة جماعية للحالات")
    st.caption("ارفع مئات الحالات دفعةً واحدة — فحص فوري، قائمة أولويات، تقرير جاهز للطباعة")
    st.divider()

    # ── Template download ─────────────────────────────────────────────
    template_bytes = _build_template()
    st.download_button(
        "⬇️ تحميل نموذج Excel للتعبئة",
        template_bytes,
        "ucaaf_template.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    # ── File upload ───────────────────────────────────────────────────
    uploaded = st.file_uploader(
        "ارفع ملف Excel أو CSV يحتوي المطالبات",
        type=["xlsx","xls","csv"],
        help="استخدم نفس أعمدة النموذج أعلاه",
    )

    # Use existing data if no upload
    if uploaded is None:
        use_existing = st.checkbox(
            f"استخدم بيانات العيادة الحالية ({len(_df_existing)} حالة) للعرض التجريبي",
            value=True,
        )
        if not use_existing:
            st.info("ارفع ملف للبدء")
            return
        df = _df_existing.copy()
        is_demo = True
    else:
        is_demo = False
        try:
            if uploaded.name.endswith(".csv"):
                df = pd.read_csv(io.StringIO(uploaded.read().decode("utf-8-sig")))
            else:
                df = pd.read_excel(uploaded)
        except Exception as e:
            st.error(f"تعذّر قراءة الملف: {e}")
            return

        missing = [c for c in REQUIRED_COLS if c not in df.columns]
        if missing:
            st.error(f"الأعمدة التالية مفقودة: {', '.join(missing)}")
            return

        df = _prepare_df(df)

    # ── Run analyzer ──────────────────────────────────────────────────
    with st.spinner("جاري تحليل الحالات..."):
        results = analyze_dataframe(df)

    # Build enriched results table
    rows = []
    for i, (r, (_, row)) in enumerate(zip(results, df.iterrows())):
        high = sum(1 for e in r.errors if e["level"] == "عالي")
        med  = sum(1 for e in r.errors if e["level"] == "متوسط")
        score = _priority_score(len(r.errors), float(row.get("amount",0)), high)
        rows.append({
            "claim_id":     r.claim_id,
            "patient_name": str(row.get("patient_name","")),
            "doctor_name":  str(row.get("doctor_name","")),
            "service_date": str(row.get("service_date","")),
            "icd_code":     str(row.get("icd_code","")),
            "cpt_code":     str(row.get("cpt_code","")),
            "amount":       float(row.get("amount",0)),
            "approval_no":  str(row.get("approval_no","")),
            "status":       str(row.get("status","—")),
            "error_count":  len(r.errors),
            "high_errors":  high,
            "med_errors":   med,
            "errors_detail":"||".join(
                f"[{e['code']}] {e['msg']} → {e['fix']}" for e in r.errors
            ),
            "severity":     r.severity,
            "priority":     round(score, 1),
        })

    rdf = pd.DataFrame(rows)
    errs_df = rdf[rdf["error_count"] > 0].copy()
    clean_df = rdf[rdf["error_count"] == 0]

    # ── KPIs ──────────────────────────────────────────────────────────
    total      = len(rdf)
    err_count  = len(errs_df)
    clean_count= len(clean_df)
    high_count = (rdf["high_errors"] > 0).sum()
    total_at_risk = rdf[rdf["error_count"] > 0]["amount"].sum()

    kpi_row([
        {"label": "إجمالي الحالات",      "value": total,               "color": "#6366f1"},
        {"label": "سليمة ✅",             "value": clean_count,         "color": "#22c55e",
         "delta": f"{round(clean_count/total*100,1)}%"},
        {"label": "تحتاج تصحيح ⚠️",      "value": err_count,           "color": "#f59e0b",
         "delta": f"{round(err_count/total*100,1)}%"},
        {"label": "خطورة عالية 🔴",       "value": high_count,          "color": "#ef4444"},
        {"label": "مبالغ في خطر",         "value": f"{total_at_risk:,.0f} ر.س","color": "#ef4444"},
    ])

    # ── Tabs ──────────────────────────────────────────────────────────
    t1, t2, t3, t4 = st.tabs([
        "🔴 قائمة الأولويات",
        "📊 تحليل الأخطاء",
        "✅ الحالات السليمة",
        "📥 تصدير التقرير",
    ])

    # ════════════════════════════════════════════════════════════════
    with t1:
        st.markdown(f"### {err_count} حالة تحتاج تصحيح — مرتبة حسب الأولوية")
        st.caption("الأولوية = المبلغ + عدد الأخطاء العالية × 30 — الأعلى يُصحَّح أولاً")

        if err_count == 0:
            st.success("✅ جميع الحالات سليمة!")
        else:
            sorted_errs = errs_df.sort_values("priority", ascending=False).reset_index(drop=True)

            # Quick filters
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                sev_f = st.selectbox("الخطورة", ["الكل","عالي","متوسط"], key="bulk_sev")
            with col_f2:
                doc_f = st.selectbox(
                    "الطبيب",
                    ["الكل"] + sorted(errs_df["doctor_name"].dropna().unique()),
                    key="bulk_doc",
                )
            with col_f3:
                err_search = st.text_input("بحث برقم المطالبة أو اسم المريض", key="bulk_search")

            view = sorted_errs.copy()
            if sev_f != "الكل":
                view = view[view["severity"] == sev_f]
            if doc_f != "الكل":
                view = view[view["doctor_name"] == doc_f]
            if err_search.strip():
                q = err_search.strip().lower()
                view = view[
                    view["claim_id"].str.lower().str.contains(q) |
                    view["patient_name"].str.lower().str.contains(q)
                ]

            st.caption(f"{len(view)} حالة")

            # Render each claim as a card (first 50, rest paginated)
            page_size = st.select_slider("عدد الحالات في الصفحة", [10,25,50,100], value=25)
            page      = st.number_input("الصفحة", min_value=1,
                                        max_value=max(1, -(-len(view)//page_size)), value=1)
            start     = (page-1)*page_size
            chunk     = view.iloc[start:start+page_size]

            for _, row in chunk.iterrows():
                sev_color = "#ef4444" if row["severity"]=="عالي" else "#f59e0b"
                sev_icon  = "🔴" if row["severity"]=="عالي" else "🟡"
                errors_html = "".join(
                    f'<div style="color:#fca5a5;font-size:12px;margin:2px 0">• '
                    f'{line}</div>'
                    for line in row["errors_detail"].split("||") if line
                )
                st.markdown(
                    f"""
                    <div style="background:#1e293b;border-radius:10px;padding:14px 18px;
                                border-left:4px solid {sev_color};margin:6px 0">
                      <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px">
                        <div>
                          <span style="color:#94a3b8;font-size:12px">{sev_icon} الأولوية {row['priority']:.0f}</span>
                          <div style="color:#f1f5f9;font-size:15px;font-weight:700">
                            {row['claim_id']} — {row['patient_name']}
                          </div>
                          <span style="color:#94a3b8;font-size:12px">
                            {row['doctor_name']} | {row['service_date']} |
                            ICD: {row['icd_code']} | CPT: {row['cpt_code']}
                          </span>
                        </div>
                        <div style="text-align:left">
                          <div style="color:#ef4444;font-size:1.1rem;font-weight:700">
                            {row['amount']:,.0f} ر.س
                          </div>
                          <span style="background:{sev_color};color:white;border-radius:4px;
                                       padding:2px 8px;font-size:11px">
                            {row['error_count']} أخطاء
                          </span>
                        </div>
                      </div>
                      <div style="margin-top:10px;padding-top:8px;
                                  border-top:1px solid #334155">
                        {errors_html}
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # ════════════════════════════════════════════════════════════════
    with t2:
        all_errs = []
        for _, row in errs_df.iterrows():
            for line in row["errors_detail"].split("||"):
                if not line:
                    continue
                # parse [ERR-XX] msg → fix
                parts = line.split(" → ")
                all_errs.append({
                    "claim_id": row["claim_id"],
                    "doctor":   row["doctor_name"],
                    "خطأ":     parts[0] if parts else line,
                    "حل":      parts[1] if len(parts) > 1 else "",
                })

        if not all_errs:
            st.success("لا أخطاء")
        else:
            err_series = pd.Series([e["خطأ"] for e in all_errs])

            col1, col2 = st.columns(2)
            with col1:
                top = err_series.value_counts().head(10).reset_index()
                top.columns = ["الخطأ","التكرار"]
                fig = px.bar(
                    top, x="التكرار", y="الخطأ", orientation="h",
                    color="التكرار", color_continuous_scale=["#6366f1","#ef4444"],
                    title="أكثر الأخطاء تكراراً",
                )
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#f1f5f9", coloraxis_showscale=False,
                    yaxis=dict(autorange="reversed"),
                    margin=dict(t=50,b=10,l=10,r=10),
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                doc_err = pd.DataFrame(all_errs).groupby("doctor").size() \
                            .reset_index(name="أخطاء").sort_values("أخطاء", ascending=False)
                fig2 = px.bar(
                    doc_err, x="doctor", y="أخطاء",
                    color="أخطاء", color_continuous_scale=["#f59e0b","#ef4444"],
                    title="أخطاء لكل طبيب",
                    labels={"doctor":"الطبيب"},
                )
                fig2.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#f1f5f9", coloraxis_showscale=False,
                    margin=dict(t=50,b=10),
                )
                st.plotly_chart(fig2, use_container_width=True)

            # ICD mismatch table
            st.markdown("### تفاصيل أخطاء الترميز")
            err_df_show = pd.DataFrame(all_errs)[["claim_id","doctor","خطأ","حل"]]
            st.dataframe(err_df_show, use_container_width=True, hide_index=True)

    # ════════════════════════════════════════════════════════════════
    with t3:
        st.markdown(f"### ✅ {len(clean_df)} حالة سليمة — جاهزة للإرسال")
        show_cols = ["claim_id","patient_name","doctor_name","service_date",
                     "icd_code","cpt_code","amount"]
        avail = [c for c in show_cols if c in clean_df.columns]
        st.dataframe(
            clean_df[avail].rename(columns={
                "claim_id":"رقم المطالبة","patient_name":"المريض",
                "doctor_name":"الطبيب","service_date":"تاريخ الخدمة",
                "icd_code":"ICD","cpt_code":"CPT","amount":"المبلغ",
            }),
            use_container_width=True,
            hide_index=True,
        )
        ready_csv = clean_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇️ تصدير الحالات الجاهزة للإرسال",
                           ready_csv, "ready_to_send.csv", "text/csv")

    # ════════════════════════════════════════════════════════════════
    with t4:
        st.markdown("### 📥 تصدير التقارير")

        # Full report
        report_df = rdf.copy()
        report_df.columns = [c.replace("_"," ") for c in report_df.columns]
        full_csv = report_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "⬇️ التقرير الكامل (جميع الحالات) CSV",
            full_csv, "full_report.csv", "text/csv",
        )

        # Errors only with fix guide
        if len(errs_df):
            err_export = errs_df[["claim_id","patient_name","doctor_name",
                                   "service_date","icd_code","cpt_code",
                                   "amount","severity","error_count","errors_detail"]].copy()
            err_export["errors_detail"] = err_export["errors_detail"].str.replace("||","\n")
            err_csv = err_export.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "⬇️ تقرير الأخطاء مع الحلول CSV",
                err_csv, "errors_with_fixes.csv", "text/csv",
            )

            # Excel with two sheets
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                errs_df.to_excel(writer, index=False, sheet_name="حالات بأخطاء")
                clean_df.to_excel(writer, index=False, sheet_name="حالات سليمة")
                # Summary sheet
                summary = pd.DataFrame([
                    ["إجمالي الحالات", total],
                    ["سليمة",          clean_count],
                    ["تحتاج تصحيح",   err_count],
                    ["خطورة عالية",    high_count],
                    ["مبالغ في خطر",  f"{total_at_risk:,.0f} ر.س"],
                ], columns=["البيان","القيمة"])
                summary.to_excel(writer, index=False, sheet_name="ملخص")
            buf.seek(0)
            st.download_button(
                "⬇️ تقرير Excel شامل (3 صفحات)",
                buf.read(),
                "ucaaf_bulk_report.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        st.divider()
        st.markdown("### 🖨️ ملخص جاهز للطباعة")
        st.markdown(
            f"""
            <div style="background:#1e293b;border-radius:12px;padding:24px;
                        font-family:monospace;color:#f1f5f9;line-height:1.9">
              <div style="font-size:1.2rem;font-weight:700;color:#6366f1;margin-bottom:12px">
                تقرير مطالبات التأمين — عيادة الهدى
              </div>
              <hr style="border-color:#334155">
              إجمالي الحالات:          <b>{total}</b><br>
              الحالات السليمة:         <b style="color:#22c55e">{clean_count} ({round(clean_count/total*100,1)}%)</b><br>
              تحتاج تصحيح:            <b style="color:#f59e0b">{err_count} ({round(err_count/total*100,1)}%)</b><br>
              خطورة عالية:            <b style="color:#ef4444">{high_count}</b><br>
              مبالغ في خطر:           <b style="color:#ef4444">{total_at_risk:,.0f} ر.س</b><br>
              <hr style="border-color:#334155">
              أكثر خطأ تكراراً: <b>{err_series.value_counts().idxmax() if 'err_series' in dir() and len(err_series) else '—'}</b>
            </div>
            """,
            unsafe_allow_html=True,
        )
