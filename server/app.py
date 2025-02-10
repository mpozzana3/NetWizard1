from flask import Flask, render_template, request
import xml.etree.ElementTree as ET

app = Flask(__name__)

# Funzione per convertire XML in HTML formattato
def xml_to_html(xml_file):
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        return format_element(root)
    except Exception as e:
        return f"<p>Errore durante la lettura dell'XML: {e}</p>"

def format_element(elem, level=0):
    indent = "&nbsp;" * (level * 4)  # Aggiunge indentazione per leggibilità
    html = f"{indent}<b>{elem.tag}</b>: {elem.text.strip() if elem.text else ''}<br>"

    for attr, value in elem.attrib.items():
        html += f"{indent}&nbsp;&nbsp;🔹 <i>{attr}</i>: {value}<br>"

    for child in elem:
        html += format_element(child, level + 1)
    
    return html

@app.route("/")
def home():
    return render_template("index.html", content=xml_to_html("nmap_advanced_portscan.xml"))

if __name__ == "__main__":
   app.run(debug=True, host='0.0.0.0', port=5005)
