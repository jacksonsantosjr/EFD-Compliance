import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_upload_route_requires_auth():
    """
    Valida que a rota de upload não permite acesso sem o header de autorização.
    Deve retornar 403 Forbidden (comportamento padrão do FastAPI HTTPBearer).
    """
    response = client.post("/api/upload")
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authenticated"

def test_analyses_list_requires_auth():
    """
    Valida que a listagem de análises exige autenticação.
    """
    response = client.get("/api/analyses")
    assert response.status_code == 403

def test_invalid_token_returns_401():
    """
    Valida que um token inválido (malformado) é rejeitado com 401.
    """
    headers = {"Authorization": "Bearer token-invalido-123"}
    response = client.get("/api/analyses", headers=headers)
    assert response.status_code == 401

def test_export_requires_auth():
    """
    Valida que a rota de exportação exige autenticação (403).
    """
    response = client.get("/api/export/123/pdf")
    assert response.status_code == 403

def test_compare_requires_auth():
    """
    Valida que a rota de comparação exige autenticação (403).
    """
    response = client.post("/api/upload/compare")
    assert response.status_code == 403
