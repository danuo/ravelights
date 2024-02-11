import random

from loguru import logger
from ravelights.core.ravelights_app import RaveLightsApp
from ravelights.core.time_handler import BeatStatePattern


def test_all_patterns():
    FPS = 20
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

    app = RaveLightsApp()
    app.time_handler.get_current_time = get_global_time
    app.time_handler.after = increase_globaltime
    app.pattern_scheduler.load_timeline_from_index(1)  # todo: load by name

    app.settings.enable_autopilot = False

    counter_frame = 0
    counter_generators = 0
    beat_matcher = BeatStatePattern(loop_length=4)

    # get all generator names
    gen_names = []
    gen_types = []
    for i, (key, lis) in enumerate(app.meta_handler.api_content["available_generators"].items()):
        if i == 4:
            break
        for dictionary in lis:
            gen_names.append(dictionary["generator_name"])
            gen_types.append(key)

    it = iter(zip(gen_types, gen_names))

    done = False
    while not done:
        if beat_matcher.is_match(app.time_handler.beat_state):
            counter_generators += 1
            gen_type, gen_name = next(it, (None, None))
            if gen_type is None:
                done = True
            else:
                app.settings.set_generator(
                    gen_type=gen_type,
                    device_index=0,
                    timeline_level=1,
                    gen_name=gen_name,
                    renew_trigger=False,
                )

        counter_frame += 1
        app.render_frame()
    logger.info(f"tested {counter_frame} frames")
    logger.info(f"tested {counter_generators} generators")


def test_autopilot():
    FPS = 20
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

    app = RaveLightsApp()
    app.time_handler.get_current_time = get_global_time
    app.time_handler.after = increase_globaltime
    app.pattern_scheduler.load_timeline_from_index(1)  # todo: load by name

    app.settings.enable_autopilot = True

    for _ in range(2_000):
        app.render_frame()
