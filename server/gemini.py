import google.generativeai as genai
import xml.etree.ElementTree as ET
import sys

def analyze_nmap_scan(file_path, api_key):
  """
  Analyzes an Nmap scan.xml file and generates a summary using the Gemini API.

  Args:
    file_path: Path to the scan.xml file.
    api_key: Your Google Cloud API key.

  Returns:
    The generated text.
  """

  genai.configure(api_key=api_key)
  model = genai.GenerativeModel("gemini-1.5-flash")

  try:
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Extract open ports
    open_ports = []
    for host in root.findall('host'):
      for port in host.findall('ports/port[@state="open"]'):
        port_id = port.attrib['portid']
        service_name = port.find('service').get('name')
        open_ports.append(f"{port_id}/{port.attrib['protocol']} ({service_name})")

    if open_ports:
      port_list = ", ".join(open_ports)
      prompt = f"Analyze the following Nmap scan results: \n" \
               f"Host: {host.find('address').attrib['addr']}\n" \
               f"Open Ports: {port_list}\n" \
               f"Provide a exhaustive summary of the scan findings, including any potential security implications."
    else:
      prompt = f"Host: {host.find('address').attrib['addr']}\n" \
               f"No open ports found. Provide a exhaustive summary of the scan findings."

    response = model.generate_content(prompt)
    return response.text

  except FileNotFoundError:
    print(f"Error: File not found: {file_path}")
    return None
  except Exception as e:
    print(f"An error occurred: {e}")
    return None

if __name__ == "__main__":
  if len(sys.argv) != 3:
    print("Usage: python3 gemini.py <path/to/scan.xml> <YOUR_API_KEY>")
    sys.exit(1)

  file_path = sys.argv[1]
  api_key = sys.argv[2]

  generated_text = analyze_nmap_scan(file_path, api_key)

  if generated_text:
    print(generated_text)
