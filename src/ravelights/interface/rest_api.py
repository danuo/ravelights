import importlib.resources
import threading
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING, Any

from flask import Flask, Response, jsonify, make_response, request, send_from_directory
from flask_restful import Api, Resource, fields, marshal_with  # type: ignore
from flask_socketio import SocketIO, emit  # type: ignore
from loguru import logger
from ravelights.core.event_handler import EventHandler
from ravelights.core.meta_handler import MetaHandler
from ravelights.core.pattern_scheduler import PatternScheduler
from ravelights.core.settings import Settings

if TYPE_CHECKING:
    from ravelights.core.device import Device
    from ravelights.core.ravelights_app import RaveLightsApp


class RestAPI:
    def __init__(
        self,
        root: "RaveLightsApp",
        port: int = 80,
        serve_webui: bool = True,
    ):
        self.root = root
        self.port = port

        self.sse_event: str = ""
        self.sse_unblock_event = threading.Event()

        self.websocket_num_clients: int = 0

        self.flask_app = Flask(__name__)
        self.socketio = SocketIO(
            self.flask_app,
            cors_allowed_origins="*",
        )

        # ─── Static Files ─────────────────────────────────────────────

        if serve_webui:
            self.quasar_dir = self.get_quasar_ui_dir()

            # serve index at root
            @self.flask_app.route("/")
            def serve_qusar_index():
                return send_from_directory(self.quasar_dir, "index.html")

            # serve any other file in static_dir
            @self.flask_app.route("/<path:path>")
            def serve_quasar_static(path):
                return send_from_directory(self.quasar_dir, path)

        # ─── SSE ──────────────────────────────────────────────────────

        @self.flask_app.route("/sse")
        def stream():
            def event_stream():
                while True:
                    self.block_once()
                    yield f"data: {self.sse_event}\n\n"

            return Response(event_stream(), 200, content_type="text/event-stream")

        # ─── REST ─────────────────────────────────────────────────────
        self.setup_resource_routing()

        # ─── Websocket ────────────────────────────────────────────────
        @self.socketio.on("connect")
        def handle_connect():
            self.websocket_num_clients += 1
            logger.info("connected - new websocket client connected")
            logger.info(f"{self.websocket_num_clients} connected in total")
            emit("my response", {"data": "Connected"})

        @self.socketio.on("disconnect")
        def handle_disconnect():
            self.websocket_num_clients -= 1
            logger.info("disconnected - websocket client connected")
            logger.info(f"{self.websocket_num_clients} connected in total")

        self.start_threaded()

    def block_once(self):
        """this could be any function that blocks until data is ready"""
        self.sse_unblock_event.wait()
        self.sse_unblock_event.clear()

    def get_quasar_ui_dir(self) -> Path:
        """get quasar (ravelights_ui) dir"""
        path_manager = importlib.resources.path("ravelights_ui", "index.html")
        with path_manager as path:
            if path.is_file():
                return path.parent
            else:
                logger.warning("quasar ui files could not be found")
                logger.warning("trying to find the ui at path:")
                logger.warning(path)
                raise FileNotFoundError

    def setup_resource_routing(self):
        self._api = Api(self.flask_app)
        self._api.add_resource(SettingsAPIResource, "/rest/settings", resource_class_args=(self.root,))
        self._api.add_resource(TriggersAPIResource, "/rest/triggers", resource_class_args=(self.root,))
        self._api.add_resource(DevicesAPIResource, "/rest/devices", resource_class_args=(self.root,))
        self._api.add_resource(MetaAPIResource, "/rest/meta", resource_class_args=(self.root,))
        self._api.add_resource(EffectAPIResource, "/rest/effect", resource_class_args=(self.root,))

    def start_threaded(self, debug: bool = False):
        logger.info("Starting REST API thread...")
        threading.Thread(
            target=lambda: self.socketio.run(
                app=self.flask_app,
                host="0.0.0.0",
                port=self.port,
                debug=debug,
                use_reloader=False,
                allow_unsafe_werkzeug=True,
            ),
            daemon=True,
        ).start()


class SettingsAPIResource(Resource):
    def __init__(self, root: "RaveLightsApp"):
        super().__init__()
        self.eventhandler = root.event_handler
        self.settings: Settings = root.settings
        self.patternscheduler: PatternScheduler = root.pattern_scheduler

    def get(self):
        data = asdict(self.settings)
        data["colors"] = self.settings.color_engine.get_colors_rgb_target()
        # ic(data)
        return make_response(jsonify(data), 200)

    def put(self):
        receive_data: dict[str, Any] = request.get_json()
        if isinstance(receive_data, dict):
            logger.debug(receive_data)
            self.eventhandler.add_to_modification_queue(receive_data=receive_data)
        return "", 204


class TriggersAPIResource(Resource):
    def __init__(self, root: "RaveLightsApp"):
        super().__init__()
        self.settings: Settings = root.settings

    def get(self):
        data = self.settings.triggers
        return make_response(jsonify(data), 200)


resource_fields_devices = {
    "device_index": fields.Integer,
    "n_leds": fields.Integer,
    "n_lights": fields.Integer,
    "is_prim": fields.Boolean,
    "linked_to": fields.Integer(default=None),
    "device_triggerskip": fields.Integer,
    "device_frameskip": fields.Integer,
    "device_brightness": fields.Float,
    "device_manual_timeline_level": fields.Integer(default=None),
    "refresh_from_timeline": fields.Boolean,
    "use_autopilot": fields.Boolean,
    "use_effect": fields.Raw,
}


class DevicesAPIResource(Resource):
    def __init__(self, root: "RaveLightsApp"):
        super().__init__()
        self.devices: list["Device"] = root.devices

    @marshal_with(resource_fields_devices)
    def get(self):
        return self.devices, 200


class MetaAPIResource(Resource):
    def __init__(self, root: "RaveLightsApp"):
        super().__init__()
        self.metahandler: MetaHandler = root.meta_handler
        self.data = None

    def get(self):
        if self.data is None:
            self.data = jsonify(self.metahandler.api_content)
        return make_response(self.data, 200)


resource_fields_effect = {
    "name": fields.String,
    "mode": fields.String,
    "draw_mode": fields.String,
    "limit_frames": fields.String,
    "loop_length": fields.String,
    "trigger": fields.String,
}


class EffectAPIResource(Resource):
    def __init__(self, root: "RaveLightsApp"):
        super().__init__()
        self.settings: Settings = root.settings
        self.effecthandler = root.effect_handler
        self.eventhandler: EventHandler = root.event_handler

    @marshal_with(resource_fields_effect)
    def get(self):
        return self.effecthandler.effect_queues, 200

    def put(self):
        receive_data = request.get_json()
        logger.debug(receive_data)
        if isinstance(receive_data, dict):
            self.eventhandler.add_to_modification_queue(receive_data=receive_data)
        return "", 204
