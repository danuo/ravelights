import logging

from ravelights import (
    DeviceLightConfig,
    Profiler,
    RaveLightsApp,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

device_config = [DeviceLightConfig(n_lights=10, n_leds=144), DeviceLightConfig(n_lights=10, n_leds=144)]

app = RaveLightsApp(
    device_config=device_config,
    run=False,
)

profiler = Profiler(app=app)
profiler.run()
profiler.plot()
