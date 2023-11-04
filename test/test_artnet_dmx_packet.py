import numpy as np
from ravelights.interface.artnet.art_dmx_packet import ArtDmxPacket


def test_ArtDmxPacket():
    data = np.array((1, 2, 3, 4, 5), dtype=np.uint8).tobytes()
    packet = ArtDmxPacket(universe=0, data=data)

    assert packet.get_bytes()
