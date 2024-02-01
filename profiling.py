import sys

from loguru import logger
from ravelights import (
    DeviceLightConfig,
    Profiler,
    RaveLightsApp,
)

logger.remove()
logger.add(sys.stdout, colorize=True, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> <level>{message}</level>")

device_config = [DeviceLightConfig(n_lights=10, n_leds=144), DeviceLightConfig(n_lights=10, n_leds=144)]

app = RaveLightsApp(device_config=device_config)

profiler = Profiler(app=app)
profiler.run()
profiler.plot()
