import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def get_auth_token(username, password):
    response = client.post("/api/auth", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["token"]

def test_send_coin():
    # Создаем двух пользователей: alice и bob
    alice_token = get_auth_token("alice", "alicepass")
    bob_token = get_auth_token("bob", "bobpass")
    
    headers_alice = {"Authorization": f"Bearer {alice_token}"}
    
    # alice отправляет 100 монет bob
    response = client.post("/api/sendCoin", json={"toUser": "bob", "amount": 100}, headers=headers_alice)
    assert response.status_code == 200
    
    # Проверяем, что у bob в истории полученных транзакций появилась запись от alice
    headers_bob = {"Authorization": f"Bearer {bob_token}"}
    response = client.get("/api/info", headers=headers_bob)
    info = response.json()
    received = info.get("coinHistory", {}).get("received", [])
    assert any(tx.get("fromUser") == "alice" and tx.get("amount") == 100 for tx in received)
