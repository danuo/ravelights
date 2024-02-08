import argparse
import logging
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
from ravelights.constants import __version__

# ─── Argparse ─────────────────────────────────────────────────────────────────


def get_version():
    return __version__


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
    parser.add_argument("--audio", default=True, action=argparse.BooleanOptionalAction)
    parser.add_argument("--debug", default=False, action=argparse.BooleanOptionalAction)
    parser.add_argument("--debug-filter", default=None, type=str, help="filter logs with string")
    args = parser.parse_args()
    return args


args = parse_args()

# ─── Logging ──────────────────────────────────────────────────────────────────


class InterceptHandler(logging.Handler):
    def emit(self, record):
        logger_opt = logger.opt(depth=6, exception=record.exc_info)
        logger_opt.log(record.levelno, record.getMessage())


log = logging.getLogger("werkzeug")
log.addHandler(InterceptHandler())


logger.remove()


log_filter = None
if args.debug_filter:
    args.debug = True
    log_filter = lambda record: args.debug_filter in record["message"]  # noqa: E731


if args.debug:
    logger.add(
        sink=sys.stdout,
        colorize=True,
        format="<magenta>{time:HH:mm:ss}</magenta> <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> <level>{message}</level>",
        level="DEBUG",
        filter=log_filter,
    )
else:
    logger.add(
        sink=sys.stdout,
        colorize=True,
        format="<magenta>{time:HH:mm:ss}</magenta> <level>{message}</level>",
        level="INFO",
        filter=lambda record: record["level"].name == "INFO",
    )
    logger.add(
        sink=sys.stdout,
        colorize=True,
        format="<magenta>{time:HH:mm:ss}</magenta> <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> <level>{message}</level>",
        level="WARNING",
    )


# ─── Test Imports ─────────────────────────────────────────────────────────────

if args.audio:
    try:
        from pyaudio import PyAudio  # noqa: F401
    except ModuleNotFoundError:
        logger.error("Could not load pyaudio. Continue with audio=False")
        args.audio = False

if args.visualizer:
    try:
        import pygame  # noqa: F401
    except ModuleNotFoundError:
        logger.error("Could not load pygame. Continue with visualizer=False")
        args.visualizer = False


# ─── Device Config ────────────────────────────────────────────────────────────

# for devices in ravelights app
# device_config = [DeviceDict(n_lights=10, n_leds=144), DeviceDict(n_lights=10, n_leds=144)]
device_config = [
    DeviceLightConfig(n_lights=5, n_leds=144, color_profile=ColorProfiles.LINEAR),
    DeviceLightConfig(n_lights=5, n_leds=144, color_profile=ColorProfiles.LINEAR),
    DeviceLightConfig(n_lights=5, n_leds=144, color_profile=ColorProfiles.LINEAR),
]


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
    logger.warning(
        "Running flask on port 5000, such that the web interface can be served by quasar or nginx on port 80"
    )


if __name__ == "__main__":
    app = RaveLightsApp(
        device_config=device_config,
        fps=args.fps,
        webui_port=webui_port,
        serve_webui=args.webui,
        transmitter_recipes=transmitter_recipes,
        use_visualizer=args.visualizer,
        use_audio=args.audio,
    )
    app.start()
