import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as test_client:
        yield test_client


def test_home_endpoint_v1(client, monkeypatch):
    monkeypatch.setattr("app.APP_VERSION", "v1")

    response = client.get("/")

    assert response.status_code == 200
    assert response.get_json() == {
        "application": "canary-demo",
        "version": "v1",
        "message": "Welcome to Canary Demo v1!",
    }


def test_home_endpoint_v2(client, monkeypatch):
    monkeypatch.setattr("app.APP_VERSION", "v2")

    response = client.get("/")

    assert response.status_code == 200
    assert response.get_json() == {
        "application": "canary-demo",
        "version": "v2",
        "message": "Welcome to Canary Demo v2 - Improved Experience!",
    }


@pytest.mark.parametrize("version", ["v1", "v2"])
def test_health_endpoint(client, monkeypatch, version):
    monkeypatch.setattr("app.APP_VERSION", version)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {
        "status": "healthy",
        "application": "canary-demo",
        "version": version,
    }


@pytest.mark.parametrize("version", ["v1", "v2"])
def test_version_endpoint(client, monkeypatch, version):
    monkeypatch.setattr("app.APP_VERSION", version)

    response = client.get("/version")

    assert response.status_code == 200
    assert response.get_json() == {
        "application": "canary-demo",
        "version": version,
    }
