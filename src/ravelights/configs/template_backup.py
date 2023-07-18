    [  # 0
        # dict(style=["techno", "disco", "ambient"], function="normal", weight=2),
        [  # items
            dict(obj=GeneratorObject, typ=Pattern),
            dict(obj=GeneratorObject, typ=Pattern),
            dict(obj=FunctionObject, func="swap_color"),
            dict(obj=FunctionObject, func="set_frame_skip", func_args=None),
            dict(obj=FunctionObject, func="set_frame_skip", func_args=5),
            dict(obj=EffectObject, effect="test"),  # todo: use name
            dict(obj=GeneratorObject, typ=Vfilter),
        ],
        [  # timings
            dict(obj=PlacementObject, placements=[0, 8 * 4, 16 * 4, 24 * 4], item=0),
            dict(obj=PlacementObject, placements=[0 + 4, 8 * 4 + 4, 16 * 4 + 4, 24 * 4 + 4], item=1),
            dict(obj=PlacementObject, placements=[0, 8 * 4, 16 * 4, 24 * 4, 0 + 4, 8 * 4 + 4, 16 * 4 + 4, 24 * 4 + 4], item=2, p=1.0),
            dict(obj=PlacementObject, placements=[0], item=3),
            dict(obj=PlacementObject, placements=[24 * 4], item=4),
            dict(obj=PlacementObject, placements=[8], item=5, to_effect=True),
            # dict(obj=PlacementObject, placements=[0], item=6),
        ],
    ],
    [  # 1
        [
            dict(obj=GeneratorObject, typ=Pattern, name="p_moving_blocks", trigger=""),
            dict(obj=GeneratorObject, typ=Vfilter, name="v_decay"),
        ],
        [
            dict(obj=PlacementObject, placements=[4], item=0),
            dict(obj=PlacementObject, placements=[4], item=1)
        ],
    ],
    [  # 2
        [
            dict(obj=GeneratorObject, typ=Pattern, name="p_moving_strobe_v2", trigger=""),
        ],
        [
            dict(obj=PlacementObject, placements=[4], item=0),
        ],
    ],
