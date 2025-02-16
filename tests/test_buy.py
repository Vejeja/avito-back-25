import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def get_auth_token(username="buyer", password="password"):
    response = client.post("/api/auth", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["token"]

def test_buy_item():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Покупка мерча (например, t-shirt за 80 монет)
    response = client.get("/api/buy/t-shirt", headers=headers)
    assert response.status_code == 200
    assert "Successfully purchased t-shirt" in response.json()["detail"]
    
    # Проверка информации – наличие купленного товара в инвентаре
    response = client.get("/api/info", headers=headers)
    info = response.json()
    inventory = {item["type"]: item["quantity"] for item in info.get("inventory", [])}
    assert inventory.get("t-shirt", 0) >= 1
