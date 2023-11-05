from dataclasses import asdict

import pytest
from ravelights import RaveLightsApp


@pytest.fixture(scope="session")
def app():
    app = RaveLightsApp(run=False)
    return app.rest_api.flask_app


def test_flask_endpoints(client):
    response = client.get("/")
    assert response.status_code == 200
    print(response.data)
    # assert b"Welcome to the root endpoint" in response.data
