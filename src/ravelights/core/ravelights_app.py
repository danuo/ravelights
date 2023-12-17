import logging
from dataclasses import asdict

from ravelights import DeviceLightConfig, TransmitterConfig
from ravelights.core.autopilot import AutoPilot
from ravelights.core.device import Device
from ravelights.core.effecthandler import EffectHandler
from ravelights.core.eventhandler import EventHandler
from ravelights.core.methandler import MetaHandler
from ravelights.core.patternscheduler import PatternScheduler
from ravelights.core.settings import Settings
from ravelights.core.timehandler import TimeHandler
from ravelights.interface.datarouter import DataRouter, DataRouterTransmitter, DataRouterVisualizer, DataRouterWebsocket
from ravelights.interface.discovery import discovery_service
from ravelights.interface.restapi import RestAPI

logger = logging.getLogger(__name__)


class RaveLightsApp:
    def __init__(
        self,
        *,
        fps: int = 20,
        webui_port: int = 80,
        serve_webui: bool = True,
        device_config: list[DeviceLightConfig] = [DeviceLightConfig(n_lights=2, n_leds=100)],
        transmitter_recipes: list[TransmitterConfig] = [],
        use_visualizer: bool = False,
        print_stats: bool = False,
        run: bool = True,
    ):
        self.settings = Settings(root_init=self, device_config=device_config, fps=fps, bpm_base=140.0)
        self.timehandler = TimeHandler(root=self)
        self.devices = [Device(root=self, device_id=idx, **asdict(conf)) for idx, conf in enumerate(device_config)]
        self.autopilot = AutoPilot(root=self)
        self.effecthandler = EffectHandler(root=self)
        self.patternscheduler = PatternScheduler(root=self)
        self.metahandler = MetaHandler(root=self)
        self.eventhandler = EventHandler(root=self)

        self.data_routers = self.initiate_data_routers(transmitter_recipes)

        self.rest_api = RestAPI(
            root=self,
            serve_webui=serve_webui,
            port=webui_port,
        )

        self.use_visualizer = use_visualizer
        self.print_stats = print_stats

        discovery_service.start()

        if run:
            if self.use_visualizer:
                from ravelights.interface.visualizer import Visualizer

                self.visualizer = Visualizer(root=self)
            self.run()

    def initiate_data_routers(self, transmitter_recipes: list[TransmitterConfig]) -> list[DataRouter]:
        data_routers: list[DataRouter] = [DataRouterVisualizer(root=self), DataRouterWebsocket(root=self)]
        for receipt in transmitter_recipes:
            # at the moment, all datarouters created from receipts are DataRouterTransmitter
            data_router_transmitter = DataRouterTransmitter(root=self)
            data_router_transmitter.apply_transmitter_receipt(**receipt)
            data_routers.append(data_router_transmitter)

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
        self.timehandler.before()
        self.settings.color_engine.before()
        # ─── Apply Inputs ─────────────────────────────────────────────
        self.eventhandler.apply_settings_modifications_queue()
        # ─── Prepare ──────────────────────────────────────────────────
        self.autopilot.randomize()
        for device in self.devices:
            device.instructionhandler.load_and_apply_instructions()
        self.effecthandler.run_before()
        # ─── Sync ─────────────────────────────────────────────────────
        self.sync_generators(["pattern", "vfilter"])
        # ─── Render ───────────────────────────────────────────────────
        for device in self.devices:
            device.render()
        # ─── Effect After ─────────────────────────────────────────────
        self.effecthandler.run_after()
        # ─── Output ───────────────────────────────────────────────────
        if self.print_stats:
            self.timehandler.print_performance_stats()
        # ─── Send Data ────────────────────────────────────────────────
        matrices_processed_int = [device.get_matrix_processed_int() for device in self.devices]
        matrices_int = [device.get_matrix_int() for device in self.devices]
        for datarouter in self.data_routers:
            datarouter.transmit_matrix(matrices_processed_int, matrices_int)
        # ─── After ────────────────────────────────────────────────────
        self.timehandler.after()

    def refresh_ui(self, sse_event: str):
        if hasattr(self, "rest_api"):
            self.rest_api.sse_event = sse_event
            self.rest_api.sse_unblock_event.set()
