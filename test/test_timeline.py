from collections import Counter

from ravelights import RaveLightsApp
from ravelights.core.custom_typing import Timeline, TimelineMeta
from ravelights.core.generator_super import (
    Pattern,
)
from ravelights.core.timeline import GenPlacing, GenSelector

debug_timeline: Timeline = {
    "meta": TimelineMeta(name="8beat 3level"),
    "selectors": [
        GenSelector(gen_type=Pattern, level=1),
        GenSelector(gen_type=Pattern, level=2),
        GenSelector(gen_type=Pattern, level=3),
    ],
    "placements": [
        GenPlacing(level=1, timings=[16 * x for x in range(128 // 16)]),
        GenPlacing(level=2, timings=[16 * x + 4 for x in range(128 // 16)], trigger_on_change=True),
        GenPlacing(level=3, timings=[16 * x + 8 for x in range(128 // 16)], trigger_on_change=True),
    ],
}


def test_timeline(app_time_patched_1: RaveLightsApp):
    counter: Counter[int] = Counter()

    app = app_time_patched_1
    app.settings.enable_autopilot = False

    for selector in debug_timeline["selectors"]:
        selector.set_root(app)

    app.pattern_scheduler._load_timeline(debug_timeline)

    for _ in range(1_000):
        app.render_frame()
        effective_timeline_level = app.pattern_scheduler.get_effective_timeline_level(0)
        counter.update((effective_timeline_level,))

    assert counter[1] > 100
    assert counter[2] > 100
    assert counter[3] > 100
