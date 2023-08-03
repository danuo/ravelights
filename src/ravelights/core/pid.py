from enum import Enum


class PIDSpeeds(Enum):
    """available speeds for pid controler"""

    INSTANT = "instant"
    FAST = "fast"
    FAST_BOUNCY = "fast"
    MEDIUM = "medium"
    MEDIUM_BOUNCY = "medium_bouncy"
    SLOW = "slow"
    SLOW_BOUNCY = "slow"


class PIDController:
    """
    simple implementation of a PID controller
    set target with object.target
    read current value with object.value
    run perform_pid_step() each frame to simulate one step
    """

    def __init__(self, start_val=0.0, kp=0.2, kd=0.1, ki=0.0, dt=1 / 20, instant=False):
        self.target: float = start_val
        self._x: float = start_val  # read value property instead
        self._dx: float = 0.0
        self._ddx: float = 0.0
        self._previous_error: float = 0.0
        self._integral: float = 0.0
        self.m: float = 0.01

        self.kp: float = kp
        self.kd: float = kd
        self.ki: float = ki
        self.dt: float = dt

        self.instant: bool = instant

    @property
    def value(self) -> float:
        return self.target if self.instant else self._x

    def load_parameter_preset(self, preset):
        match preset:
            case PIDSpeeds.INSTANT.value:
                self.instant = True

            case PIDSpeeds.FAST.value:
                self.instant = False
                self.kp = 0.2
                self.kd = 0.1
                self.ki = 0.0
                self.dt = 1 / 20

            case PIDSpeeds.FAST.value:
                self.instant = False
                self.kp = 0.2
                self.kd = 0.1
                self.ki = 0.0
                self.dt = 1 / 20

            case PIDSpeeds.FAST_BOUNCY.value:
                self.instant = False
                # todo
                self.kp = 0.2
                self.kd = 0.1
                self.ki = 0.0
                self.dt = 1 / 20

            case PIDSpeeds.MEDIUM.value:
                self.instant = False
                self.kp = 0.3
                self.kd = 0.05
                self.ki = 0.0
                self.dt = 1 / 20

            case PIDSpeeds.MEDIUM_BOUNCY.value:
                self.instant = False
                self.kp = 0.5
                self.kd = 0.1
                self.ki = 0.0
                self.dt = 1 / 20

            case PIDSpeeds.SLOW.value:
                self.instant = False
                self.kp = 0.2
                self.kd = 0.1
                self.ki = 0.0
                self.dt = 1 / 100

            case PIDSpeeds.SLOW_BOUNCY.value:
                self.instant = False
                self.kp = 0.2
                self.kd = 0.1
                self.ki = 0.0
                self.dt = 1 / 100

    def perform_pid_step(self):
        self.error = self.target - self._x
        self.derivative = (self.error - self._previous_error) / self.dt
        self._previous_error = self.error
        self._integral += self.error * self.dt
        self.force = self.kp * self.error + self.ki * self._integral + self.kd * self.derivative

        self._x = self._x + self._dx * self.dt + 0.5 * self._ddx * (self.dt**2)
        self._dx = (self._dx + self._ddx * self.dt) * 0.7
        self._ddx = self.force / self.m
