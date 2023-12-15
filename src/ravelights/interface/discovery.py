import time

from zeroconf import ServiceBrowser, ServiceListener, Zeroconf


def discover_pixeldrivers(duration_seconds: int = 1) -> dict[str, str]:
    """Discovers pixeldrivers on the local network using mDNS

    Args:
        duration_seconds (int, optional): The discovery duration in seconds. Defaults to 1 second.

    Returns:
        dict[str, str]: A dictionary of the discovered pixeldrivers, where the hostname is mapped to the IP address
    """

    zeroconf = Zeroconf()
    device_discoverer = _DeviceDiscoverer()
    service_browser = ServiceBrowser(
        zc=zeroconf, type_=["_artnet._udp.local.", "_http._tcp.local."], listener=device_discoverer
    )

    # Wait for devices to be discovered by the service browser in the background
    time.sleep(duration_seconds)

    service_browser.cancel()
    zeroconf.close()

    return device_discoverer.devices


class _DeviceDiscoverer(ServiceListener):
    def __init__(self) -> None:
        super().__init__()
        self._devices: dict[str, str] = {}

    @property
    def devices(self):
        return self._devices

    def update_service(self, zeroconf: Zeroconf, service_type: str, service_name: str) -> None:
        pass

    def remove_service(self, zeroconf: Zeroconf, service_type: str, service_name: str) -> None:
        pass

    def add_service(self, zeroconf: Zeroconf, service_type: str, service_name: str) -> None:
        service_info = zeroconf.get_service_info(service_type, service_name)

        if service_info is not None and service_info.server is not None:
            hostname = service_info.server.replace(".local.", "")
            ip_address = service_info.parsed_addresses()[0]

            if hostname.startswith("pixeldriver-"):
                self._devices[hostname] = ip_address
