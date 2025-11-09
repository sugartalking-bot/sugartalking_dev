"""
change_input.py
Function to change input source on the Denon AVR-X2300W receiver

This module contains the change_input() function which sends an HTTP request
to switch the input source on the Denon receiver.
"""

import requests
import logging

# Configure logger for this module
logger = logging.getLogger(__name__)

# Input source mapping for Denon AVR-X2300W
INPUT_MAPPING = {
    'TV': 'TV',
    'CBL': 'SAT/CBL',
    'SAT/CBL': 'SAT/CBL',
    'DVD': 'DVD',
    'BD': 'BD',
    'GAME': 'GAME',
    'MPLAY': 'MPLAY',
    'TUNER': 'TUNER',
    'AUX1': 'AUX1',
    'AUX2': 'AUX2',
    'NET': 'NET',
    'PANDORA': 'PANDORA',
    'SIRIUSXM': 'SIRIUSXM',
    'SPOTIFY': 'SPOTIFY',
    'USB': 'USB/IPOD',
    'BT': 'BT'
}


def change_input(host: str = "denon.local", port: int = 80, input_source: str = "TV", timeout: int = 5) -> bool:
    """
    Change the input source on the Denon AVR-X2300W receiver.

    Args:
        host (str): Hostname or IP address of the receiver. Default: "denon.local"
        port (int): Port number for HTTP API. Default: 80
        input_source (str): Input source name (TV, CBL, DVD, BD, GAME, etc.). Default: "TV"
        timeout (int): Request timeout in seconds. Default: 5

    Returns:
        bool: True if command was successful, False otherwise
    """
    logger.info(
        f"Starting change_input function with parameters: host={host}, port={port}, input={input_source}, timeout={timeout}")

    # Map the input source to Denon command
    input_source_upper = input_source.upper()
    if input_source_upper in INPUT_MAPPING:
        denon_input = INPUT_MAPPING[input_source_upper]
        logger.debug(f"Mapped input '{input_source}' to Denon command '{denon_input}'")
    else:
        logger.warning(f"Unknown input source: {input_source}, using as-is")
        denon_input = input_source_upper

    # Construct the API endpoint URL
    if port == 80:
        url = f"http://{host}/MainZone/index.put.asp"
    else:
        url = f"http://{host}:{port}/MainZone/index.put.asp"
    logger.debug(f"Constructed URL: {url}")

    # Define the input change command
    params = {"cmd0": f"PutZone_InputFunction/{denon_input}"}
    logger.debug(f"Command parameters: {params}")

    try:
        logger.info(f"Changing input to {input_source} ({denon_input})...")

        # Send GET request to the receiver
        response = requests.get(url, params=params, timeout=timeout)
        logger.debug(f"Response status code: {response.status_code}")
        logger.debug(f"Response headers: {response.headers}")
        logger.debug(f"Response content: {response.text[:200] if response.text else 'Empty'}")

        # Check if request was successful
        if response.status_code == 200:
            logger.info(f"Input changed to {input_source} successfully")
            logger.debug(f"Full response: {response.text}")
            return True
        else:
            logger.error(f"Failed to change input. Status code: {response.status_code}")
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
        logger.error(f"Unexpected error in change_input function: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        return False

    finally:
        logger.debug("Exiting change_input function")