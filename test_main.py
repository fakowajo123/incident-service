# incident-service/test_main.py
import pytest
from fastapi.testclient import TestClient
# We import the main app and the DB store to test the core logic
from main import app, incidents_db, next_id 
from models import Severity, Status
from datetime import datetime

# Use the TestClient with the main FastAPI app
client = TestClient(app)

test_incident_data = {
    "title": "Authentication Service Degraded",
    "description": "Login attempts are failing 10% of the time.",
    "severity": Severity.CRITICAL.value 
}

# --- Fixture to Reset DB between tests ---
@pytest.fixture(autouse=True)
def cleanup_db():
    """Clears the in-memory database and resets the ID counter before each test."""
    incidents_db.clear()
    global next_id
    next_id = 1
    yield # Executes test

# --- Test Cases ---

def test_create_and_read_incident():
    """Test POST /incidents and GET /incidents/{id}"""
    response = client.post("/incidents", json=test_incident_data)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == test_incident_data["title"]
    assert data["id"] == 1
    
    # Test GET (Read One)
    response = client.get(f"/incidents/{data['id']}")
    assert response.status_code == 200

def test_update_incident_status():
    """Test PUT /incidents/{id} for status change"""
    
    create_response = client.post("/incidents", json=test_incident_data)
    incident_id = create_response.json()["id"]
    
    # Test PUT (Update Status)
    update_payload = {"status": Status.RESOLVED.value}
    response = client.put(f"/incidents/{incident_id}", json=update_payload)
    
    assert response.status_code == 200
    updated_data = response.json()
    assert updated_data["status"] == Status.RESOLVED.value
    
    # Check that updated_at is later than created_at (shows an update occurred)
    created_at = datetime.fromisoformat(updated_data["created_at"].replace('Z', '+00:00'))
    updated_at = datetime.fromisoformat(updated_data["updated_at"].replace('Z', '+00:00'))
    assert updated_at > created_at


def test_delete_incident():
    """Test DELETE /incidents/{id}"""
    create_response = client.post("/incidents", json=test_incident_data)
    incident_id = create_response.json()["id"]
    
    # Test DELETE
    response = client.delete(f"/incidents/{incident_id}")
    assert response.status_code == 204
    
    # Verify deletion
    verify_response = client.get(f"/incidents/{incident_id}")
    assert verify_response.status_code == 404
