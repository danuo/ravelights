import time
from collections import deque
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional, cast

from loguru import logger
from ravelights.core.performance_logger import PerformanceLogger
from ravelights.core.utils import p

if TYPE_CHECKING:
    from ravelights.core.device import Device
    from ravelights.core.ravelights_app import RaveLightsApp


@dataclass
class BeatState:
    root: "RaveLightsApp"
    is_quarter: bool = False
    beat_progress: float = 0.0
    n_quarters_long: int = 0

    @property
    def n_beats(self):
        return self.n_quarters_long // 4

    @property
    def string_quarters(self):
        return "ABCD"[self.n_quarters_long % 4]

    @property
    def is_beat(self) -> bool:
        return self.is_quarter and (self.n_quarters_long % 4 == 0)

    def __repr__(self):
        string_beats = f"beats: {self.n_beats}"
        string_quarters = "ABCD"[self.n_quarters_long % 4] if self.is_quarter else ""
        return string_beats + " | " + string_quarters


@dataclass
class BeatStatePattern:
    """
    Create Beat Matching Patterns to define beat dependant triggers

    beats: list[int] - [0, 4, 5] -> triggers on beats 0, 4 and 5
    quarters:    str - "AC"      -> triggers on quarters 0 and 2 (a beat has 4 quarters, 0 is exactly on beat
                                    , 2 is halfbeat)
    loop_length: int - 16        -> defines, how long the pattern is. With beats = [0] and loop_length = 16
                                    , every 16th beats

    p: float - 0.5 -> triggers if the above are true, at a chance of 0.5

    beats_array: list of length 32, containing True or False
    quarters: list of length 4, containing True or False
    """

    beats: Optional[list[int]] = None
    quarters: str = "A"
    loop_length: int = 4
    p: float = 1.0

    beats_array: list[bool] = field(init=False)
    quarters_array: list[bool] = field(init=False)

    def __post_init__(self):
        if self.beats is None:
            self.beats = [0]
        self.beats_array = [idx in self.beats for idx in range(32)]
        self.quarters_array = ["ABCD"[idx] in self.quarters for idx in range(4)]

        # for global frame skip
        self.previous_triggered_time = None
        self.trigger_counter = -1

    def is_match(self, other: BeatState, device: Optional["Device"] = None) -> bool:
        """
        Will return True, if pattern matches current BeatState.
        """

        # check if BeatPattern conditions are met
        # current_beat: other.n_quarters_long % (self.loop_length * 4) // 4
        # current_quarter: other.n_quarters_long % (self.loop_length * 4) % 4
        current_beat, current_quarter = divmod(other.n_quarters_long % (self.loop_length * 4), 4)
        is_triggered = all(
            [
                other.is_quarter,
                self.beats_array[current_beat],
                self.quarters_array[current_quarter],
            ]
        )

        # ----------------------------------- skip ----------------------------------- #
        # global skip trigger = 1: each trigger works
        # global skip trigger = 2: every second trigger works
        # global skip trigger = 3: every third trigger works
        # global skip trigger = 4: every fourth trigger works

        # determine triggerskip from global and device settings
        triggerskip = other.root.settings.global_triggerskip
        if device:
            triggerskip = max(triggerskip, device.device_triggerskip)

        if is_triggered:
            if self.previous_triggered_time == other.root.timehandler.time_0:
                # the BeatStatePattern was already triggered within the current frame
                pass
            else:
                self.trigger_counter += 1
                self.previous_triggered_time = other.root.timehandler.time_0

            is_triggered = self.trigger_counter % triggerskip == 0

        # ------------------------------- random chance ------------------------------ #
        # add random chance for trigger to fail if p < 1.0
        # trigger will be omitted by chance even if trigger conditions are met
        if p(self.p):
            return is_triggered
        else:
            return False

    def __repr__(self):
        return f"n_beats: {len(cast(list[Any], self.beats))}, quarters: {self.quarters}, loop_length: {self.loop_length}, p: {self.p}"

    def update_from_dict(self, update_dict: dict[str, Any]):
        assert isinstance(update_dict, dict)
        for key, value in update_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                logger.warning(f"key {key} does not exist in settings")


class TimeHandler:
    """This class will handle time related routines. The goal is to produce static fps, given
    processing power of the hardware is sufficient"""

    def __init__(self, root: "RaveLightsApp"):
        self.root = root
        self.settings = self.root.settings
        self.avg_segment_length = 20
        self.time_0_deque: deque[float] = deque(maxlen=self.avg_segment_length)
        self.render_time_deque: deque[float] = deque(maxlen=self.avg_segment_length)
        self.measure_time_0()
        self.measure_time_1()
        self.measure_time_2()
        self.bpm_sync()
        self.dynamic_sleep_time = 0
        self.dynamic_sleep_time_correction = 0
        self.stats: dict[str, float | int] = dict(delayed_frame_counter=0)
        self._performance_logger = PerformanceLogger(log_interval_seconds=10)
        self._calculate_stats()

        # bpmhandler
        self.n_quarters_long_memory = 0
        self.time_0_cache: float = self.time_0
        self.beat_state_cache: BeatState = BeatState(self.root)

    def before(self):
        """Abstract function called before rendering"""
        self.measure_time_0()
        self._calculate_stats()

    def after(self):
        """Abstract function called after rendering"""
        self.measure_time_1()
        self.sleep_dynamic()
        self.measure_time_2()
        self._calibrate_sleep_dynamic()

    def get_current_time(self) -> float:
        return time.perf_counter()

    def measure_time_0(self):
        """Measure time at beginning of render cycle"""
        self.time_0 = self.get_current_time()
        self.time_0_deque.append(self.time_0)

    def measure_time_1(self):
        """Measure time after render cycle"""
        self.time_1 = self.get_current_time()
        self.render_time = self.time_1 - self.time_0
        self.render_time_deque.append(self.render_time)

    def measure_time_2(self):
        """Measure time after render cycle and sleep"""
        self.time_2 = self.get_current_time()

    def bpm_sync(self):
        """Synchronize bpm"""
        self.time_sync = self.get_current_time()

    def sleep_static(self, t: float = 1 / 30):
        time.sleep(t)

    def sleep_dynamic(self):
        """Perform sleep of dynamic length to hit fps target
        <------- frame  time ------>
        |           frame          |
        | render |      sleep      |
        """
        self.avg_time_excess = self.stats["avg_frame_time"] - self.frame_time, 0
        self.dynamic_sleep_time = self.frame_time - self.render_time - self.dynamic_sleep_time_correction
        if self.dynamic_sleep_time > 0:
            time.sleep(self.dynamic_sleep_time)
        else:
            self.stats["delayed_frame_counter"] += 1

    def get_stats(self, precision: int = 2) -> dict[str, float | int]:
        return {k: round(v, precision) for k, v in self.stats.items()}

    def _calculate_stats(self):
        """Calculate metrics for gui output"""
        self._calculate_sleep_stats()
        self._calculate_fps_stats()
        self._calculate_avg_render_time()

    def print_performance_stats(self):
        self._performance_logger.notify(self.get_stats())

    def _calculate_sleep_stats(self):
        self.stats["dynamic_sleep_time"] = self.dynamic_sleep_time
        self.stats["dynamic_sleep_time_inv"] = 1 / (self.dynamic_sleep_time + 1e-5)

    def _calculate_fps_stats(self):
        """Calculates average of time1-time0 (render time) for last 10 framess"""
        if len(self.render_time_deque) < 5:
            self.stats["avg_frame_time_inv"], self.stats["avg_frame_time"] = 0, 0
        else:
            self.stats["avg_frame_time"] = (self.time_0_deque[-1] - self.time_0_deque[0]) / (len(self.time_0_deque) - 1)
            self.stats["avg_frame_time_inv"] = 1 / self.stats["avg_frame_time"]

    def _calculate_avg_render_time(self):
        """Calculates average of time1-time0 (render time) for last 10 framess"""
        if len(self.render_time_deque) < 5:
            self.stats["avg_render_time_inv"], self.stats["avg_render_time"] = 0, 0
        else:
            self.stats["avg_render_time"] = sum(self.render_time_deque) / len(self.render_time_deque)
            self.stats["avg_render_time_inv"] = 1 / self.stats["avg_render_time"]

    def _calibrate_sleep_dynamic(self):
        """Calibrates sleep_dynamic, so that resulting frame time is accurate.
        This is the integral part of a pid feedback loop control"""
        correction_tuning = 0.02
        excess = (self.time_2 - self.time_0) - self.frame_time
        self.dynamic_sleep_time_correction += excess * correction_tuning

    def bpm_adjust(self, amount: float | int):
        """Shifts the bpm sync point in seconds."""
        # self.timehandler.time_sync += amount
        self.time_sync += amount

    def get_beat_progress_n(self, n_beats: int) -> float:
        """gives progress within a time interval of length n_beats

        n_beats: length of time interval
        return: current time position within interval, as float from 0 to 1"""

        n_beats_till = self.n_quarters_long_memory // 4
        return (n_beats_till % n_beats + self.beat_progress) / n_beats

    @property
    def beat_state(self):
        """Cache function for beat_state. Only needs to be calculated once per frame."""
        if self.time_0_cache == self.time_0:
            return self.beat_state_cache
        else:
            self.beat_state_cache = self._get_beat_state()
            self.time_0_cache = self.time_0
        return self.beat_state_cache

    def _get_beat_state(self):
        time_since_sync = self.time_0 - self.time_sync
        time_since_quarter = time_since_sync % self.quarter_time
        n_quarters_long = int((time_since_sync // self.quarter_time) % self.queue_length)
        is_quarterbeat = n_quarters_long != self.n_quarters_long_memory  # this frame is beginninf of new quarter beat
        beat_progress = (n_quarters_long % 4 + time_since_quarter / self.quarter_time) * 0.25
        beat_state = BeatState(self.root, is_quarterbeat, beat_progress, n_quarters_long)
        self.n_quarters_long_memory = n_quarters_long
        return beat_state

    @property
    def bpm(self) -> float:
        return self.settings.bpm_multiplier * self.settings.bpm_base

    @property
    def beat_time(self) -> float:
        """time of a beat in seconds"""
        return 60 / self.bpm

    @property
    def quarter_time(self) -> float:
        """time of a quarter in seconds"""
        return 60 / (self.bpm * 4)

    @property
    def n_quarters(self) -> int:
        """self.n_quarters: will always represent current quarter number [0,15]"""
        return self.n_quarters_long % 16

    @property
    def n_quarters_long(self) -> int:
        """self.n_quarters: will always represent current quarter number [0,127]"""
        return self.beat_state.n_quarters_long

    @property
    def beat_progress(self) -> float:
        return self.beat_state.beat_progress

    @property
    def frame_time(self) -> float:
        return 1 / self.fps

    @property
    def fps(self) -> float:
        return self.settings.fps

    @property
    def queue_length(self) -> int:
        return self.settings.queue_length
