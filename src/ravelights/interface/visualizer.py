from typing import TYPE_CHECKING, cast

import numpy as np
import numpy.typing as npt
import pygame

from ravelights.configs.visualizer_configurations import configurations
from ravelights.core.bpmhandler import BeatStatePattern, BPMhandler
from ravelights.core.device import Device
from ravelights.core.eventhandler import EventHandler
from ravelights.core.settings import Settings
from ravelights.core.timehandler import TimeHandler

if TYPE_CHECKING:
    from ravelights.core.ravelights_app import RaveLightsApp

C_BLACK = (0, 0, 0)
SCREENWIDTH = 1200
SCREENHEIGHT = 800
EDGE_HEIGHT = 5
CELLWIDTH = 7
GUISCALE = 1.5


class Visualizer:
    def __init__(self, root: "RaveLightsApp"):
        self.root = root
        self.settings: Settings = self.root.settings
        self.devices: list[Device] = self.root.devices
        self.eventhandler: EventHandler = self.root.eventhandler
        self.bpmhandler: BPMhandler = self.settings.bpmhandler
        self.timehandler: TimeHandler = self.settings.timehandler
        self.visualizer_config = self.get_visualizer_config()
        pygame.init()
        pygame.display.set_caption("ravelights")
        self.surface = pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT))
        self.surface.fill(C_BLACK)
        self.bpmhandler.bpm_sync()
        self.create_surfaces()

    def get_visualizer_config(self):
        device_config_string = str(self.settings.device_config)
        for configuration in configurations:
            if device_config_string == str(configuration["device_config"]):
                return configuration["visualizer_config"]
        raise Exception("could not find matching visualizer_configuration")

    def send_inputs_to_eventhandler(self):
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.bpmhandler.bpm_sync()
            if event.type == pygame.QUIT:
                exit()

    def create_surfaces(self):
        self.surfaces_small: list[list[pygame.Surface]] = []
        self.surfaces_big: list[list[pygame.Surface]] = []
        for device in self.devices:
            n_leds = device.pixelmatrix.n_leds
            n_lights = device.pixelmatrix.n_lights
            s_list_small: list[pygame.Surface] = []
            s_list_big: list[pygame.Surface] = []
            surface_size_small = (1, n_leds)
            surface_size_big = (10, n_leds)
            for _ in range(n_lights):
                s_list_small.append(pygame.Surface(surface_size_small))
                s_list_big.append(pygame.Surface(surface_size_big))
            self.surfaces_small.append(s_list_small)
            self.surfaces_big.append(s_list_big)

    def render(self):
        self.surface.fill(C_BLACK)
        for device_id, device in enumerate(self.devices):
            matrix_int = device.pixelmatrix.get_matrix_int()
            for light_id in range(device.pixelmatrix.n_lights):
                matrix_int_view = matrix_int[:, light_id, :]

                # RENDER AND SCALE
                surf_small = self.surfaces_small[device_id][light_id]
                surf_big = self.surfaces_big[device_id][light_id]
                array = np.expand_dims(cast(npt.NDArray[np.uint8], matrix_int_view), 0)
                pygame.surfarray.blit_array(surf_small, array)  # typing: ignore
                pygame.transform.scale(surf_small, surf_big.get_size(), surf_big)

                # GET POSITIONS FROM CONFIG
                x_pos_rel = self.visualizer_config[device_id][light_id]["x"]
                y_pos_rel = self.visualizer_config[device_id][light_id]["y"]
                rot = self.visualizer_config[device_id][light_id]["rot"]
                scale = self.visualizer_config[device_id][light_id]["scale"]

                # ROTATE AND PLACE
                new_surface = pygame.transform.rotozoom(surf_big, rot, scale * GUISCALE)
                x_shift, y_shift = new_surface.get_size()
                x_pos = int(SCREENWIDTH * x_pos_rel - x_shift * 0.5)
                y_pos = int(SCREENHEIGHT * y_pos_rel - y_shift * 0.5)
                self.surface.blit(new_surface, (x_pos, y_pos))
        self.draw_GUI()
        pygame.display.update()
        self.send_inputs_to_eventhandler()

    def draw_GUI(self):
        self._draw_beat_progress()
        self._draw_beat_state()
        self._draw_stats()

    def _draw_beat_progress(self):
        beat_progress = self.settings.beat_progress
        beat_progress_adjusted = (0.5 + beat_progress) % 1
        color = (0, 255, 0)
        square_w = 50
        square_h = 30
        x_pos = int(beat_progress_adjusted * SCREENWIDTH - 0.5 * square_w)
        y_pos = int(SCREENHEIGHT - square_h)
        pygame.draw.rect(self.surface, color, (x_pos, y_pos, square_w, square_h))

    def _draw_beat_state(self):
        """Draws blue rectangle on frames with beat."""
        if BeatStatePattern(loop_length=1).is_match(self.settings.beat_state):
            color = (0, 255, 255)
            square_w = 50
            square_h = 60
            x_pos = int(0.5 * (SCREENWIDTH) - 0.5 * square_w)
            y_pos = int(SCREENHEIGHT - square_h)
            pygame.draw.rect(self.surface, color, (x_pos, y_pos, square_w, square_h))

    def _draw_stats(self):
        stats = {k: str(v) for k, v in self.timehandler.get_stats().items()}
        fps = "".join(
            [
                "fps:",
                stats["avg_frame_time_inv"],
                "[",
                stats["avg_frame_time"],
                "s]",
            ]
        )
        render_time = "".join(
            [
                "cap:",
                stats["avg_render_time_inv"],
                "[",
                stats["avg_render_time"],
                "s]",
            ]
        )
        sleep = "".join(
            [
                "sleep:",
                stats["dynamic_sleep_time_inv"],
                "[",
                stats["dynamic_sleep_time"],
                "s]",
            ]
        )
        delayed_frames = "".join(
            [
                "delayed frames:",
                stats["delayed_frame_counter"],
            ]
        )
        bpm = "".join(
            [
                "bpm:",
                str(self.settings.bpm),
            ]
        )
        brightthinningenergy = "".join(
            [
                "bri:",
                str(self.settings.global_brightness),
                " thi:",
                str(self.settings.global_thinning_ratio),
                " energy:",
                str(self.settings.global_energy),
            ]
        )
        n_quarters_long = "nql: " + str(self.settings.n_quarters_long).zfill(3)

        self._draw_text(text=fps, x=10, y=10)
        self._draw_text(text=render_time, x=250, y=10)
        self._draw_text(text=sleep, x=500, y=10)
        self._draw_text(text=delayed_frames, x=750, y=10)

        self._draw_text(text=bpm, x=10, y=50)
        self._draw_text(text=brightthinningenergy, x=250, y=50)
        self._draw_text(text=n_quarters_long, x=SCREENWIDTH - 10, y=10, position="topright")

    def _draw_text(
        self,
        text: str,
        size: int = 20,
        x: int = 0,
        y: int = 0,
        font_name: str = pygame.font.match_font("consolas"),
        position: str = "topleft",
    ):
        font = pygame.font.Font(font_name, size)
        text_surface = font.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect()
        if position == "topleft":
            text_rect.topleft = (x, y)
        if position == "topright":
            text_rect.topright = (x, y)
        self.surface.blit(text_surface, text_rect)
