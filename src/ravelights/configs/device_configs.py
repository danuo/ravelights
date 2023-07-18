import numpy as np

X_SPACINGS_1 = np.linspace(0.2, 0.8, 5)
device_configs: list[list[list[dict[str, float | int]]]] = [
    # ─── CONFIGURATION 1 ─────────────────────────────────────────────────
    # this is the default configuration with 2 devices n_leds=144 and
    # n_lights=5 each. All lights are vertically oriented.
    #
    # | | | | |
    # | | | | |
    #
    [
        # ─── DEVICE 1 ────────────────────────────────────────────────────
        [
            dict(x=X_SPACINGS_1[0], y=0.3, rot=0.0, scale=1.0),
            dict(x=X_SPACINGS_1[1], y=0.3, rot=0.0, scale=1.0),
            dict(x=X_SPACINGS_1[2], y=0.3, rot=0.0, scale=1.0),
            dict(x=X_SPACINGS_1[3], y=0.3, rot=0.0, scale=1.0),
            dict(x=X_SPACINGS_1[4], y=0.3, rot=0.0, scale=1.0),
            dict(n_lights=144),
        ],
        # ─── DEVICE 2 ────────────────────────────────────────────────────
        [
            dict(x=X_SPACINGS_1[0], y=0.7, rot=0.0, scale=1.0),
            dict(x=X_SPACINGS_1[1], y=0.7, rot=0.0, scale=1.0),
            dict(x=X_SPACINGS_1[2], y=0.7, rot=0.0, scale=1.0),
            dict(x=X_SPACINGS_1[3], y=0.7, rot=0.0, scale=1.0),
            dict(x=X_SPACINGS_1[4], y=0.7, rot=0.0, scale=1.0),
            dict(n_lights=144),
        ],
    ]
]
