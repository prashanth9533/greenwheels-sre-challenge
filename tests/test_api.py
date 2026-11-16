
def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_lease_event(client):
    response = client.post(
        "/leases/events",
        json={
            "driver_id": "GW1001",
            "event_type": "payment_made",
        },
    )

    assert response.status_code == 202
    assert response.json()["event"]["driver_id"] == "GW1001"
    assert response.json()["event"]["event_type"] == "payment_made"


def test_get_lease_after_event(client):
    client.post(
        "/leases/events",
        json={
            "driver_id": "GW1001",
            "event_type": "payment_made",
        },
    )

    response = client.get("/leases/GW1001")

    assert response.status_code == 200
    assert response.json()["lease_status"] == "active"


def test_metrics_endpoint(client):
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "http_requests_total" in response.text
