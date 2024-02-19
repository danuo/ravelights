import time
from functools import partial

from loguru import logger
from ravelights.core.effect_super import EffectWrapper
from ravelights.core.generator_super import Dimmer, Pattern, Thinner, Vfilter
from ravelights.core.ravelights_app import RaveLightsApp
from ravelights.core.time_handler import BeatState


class Profiler:
    def __init__(self, app: RaveLightsApp, samples: int = 1500):
        self.app = app
        self.samples = samples
        self.time_0 = 0
        self.time_sync = 0
        self.n_quarters_long_memory = 0
        self.data: dict[str, float] = dict()

    def run(self):
        logger.info("start profiling")

        logger.info("profiling generators:")
        for gen_name, gen in self.app.devices[0].rendermodule.generators_dict.items():
            dtime_ms = self.profile_generator(gen)
            self.data[gen_name] = dtime_ms

        logger.info("profiling effects:")
        for effect_name, effect in self.app.effect_handler.effect_wrappers_dict.items():
            dtime_ms = self.profile_generator(effect)
            self.data[effect_name] = dtime_ms

        logger.info("profiling finished")

    def profile_generator(self, generator: Pattern | Vfilter | Thinner | Dimmer | EffectWrapper):
        logger.info("generator.name")
        colors = self.app.settings.color_engine.get_colors_rgb(1)
        matrix = self.app.devices[0].pixelmatrix.get_float_matrix_rgb()
        if isinstance(generator, Pattern):
            closure = partial(generator.render, colors=colors)
        elif isinstance(generator, EffectWrapper):
            closure = partial(generator.render, in_matrix=matrix, colors=colors, device_index=0)
        else:
            closure = partial(generator.render, in_matrix=matrix, colors=colors)
        t0 = time.time_ns()
        for i in range(self.samples):
            if i % 200 == 0:  # alternate every 200 frames
                generator.alternate()
            if i % (4 * self.app.time_handler.fps):  # on_trigger every 4
                generator.on_trigger()
            closure()
        t1 = time.time_ns()
        dtime_ms = (t1 - t0) / (10**6) / self.samples
        return dtime_ms

    def plot(self):
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            import seaborn as sns

            names = list(self.data.keys())
            data = list(self.data.values())

            combined = list(zip(data, names))
            combined.sort(key=lambda x: x[0], reverse=True)
            data, names = zip(*combined)
            data = np.asarray(data) * 1000
            names = np.asarray(names)

            f, ax = plt.subplots(figsize=(6, 15))
            sns.set_theme(style="whitegrid")
            sns.set_color_codes("pastel")
            sns.set_color_codes("muted")

            sns.barplot(y=names, x=data, color="b")
            sns.despine(left=True, bottom=True)
            ax.set(xlabel="render_time [µs]")
            ax.xaxis.grid(True)
            plt.tight_layout()
            f.savefig("profiling_results.png")
        except Exception:
            logger.warning("could not load seaborn. output results as text instead:")
            self.write_data()

    def write_data(self, path=None):
        with open("profiling_results.txt", "a") as f:
            for key, value in self.data.items():
                key = str(key)
                f.write(f"{key.ljust(30)} {round(value,5)} ms\n")

    def fake_timestep(self):
        self.time_0 += 1 / self.app.time_handler.fps
        self.app.beat_state_cache = self.get_beat_state()

    def get_beat_state(self):
        time_since_sync = self.time_0 - self.time_sync
        time_since_quarter = time_since_sync % self.app.time_handler.quarter_time
        n_quarters_long = int(
            (time_since_sync // self.app.time_handler.quarter_time) % self.app.time_handler.queue_length
        )
        is_quarterbeat = n_quarters_long != self.n_quarters_long_memory  # this frame is beginninf of new quarter beat
        beat_progress = (n_quarters_long % 4 + time_since_quarter / self.app.time_handler.quarter_time) * 0.25
        beat_state = BeatState(self.app, is_quarterbeat, beat_progress, n_quarters_long)
        self.n_quarters_long_memory = n_quarters_long
        return beat_state

    """
    todo
    import cProfile
    import pstats

    logging.info("To visualize the profiling file, run `snakeviz ./log/profiling.prof` in terminal")
    with cProfile.Profile() as pr:
        self.app.profile()

    stats = pstats.Stats(pr)
    stats.sort_stats(pstats.SortKey.TIME)
    # stats.print_stats()
    filename = Path("log") / "profiling.prof"
    stats.dump_stats(filename=filename)
    """
