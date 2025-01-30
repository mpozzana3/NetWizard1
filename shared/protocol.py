def create_request(command, args):
    """Crea un JSON standard per la richiesta."""
    return {"command": command, "args": args}

def parse_response(response):
    """Parsa la risposta JSON."""
    return response.get("result", "Errore sconosciuto")
