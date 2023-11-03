import importlib.resources
import logging
import threading
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from flask import Flask, Response, jsonify, make_response, request, send_from_directory
from flask_restful import Api, Resource, fields, marshal_with  # type: ignore
from flask_socketio import SocketIO, emit
from ravelights.core.eventhandler import EventHandler
from ravelights.core.methandler import MetaHandler
from ravelights.core.patternscheduler import PatternScheduler
from ravelights.core.settings import Settings

if TYPE_CHECKING:
    from ravelights.core.device import Device
    from ravelights.core.ravelights_app import RaveLightsApp

logger = logging.getLogger(__name__)


class RestAPI:
    def __init__(
        self,
        root: "RaveLightsApp",
        port: int = 80,
        serve_static_files: bool = True,
        static_files_dir: Optional[Path] = None,
    ):
        self.root = root
        self.port = port

        self.sse_event: str = ""
        self.sse_unblock_event = threading.Event()

        static_files_dir = self.check_static_files_dir(static_files_dir)

        self.websocket_html = self.get_websocket_html()
        self.websocket_num_clients: int = 0

        self.flask_app = Flask(__name__)
        self.socketio = SocketIO(self.flask_app)

        # ─── Static Files ─────────────────────────────────────────────

        self.get_websocket_html()

        if serve_static_files:
            if len(list(static_files_dir.iterdir())) < 5:
                logger.warning(f"Could not find static files for webui in {static_files_dir=}")

            # serve index.html
            @self.flask_app.route("/")
            def serve_index():
                return send_from_directory(static_files_dir, "index.html")

            # serve index.html
            @self.flask_app.route("/websocket")
            def serve_websocket():
                # return self.websocket_html
                return self.get_websocket_html()

            # serve any other file in static_dir
            @self.flask_app.route("/<path:path>")
            def serve_static(path):
                return send_from_directory(static_files_dir, path)

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
        @self.socketio.event
        def my_event(message):
            emit("my response", {"data": "got it!"})

        @self.socketio.on("connect")
        def handle_connect():
            self.websocket_num_clients += 1
            print(self.websocket_num_clients)
            print("connected - socket stuff is happening")
            emit("my response", {"data": "Connected"})

        @self.socketio.on("disconnect")
        def handle_disconnect():
            self.websocket_num_clients -= 1
            print(self.websocket_num_clients)
            print("disconnected - socket stuff is happening")

        self.start_threaded()

    def block_once(self):
        """this could be any function that blocks until data is ready"""
        self.sse_unblock_event.wait()
        self.sse_unblock_event.clear()

    def check_static_files_dir(self, static_files_dir: Optional[Path] = None) -> Path:
        """Hacky way to obtain an actual str/path object of the directory. Methods such as str() do not work."""
        if not static_files_dir:
            lib_path = importlib.resources.files("ravelights_ui")
            if isinstance(lib_path, Path):
                static_files_dir = lib_path
            else:
                static_files_dir = Path(lib_path._paths[0])  # type: ignore

        if not (static_files_dir / "index.html").is_file():
            logger.warning("warning, static UI files could not be found")
            logger.warning("trying to find the ui at path:")
            logger.warning(static_files_dir)

        return static_files_dir

    def get_websocket_html(self):
        MODULE_PATH = importlib.resources.files(__package__)
        return (MODULE_PATH / "websocket_assets" / "websocket_ui.html").read_text()

    def setup_resource_routing(self):
        self._api = Api(self.flask_app)
        self._api.add_resource(SettingsAPIResource, "/rest/settings", resource_class_args=(self.root,))
        self._api.add_resource(TriggersAPIResource, "/rest/triggers", resource_class_args=(self.root,))
        self._api.add_resource(DevicesAPIResource, "/rest/devices", resource_class_args=(self.root,))
        self._api.add_resource(MetaAPIResource, "/rest/meta", resource_class_args=(self.root,))
        self._api.add_resource(EffectAPIResource, "/rest/effect", resource_class_args=(self.root,))

    def start_threaded(self, debug: bool = False):
        logger.info("Starting REST API thread...")
        # threading.Thread(
        #     target=lambda: self.flask_app.run(host="0.0.0.0", port=self.port, debug=debug, use_reloader=False),
        #     daemon=True,
        # ).start()
        threading.Thread(
            target=lambda: self.socketio.run(
                app=self.flask_app, host="0.0.0.0", port=self.port, debug=debug, use_reloader=False
            ),
            daemon=True,
        ).start()


class SettingsAPIResource(Resource):
    def __init__(self, root: "RaveLightsApp"):
        super().__init__()
        self.eventhandler = root.eventhandler
        self.settings: Settings = root.settings
        self.patternscheduler: PatternScheduler = root.patternscheduler

    def get(self):
        data = asdict(self.settings)
        data["colors"] = self.settings.color_engine.get_colors_rgb_target()
        # ic(data)
        return make_response(jsonify(data), 200)

    def put(self):
        receive_data: dict[str, Any] = request.get_json()
        if isinstance(receive_data, dict):
            print(receive_data)
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
    "device_id": fields.Integer,
    "n_leds": fields.Integer,
    "n_lights": fields.Integer,
    "is_prim": fields.Boolean,
    "device_manual_timeline_level": fields.Integer,
    "device_triggerskip": fields.Integer,
    "device_frameskip": fields.Integer,
    "device_brightness": fields.Float,
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
        self.metahandler: MetaHandler = root.metahandler
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
        self.effecthandler = root.effecthandler
        self.eventhandler: EventHandler = root.eventhandler

    @marshal_with(resource_fields_effect)
    def get(self):
        return self.effecthandler.effect_queues, 200

    def put(self):
        receive_data = request.get_json()
        print(receive_data)
        if isinstance(receive_data, dict):
            self.eventhandler.add_to_modification_queue(receive_data=receive_data)
        return "", 204
