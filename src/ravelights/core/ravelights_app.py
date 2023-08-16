import logging

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
        n_leds = config["n_leds"]
        n_lights = config["n_lights"]
        prim = True if device_id == 0 else False
        devices.append(Device(root=root, device_id=device_id, n_leds=n_leds, n_lights=n_lights, is_prim=prim))
    return devices


class RaveLightsApp:
    def __init__(
        self,
        *,
        fps=20,
        device_config: list[dict[str, int]],
        data_routers_configs: list[dict],
        webserver_port=80,
        serve_webinterface=True,
        visualizer=True,
    ):
        self.settings = Settings(device_config=device_config, fps=fps, bpm_base=80.0)
        self.devices = create_devices(root=self)
        self.autopilot = AutoPilot(root=self, autopilot_loop_length=16)
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
        self.rest_api.start_threaded(debug=True)

    def initiate_data_routers(self, data_routers_configs: list[dict]) -> list[DataRouter]:
        data_routers = []
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
        # todo: generalize
        # generators
        sync_dict = self.devices[0].rendermodule.get_selected_generator("pattern").sync_send()
        for device in self.devices[1:]:
            device.rendermodule.get_selected_generator("pattern").sync_load(in_dict=sync_dict)

        # vfilter
        sync_dict = self.devices[0].rendermodule.get_selected_generator("vfilter").sync_send()
        for device in self.devices[1:]:
            device.rendermodule.get_selected_generator("vfilter").sync_load(in_dict=sync_dict)
        # ---------------------------------- render ---------------------------------- #
        for i, device in enumerate(self.devices):
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
        matrices_int = [device.pixelmatrix.get_matrix_int(brightness=brightness) for device in self.devices]
        for datarouter in self.data_routers:
            datarouter.transmit_matrix(matrices_int)
        self.settings.after()
