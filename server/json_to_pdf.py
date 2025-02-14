import json
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def json_to_pdf(json_file, pdf_file):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    c = canvas.Canvas(pdf_file, pagesize=A4)
    c.setFont("Helvetica", 10)

    y_position = 800  # Posizione iniziale verticale

    def write_line(text, y):
        c.drawString(50, y, text)

    for key, value in data.items():
        text = f"{key}: {json.dumps(value, ensure_ascii=False, indent=2)}"
        if y_position < 50:
            c.showPage()  # Nuova pagina se non c'è più spazio
            y_position = 800
        write_line(text, y_position)
        y_position -= 20

    c.save()
    print(f"PDF generato: {pdf_file}")

# Esegui lo script dalla riga di comando
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Uso: python json_to_pdf.py input.json output.pdf")
        sys.exit(1)

    json_to_pdf(sys.argv[1], sys.argv[2])
