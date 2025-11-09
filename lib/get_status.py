"""
get_status.py
Function to get current status from the Denon AVR-X2300W receiver

This module contains the get_status() function which retrieves the current
status of the receiver including power, volume, input, and other settings.
"""

import requests
import xml.etree.ElementTree as ET
import logging
from typing import Dict, Any

# Configure logger for this module
logger = logging.getLogger(__name__)


def get_status(host: str = "denon.local", port: int = 80, timeout: int = 5) -> Dict[str, Any]:
    """
    Get the current status of the Denon AVR-X2300W receiver.

    Args:
        host (str): Hostname or IP address of the receiver. Default: "denon.local"
        port (int): Port number for HTTP API. Default: 80
        timeout (int): Request timeout in seconds. Default: 5

    Returns:
        dict: Status dictionary containing:
            - power (str): 'ON' or 'OFF'
            - volume (float): Current volume in dB
            - mute (bool): Mute status
            - input (str): Current input source
            - surround_mode (str): Current surround mode
            - success (bool): True if status was retrieved successfully
    """
    logger.info(f"Starting get_status function with parameters: host={host}, port={port}, timeout={timeout}")

    # Default status
    status = {
        'success': False,
        'power': 'UNKNOWN',
        'volume': -40,
        'mute': False,
        'input': '--',
        'surround_mode': '--'
    }

    # Construct the API endpoint URL for status
    if port == 80:
        url = f"http://{host}/goform/formMainZone_MainZoneXmlStatusLite.xml"
    else:
        url = f"http://{host}:{port}/goform/formMainZone_MainZoneXmlStatusLite.xml"
    logger.debug(f"Constructed URL: {url}")

    try:
        logger.info("Requesting receiver status...")

        # Send GET request to the receiver
        response = requests.get(url, timeout=timeout)
        logger.debug(f"Response status code: {response.status_code}")
        logger.debug(f"Response headers: {response.headers}")

        # Check if request was successful
        if response.status_code == 200:
            logger.debug(f"Response content: {response.text[:500] if response.text else 'Empty'}")

            # Parse XML response
            try:
                root = ET.fromstring(response.text)

                # Extract power status
                power_elem = root.find('.//Power/value')
                if power_elem is not None:
                    status['power'] = power_elem.text
                    logger.debug(f"Power: {status['power']}")

                # Extract volume
                volume_elem = root.find('.//MasterVolume/value')
                if volume_elem is not None:
                    try:
                        # Volume comes as a string like "-40.0" or "--"
                        volume_str = volume_elem.text
                        if volume_str and volume_str != '--':
                            status['volume'] = float(volume_str)
                            logger.debug(f"Volume: {status['volume']} dB")
                    except (ValueError, TypeError):
                        logger.warning(f"Could not parse volume: {volume_elem.text}")

                # Extract mute status
                mute_elem = root.find('.//Mute/value')
                if mute_elem is not None:
                    status['mute'] = mute_elem.text == 'on'
                    logger.debug(f"Mute: {status['mute']}")

                # Extract input source
                input_elem = root.find('.//InputFuncSelect/value')
                if input_elem is not None:
                    status['input'] = input_elem.text
                    logger.debug(f"Input: {status['input']}")

                # Extract surround mode
                surround_elem = root.find('.//selectSurround/value')
                if surround_elem is not None:
                    status['surround_mode'] = surround_elem.text
                    logger.debug(f"Surround Mode: {status['surround_mode']}")

                status['success'] = True
                logger.info("Status retrieved successfully")

            except ET.ParseError as e:
                logger.error(f"Failed to parse XML response: {str(e)}")
                logger.debug(f"Raw response: {response.text}")
                status['success'] = False

        else:
            logger.error(f"Failed to get status. Status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            status['success'] = False

    except requests.exceptions.Timeout:
        logger.error(f"Request timeout after {timeout} seconds - receiver may be unreachable")
        status['success'] = False

    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error - could not reach receiver at {host}:{port}")
        logger.error(f"Error details: {str(e)}")
        status['success'] = False

    except Exception as e:
        logger.error(f"Unexpected error in get_status function: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        status['success'] = False

    finally:
        logger.debug(f"Final status: {status}")
        logger.debug("Exiting get_status function")

    return status