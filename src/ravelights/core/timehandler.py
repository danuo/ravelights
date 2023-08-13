import logging
import time
from collections import deque
from typing import TYPE_CHECKING

from ravelights.core.performancelogger import PerformanceLogger

if TYPE_CHECKING:
    from ravelights.core.settings import Settings


logger = logging.getLogger(__name__)


class TimeHandler:
    """This class will handle time related routines. The goal is to produce static fps, given
    processing power of the hardware is sufficient"""

    def __init__(self, settings: "Settings"):
        self.settings = settings
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
        self.avg_time_excess = self.stats["avg_frame_time"] - self.settings.frame_time, 0
        self.dynamic_sleep_time = self.settings.frame_time - self.render_time - self.dynamic_sleep_time_correction
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
        excess = (self.time_2 - self.time_0) - self.settings.frame_time
        self.dynamic_sleep_time_correction += excess * correction_tuning
