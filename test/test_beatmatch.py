import random

from ravelights.core.bpmhandler import BeatStatePattern, BPMhandler
from ravelights.core.settings import Settings
from ravelights.core.timehandler import TimeHandler

settings = Settings()
timehandler = TimeHandler(settings=settings)
bpmhandler = BPMhandler(settings=settings, timehandler=timehandler)

FPS = 20


def test_beat_matchings():
    print('test_beat_matchings')
    BEAT_TARGET = 16
    TRIGGER_TARGET = 8  # [0A, 0C, 3A, 3C] * 2
    beat_counter = 0
    trigger_counter = 0

    pattern = BeatStatePattern(beats=[0, 3], quarters="AC", loop_length=8)

    for _ in range(1000):
        beat_state = bpmhandler.beat_state
        if beat_state.is_beat:
            beat_counter += 1

        if beat_state == pattern:
            print(f"trigger at {beat_state}")
            trigger_counter += 1

        norm = random.normalvariate(0, 0.004)
        assert abs(norm) < 1/FPS
        random_frame_time = 1/FPS + norm
        timehandler.time_0 += random_frame_time

        if beat_counter == BEAT_TARGET:
            break

    assert beat_counter == BEAT_TARGET
    assert trigger_counter == TRIGGER_TARGET
