import argparse
import logging

from ravelights import (
    ArtnetUdpTransmitter,
    DeviceLightConfig,
    LightIdentifier,
    Profiler,
    RaveLightsApp,
    TransmitterConfig,
)

# ─── Logging ──────────────────────────────────────────────────────────────────

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# ─── Argparse ─────────────────────────────────────────────────────────────────


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
    args = parser.parse_args()
    parser.print_usage()
    return args


args = parse_args()


# ─── Device Config ────────────────────────────────────────────────────────────

# for devices in ravelights app
# device_config = [DeviceDict(n_lights=10, n_leds=144), DeviceDict(n_lights=10, n_leds=144)]
device_config = [DeviceLightConfig(n_lights=9, n_leds=144)]

# ─── Transmitters ─────────────────────────────────────────────────────────────


# one output_config for each transmitter, defines which lights are broadcasted on which output
light_mapping_config_example: list[list[LightIdentifier]] = [
    [
        LightIdentifier(device=0, light=0, flip=False),
        LightIdentifier(device=0, light=1, flip=False),
    ],
    [],
    [],
    [],
]

transmitter_receipts: list[TransmitterConfig] = []
if args.artnet_wifi:
    ip_laser = "192.168.188.30"
    ip_box = "192.168.188.23"

    transmitter_receipts.append(
        TransmitterConfig(
            transmitter=ArtnetUdpTransmitter(ip_address=ip_laser), light_mapping_config=light_mapping_config_example
        )
    )
    transmitter_receipts.append(
        TransmitterConfig(
            transmitter=ArtnetUdpTransmitter(ip_address=ip_box), light_mapping_config=light_mapping_config_example
        )
    )


if args.artnet_serial:
    # import here because of serial dependency
    from ravelights import ArtnetSerialTransmitter

    transmitter = ArtnetSerialTransmitter(
        serial_port_address=args.artnet_serial_port, baud_rate=args.artnet_serial_baudrate
    )
    transmitter_receipts.append(
        TransmitterConfig(transmitter=transmitter, light_mapping_config=light_mapping_config_example)
    )


# ─── Webui Port ───────────────────────────────────────────────────────────────


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

webui_port = 80
if not args.webui:
    webui_port = 5000
    logger.info("Running flask on port 5000, such that the web interface can be served by quasar or nginx on port 80")


app = RaveLightsApp(
    device_config=device_config,
    fps=args.fps,
    webui_port=webui_port,
    serve_webui=args.webui,
    transmitter_receipts=transmitter_receipts,
    visualizer=visualizer,
    run=False,
)

if args.profiling:
    profiler = Profiler(app=app)
    profiler.run()
    profiler.plot()
else:
    app.run()
