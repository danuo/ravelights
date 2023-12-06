import json
import logging

import requests

logger = logging.getLogger(__name__)


class RestClient:
    def __init__(self, ip_address: str, port: int = 80):
        self._OUTPUT_CONFIG_LENGTH = 4
        self._REQUEST_TIMEOUT_SECONDS = 3

        base_url = f"http://{ip_address}:{port}/api"
        self._config_url = f"{base_url}/config"

    def get_output_config(self) -> list[int] | None:
        try:
            response = requests.get(self._config_url, timeout=self._REQUEST_TIMEOUT_SECONDS)
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
            isinstance(output_config, list)
            and len(output_config) == self._OUTPUT_CONFIG_LENGTH
            and all(isinstance(entry, int) for entry in output_config)
        ):
            logger.error(f"Output config is not a list of 4 ints: {output_config}")
            return None

        return output_config

    def set_output_config(self, output_config: list[int]) -> bool:
        assert len(output_config) == 4

        headers = {"Content-Type": "application/json"}
        try:
            response = requests.post(
                self._config_url, data=json.dumps(output_config), headers=headers, timeout=self._REQUEST_TIMEOUT_SECONDS
            )
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Error setting output config: {e}")
            return False

        return True
