"""
volume_up_down.py
Functions to increase/decrease volume on the Denon AVR-X2300W receiver

This module contains volume_up() and volume_down() functions which send
HTTP requests to adjust the volume incrementally.
"""

import requests
import logging

# Configure logger for this module
logger = logging.getLogger(__name__)


def volume_up(host: str = "denon.local", port: int = 80, timeout: int = 5) -> bool:
    """
    Increase the volume by one step on the Denon AVR-X2300W receiver.

    Args:
        host (str): Hostname or IP address of the receiver. Default: "denon.local"
        port (int): Port number for HTTP API. Default: 80
        timeout (int): Request timeout in seconds. Default: 5

    Returns:
        bool: True if command was successful, False otherwise
    """
    logger.info(f"Starting volume_up function with parameters: host={host}, port={port}, timeout={timeout}")

    # Construct the API endpoint URL
    if port == 80:
        url = f"http://{host}/MainZone/index.put.asp"
    else:
        url = f"http://{host}:{port}/MainZone/index.put.asp"
    logger.debug(f"Constructed URL: {url}")

    # Define the volume up command
    params = {"cmd0": "PutMasterVolumeBtn/>"}
    logger.debug(f"Command parameters: {params}")

    try:
        logger.info("Increasing volume...")

        # Send GET request to the receiver
        response = requests.get(url, params=params, timeout=timeout)
        logger.debug(f"Response status code: {response.status_code}")

        # Check if request was successful
        if response.status_code == 200:
            logger.info("Volume increased successfully")
            return True
        else:
            logger.error(f"Failed to increase volume. Status code: {response.status_code}")
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
        logger.debug("Exiting volume_up function")


def volume_down(host: str = "denon.local", port: int = 80, timeout: int = 5) -> bool:
    """
    Decrease the volume by one step on the Denon AVR-X2300W receiver.

    Args:
        host (str): Hostname or IP address of the receiver. Default: "denon.local"
        port (int): Port number for HTTP API. Default: 80
        timeout (int): Request timeout in seconds. Default: 5

    Returns:
        bool: True if command was successful, False otherwise
    """
    logger.info(f"Starting volume_down function with parameters: host={host}, port={port}, timeout={timeout}")

    # Construct the API endpoint URL
    if port == 80:
        url = f"http://{host}/MainZone/index.put.asp"
    else:
        url = f"http://{host}:{port}/MainZone/index.put.asp"
    logger.debug(f"Constructed URL: {url}")

    # Define the volume down command
    params = {"cmd0": "PutMasterVolumeBtn/<"}
    logger.debug(f"Command parameters: {params}")

    try:
        logger.info("Decreasing volume...")

        # Send GET request to the receiver
        response = requests.get(url, params=params, timeout=timeout)
        logger.debug(f"Response status code: {response.status_code}")

        # Check if request was successful
        if response.status_code == 200:
            logger.info("Volume decreased successfully")
            return True
        else:
            logger.error(f"Failed to decrease volume. Status code: {response.status_code}")
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
        logger.debug("Exiting volume_down function")