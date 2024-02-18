import random

import pytest
from ravelights import RaveLightsApp


@pytest.fixture(scope="module")
def app_normal() -> RaveLightsApp:
    return RaveLightsApp()


@pytest.fixture(scope="module")
def app_time_patched() -> RaveLightsApp:
    app = RaveLightsApp()
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
