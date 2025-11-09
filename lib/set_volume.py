"""
set_volume.py
Function to set volume on the Denon AVR-X2300W receiver via HTTP API

This module contains the set_volume() function which sends an HTTP request
to set the volume level on the Denon receiver.
"""

import requests
import logging


# Configure logger for this module
logger = logging.getLogger(__name__)


def set_volume(host: str = "denon.local", port: int = 80, volume: float = -40.0, timeout: int = 5) -> bool:
    """
    Set the volume level on the Denon AVR-X2300W receiver.

    The Denon receiver uses a scale from -80.0 to +18.0 dB

    Args:
        host (str): Hostname or IP address of the receiver. Default: "denon.local"
        port (int): Port number for HTTP API. Default: 80
        volume (float): Volume level in dB (-80.0 to +18.0). Default: -40.0
        timeout (int): Request timeout in seconds. Default: 5

    Returns:
        bool: True if command was successful, False otherwise
    """
    logger.info(f"Starting set_volume function with parameters: host={host}, port={port}, volume={volume}, timeout={timeout}")

    # Validate volume range
    if volume < -80:
        logger.warning(f"Volume {volume} too low, setting to -80")
        volume = -80
    elif volume > 18:
        logger.warning(f"Volume {volume} too high, setting to 18")
        volume = 18

    # Format volume for Denon API (requires specific format)
    if volume < 0:
        volume_str = f"{volume:05.1f}"  # Format: -XX.X (e.g., -40.0)
    else:
        volume_str = f"{volume:04.1f}"   # Format: XX.X (e.g., 10.0)

    logger.debug(f"Formatted volume string: {volume_str}")

    # Construct the API endpoint URL
    if port == 80:
        url = f"http://{host}/MainZone/index.put.asp"
    else:
        url = f"http://{host}:{port}/MainZone/index.put.asp"
    logger.debug(f"Constructed URL: {url}")

    # Define the volume command
    params = {"cmd0": f"PutMasterVolumeSet/{volume_str}"}
    logger.debug(f"Command parameters: {params}")

    try:
        logger.info(f"Setting volume to {volume} dB...")

        # Send GET request to the receiver
        response = requests.get(url, params=params, timeout=timeout)
        logger.debug(f"Response status code: {response.status_code}")
        logger.debug(f"Response headers: {response.headers}")
        logger.debug(f"Response content: {response.text[:200] if response.text else 'Empty'}")

        # Check if request was successful
        if response.status_code == 200:
            logger.info(f"Volume set to {volume} dB successfully")
            logger.debug(f"Full response: {response.text}")
            return True
        else:
            logger.error(f"Failed to set volume. Status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False

    except requests.exceptions.Timeout:
        logger.error(f"Request timeout after {timeout} seconds - receiver may be unreachable")
        return False

    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error - could not reach receiver at {host}:{port}")
        logger.error(f"Error details: {str(e)}")
        return False

    except requests.exceptions.RequestException as e:
        logger.error(f"Unexpected request error occurred: {str(e)}")
        return False

    except Exception as e:
        logger.error(f"Unexpected error in set_volume function: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        return False

    finally:
        logger.debug("Exiting set_volume function")