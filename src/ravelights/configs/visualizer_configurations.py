import numpy as np
from numpy.typing import NDArray
from ravelights.core.custom_typing import VisualizerConfig

X_SPACINGS: dict[int, NDArray[np.float_]] = dict()
for i in range(1, 11):
    X_SPACINGS[i] = np.linspace(0.2, 0.8, i)


configurations: list[VisualizerConfig] = [
    # ─── CONFIGURATION 1 ─────────────────────────────────────────────────
    # this is the default configuration with 2 devices n_leds=144 and
    # n_lights=5 each. All lights are vertically oriented.
    #
    # | | | | |
    # | | | | |
    #
    VisualizerConfig(
        name="5 top, 5 bottom",
        device_config=[dict(n_lights=5, n_leds=144), dict(n_lights=5, n_leds=144)],
        visualizer_config=[
            # ─── DEVICE 1 ────────────────────────────────────────────────────
            [
                dict(x=X_SPACINGS[5][0], y=0.3, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[5][1], y=0.3, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[5][2], y=0.3, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[5][3], y=0.3, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[5][4], y=0.3, rot=0.0, scale=1.0),
            ],
            # ─── DEVICE 2 ────────────────────────────────────────────────────
            [
                dict(x=X_SPACINGS[5][0], y=0.7, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[5][1], y=0.7, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[5][2], y=0.7, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[5][3], y=0.7, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[5][4], y=0.7, rot=0.0, scale=1.0),
            ],
        ],
    ),
    VisualizerConfig(
        name="5 top, 10 bottom",
        device_config=[dict(n_lights=5, n_leds=144), dict(n_lights=10, n_leds=144)],
        visualizer_config=[
            # ─── DEVICE 1 ────────────────────────────────────────────────────
            [
                dict(x=X_SPACINGS[5][0], y=0.3, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[5][1], y=0.3, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[5][2], y=0.3, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[5][3], y=0.3, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[5][4], y=0.3, rot=0.0, scale=1.0),
            ],
            # ─── DEVICE 2 ────────────────────────────────────────────────────
            [
                dict(x=X_SPACINGS[10][0], y=0.7, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][1], y=0.7, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][2], y=0.7, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][3], y=0.7, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][4], y=0.7, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][5], y=0.7, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][6], y=0.7, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][7], y=0.7, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][8], y=0.7, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][9], y=0.7, rot=0.0, scale=1.0),
            ],
        ],
    ),
    VisualizerConfig(
        name="6 top, 10 bottom",
        device_config=[dict(n_lights=6, n_leds=144), dict(n_lights=10, n_leds=144)],
        visualizer_config=[
            # ─── DEVICE 1 ────────────────────────────────────────────────────
            [
                dict(x=X_SPACINGS[6][0], y=0.3, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[6][1], y=0.3, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[6][2], y=0.3, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[6][3], y=0.3, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[6][4], y=0.3, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[6][5], y=0.3, rot=0.0, scale=1.0),
            ],
            # ─── DEVICE 2 ────────────────────────────────────────────────────
            [
                dict(x=X_SPACINGS[10][0], y=0.7, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][1], y=0.7, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][2], y=0.7, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][3], y=0.7, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][4], y=0.7, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][5], y=0.7, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][6], y=0.7, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][7], y=0.7, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][8], y=0.7, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][9], y=0.7, rot=0.0, scale=1.0),
            ],
        ],
    ),
    VisualizerConfig(
        name="10 middle",
        device_config=[dict(n_lights=10, n_leds=144)],
        visualizer_config=[
            # ─── DEVICE 1 ────────────────────────────────────────────────────
            [
                dict(x=X_SPACINGS[10][0], y=0.5, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][1], y=0.5, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][2], y=0.5, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][3], y=0.5, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][4], y=0.5, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][5], y=0.5, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][6], y=0.5, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][7], y=0.5, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][8], y=0.5, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][9], y=0.5, rot=0.0, scale=1.0),
            ],
        ],
    ),
    VisualizerConfig(
        name="10 top, 10 bottom",
        device_config=[dict(n_lights=10, n_leds=144), dict(n_lights=10, n_leds=144)],
        visualizer_config=[
            # ─── DEVICE 1 ────────────────────────────────────────────────────
            [
                dict(x=X_SPACINGS[10][0], y=0.3, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][1], y=0.3, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][2], y=0.3, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][3], y=0.3, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][4], y=0.3, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][5], y=0.3, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][6], y=0.3, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][7], y=0.3, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][8], y=0.3, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][9], y=0.3, rot=0.0, scale=1.0),
            ],
            # ─── DEVICE 2 ────────────────────────────────────────────────────
            [
                dict(x=X_SPACINGS[10][0], y=0.7, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][1], y=0.7, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][2], y=0.7, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][3], y=0.7, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][4], y=0.7, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][5], y=0.7, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][6], y=0.7, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][7], y=0.7, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][8], y=0.7, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][9], y=0.7, rot=0.0, scale=1.0),
            ],
        ],
    ),
    VisualizerConfig(
        name="6 top, 10 bottom, laser",
        device_config=[dict(n_lights=6, n_leds=144), dict(n_lights=10, n_leds=144), dict(n_lights=1, n_leds=44)],
        visualizer_config=[
            # ─── DEVICE 1 ────────────────────────────────────────────────────
            [
                dict(x=X_SPACINGS[6][0], y=0.3, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[6][1], y=0.3, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[6][2], y=0.3, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[6][3], y=0.3, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[6][4], y=0.3, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[6][5], y=0.3, rot=0.0, scale=1.0),
            ],
            # ─── DEVICE 2 ────────────────────────────────────────────────────
            [
                dict(x=X_SPACINGS[10][0], y=0.7, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][1], y=0.7, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][2], y=0.7, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][3], y=0.7, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][4], y=0.7, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][5], y=0.7, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][6], y=0.7, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][7], y=0.7, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][8], y=0.7, rot=0.0, scale=1.0),
                dict(x=X_SPACINGS[10][9], y=0.7, rot=0.0, scale=1.0),
            ],
            [
                dict(x=0.5, y=0.5, rot=90, scale=5.0),
            ],
        ],
    ),
]
