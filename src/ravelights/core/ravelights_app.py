import logging
from typing import Any

from ravelights.core.autopilot import AutoPilot
from ravelights.core.device import Device
from ravelights.core.effecthandler import EffectHandler
from ravelights.core.eventhandler import EventHandler
from ravelights.core.methandler import MetaHandler
from ravelights.core.patternscheduler import PatternScheduler
from ravelights.core.settings import Settings
from ravelights.interface.datarouter import DataRouter
from ravelights.interface.restapi import RestAPI

logger = logging.getLogger(__name__)


def create_devices(root: "RaveLightsApp") -> list[Device]:
    settings: Settings = root.settings
    devices: list[Device] = []
    for device_id, config in enumerate(settings.device_config):
        n_leds: int = config["n_leds"]
        assert isinstance(n_leds, int)
        n_lights: int = config["n_lights"]
        assert isinstance(n_lights, int)
        prim = True if device_id == 0 else False
        devices.append(Device(root=root, device_id=device_id, n_leds=n_leds, n_lights=n_lights, is_prim=prim))
    return devices


class RaveLightsApp:
    def __init__(
        self,
        *,
        fps: int = 20,
        device_config: list[dict[str, int]],
        data_routers_configs: list[dict[str, Any]],
        webserver_port: int = 80,
        serve_webinterface: bool = True,
        visualizer: bool = True,
    ):
        self.settings = Settings(root_init=self, device_config=device_config, fps=fps, bpm_base=140.0)
        self.devices = create_devices(root=self)
        self.autopilot = AutoPilot(root=self)
        self.effecthandler = EffectHandler(root=self)
        self.patternscheduler = PatternScheduler(root=self)
        self.metahandler = MetaHandler(root=self)
        self.eventhandler = EventHandler(root=self)

        self.visualizer = None
        if visualizer:
            from ravelights.interface.visualizer import Visualizer

            self.visualizer = Visualizer(root=self)

        self.data_routers = self.initiate_data_routers(data_routers_configs)

        self.rest_api = RestAPI(
            root=self,
            serve_static_files=serve_webinterface,
            port=webserver_port,
        )

    def initiate_data_routers(self, data_routers_configs: list[dict[str, Any]]) -> list[DataRouter]:
        data_routers: list[DataRouter] = []
        for config in data_routers_configs:
            data_routers.append(DataRouter(root=self, **config))

        return data_routers

    def run(self):
        logger.info("Starting main loop...")
        while True:
            self.render_frame()

    def profile(self, n_frames: int = 200):
        logger.info(f"Starting profiling of {n_frames} frames...")
        for _ in range(n_frames):
            self.render_frame()

    def sync_generators(self, gen_type_list: list[str]):
        for gen_type in gen_type_list:
            sync_dict = self.devices[0].rendermodule.get_selected_generator(gen_type).sync_send()
            for device in self.devices[1:]:
                device.rendermodule.get_selected_generator(gen_type).sync_load(in_dict=sync_dict)

    def render_frame(self):
        self.settings.before()
        # ------------------------------- apply inputs ------------------------------- #
        self.eventhandler.apply_settings_modifications_queue()
        # ---------------------------------- prepare --------------------------------- #
        self.autopilot.randomize()
        for device in self.devices:
            device.instructionhandler.load_and_apply_instructions()
        self.effecthandler.run_before()
        # ----------------------------------- sync ----------------------------------- #
        self.sync_generators(["pattern", "vfilter"])
        # ---------------------------------- render ---------------------------------- #
        for device in self.devices:
            device.render()
        # ------------------------------- effect after ------------------------------- #
        self.effecthandler.run_after()
        # ---------------------------------- output ---------------------------------- #
        if self.visualizer:
            self.visualizer.render()
        else:
            self.settings.timehandler.print_performance_stats()
        # --------------------------------- send data -------------------------------- #
        brightness = self.settings.global_brightness
        brightness = min(brightness, 0.5)
        matrices_int = [device.pixelmatrix.get_matrix_int(brightness=brightness) for device in self.devices]
        for datarouter in self.data_routers:
            datarouter.transmit_matrix(matrices_int)
        self.settings.after()

    def refresh_ui(self, sse_event: str):
        if hasattr(self, "rest_api"):
            self.rest_api.sse_event = sse_event
            self.rest_api.sse_unblock_event.set()
