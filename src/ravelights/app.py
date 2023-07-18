import logging
from enum import Enum, auto
from typing import Optional

from ravelights.configs.device_configs import device_configs
from ravelights.core.controls import Controls
from ravelights.core.device import Device
from ravelights.core.effecthandler import EffectHandler
from ravelights.core.eventhandler import EventHandler
from ravelights.core.patternscheduler import PatternScheduler
from ravelights.core.settings import Settings
from ravelights.restapi.restapi import RestAPI

logger = logging.getLogger(__name__)


class ArtnetMode(Enum):
    WIFI_UDP = auto()
    SERIAL = auto()
    NONE = auto()


def create_devices(root: "RaveLightsApp") -> list[Device]:
    settings: Settings = root.settings
    devices: list[Device] = []
    for device_id in range(settings.n_devices):
        n_leds = settings.devices_n_leds[device_id]
        n_lights = settings.devices_n_lights[device_id]
        prim = True if device_id == 0 else False
        devices.append(Device(root=root, n_leds=n_leds, n_lights=n_lights, is_prim=prim))
    return devices


class RaveLightsApp:
    def __init__(
        self,
        *,
        fps=20,
        artnet_mode: ArtnetMode = ArtnetMode.NONE,
        artnet_address: Optional[str] = None,
        artnet_serial_port: Optional[str] = None,
        webserver_port=80,
        serve_webinterface=True,
        visualizer=True,
    ):
        self.settings = Settings(device_config=device_configs[0], bpm_base=80.0, fps=fps)
        self.effecthandler = EffectHandler(root=self)
        self.devices = create_devices(root=self)
        self.patternscheduler = PatternScheduler(root=self)
        self.eventhandler = EventHandler(root=self)
        self.controls = Controls(root=self)

        if visualizer:
            # move import here to make pygame optional
            from ravelights.pygame_visualizer.visualizer import Visualizer  # fmt: skip
            self.visualizer = Visualizer(root=self)

        match artnet_mode:
            case ArtnetMode.WIFI_UDP:
                if not artnet_address:
                    raise ValueError("Artnet address must be provided when artnet wifi output is enabled")
                from ravelights.artnet.artnet_udp_transmitter import ArtnetUdpTransmitter  # fmt: skip
                self.artnet = ArtnetUdpTransmitter(ip_address=artnet_address)

            case ArtnetMode.SERIAL:
                if not artnet_serial_port:
                    raise ValueError("Artnet serial port address must be provided when artnet serial output is enabled")
                from ravelights.artnet.artnet_serial_transmitter import ArtnetSerialTransmitter  # fmt: skip
                self.artnet = ArtnetSerialTransmitter(serial_port_address=artnet_serial_port)

        self.rest_api = RestAPI(
            root=self,
            serve_static_files=serve_webinterface,
            port=webserver_port,
        )
        self.rest_api.start_threaded(debug=True)

    def run(self):
        logger.info("Starting main loop...")
        while True:
            self.render_frame()

    def profile(self, n_frames: int = 200):
        logger.info(f"Starting profiling of {n_frames} frames...")
        for _ in range(n_frames):
            self.render_frame()

    def render_frame(self):
        self.settings.before()
        # ─── Apply Inputs ─────────────────────────────────────────────
        self.eventhandler.apply_settings_modifications_queue()
        # ─── PREPARE ─────────────────────────────────────────────────────
        self.patternscheduler.autopilot.randomize()
        for device in self.devices:
            device.instructionhandler.load_and_apply_instructions()
        self.patternscheduler.effecthandler.load_and_apply_instructions()
        # ─── RENDER ──────────────────────────────────────────────────────
        # sync
        for i, device in enumerate(self.devices):
            if i == 0:
                sync_dict = device.rendermodule.get_selected_generator("pattern").sync_send()
            else:
                device.rendermodule.get_selected_generator("pattern").sync_load(in_dict=sync_dict)
        # render
        for i, device in enumerate(self.devices):
            device.render()
        # ─── OUTPUT ──────────────────────────────────────────────────────
        if hasattr(self, "visualizer"):
            self.visualizer.render()
            # todo: transmit to all devices, not just one
        if hasattr(self, "artnet"):
            self.artnet.transmit_matrix(
                self.devices[0].pixelmatrix.get_matrix_int(brightness=self.settings.global_brightness)
            )
        self.settings.after()
