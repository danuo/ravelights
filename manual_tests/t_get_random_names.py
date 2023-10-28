from collections import Counter

import matplotlib.pyplot as plt
from ravelights import DeviceDict, RaveLightsApp
from ravelights.configs.components import Keywords as K
from ravelights.core.generator_super import Pattern
from ravelights.core.templateobjects import GenSelector

app = RaveLightsApp(device_config=[DeviceDict(n_lights=10, n_leds=144)])

names: list[str] = []

for _ in range(10000):
    gen_selector = GenSelector(root=app, gen_type=Pattern, keywords=[K.STROBE])
    names.append(gen_selector.pattern_name)


c1 = Counter(names)

test = tuple(c1.items())
counts: list[int]
names, counts = zip(*tuple(c1.items()))

plt.bar(names, counts)
plt.show()
