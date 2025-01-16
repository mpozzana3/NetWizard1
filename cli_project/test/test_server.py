import pytest
from server.server import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()

def test_echo_command(client):
    response = client.post("/execute", json={"command": "echo", "args": ["hello", "world"]})
    assert response.status_code == 200
    assert response.json["result"] == "hello world"

def test_add_command(client):
    response = client.post("/execute", json={"command": "add", "args": ["1", "2", "3"]})
    assert response.status_code == 200
    assert response.json["result"] == 6
