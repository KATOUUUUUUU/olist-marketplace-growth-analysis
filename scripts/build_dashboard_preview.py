"""Wrap verified Tableau presentation screenshots in a two-page preview PDF."""
from pathlib import Path

from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / "dashboard"
IMAGES = ["01_market_priorities.jpg", "02_growth_customer_experience.jpg"]


def main():
    output = DASHBOARD / "olist_growth_dashboard_preview.pdf"
    pdf = canvas.Canvas(str(output), pagesize=(1200, 800))
    pdf.setTitle("Where Should Olist Grow Next? | Dashboard Preview")
    pdf.setAuthor("Liang Yao")
    pdf.setSubject("Static screenshots of the local Tableau workbook; not a native PDF export")
    for index, filename in enumerate(IMAGES, 1):
        image = ImageReader(str(DASHBOARD / filename))
        width, height = image.getSize()
        scale = min(1176 / width, 756 / height)
        pdf.drawImage(image, (1200 - width * scale) / 2, 40,
                      width=width * scale, height=height * scale)
        pdf.setFont("Helvetica", 9)
        pdf.setFillColorRGB(0.3, 0.3, 0.3)
        pdf.drawString(16, 16, "Tableau presentation screenshot | Interactive version: olist_growth_dashboard.twbx")
        pdf.drawRightString(1184, 16, f"Liang Yao | {index} / 2")
        pdf.showPage()
    pdf.save()
    print(output)


if __name__ == "__main__":
    main()
