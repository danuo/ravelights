import logging
from collections import defaultdict
from typing import DefaultDict

from ravelights.core.custom_typing import DiscoveryUpdateCallback
from zeroconf import ServiceInfo, ServiceListener, Zeroconf

_logger = logging.getLogger(__name__)


class PixeldriverServiceListener(ServiceListener):
    def __init__(self) -> None:
        super().__init__()
        self._hosts: dict[str, str] = {}
        self._callbacks: DefaultDict[str, list[DiscoveryUpdateCallback]] = defaultdict(list)

    def _extract_hostname_and_ip(self, service_info: ServiceInfo | None) -> tuple[str, str] | tuple[None, None]:
        if service_info is None or service_info.server is None:
            return None, None

        hostname = service_info.server.replace(".local.", "")
        ip_address = service_info.parsed_addresses()[0]

        if hostname in self._callbacks:
            return hostname, ip_address

        return None, None

    def _notify_listeners(self, hostname: str, ip_address: str | None) -> None:
        _logger.info(f"Sending discovery update for device {hostname} ({ip_address})...")
        for callback in self._callbacks[hostname]:
            callback(hostname, ip_address)

    def register_callback(self, hostname: str, on_discovery_update: DiscoveryUpdateCallback) -> None:
        self._callbacks[hostname].append(on_discovery_update)

    def update_service(self, zeroconf: Zeroconf, service_type: str, service_name: str) -> None:
        service_info = zeroconf.get_service_info(service_type, service_name)
        hostname, ip_address = self._extract_hostname_and_ip(service_info)

        if hostname is None or ip_address is None:
            return

        if hostname not in self._hosts:
            _logger.warn("Received service update for unknown device. Treating as new device")
            self._hosts[hostname] = ip_address
            self._notify_listeners(hostname, ip_address)
            return

        if self._hosts[hostname] != ip_address:
            self._hosts[hostname] = ip_address
            self._notify_listeners(hostname, ip_address)

    def remove_service(self, zeroconf: Zeroconf, service_type: str, service_name: str) -> None:
        service_info = zeroconf.get_service_info(service_type, service_name)
        hostname, ip_address = self._extract_hostname_and_ip(service_info)

        if hostname not in self._callbacks:
            return

        if hostname not in self._hosts:
            _logger.warn(f"Received service removal for unknown device {hostname} ({ip_address})")
            return

        del self._hosts[hostname]
        self._notify_listeners(hostname, None)

    def add_service(self, zeroconf: Zeroconf, service_type: str, service_name: str) -> None:
        service_info = zeroconf.get_service_info(service_type, service_name)
        hostname, ip_address = self._extract_hostname_and_ip(service_info)

        if hostname is None or ip_address is None:
            return

        if hostname in self._hosts and self._hosts[hostname] == ip_address:
            return

        self._hosts[hostname] = ip_address
        self._notify_listeners(hostname, ip_address)
