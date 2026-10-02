from typing import Any, Dict
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO


def generate_forensic_pdf(report: Dict[str, Any]) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Forensic Evidence Report", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Evidence ID: {report.get('evidence_id')}", styles["Normal"]))
    story.append(Paragraph(f"Hash: {report.get('evidence_hash')}", styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Content", styles["Heading2"]))
    story.append(Paragraph(report.get("content", ""), styles["Normal"]))
    story.append(Spacer(1, 12))

    triage = report.get("triage", {})
    if triage:
        story.append(Paragraph("Triage Result", styles["Heading2"]))
        data = [
            ["Prediction", triage.get("prediction", "")],
            ["Confidence", f"{triage.get('confidence', 0):.2f}"],
            ["Risk Level", triage.get("risk_level", "")],
            ["Model Version", triage.get("model_version", "")],
        ]
        t = Table(data, colWidths=[200, 300])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(t)
        story.append(Spacer(1, 12))

    reviews = report.get("examiner_reviews", [])
    if reviews:
        story.append(Paragraph("Examiner Reviews", styles["Heading2"]))
        for r in reviews:
            story.append(Paragraph(f"Decision: {r.get('decision')} — {r.get('notes', '')}", styles["Normal"]))
        story.append(Spacer(1, 12))

    audit = report.get("audit_trail", [])
    if audit:
        story.append(Paragraph("Audit Trail", styles["Heading2"]))
        for entry in audit:
            story.append(Paragraph(f"{entry.get('created_at')} — {entry.get('event_type')} — {entry.get('actor')}", styles["Normal"]))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
