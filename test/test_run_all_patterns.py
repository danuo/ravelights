from typing import Literal

import pytest
from loguru import logger
from ravelights import RaveLightsApp
from ravelights.core.time_handler import BeatStatePattern


@pytest.mark.slow  # only run in ci for speed
def test_all_patterns_1(app_time_patched_1):
    run_all_patterns(app_time_patched_1)


def test_all_patterns_2(app_time_patched_2):
    run_all_patterns(app_time_patched_2)


@pytest.mark.slow  # only run in ci for speed
def test_all_patterns_3(app_time_patched_3):
    run_all_patterns(app_time_patched_3)


def run_all_patterns(app: RaveLightsApp):
    app.settings.enable_autopilot = False

    counter_frame = 0
    counter_generators = 0
    beat_matcher = BeatStatePattern(loop_length=4)

    # get all generator names
    gen_names: list[str] = []
    gen_types: list[Literal["pattern", "vfilter", "dimmer", "thinner"]] = []

    for key in ("pattern", "vfilter", "thinner", "dimmer"):
        for dictionary in app.meta_handler.api_content["available_generators"][key]:
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
                assert isinstance(gen_name, str)
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
