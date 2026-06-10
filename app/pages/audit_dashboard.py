"""
لوحة التدقيق وإدارة جودة التأمين — UCAAF Audit Dashboard
المحور: الأطباء والتخصصات → حالات كل طبيب → تحليل الأخطاء → تصدير PDF/Excel
"""
import io
import json
from datetime import date
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px

from app.ucaaf_analyzer import analyze

DOCTORS_PATH = Path(__file__).parent.parent.parent / "data" / "doctors.json"


# ─── PDF generator ────────────────────────────────────────────────────────────
def _generate_pdf(records: list, doc_name: str, specialty: str) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                     Table, TableStyle, HRFlowable)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import mm

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            rightMargin=15*mm, leftMargin=15*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("Title", parent=styles["Heading1"],
                                  fontSize=16, leading=20,
                                  textColor=colors.HexColor("#0f172a"),
                                  alignment=1)
    sub_style   = ParagraphStyle("Sub", parent=styles["Normal"],
                                  fontSize=10, leading=14,
                                  textColor=colors.HexColor("#475569"),
                                  alignment=1)
    cell_style  = ParagraphStyle("Cell", parent=styles["Normal"],
                                  fontSize=8, leading=11,
                                  textColor=colors.HexColor("#1e293b"))

    story = []

    # Header
    story.append(Paragraph("Al-Huda Medical Center", title_style))
    story.append(Paragraph("UCAAF Audit Quality Report", sub_style))
    story.append(HRFlowable(width="100%", thickness=1,
                             color=colors.HexColor("#6366f1"), spaceAfter=8))
    story.append(Paragraph(
        f"<b>Doctor:</b> {doc_name} &nbsp;&nbsp; "
        f"<b>Specialty:</b> {specialty} &nbsp;&nbsp; "
        f"<b>Date:</b> {date.today().strftime('%Y-%m-%d')}",
        sub_style))
    story.append(Spacer(1, 10*mm))

    # Summary row
    total   = len(records)
    with_err = sum(1 for r in records if r["الأخطاء"] != "✅ سليمة")
    summary_data = [
        ["إجمالي الحالات", "حالات بأخطاء", "حالات سليمة", "نسبة الأخطاء"],
        [str(total), str(with_err), str(total - with_err),
         f"{round(with_err/total*100,1)}%" if total else "0%"],
    ]
    st_tbl = Table(summary_data, colWidths=[38*mm]*4)
    st_tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,0), colors.HexColor("#6366f1")),
        ("TEXTCOLOR",   (0,0), (-1,0), colors.white),
        ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1), 9),
        ("ALIGN",       (0,0), (-1,-1), "CENTER"),
        ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1),
         [colors.HexColor("#f1f5f9"), colors.white]),
        ("GRID",        (0,0), (-1,-1), 0.4, colors.HexColor("#cbd5e1")),
        ("TOPPADDING",  (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0), (-1,-1), 5),
    ]))
    story.append(st_tbl)
    story.append(Spacer(1, 8*mm))

    # Main table
    headers = ["رقم المطالبة", "رقم المريض", "ICD-10", "CPT", "الأخطاء المكتشفة", "الحل المقترح", "الخطورة"]
    col_w   = [28*mm, 25*mm, 18*mm, 18*mm, 55*mm, 50*mm, 18*mm]

    table_data = [[Paragraph(f"<b>{h}</b>", cell_style) for h in headers]]
    for r in records:
        row_color = colors.HexColor("#fef2f2") if r["الخطورة"] == "عالي" \
               else colors.HexColor("#fffbeb") if r["الخطورة"] == "متوسط" \
               else colors.white
        table_data.append([
            Paragraph(str(r["رقم المطالبة"]), cell_style),
            Paragraph(str(r["رقم المريض"]),   cell_style),
            Paragraph(str(r["ICD"]),           cell_style),
            Paragraph(str(r["CPT"]),           cell_style),
            Paragraph(str(r["الأخطاء"]),       cell_style),
            Paragraph(str(r["الحل"]),          cell_style),
            Paragraph(str(r["الخطورة"]),       cell_style),
        ])

    main_tbl = Table(table_data, colWidths=col_w, repeatRows=1)
    main_tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0), colors.HexColor("#0f172a")),
        ("TEXTCOLOR",    (0,0), (-1,0), colors.white),
        ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,-1), 8),
        ("ALIGN",        (0,0), (-1,-1), "CENTER"),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("GRID",         (0,0), (-1,-1), 0.4, colors.HexColor("#cbd5e1")),
        ("TOPPADDING",   (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0), (-1,-1), 4),
        ("ROWBACKGROUNDS",(0,1), (-1,-1),
         [colors.HexColor("#f8fafc"), colors.white]),
    ]))
    story.append(main_tbl)

    # Footer
    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width="100%", thickness=0.5,
                             color=colors.HexColor("#cbd5e1")))
    story.append(Paragraph(
        "Generated by AlHuda Med Platform — UCAAF Quality Audit System",
        ParagraphStyle("Footer", parent=styles["Normal"],
                       fontSize=7, textColor=colors.HexColor("#94a3b8"),
                       alignment=1)))

    doc.build(story)
    buf.seek(0)
    return buf.read()


# ─── Main render ──────────────────────────────────────────────────────────────
def render(df: pd.DataFrame, user: dict):
    st.markdown("## 🩺 لوحة التدقيق وجودة التأمين")
    st.caption("تدقيق أخطاء اليوكاف لكل طبيب — ICD-10 | CPT | التواقيع | الموافقات")
    st.divider()

    # ── Ensure clean dataframe ────────────────────────────────────────
    for col in ["doctor_name","doctor_id","specialty","status","errors",
                "error_count","amount","recovered","icd_code","cpt_code",
                "claim_id","patient_id","patient_name","service_date"]:
        if col not in df.columns:
            df[col] = "" if col not in ["amount","recovered","error_count"] else 0
    df["amount"]    = pd.to_numeric(df["amount"],    errors="coerce").fillna(0)
    df["recovered"] = pd.to_numeric(df["recovered"], errors="coerce").fillna(0)
    df["errors"]    = df["errors"].fillna("")
    df["specialty"] = df["specialty"].fillna("غير محدد")

    # ── Load doctors list ─────────────────────────────────────────────
    doctors_json = []
    if DOCTORS_PATH.exists():
        doctors_json = json.loads(DOCTORS_PATH.read_text(encoding="utf-8"))

    # Build doctors summary from doctors.json + case counts from df
    doc_rows = []
    for d in doctors_json:
        did   = str(d["id"])
        dname = d["name"]
        spec  = d.get("specialty", "غير محدد")
        count = len(df[df["doctor_id"].astype(str) == did]) if len(df) else 0
        doc_rows.append({
            "doctor_id": did,
            "الاسم":     dname,
            "التخصص":    spec,
            "عدد الحالات": count,
        })

    docs_df = pd.DataFrame(doc_rows) if doc_rows else pd.DataFrame(
        columns=["doctor_id","الاسم","التخصص","عدد الحالات"])

    # ── Section 1: Doctors table ──────────────────────────────────────
    st.markdown("### 🗂️ الأطباء والتخصصات")

    if docs_df.empty:
        st.info("لا يوجد أطباء مسجلون. أضفهم من **⚙️ الإعدادات**.")
        return

    # Color code case count
    def _color_count(val):
        if val == 0:   return "color: #94a3b8"
        if val < 5:    return "color: #f59e0b"
        return "color: #22c55e"

    display_docs = docs_df[["الاسم","التخصص","عدد الحالات"]].copy()
    st.dataframe(
        display_docs.style.applymap(_color_count, subset=["عدد الحالات"]),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    # ── Section 2: Doctor selector + analysis ────────────────────────
    st.markdown("### 🔍 تحليل حالات طبيب محدد")

    doc_options = docs_df["الاسم"].tolist()
    selected_name = st.selectbox("اختر الطبيب", doc_options, key="audit_doc_sel")

    sel_row   = docs_df[docs_df["الاسم"] == selected_name].iloc[0]
    sel_id    = sel_row["doctor_id"]
    sel_spec  = sel_row["التخصص"]

    # Filter cases for this doctor
    doc_df = df[df["doctor_id"].astype(str) == sel_id].copy()

    col1, col2, col3 = st.columns(3)
    col1.metric("إجمالي الحالات", len(doc_df))
    col2.metric("المبلغ الإجمالي", f"{doc_df['amount'].sum():,.0f} ر.س")
    col3.metric("التخصص", sel_spec)

    if len(doc_df) == 0:
        st.info(f"لا توجد حالات مسجلة لـ {selected_name} بعد.")
        st.caption("أضف حالات من **📦 معالجة جماعية**.")
        return

    # Run analyzer on each case
    records = []
    for _, row in doc_df.iterrows():
        case = row.to_dict()
        try:
            result = analyze(case)
            errs = result.errors
            sev  = result.severity if errs else "سليمة"
        except Exception:
            errs, sev = [], "سليمة"

        err_text = " | ".join(e["msg"] for e in errs) if errs else "✅ سليمة"
        fix_text = " | ".join(e["fix"] for e in errs) if errs else "جاهزة للإرسال"
        records.append({
            "رقم المطالبة": str(row.get("claim_id","—")),
            "رقم المريض":   str(row.get("patient_id","—")),
            "المريض":       str(row.get("patient_name","—")),
            "تاريخ الخدمة": str(row.get("service_date","—")),
            "ICD":          str(row.get("icd_code","—")),
            "CPT":          str(row.get("cpt_code","—")),
            "المبلغ":       f"{float(row.get('amount',0)):,.0f}",
            "الأخطاء":      err_text,
            "الحل":         fix_text,
            "الخطورة":      sev,
        })

    result_df = pd.DataFrame(records)

    # Color rows by severity
    def _row_color(row):
        if row["الخطورة"] == "عالي":
            return ["background-color: rgba(239,68,68,0.12)"] * len(row)
        if row["الخطورة"] == "متوسط":
            return ["background-color: rgba(245,158,11,0.10)"] * len(row)
        return ["background-color: rgba(34,197,94,0.07)"] * len(row)

    err_count  = sum(1 for r in records if r["الأخطاء"] != "✅ سليمة")
    clean_count= len(records) - err_count

    # Mini KPIs
    k1, k2, k3 = st.columns(3)
    k1.metric("حالات بأخطاء ⚠️", err_count,
              delta=f"{round(err_count/len(records)*100,1)}%" if records else "0%",
              delta_color="inverse")
    k2.metric("حالات سليمة ✅", clean_count)
    k3.metric("إجمالي الأخطاء",
              sum(len(r["الأخطاء"].split("|")) for r in records
                  if r["الأخطاء"] != "✅ سليمة"))

    st.markdown(f"#### نتائج تحليل حالات {selected_name}")
    st.dataframe(
        result_df.style.apply(_row_color, axis=1),
        use_container_width=True,
        hide_index=True,
    )

    # ── Error chart ───────────────────────────────────────────────────
    all_errs = [e for r in records for e in r["الأخطاء"].split(" | ")
                if r["الأخطاء"] != "✅ سليمة"]
    if all_errs:
        top_errs = pd.Series(all_errs).value_counts().head(8).reset_index()
        top_errs.columns = ["الخطأ","التكرار"]
        fig = px.bar(top_errs, x="التكرار", y="الخطأ", orientation="h",
                     color="التكرار",
                     color_continuous_scale=["#f59e0b","#ef4444"],
                     title=f"أكثر الأخطاء تكراراً — {selected_name}")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                          plot_bgcolor="rgba(0,0,0,0)",
                          font_color="#f1f5f9",
                          coloraxis_showscale=False,
                          yaxis=dict(autorange="reversed"),
                          margin=dict(t=40,b=10))
        st.plotly_chart(fig, use_container_width=True)

    # ── Export buttons ────────────────────────────────────────────────
    st.divider()
    st.markdown("### 📤 تصدير التقرير")
    c1, c2 = st.columns(2)

    with c1:
        excel_buf = io.BytesIO()
        with pd.ExcelWriter(excel_buf, engine="xlsxwriter") as writer:
            result_df.to_excel(writer, index=False, sheet_name="UCAAF_Errors")
            ws = writer.sheets["UCAAF_Errors"]
            ws.set_column(0, len(result_df.columns)-1, 20)
        excel_buf.seek(0)
        st.download_button(
            f"📥 تصدير Excel — {selected_name}",
            excel_buf.read(),
            f"UCAAF_{sel_id}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with c2:
        try:
            pdf_bytes = _generate_pdf(records, selected_name, sel_spec)
            st.download_button(
                f"📄 تصدير PDF — {selected_name}",
                pdf_bytes,
                f"UCAAF_Audit_{sel_id}.pdf",
                "application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"تعذّر توليد PDF: {e}")
