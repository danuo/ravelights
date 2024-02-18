import multiprocessing
from dataclasses import asdict
from typing import Literal

from loguru import logger
from ravelights.audio.audio_data import AudioDataProvider
from ravelights.constants import __api_version__, logo
from ravelights.core.autopilot import AutoPilot
from ravelights.core.custom_typing import TransmitterConfig
from ravelights.core.device import Device
from ravelights.core.device_shared import DeviceLightConfig
from ravelights.core.effect_handler import EffectHandler
from ravelights.core.event_handler import EventHandler
from ravelights.core.meta_handler import MetaHandler
from ravelights.core.pattern_scheduler import PatternScheduler
from ravelights.core.settings import Settings
from ravelights.core.time_handler import TimeHandler
from ravelights.interface.data_router import (
    DataRouter,
    DataRouterTransmitter,
    DataRouterVisualizer,
    DataRouterWebsocket,
)
from ravelights.interface.discovery import connectivity_check, discovery_service
from ravelights.interface.rest_api import RestAPI


class RaveLightsApp:
    def __init__(
        self,
        *,
        fps: int = 30,
        webui_port: int = 80,
        serve_webui: bool = True,
        device_config: list[DeviceLightConfig] = [DeviceLightConfig(n_lights=2, n_leds=100)],
        transmitter_recipes: list[TransmitterConfig] = [],
        use_audio: bool = True,
        use_visualizer: bool = False,
        print_stats: bool = False,
    ) -> None:
        self.API_VERSION = __api_version__
        self.settings = Settings(
            root_init=self,
            device_config=device_config,
            fps=fps,
            bpm_base=140.0,
            serve_webui=serve_webui,
            use_audio=use_audio,
            use_visualizer=use_visualizer,
            print_stats=print_stats,
        )
        self.time_handler = TimeHandler(root=self)
        self.devices = [Device(root=self, device_index=idx, **asdict(conf)) for idx, conf in enumerate(device_config)]
        self.autopilot = AutoPilot(root=self)
        self.effect_handler = EffectHandler(root=self)
        self.pattern_scheduler = PatternScheduler(root=self)
        self.meta_handler = MetaHandler(root=self)
        self.event_handler = EventHandler(root=self)
        self.data_routers = self.initiate_data_routers(transmitter_recipes)
        self.rest_api = RestAPI(root=self, serve_webui=serve_webui, port=webui_port)
        self.audio_data = AudioDataProvider(root=self)

        self.pattern_scheduler.load_timeline_from_index(self.settings.active_timeline_index)

    def initiate_data_routers(self, transmitter_recipes: list[TransmitterConfig]) -> list[DataRouter]:
        data_routers: list[DataRouter] = [DataRouterVisualizer(root=self), DataRouterWebsocket(root=self)]
        for receipt in transmitter_recipes:
            # at the moment, all datarouters created from receipts are DataRouterTransmitter
            data_router_transmitter = DataRouterTransmitter(root=self)
            data_router_transmitter.apply_transmitter_receipt(**receipt)
            data_routers.append(data_router_transmitter)

        return data_routers

    def start(self) -> None:
        connectivity_check.wait_until_connected_to_network()
        discovery_service.start()

        if self.settings.use_audio:
            from ravelights.audio.audio_analyzer import audio_analyzer_process

            sender_connection, receiver_connection = multiprocessing.Pipe()
            self.audio_analyzer_process = multiprocessing.Process(
                target=audio_analyzer_process,
                args=(sender_connection,),
                daemon=True,
            )
            self.audio_analyzer_process.start()
            self.audio_data.set_connection(connection=receiver_connection)

        if self.settings.use_visualizer:
            from ravelights.interface.visualizer import Visualizer

            self.visualizer = Visualizer(root=self)

        # load default timeline
        # self.patternscheduler.load_timeline_from_index(0)
        self.pattern_scheduler.load_timeline_by_name("DEBUG_TIMELINE")
        logger.info("Starting main loop...")
        logger.opt(raw=True, colors=True).info(f"<magenta>{logo}</magenta>\n")

        while True:
            self.render_frame()

    def profile(self, n_frames: int = 200) -> None:
        logger.info(f"Starting profiling of {n_frames} frames...")
        for _ in range(n_frames):
            self.render_frame()

    def sync_generators(
        self, gen_type_list: list[Literal["pattern", "pattern_sec", "pattern_break", "vfilter", "dimmer", "thinner"]]
    ) -> None:
        """synchronizes the generators of given type across devices, if they are linked"""
        for gen_type in gen_type_list:
            for device in self.devices:
                if device.linked_to is None:
                    continue

                sync_dict = self.devices[device.linked_to].rendermodule.get_selected_generator(gen_type).sync_send()
                device.rendermodule.get_selected_generator(gen_type).sync_load(in_dict=sync_dict)

    def render_frame(self) -> None:
        self.time_handler.before()
        self.settings.color_engine.before()
        self.audio_data.collect_audio_data()
        # ─── Apply Inputs ─────────────────────────────────────────────
        self.event_handler.apply_settings_modifications_queue()
        # ─── Prepare ──────────────────────────────────────────────────
        self.autopilot.randomize()
        for device in self.devices:
            device.instructionhandler.load_and_apply_instructions()
        self.effect_handler.run_before()
        # ─── Sync ─────────────────────────────────────────────────────
        self.sync_generators(["pattern", "vfilter"])
        # ─── Render ───────────────────────────────────────────────────
        for device in self.devices:
            device.render()
        # ─── Effect After ─────────────────────────────────────────────
        self.effect_handler.run_after()
        # ─── Output ───────────────────────────────────────────────────
        if self.settings.print_stats:  # this doesnt have to be frozen
            self.time_handler.print_performance_stats()
        # ─── Send Data ────────────────────────────────────────────────
        matrices_processed_int = [device.get_matrix_processed_int() for device in self.devices]
        matrices_int = [device.get_matrix_int() for device in self.devices]
        for datarouter in self.data_routers:
            datarouter.transmit_matrix(matrices_processed_int, matrices_int)
        # ─── After ────────────────────────────────────────────────────
        self.time_handler.after()

    def refresh_ui(self, sse_event: str) -> None:
        if hasattr(self, "rest_api"):
            self.rest_api.sse_event = sse_event
            self.rest_api.sse_unblock_event.set()
