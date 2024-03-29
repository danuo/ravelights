import argparse
import sys

from loguru import logger
from ravelights import (
    ArtnetUdpTransmitter,
    ColorProfiles,
    DeviceLightConfig,
    LightIdentifier,
    RaveLightsApp,
    TransmitterConfig,
)

# ─── Logging ──────────────────────────────────────────────────────────────────

logger.remove()
logger.add(sys.stdout, colorize=True, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> <level>{message}</level>")

# ─── Argparse ─────────────────────────────────────────────────────────────────


def parse_args():
    parser = argparse.ArgumentParser(description="Ravelights")
    parser.add_argument("--fps", type=int, default=20, help="Frames per second (default: 20)")
    artnet_group = parser.add_mutually_exclusive_group()
    artnet_group.add_argument("--artnet-wifi", default=False, action=argparse.BooleanOptionalAction)
    artnet_group.add_argument("--artnet-serial", default=False, action=argparse.BooleanOptionalAction)
    parser.add_argument("--artnet-serial-port", type=str, default="/dev/ttyAMA0")
    parser.add_argument("--artnet-serial-baudrate", type=int, default=3_000_000)
    parser.add_argument("--webui", default=True, action=argparse.BooleanOptionalAction)
    parser.add_argument("--visualizer", default=True, action=argparse.BooleanOptionalAction)
    args = parser.parse_args()
    return args


args = parse_args()


# ─── Device Config ────────────────────────────────────────────────────────────

# for devices in ravelights app
# device_config = [DeviceDict(n_lights=10, n_leds=144), DeviceDict(n_lights=10, n_leds=144)]
device_config = [DeviceLightConfig(n_lights=9, n_leds=144, color_profile=ColorProfiles.LINEAR)]


# ─── Transmitters ─────────────────────────────────────────────────────────────

# one output_config for each transmitter, defines which lights are broadcasted on which output

ravelights_box_light_mapping: list[list[LightIdentifier]] = [
    # Output 1
    [
        LightIdentifier(device=0, light=0, flip=False),
        LightIdentifier(device=0, light=1, flip=False),
        LightIdentifier(device=0, light=2, flip=False),
        LightIdentifier(device=0, light=3, flip=False),
        LightIdentifier(device=0, light=4, flip=False),
    ],
    # Output 2
    [],
    # Output 3
    [],
    # Output 4
    [],
]

laser_cage_light_mapping: list[list[LightIdentifier]] = [
    [
        LightIdentifier(device=0, light=0, flip=False),
    ],
    [],
    [],
    [],
]

transmitter_recipes: list[TransmitterConfig] = []


if args.artnet_wifi:
    # Ravelights
    box_hostname = "pixeldriver-box"
    ravelights_box_recipe = TransmitterConfig(
        transmitter=ArtnetUdpTransmitter(ip_address=None),
        light_mapping_config=ravelights_box_light_mapping,
        hostname=box_hostname,
    )
    transmitter_recipes.append(ravelights_box_recipe)

    # Laser Cage
    lasercage_hostname = "pixeldriver-lasercage"
    laser_cage_recipe = TransmitterConfig(
        transmitter=ArtnetUdpTransmitter(ip_address=None),
        light_mapping_config=laser_cage_light_mapping,
        hostname=lasercage_hostname,
    )
    transmitter_recipes.append(laser_cage_recipe)


if args.artnet_serial:
    # import here because of serial dependency
    from ravelights import ArtnetSerialTransmitter

    box_hostname = "ravelights-box"
    transmitter_recipe = TransmitterConfig(
        transmitter=ArtnetSerialTransmitter(
            serial_port_address=args.artnet_serial_port, baud_rate=args.artnet_serial_baudrate
        ),
        light_mapping_config=ravelights_box_light_mapping,
        hostname=box_hostname,
    )
    transmitter_recipes.append(transmitter_recipe)


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
    transmitter_recipes=transmitter_recipes,
    use_visualizer=args.visualizer,
)
