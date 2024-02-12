import pytest
from ravelights import RaveLightsApp


@pytest.fixture(scope="session")
def ravelights_app():
    return RaveLightsApp()
