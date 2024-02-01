from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

import numpy as np
from loguru import logger
from ravelights.core.custom_typing import ArrayUInt8, LightIdentifier, Transmitter
from ravelights.interface.artnet.artnet_transmitter import ArtnetTransmitter
from ravelights.interface.artnet.artnet_udp_transmitter import ArtnetUdpTransmitter
from ravelights.interface.discovery import discovery_service
from ravelights.interface.rest_client import RestClient

if TYPE_CHECKING:
    from ravelights import RaveLightsApp


class DataRouter(ABC):
    def __init__(self, root: "RaveLightsApp"):
        self.root = root
        self.settings = self.root.settings
        self.devices = self.root.devices

    @abstractmethod
    def transmit_matrix(self, matrices_processed_int: list[ArrayUInt8], matrices_int: list[ArrayUInt8]):
        ...


class DataRouterTransmitter(DataRouter):
    def __init__(self, root: "RaveLightsApp"):
        self.root = root
        self.settings = self.root.settings
        self.devices = self.root.devices
        self._ip_address: Optional[str] = None

    def _on_discovery_update(self, hostname: str, new_ip_address: Optional[str]):
        if new_ip_address != self._ip_address:
            if new_ip_address is not None:
                rest_client = RestClient(ip_address=new_ip_address)
                rest_client.set_output_config(self.leds_per_output)
                logger.info(f"Set output config for {hostname} ({new_ip_address}) to {self.leds_per_output}")

            if isinstance(self.transmitter, ArtnetUdpTransmitter):
                self.transmitter.update_ip_address(new_ip_address)

            self._ip_address = new_ip_address

    def apply_transmitter_receipt(
        self,
        transmitter: Transmitter,
        light_mapping_config: list[list[LightIdentifier]],
        hostname: str,
    ):
        assert isinstance(transmitter, ArtnetTransmitter)
        self.transmitter = transmitter
        self.leds_per_output, self.out_lights, self.n = self.process_light_mapping_config(light_mapping_config)
        # one out matrix per datarouter / transmitter
        self.out_matrix = np.zeros((self.n, 3), dtype=np.uint8)

        discovery_service.register_callback(hostname, self._on_discovery_update)
        logger.info(f"Initialized transmitter for device {hostname}. Waiting for IP address to be discovered...")

    def process_light_mapping_config(self, light_mapping_config: list[list[LightIdentifier]]):
        leds_per_output: list[int] = []
        out_lights: list[LightIdentifier] = []
        for transmitter_output in light_mapping_config:
            n_output: int = 0
            light_identifier: LightIdentifier
            for light_identifier in transmitter_output:
                out_lights.append(light_identifier)
                n_output += self.devices[light_identifier["device"]].n_leds
            leds_per_output.append(n_output)
        n_total = sum(leds_per_output)
        return leds_per_output, out_lights, n_total

    def transmit_matrix(self, matrices_processed_int: list[ArrayUInt8], matrices_int: list[ArrayUInt8]):
        index = 0
        for out_light in self.out_lights:
            matrix_view = matrices_processed_int[out_light["device"]][:, out_light["light"], :]
            length = matrix_view.shape[0]
            if "flip" in out_light and out_light["flip"]:
                matrix_view = np.flip(matrix_view, axis=0)
            self.out_matrix[index : index + length] = matrix_view
            index += length
        self.transmitter.transmit_matrix(matrix=self.out_matrix)


class DataRouterWebsocket(DataRouter):
    """sends matrices_int at full brightness to websocket"""

    def transmit_matrix(self, matrices_processed_int: list[ArrayUInt8], matrices_int: list[ArrayUInt8]):
        if hasattr(self.root, "rest_api"):
            if self.root.rest_api.websocket_num_clients > 0:
                matrix_int = matrices_int[0]
                matrix_int = matrix_int.reshape((-1, 3), order="F")

                # turn into rgba
                matrix_int_padded = np.pad(matrix_int, pad_width=((0, 0), (0, 1)), constant_values=255)
                data = matrix_int_padded.flatten().tobytes()
                self.root.rest_api.socketio.send(data)


class DataRouterVisualizer(DataRouter):
    """sends matrices_int at full brightness to pygame visualizer"""

    def transmit_matrix(self, matrices_processed_int: list[ArrayUInt8], matrices_int: list[ArrayUInt8]):
        if hasattr(self.root, "visualizer"):
            self.root.visualizer.render(matrices_int)
