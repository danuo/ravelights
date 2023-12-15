import json
import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class RestClient:
    OUTPUT_CONFIG_LENGTH: int = 4
    REQUEST_TIMEOUT_SECONDS: float = 3.0

    def __init__(self, ip_address: str, port: int = 80):
        base_url = f"http://{ip_address}:{port}/api"
        self._config_url = f"{base_url}/config"

    def get_output_config(self) -> Optional[list[int]]:
        try:
            response = requests.get(self._config_url, timeout=self.REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Error getting output config: {e}")
            return None

        try:
            output_config = response.json()
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding output config: {e}")
            return None

        if not (
            all(
                [
                    isinstance(output_config, list),
                    len(output_config) == self.OUTPUT_CONFIG_LENGTH,
                    all(isinstance(entry, int) for entry in output_config),
                ]
            )
        ):
            logger.error(f"Output config is not a list of {self.OUTPUT_CONFIG_LENGTH} ints: {output_config}")
            return None

        return output_config

    def set_output_config(self, output_config: list[int]) -> bool:
        assert len(output_config) == 4

        headers = {"Content-Type": "application/json"}
        try:
            response = requests.post(
                self._config_url, data=json.dumps(output_config), headers=headers, timeout=self.REQUEST_TIMEOUT_SECONDS
            )
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Error setting output config: {e}")
            return False

        return True
