import json

import pytest
from ravelights import RaveLightsApp


@pytest.fixture(scope="session")
def app():
    app = RaveLightsApp(run=False)
    return app.rest_api.flask_app


def test_flask_endpoints_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"<html><head><title>" in response.data


def test_flask_endpoints_rest_settings(client):
    response = client.get("/rest/settings")
    assert response.status_code == 200
    response_dict = json.loads(response.data)
    assert "bpm_base" in response_dict


def test_flask_endpoints_rest_triggers(client):
    response = client.get("/rest/triggers")
    assert response.status_code == 200
    response_dict = json.loads(response.data)
    assert "dimmer" in response_dict


def test_flask_endpoints_rest_devices(client):
    response = client.get("/rest/devices")
    assert response.status_code == 200
    response_dict = json.loads(response.data)
    assert "n_leds" in response_dict[0]


def test_flask_endpoints_rest_meta(client):
    response = client.get("/rest/meta")
    assert response.status_code == 200
    response_dict = json.loads(response.data)
    assert "available_generators" in response_dict


def test_flask_endpoints_rest_effect(client):
    response = client.get("/rest/effect")
    assert response.status_code == 200
    response_dict = json.loads(response.data)
    assert isinstance(response_dict[0], list)
