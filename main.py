import argparse
import cProfile
import logging
import pstats
from pathlib import Path

from ravelights import RaveLightsApp
from ravelights.interface.artnet.artnet_udp_transmitter import ArtnetUdpTransmitter

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# for devices in ravelights app
device_config = [dict(n_lights=5, n_leds=144), dict(n_lights=5, n_leds=144)]

# one output_config for each transmitter, defines which lights are broadcasted on which output
transmitter_config: list[list[dict]] = [
    [  # output 0
        dict(device=0, light=0),
        dict(device=0, light=1),
        dict(device=0, light=2, flip=True),
        dict(device=0, light=3, flip=True),
        dict(device=0, light=4, flip=True),
    ],
    [  # output 1
        dict(device=1, light=0),
        dict(device=1, light=1),
        dict(device=1, light=2),
        dict(device=1, light=3),
        dict(device=1, light=4),
    ],
    [],  # output 2
    [],  # output 3
]


def parse_args():
    parser = argparse.ArgumentParser(description="Ravelights")
    parser.add_argument("--fps", type=int, default=20, help="Frames per second (default: 20)")
    artnet_group = parser.add_mutually_exclusive_group()
    artnet_group.add_argument("--artnet-wifi", default=True, action=argparse.BooleanOptionalAction)
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
# idea:
# keep transmitters simple
# construct them here, with datarouter config
# inside of app, they are wrapped into datawrapper object


data_routers_configs = []
if args.artnet_wifi:
    transmitter = ArtnetUdpTransmitter(ip_address=args.artnet_address)
    data_routers_configs.append(dict(transmitter=transmitter, transmitter_config=transmitter_config))
if args.artnet_serial:
    # import here because of serial dependency
    from ravelights.interface.artnet.artnet_serial_transmitter import ArtnetSerialTransmitter

    transmitter = ArtnetSerialTransmitter(serial_port_address=args.artnet_serial_port, baud_rate=args.artnet_serial_baudrate)
    data_routers_configs.append(dict(transmitter=transmitter, transmitter_config=transmitter_config))

app = RaveLightsApp(
    fps=args.fps,
    device_config=device_config,
    data_routers_configs=data_routers_configs,
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
