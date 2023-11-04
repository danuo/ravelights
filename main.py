import argparse
import logging
from typing import Any

from ravelights import DeviceLightConfig, RaveLightsApp, TransmitDict
from ravelights.devtools.profiler import Profiler
from ravelights.interface.artnet.artnet_udp_transmitter import ArtnetUdpTransmitter

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# for devices in ravelights app
device_config = [DeviceDict(n_lights=10, n_leds=144), DeviceDict(n_lights=10, n_leds=144)]

# one output_config for each transmitter, defines which lights are broadcasted on which output
TRANSMITTER_CONFIG_TYPE = list[list[TransmitDict]]
transmitter_config_example: TRANSMITTER_CONFIG_TYPE = [
    [
        TransmitDict(device=2, light=0, flip=False),
    ],
    [],
    [],
    [],
]


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
visualizer = args.visualizer if not args.profiling else False

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

data_routers_configs: list[dict[str, Any]] = []
if args.artnet_wifi:
    ip_laser = "192.168.188.30"
    ip_box = "192.168.188.23"

    data_routers_configs.append(
        dict(transmitter=ArtnetUdpTransmitter(ip_address=ip_laser), transmitter_config=transmitter_config_example)
    )
    data_routers_configs.append(
        dict(transmitter=ArtnetUdpTransmitter(ip_address=ip_box), transmitter_config=transmitter_config_example)
    )


if args.artnet_serial:
    # import here because of serial dependency
    from ravelights.interface.artnet.artnet_serial_transmitter import ArtnetSerialTransmitter

    transmitter = ArtnetSerialTransmitter(
        serial_port_address=args.artnet_serial_port, baud_rate=args.artnet_serial_baudrate
    )
    data_routers_configs.append(dict(transmitter=transmitter, transmitter_config=transmitter_config_example))

app = RaveLightsApp(
    device_config=device_config,
    fps=args.fps,
    webserver_port=webserver_port,
    serve_webinterface=args.webui,
    data_routers_configs=data_routers_configs,
    visualizer=visualizer,
    run=False,
)

if args.profiling:
    profiler = Profiler(app=app)
    profiler.run()
    profiler.plot()
else:
    app.run()
