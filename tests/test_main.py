from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs_url": f"{settings.API_PREFIX}{settings.DOCS_URL}" if settings.DOCS_URL else None,
        "health_url": f"{settings.API_PREFIX}/health",
        "webhook_url": f"{settings.API_PREFIX}/whatsapp/webhook"
    }
