from collections import Counter

import matplotlib.pyplot as plt

from main import create_devices
from ravelights.configs.components import Keywords as K
from ravelights.configs.visualizer_configurations import device_configs
from ravelights.core.device import Device
from ravelights.core.generator_super import Pattern
from ravelights.core.patternscheduler import PatternScheduler
from ravelights.core.settings import Settings
from ravelights.core.templateobjects import GenSelector

settings = Settings(device_config=device_configs[0], bpm=80, fps=20)
devices = create_devices(settings=settings)
patternscheduler = PatternScheduler(settings=settings, devices=devices)

names = []

for _ in range(10000):
    # sel = GenSelector(gen_type=Pattern, patternscheduler=patternscheduler)
    sel = GenSelector(gen_type=Pattern, keywords=[K.STROBE], patternscheduler=patternscheduler)
    names.append(sel.pattern_name)


c1 = Counter(names)

test = tuple(c1.items())
names, counts = zip(*tuple(c1.items()))

plt.bar(names, counts)
plt.show()
