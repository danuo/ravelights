import argparse
import cProfile
import logging
import pstats
from pathlib import Path

from ravelights import RaveLightsApp
from ravelights.interface.artnet.artnet_udp_transmitter import ArtnetUdpTransmitter

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

device_config = [dict(n_lights=5, n_leds=144), dict(n_lights=5, n_leds=144)]

output_config = {
    0: [
        dict(device=0, light=0),
        dict(device=0, light=1),
        dict(device=0, light=2, flip=True),
    ],
    1: [
        dict(device=0, light=5),
        dict(device=0, light=4),
        dict(device=0, light=3),
    ],
    2: [
        dict(device=1, light=1),
        dict(device=1, light=3),
    ],
    3: [
        dict(device=1, light=0, flip=True),
        dict(device=1, light=2),
    ],
}


class DataRouter:
    def __init__(self, devices, output_config):
        self.devices = devices  # list[Device]
        self.output_config = output_config


def parse_args():
    parser = argparse.ArgumentParser(description="Ravelights")
    parser.add_argument("--fps", type=int, default=20, help="Frames per second (default: 20)")
    artnet_group = parser.add_mutually_exclusive_group()
    artnet_group.add_argument("--artnet-wifi", default=False, action=argparse.BooleanOptionalAction)
    artnet_group.add_argument("--artnet-serial", default=False, action=argparse.BooleanOptionalAction)
    parser.add_argument("--artnet-address", type=str, default=None)
    parser.add_argument("--artnet-serial-port", type=str, default="/dev/ttyAMA0")
    parser.add_argument("--artnet-serial-baudrate", type=int, default=3_000_000)
    parser.add_argument("--webui", default=True, action=argparse.BooleanOptionalAction)
    parser.add_argument("--visualizer", default=True, action=argparse.BooleanOptionalAction)
    parser.add_argument("--profiling", default=False, action=argparse.BooleanOptionalAction)
    args = parser.parse_args()
    parser.print_usage()
    return args


args = parse_args()

# ------------------------------ port selection ------------------------------ #

"""
Case A (default)
--webui
web static via flask @ port 80
rest via flask @ port 80

Case B
--no-webui
web dynamic via quasar dev @ port 80
rest via flask @ port 5000

Case C
--no-webui
web static via nginx @ port 80
rest via flask @ port 5000
"""

webserver_port = 80
if not args.webui:
    webserver_port = 5000
    logger.info("Running flask on port 5000, such that the web interface can be served by quasar or nginx on port 80")

# -------------------------- construct transmitters -------------------------- #
artnet_transmitters = []
if args.artnet_wifi:
    artnet_transmitters.append(ArtnetUdpTransmitter(ip_address=args.artnet_address))
if args.artnet_serial:
    # import here because of serial dependency
    from ravelights.interface.artnet.artnet_serial_transmitter import ArtnetSerialTransmitter

    artnet_transmitters.append(ArtnetSerialTransmitter(serial_port_address=args.artnet_serial_port, baud_rate=args.artnet_serial_baudrate))

app = RaveLightsApp(
    fps=args.fps,
    device_config=device_config,
    artnet_transmitters=artnet_transmitters,
    visualizer=args.visualizer,
    webserver_port=webserver_port,
    serve_webinterface=args.webui,
)

if not args.profiling:
    app.run()
else:
    logging.info("To visualize the profiling file, run `snakeviz ./log/profiling.prof` in terminal")
    with cProfile.Profile() as pr:
        app.profile()

    stats = pstats.Stats(pr)
    stats.sort_stats(pstats.SortKey.TIME)
    # stats.print_stats()
    filename = Path("log") / "profiling.prof"
    stats.dump_stats(filename=filename)
