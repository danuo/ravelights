import socket
import time

from loguru import logger


def is_connected_to_network() -> bool:
    s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    s.settimeout(0)

    try:
        s.connect(("10.254.254.254", 1))  # Any IP address works
        return True
    except socket.error:
        return False
    finally:
        s.close()


def wait_until_connected_to_network() -> None:
    logger.info("Waiting until connected to network...")

    while not is_connected_to_network():
        time.sleep(5)

    logger.info("Successfully connected to network")
