def test_create_user(client):
    """Test user creation endpoint"""
    response = client.post(
        "/api/v1/users",
        json={"email": "test@example.com", "password": "secret123"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"