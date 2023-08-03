import logging
from enum import Enum, auto
from typing import Optional

from ravelights.artnet.artnet_transmitter import ArtnetTransmitter
from ravelights.configs.device_configs import device_configs
from ravelights.core.controls import Controls
from ravelights.core.device import Device
from ravelights.core.effecthandler import EffectHandler
from ravelights.core.eventhandler import EventHandler
from ravelights.core.patternscheduler import PatternScheduler
from ravelights.core.settings import Settings
from ravelights.restapi.restapi import RestAPI

logger = logging.getLogger(__name__)


def create_devices(root: "RaveLightsApp") -> list[Device]:
    settings: Settings = root.settings
    devices: list[Device] = []
    for device_id in range(settings.n_devices):
        n_leds = settings.devices_n_leds[device_id]
        n_lights = settings.devices_n_lights[device_id]
        prim = True if device_id == 0 else False
        devices.append(Device(root=root, device_id=device_id, n_leds=n_leds, n_lights=n_lights, is_prim=prim))
    return devices


class RaveLightsApp:
    def __init__(
        self,
        *,
        fps=20,
        artnet_transmitter: Optional[ArtnetTransmitter] = None,
        webserver_port=80,
        serve_webinterface=True,
        visualizer=True,
    ):
        self.settings = Settings(device_config=device_configs[0], bpm_base=80.0, fps=fps)
        self.devices = create_devices(root=self)
        self.effecthandler = EffectHandler(root=self)
        self.patternscheduler = PatternScheduler(root=self)
        self.eventhandler = EventHandler(root=self)
        self.controls = Controls(root=self)

        self.visualizer = None
        if visualizer:
            from ravelights.pygame_visualizer.visualizer import Visualizer

            self.visualizer = Visualizer(root=self)

        self.artnet = artnet_transmitter

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
        self.effecthandler.load_and_apply_instructions()
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
        # aftermath
        self.effecthandler.perform_counting_per_frame()
        # ─── OUTPUT ──────────────────────────────────────────────────────
        if self.visualizer:
            self.visualizer.render()
            # todo: transmit to all devices, not just one
        else:
            self.settings.timehandler.print_performance_stats()
        if self.artnet is not None:
            self.artnet.transmit_matrix(self.devices[0].pixelmatrix.get_matrix_int(brightness=self.settings.global_brightness))
        self.settings.after()
