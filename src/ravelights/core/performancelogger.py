import time

from loguru import logger  # type:ignore


class PerformanceLogger:
    def __init__(self, log_interval_seconds: int = 5) -> None:
        self._log_interval_seconds = log_interval_seconds
        self._last_log_seconds = time.time()
        self._last_delayed_frame_count: int = 0

    def notify(self, stats: dict[str, float | int]) -> None:
        if time.time() - self._last_log_seconds >= self._log_interval_seconds:
            logger.debug(f"Stats: {stats}")

            delayed_frames_this_interval = stats["delayed_frame_counter"] - self._last_delayed_frame_count
            if delayed_frames_this_interval > 0:
                logger.warning(
                    f"{delayed_frames_this_interval} delayed frames in the last {self._log_interval_seconds} s"
                )

            # Reset interval
            self._last_log_seconds = time.time()
            self._last_delayed_frame_count = int(stats["delayed_frame_counter"])
