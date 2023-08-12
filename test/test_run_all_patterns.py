import random

from ravelights.core.bpmhandler import BeatStatePattern
from ravelights.core.ravelights_app import RaveLightsApp

FPS = 20


def test_all_patterns():
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

    app = RaveLightsApp(fps=FPS, visualizer=False, restapi=False)
    app.settings.timehandler.get_current_time = get_global_time
    app.settings.timehandler.after = increase_globaltime
    app.patternscheduler.load_timeline_from_index(1)  # todo: load by name

    counter_frame = 0
    counter_generators = 0
    beat_matcher = BeatStatePattern(loop_length=4)

    # get all generator names
    gen_names = []
    gen_types = []
    for i, (key, lis) in enumerate(app.settings.meta["available_generators"].items()):
        if i == 4:
            break
        for dictionary in lis:
            gen_names.append(dictionary["generator_name"])
            gen_types.append(key)

    it = iter(zip(gen_types, gen_names))

    done = False
    while not done:
        if app.settings.beat_state == beat_matcher:
            counter_generators += 1
            gen_type, gen_name = next(it, (None, None))
            if gen_type is None:
                done = True
            else:
                app.settings.set_generator(gen_type=gen_type, timeline_level=1, gen_name=gen_name)

        counter_frame += 1
        app.render_frame()
    print(f"tested {counter_frame} frames")
    print(f"tested {counter_generators} generators")
