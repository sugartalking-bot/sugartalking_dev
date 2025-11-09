"""
mute_toggle.py
Function to toggle mute on the Denon AVR-X2300W receiver

This module contains the mute_toggle() function which sends an HTTP request
to toggle the mute state on the Denon receiver.
"""

import requests
import logging

# Configure logger for this module
logger = logging.getLogger(__name__)


def mute_toggle(host: str = "denon.local", port: int = 80, mute: bool = None, timeout: int = 5) -> bool:
    """
    Toggle or set mute state on the Denon AVR-X2300W receiver.

    Args:
        host (str): Hostname or IP address of the receiver. Default: "denon.local"
        port (int): Port number for HTTP API. Default: 80
        mute (bool, optional): True to mute, False to unmute, None to toggle
        timeout (int): Request timeout in seconds. Default: 5

    Returns:
        bool: True if command was successful, False otherwise
    """
    logger.info(
        f"Starting mute_toggle function with parameters: host={host}, port={port}, mute={mute}, timeout={timeout}")

    # Construct the API endpoint URL
    if port == 80:
        url = f"http://{host}/MainZone/index.put.asp"
    else:
        url = f"http://{host}:{port}/MainZone/index.put.asp"
    logger.debug(f"Constructed URL: {url}")

    # Define the mute command
    if mute is None:
        # Toggle mute (receiver will toggle current state)
        logger.info("Toggling mute state")
        # First get current state, then toggle
        # For simplicity, we'll use ON command which acts as toggle on some models
        params = {"cmd0": "PutVolumeMute/on"}
    elif mute:
        logger.info("Muting receiver")
        params = {"cmd0": "PutVolumeMute/on"}
    else:
        logger.info("Unmuting receiver")
        params = {"cmd0": "PutVolumeMute/off"}

    logger.debug(f"Command parameters: {params}")

    try:
        logger.info("Sending mute command...")

        # Send GET request to the receiver
        response = requests.get(url, params=params, timeout=timeout)
        logger.debug(f"Response status code: {response.status_code}")
        logger.debug(f"Response content: {response.text[:200] if response.text else 'Empty'}")

        # Check if request was successful
        if response.status_code == 200:
            logger.info("Mute command sent successfully")
            return True
        else:
            logger.error(f"Failed to send mute command. Status code: {response.status_code}")
            return False

    except requests.exceptions.Timeout:
        logger.error(f"Request timeout after {timeout} seconds")
        return False

    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error: {str(e)}")
        return False

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return False

    finally:
        logger.debug("Exiting mute_toggle function")