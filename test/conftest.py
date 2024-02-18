import random
from collections.abc import Generator
from unittest.mock import patch

import pytest
from ravelights import DeviceLightConfig, RaveLightsApp

device_config_1 = [DeviceLightConfig(n_lights=1, n_leds=100)]

device_config_2 = [DeviceLightConfig(n_lights=5, n_leds=144), DeviceLightConfig(n_lights=5, n_leds=144)]

device_config_3 = [
    DeviceLightConfig(n_lights=5, n_leds=144),
    DeviceLightConfig(n_lights=5, n_leds=144),
    DeviceLightConfig(n_lights=5, n_leds=144),
]


@pytest.fixture(scope="module")
def app_1() -> RaveLightsApp:
    return RaveLightsApp(device_config=device_config_1)


@pytest.fixture(scope="module")
def app_2() -> RaveLightsApp:
    return RaveLightsApp(device_config=device_config_2)


@pytest.fixture(scope="module")
def app_3() -> RaveLightsApp:
    return RaveLightsApp(device_config=device_config_3)


@pytest.fixture(scope="module")
def app_time_patched_1(app_1: RaveLightsApp) -> RaveLightsApp:
    """time patched app with 1 device"""
    return patch_time(app_1)


@pytest.fixture(scope="module")
def app_time_patched_2(app_2: RaveLightsApp) -> RaveLightsApp:
    """time patched app with 2 devices"""
    return patch_time(app_2)


@pytest.fixture(scope="module")
def app_time_patched_3(app_3: RaveLightsApp) -> RaveLightsApp:
    """time patched app with 3 devices"""
    return patch_time(app_3)


@pytest.fixture(scope="function")
def app_render_patched_1(app_time_patched_1: RaveLightsApp) -> Generator[RaveLightsApp, None, None]:
    """app without actually rendering for fast testing"""

    mocked_render = patch("ravelights.core.render_module.RenderModule.render").start()
    yield app_time_patched_1
    mocked_render.stop()


@pytest.fixture(scope="function")
def app_render_patched_2(app_time_patched_2: RaveLightsApp) -> Generator[RaveLightsApp, None, None]:
    """app without actually rendering for fast testing"""

    mocked_render = patch("ravelights.core.render_module.RenderModule.render").start()
    yield app_time_patched_2
    mocked_render.stop()


@pytest.fixture(scope="function")
def app_render_patched_3(app_time_patched_3: RaveLightsApp) -> Generator[RaveLightsApp, None, None]:
    """app without actually rendering for fast testing"""

    mocked_render = patch("ravelights.core.render_module.RenderModule.render").start()
    yield app_time_patched_3
    mocked_render.stop()


def patch_time(app: RaveLightsApp) -> RaveLightsApp:
    """time patched will render as fast as possible (hardware limited), without FPS cap"""
    FPS = app.settings.fps
    global_time = 0

    def get_global_time():
        nonlocal global_time
        return global_time

    def increase_globaltime():
        nonlocal global_time
        norm = random.normalvariate(0, 0.004)
        assert abs(norm) < 1 / FPS
        random_frame_time = 1 / FPS + norm
        global_time += random_frame_time

    app.time_handler.get_current_time = get_global_time  # type: ignore[method-assign]
    app.time_handler.after = increase_globaltime  # type: ignore[method-assign]
    app.pattern_scheduler.load_timeline_from_index(1)  # todo: load by name

    # disable autopilot
    app.settings.enable_autopilot = False

    return app
