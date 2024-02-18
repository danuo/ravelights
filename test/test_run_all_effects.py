from ravelights import RaveLightsApp

LIMIT = 50


def test_all_effects_2(app_time_patched_2):
    run_all_effects(app_time_patched_2)


def run_all_effects(app: RaveLightsApp):
    app.settings.enable_autopilot = False

    effect_names = []

    for dictionary in app.meta_handler.api_content["available_generators"]["effect"]:
        effect_names.append(dictionary["generator_name"])

    # add effects with infinity length
    for effect_name in effect_names:
        app.effect_handler.clear_qeueues()
        assert len(app.effect_handler.effect_queue) == 0
        app.effect_handler.load_effect(effect_name=effect_name, mode="frames", limit_frames=None)
        assert len(app.effect_handler.effect_queue) == 1

        for _ in range(LIMIT):
            app.render_frame()
