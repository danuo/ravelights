import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from ravelights.core.custom_typing import T_JSON
from ravelights.core.utils import p

if TYPE_CHECKING:
    from ravelights.core.device import Device
    from ravelights.core.settings import Settings
    from ravelights.core.timehandler import TimeHandler


logger = logging.getLogger(__name__)


@dataclass
class BeatState:
    settings: "Settings"
    is_quarter: bool = False
    beat_progress: float = 0.0
    n_quarters_long: int = 0

    @property
    def n_beats(self):
        return self.n_quarters_long // 4

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
    quarters:    str - "AC"      -> triggers on quarters 0 and 2 (a beat has 4 quarters, 0 is exactly on beat, 2 is halfbeat)
    loop_length: int - 16        -> defines, how long the pattern is. With beats = [0] and loop_length = 16, every 16th beats

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
        triggerskip = other.settings.global_triggerskip
        if device:
            triggerskip = max(triggerskip, device.device_triggerskip)

        if is_triggered:
            if self.previous_triggered_time == other.settings.timehandler.time_0:
                # the BeatStatePattern was already triggered within the current frame
                pass
            else:
                self.trigger_counter += 1
                self.previous_triggered_time = other.settings.timehandler.time_0

            is_triggered = self.trigger_counter % triggerskip == 0

        # ------------------------------- random chance ------------------------------ #
        # add random chance for trigger to fail if p < 1.0
        # trigger will be omitted by chance even if trigger conditions are met
        if p(self.p):
            return is_triggered
        else:
            return False

    def __repr__(self):
        return f"n_beats: {len(self.beats)}, quarters: {self.quarters}, loop_length: {self.loop_length}, p: {self.p}"

    def update_from_dict(self, update_dict: T_JSON):
        assert isinstance(update_dict, dict)
        for key, value in update_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                logger.warning(f"key {key} does not exist in settings")


class BPMhandler:
    def __init__(self, settings: "Settings", timehandler: "TimeHandler"):
        self.settings = settings
        self.timehandler = timehandler
        self.bpm_sync()
        self.n_quarters_long_memory = 0
        self.time_0_cache: float = self.timehandler.time_0
        self.beat_state_cache: BeatState = BeatState(self.settings)

    def bpm_sync(self):
        self.timehandler.bpm_sync()

    def bpm_adjust(self, amount):
        """Shifts the bpm sync point in seconds."""
        self.timehandler.time_sync += amount

    def get_beat_progress_n(self, n_beats: int) -> float:
        """gives progress within a time interval of length n_beats

        n_beats: length of time interval
        return: current time position within interval, as float from 0 to 1"""

        n_beats_till = self.n_quarters_long_memory // 4
        return (n_beats_till % n_beats + self.settings.beat_progress) / n_beats

    @property
    def beat_state(self):
        """Cache function for beat_state. Only needs to be calculated once per frame."""
        if self.time_0_cache == self.timehandler.time_0:
            return self.beat_state_cache
        else:
            self.beat_state_cache = self._get_beat_state()
            self.time_0_cache = self.timehandler.time_0
        return self.beat_state_cache

    def _get_beat_state(self):
        time_since_sync = self.timehandler.time_0 - self.timehandler.time_sync
        time_since_quarter = time_since_sync % self.settings.quarter_time
        n_quarters_long = int((time_since_sync // self.settings.quarter_time) % self.settings.queue_length)
        is_quarterbeat = n_quarters_long != self.n_quarters_long_memory  # this frame is beginninf of new quarter beat
        beat_progress = (n_quarters_long % 4 + time_since_quarter / self.settings.quarter_time) * 0.25
        beat_state = BeatState(self.settings, is_quarterbeat, beat_progress, n_quarters_long)
        self.n_quarters_long_memory = n_quarters_long
        return beat_state
