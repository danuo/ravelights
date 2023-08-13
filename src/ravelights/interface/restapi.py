import importlib.resources
import logging
import threading
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from flask import Flask, jsonify, make_response, request, send_from_directory
from flask_restful import Api, Resource, fields, marshal_with

from ravelights.core.custom_typing import T_JSON
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
        serve_static_files=True,
        static_files_dir: Optional[Path] = None,
    ):
        self.root = root
        self.port = port

        static_files_dir = self.check_static_files_dir(static_files_dir)

        self._flask_app = Flask(__name__)

        if serve_static_files:
            if len(list(static_files_dir.iterdir())) < 5:
                logger.warning(f"Could not find static files for webui in {static_files_dir=}")

            # serve index.html
            @self._flask_app.route("/")
            def serve_index():
                return send_from_directory(static_files_dir, "index.html")

            # serve any other file in static_dir
            @self._flask_app.route("/<path:path>")
            def serve_static(path):
                return send_from_directory(static_files_dir, path)

        # add rest api
        self._api = Api(self._flask_app)
        self._setup_resource_routing()

    def check_static_files_dir(self, static_files_dir: Optional[Path] = None) -> Path:
        """Hacky way to obtain an actual str/path object of the directory. Methods such as str() do not work."""
        if not static_files_dir:
            lib_path = importlib.resources.files("ravelights_ui")
            if isinstance(lib_path, Path):
                static_files_dir = lib_path
            else:
                static_files_dir = Path(lib_path._paths[0])

        if not (static_files_dir / "index.html").is_file():
            logger.warning("warning, static UI files could not be found")
            logger.warning("trying to find the ui at path:")
            logger.warning(static_files_dir)

        return static_files_dir

    def _setup_resource_routing(self):
        self._api.add_resource(RaveAPIResource, "/rest", resource_class_args=(self.root,))
        self._api.add_resource(DevicesAPIResource, "/rest/devices", resource_class_args=(self.root,))
        self._api.add_resource(MetaAPIResource, "/rest/meta", resource_class_args=(self.root,))
        self._api.add_resource(ColorAPIResource, "/rest/color", resource_class_args=(self.root,))
        self._api.add_resource(EffectAPIResource, "/rest/effect", resource_class_args=(self.root,))

    def start_threaded(self, debug: bool = False):
        logger.info("Starting REST API thread...")
        threading.Thread(
            target=lambda: self._flask_app.run(host="0.0.0.0", port=self.port, debug=debug, use_reloader=False),
            daemon=True,
        ).start()


class RaveAPIResource(Resource):
    def __init__(self, root: "RaveLightsApp"):
        super().__init__()
        self.eventhandler = root.eventhandler
        self.settings: Settings = root.settings
        self.patternscheduler: PatternScheduler = root.patternscheduler

    def get(self):
        data = asdict(self.settings)
        return make_response(jsonify(data), 200)

    def put(self):
        receive_data: T_JSON = request.get_json()
        if isinstance(receive_data, dict):
            self.eventhandler.add_to_modification_queue(receive_data=receive_data)
        return "", 204


class DevicesAPIResource(Resource):
    def __init__(self, root: "RaveLightsApp"):
        super().__init__()
        self.devices: list["Device"] = root.devices

    def get(self):
        out = jsonify("test")
        return make_response(out, 200)


class MetaAPIResource(Resource):
    def __init__(self, root: "RaveLightsApp"):
        super().__init__()
        self.metahandler: MetaHandler = root.metahandler
        self.data = None

    def get(self):
        if self.data is None:
            self.data = jsonify(self.metahandler.api_content)
        return make_response(self.data, 200)


class ColorAPIResource(Resource):
    def __init__(self, root: "RaveLightsApp"):
        super().__init__()
        self.settings: Settings = root.settings
        self.eventhandler: EventHandler = root.eventhandler
        self.patternscheduler: PatternScheduler = root.patternscheduler

    def get(self):
        colors = self.settings.color_engine.get_colors_rgb_target()
        return make_response(jsonify(colors), 200)

    def put(self):
        """directly apply color so that resulting colors can be returned"""
        receive_data: T_JSON = request.get_json()
        print(receive_data)
        if receive_data.get("action") == "set_color":
            color_rgb = receive_data.get("color")
            level = receive_data.get("level")
            self.settings.color_engine.set_color_with_rule(color=color_rgb, color_level=level)
        colors = self.settings.color_engine.get_colors_rgb_target()
        return make_response(jsonify(colors), 201)


resource_fields = {
    "name": fields.String,
    "mode": fields.String,
    "limit_frames": fields.String,
    "loop_length": fields.String,
}


class EffectAPIResource(Resource):
    def __init__(self, root: "RaveLightsApp"):
        super().__init__()
        self.settings: Settings = root.settings
        self.effecthandler = root.effecthandler
        self.eventhandler: EventHandler = root.eventhandler

    @marshal_with(resource_fields)
    def get(self):
        return self.effecthandler.effect_queue, 200

    def put(self):
        receive_data: T_JSON = request.get_json()
        print(receive_data)
        if isinstance(receive_data, dict):
            self.eventhandler.add_to_modification_queue(receive_data=receive_data)
        return "", 204
