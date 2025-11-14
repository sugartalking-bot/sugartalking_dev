"""
Receiver status service for querying receiver state.

This module handles querying receiver status including volume, power, input, etc.
"""

import requests
import logging
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ReceiverStatus:
    """
    Queries receiver status using various methods.
    """

    def __init__(self):
        """Initialize the receiver status service."""
        pass

    def get_denon_status(self, host: str, port: int = 80, timeout: int = 3) -> Optional[Dict[str, Any]]:
        """
        Get status from Denon AVR receiver.

        The Denon receivers support multiple status query methods:
        1. XML status endpoint: /goform/formMainZone_MainZoneXmlStatus.xml
        2. Direct query commands: ?MV? for volume, ?PW? for power, etc.

        Args:
            host: Receiver hostname or IP address
            port: Port number (default 80)
            timeout: Request timeout in seconds

        Returns:
            Dictionary with status fields or None on failure
        """
        try:
            # Try XML status endpoint first
            url = f"http://{host}:{port}/goform/formMainZone_MainZoneXmlStatus.xml"
            logger.info(f"Querying receiver status: {url}")

            response = requests.get(url, timeout=timeout)

            if response.status_code == 200:
                return self._parse_denon_xml_status(response.text)
            else:
                logger.error(f"Status query failed with status {response.status_code}")
                return None

        except requests.Timeout:
            logger.error(f"Timeout querying receiver at {host}:{port}")
            return None
        except requests.ConnectionError as e:
            logger.error(f"Connection error to receiver at {host}:{port}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error getting receiver status: {str(e)}", exc_info=True)
            return None

    def _parse_denon_xml_status(self, xml_text: str) -> Dict[str, Any]:
        """
        Parse Denon XML status response.

        Expected XML format:
        <item>
            <Power><value>ON</value></Power>
            <InputFuncSelect><value>SAT/CBL</value></InputFuncSelect>
            <MasterVolume><value>-40.0</value></MasterVolume>
            <Mute><value>off</value></Mute>
            ...
        </item>

        Args:
            xml_text: XML response text

        Returns:
            Dictionary with parsed status
        """
        try:
            root = ET.fromstring(xml_text)

            status = {}

            # Parse power status
            power_elem = root.find('.//Power/value')
            if power_elem is not None:
                status['power'] = power_elem.text  # ON or STANDBY

            # Parse volume (comes as -40.0, -35.5, etc.)
            volume_elem = root.find('.//MasterVolume/value')
            if volume_elem is not None:
                try:
                    # Convert to integer dB value
                    volume_str = volume_elem.text
                    if volume_str and volume_str != '--':
                        status['volume'] = int(float(volume_str))
                    else:
                        status['volume'] = -40  # Default
                except (ValueError, TypeError):
                    logger.warning(f"Could not parse volume: {volume_elem.text}")
                    status['volume'] = -40

            # Parse mute status
            mute_elem = root.find('.//Mute/value')
            if mute_elem is not None:
                status['mute'] = mute_elem.text.lower() == 'on'

            # Parse input source
            input_elem = root.find('.//InputFuncSelect/value')
            if input_elem is not None:
                status['input'] = input_elem.text

            # Parse surround mode / sound mode
            surround_elem = root.find('.//selectSurround/value')
            if surround_elem is not None:
                status['sound_mode'] = surround_elem.text

            # Connection status
            status['connection'] = 'Connected'

            logger.info(f"Parsed receiver status: {status}")
            return status

        except ET.ParseError as e:
            logger.error(f"XML parse error: {str(e)}")
            logger.debug(f"XML content: {xml_text[:500]}")
            return {}
        except Exception as e:
            logger.error(f"Error parsing status XML: {str(e)}", exc_info=True)
            return {}

    def get_status(self, receiver_model: str, host: str, port: int = 80) -> Dict[str, Any]:
        """
        Get receiver status based on model.

        Args:
            receiver_model: Model name (e.g., "AVR-X2300W")
            host: Receiver IP/hostname
            port: Port number

        Returns:
            Status dictionary
        """
        # For now, only Denon is supported
        if 'AVR' in receiver_model or 'Denon' in receiver_model:
            status = self.get_denon_status(host, port)
            if status:
                return status

        # Return default status if query fails
        logger.warning(f"Could not get status, returning defaults")
        return {
            'power': 'UNKNOWN',
            'volume': -40,
            'mute': False,
            'input': '--',
            'connection': 'Disconnected'
        }
