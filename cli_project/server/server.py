from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/execute", methods=["POST"])
def execute():
    data = request.json
    command = data.get("command")
    args = data.get("args", [])

    if not command:
        return jsonify({"error": "Comando mancante"}), 400

    # Logica dei comandi
    if command == "echo":
        result = " ".join(args)
    elif command == "add":
        try:
            numbers = list(map(int, args))
            result = sum(numbers)
        except ValueError:
            return jsonify({"error": "Argomenti non validi per add"}), 400
    else:
        return jsonify({"error": f"Comando '{command}' non supportato"}), 400

    return jsonify({"result": result})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
