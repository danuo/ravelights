import json

import pytest
from ravelights import DeviceLightConfig, RaveLightsApp

N_DEVICES = 2
device_config = [DeviceLightConfig(n_lights=2, n_leds=144)] * N_DEVICES


@pytest.fixture(scope="session")
def app():
    app = RaveLightsApp(device_config=device_config)
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
    assert len(response_dict) == N_DEVICES
    assert "dimmer" in response_dict[0]


def test_flask_endpoints_rest_devices(client):
    response = client.get("/rest/devices")
    assert response.status_code == 200
    response_dict = json.loads(response.data)
    assert "linked_to" in response_dict[0]
    assert response_dict[0]["linked_to"] is None


def test_flask_endpoints_rest_meta(client):
    response = client.get("/rest/meta")
    assert response.status_code == 200
    response_dict = json.loads(response.data)
    assert "available_generators" in response_dict
    assert "n_leds" in response_dict["device_meta"][0]


def test_flask_endpoints_rest_effect(client):
    response = client.get("/rest/effect")
    assert response.status_code == 200
    response_dict = json.loads(response.data)
    assert isinstance(response_dict, list)
