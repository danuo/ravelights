from loguru import logger
from ravelights.core.custom_typing import DiscoveryUpdateCallback
from ravelights.interface.discovery import connectivity_check
from ravelights.interface.discovery.pixeldriver_service_listener import PixeldriverServiceListener
from zeroconf import ServiceBrowser, Zeroconf

_zeroconf: Zeroconf | None = None
_service_browser: ServiceBrowser | None = None
_service_listener = PixeldriverServiceListener()


def register_callback(hostname: str, on_discovery_update: DiscoveryUpdateCallback) -> None:
    """
    Registers a callback function to be called when a discovery update occurs for the specified hostname.

    Note: All callbacks must be registered before the discovery service is started to avoid race conditions.

    Args:
        hostname (str): The hostname for which to register the callback.
        on_discovery_update (DiscoveryUpdateCallback): The callback function to be called on discovery updates
        (add, update, remove).
        The first argument is the hostname for which the callback was registered. The second argument is the new IP address
        for the host or None, if the host is not available anymore
    """

    global _zeroconf, _service_browser
    assert _service_browser is None and _zeroconf is None, "Callbacks must be registered before discovery is started"

    _service_listener.register_callback(hostname, on_discovery_update)


def start() -> None:
    """Starts the discovery of pixeldrivers on the local network using mDNS.

    Before starting the discovery service, callbacks can be registered using register_callback() to
    get notified on discovery updates
    """

    global _zeroconf, _service_browser

    if not connectivity_check.is_connected_to_network():
        raise RuntimeError("Host must be connected to network before discovery service can be started")

    if _zeroconf is not None and _service_browser is not None:
        logger.warning("Discovery service already running. Stopping first before starting again...")
        stop()

    _zeroconf = Zeroconf()
    _service_browser = ServiceBrowser(
        zc=_zeroconf, type_=["_artnet._udp.local.", "_http._tcp.local."], listener=_service_listener
    )
    logger.info("Started pixeldriver discovery service")


def stop() -> None:
    """Stops the discovery of pixeldrivers on the local network using mDNS"""

    global _zeroconf, _service_browser
    assert _service_browser is not None and _zeroconf is not None, "Discovery must be running"

    _service_browser.cancel()
    _zeroconf.close()

    _service_browser = None
    _zeroconf = None

    logger.info("Stopped pixeldriver discovery service")
