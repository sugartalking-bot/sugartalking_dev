"""
Network discovery service for AVR receivers.

This module implements auto-discovery of receivers using mDNS/Bonjour and
HTTP probing to find compatible devices on the network.
"""

import socket
import requests
import logging
import re
from typing import List, Dict, Optional
from datetime import datetime
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf
import threading
import time

from app.models import DiscoveredReceiver, Receiver, get_session

logger = logging.getLogger(__name__)


class AVRServiceListener(ServiceListener):
    """
    Listener for mDNS service discovery.

    Detects AVR receivers advertising themselves on the network.
    """

    def __init__(self, discovery_service):
        """
        Initialize the listener.

        Args:
            discovery_service: Parent DiscoveryService instance
        """
        self.discovery_service = discovery_service
        self.zeroconf = None

    def add_service(self, zeroconf: Zeroconf, service_type: str, name: str) -> None:
        """
        Called when a new service is discovered.

        Args:
            zeroconf: Zeroconf instance
            service_type: Type of service
            name: Service name
        """
        self.zeroconf = zeroconf
        info = zeroconf.get_service_info(service_type, name)

        if info:
            logger.info(f"Discovered mDNS service: {name}")

            # Extract information
            addresses = [socket.inet_ntoa(addr) for addr in info.addresses]
            port = info.port
            server_name = info.server if hasattr(info, 'server') else None

            for address in addresses:
                self.discovery_service.add_discovered_device(
                    ip_address=address,
                    port=port,
                    hostname=server_name,
                    discovery_method='mdns'
                )

    def remove_service(self, zeroconf: Zeroconf, service_type: str, name: str) -> None:
        """Called when a service is removed."""
        logger.debug(f"Service removed: {name}")

    def update_service(self, zeroconf: Zeroconf, service_type: str, name: str) -> None:
        """Called when a service is updated."""
        logger.debug(f"Service updated: {name}")


class DiscoveryService:
    """
    Main discovery service for finding AVR receivers on the network.
    """

    def __init__(self, db_session=None):
        """
        Initialize the discovery service.

        Args:
            db_session: SQLAlchemy session (creates new if None)
        """
        self.session = db_session or get_session()
        self.zeroconf = None
        self.browser = None
        self.discovered_devices = []
        self._lock = threading.Lock()

    def start_mdns_discovery(self, duration: int = 5):
        """
        Start mDNS service discovery.

        Args:
            duration: How long to scan in seconds
        """
        try:
            logger.info(f"Starting mDNS discovery for {duration} seconds...")

            self.zeroconf = Zeroconf()
            listener = AVRServiceListener(self)

            # Common service types for AVRs and media devices
            service_types = [
                "_http._tcp.local.",
                "_device-info._tcp.local.",
                "_airplay._tcp.local.",
                "_raop._tcp.local.",
            ]

            browsers = []
            for service_type in service_types:
                browser = ServiceBrowser(self.zeroconf, service_type, listener)
                browsers.append(browser)

            # Let discovery run
            time.sleep(duration)

            # Cleanup
            self.zeroconf.close()
            logger.info(f"mDNS discovery completed")

        except Exception as e:
            logger.error(f"mDNS discovery error: {str(e)}", exc_info=True)
            if self.zeroconf:
                self.zeroconf.close()

    def scan_network_range(self, subnet: str = None, port: int = 80):
        """
        Scan a network range for HTTP-enabled receivers.

        Args:
            subnet: Subnet to scan (e.g., "192.168.1.0/24"), auto-detects if None
            port: Port to probe (default 80)
        """
        if subnet is None:
            # Check for configured subnet in environment
            import os
            subnet = os.getenv('DISCOVERY_SUBNET')
            if not subnet:
                subnet = self._get_local_subnet()

        logger.info(f"Starting HTTP probe scan on {subnet}:{port}")

        try:
            import ipaddress

            network = ipaddress.ip_network(subnet, strict=False)

            # Limit scan to reasonable subnet sizes
            if network.num_addresses > 256:
                logger.warning(f"Subnet too large ({network.num_addresses} addresses), limiting to /24")
                # Just scan the .1 to .254 range of the first /24
                base_ip = str(network.network_address)
                parts = base_ip.split('.')
                network = ipaddress.ip_network(f"{'.'.join(parts[:3])}.0/24", strict=False)

            # Scan each IP in the network
            for ip in network.hosts():
                ip_str = str(ip)
                if self._probe_http_device(ip_str, port):
                    self.add_discovered_device(
                        ip_address=ip_str,
                        port=port,
                        discovery_method='http_probe'
                    )

            logger.info(f"HTTP probe scan completed")

        except Exception as e:
            logger.error(f"Network scan error: {str(e)}", exc_info=True)

    def _get_local_subnet(self) -> str:
        """
        Auto-detect the local subnet.

        Returns:
            Subnet string (e.g., "192.168.1.0/24")
        """
        try:
            # Get local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()

            # Assume /24 subnet
            parts = local_ip.split('.')
            subnet = f"{'.'.join(parts[:3])}.0/24"
            logger.debug(f"Auto-detected subnet: {subnet}")
            return subnet

        except Exception as e:
            logger.error(f"Failed to detect local subnet: {str(e)}")
            return "192.168.1.0/24"  # Fallback

    def _probe_http_device(self, ip: str, port: int, timeout: float = 0.5) -> bool:
        """
        Probe an IP address to see if it responds to HTTP.

        Args:
            ip: IP address to probe
            port: Port to probe
            timeout: Connection timeout in seconds

        Returns:
            True if device responds to HTTP
        """
        try:
            url = f"http://{ip}:{port}/"
            response = requests.get(url, timeout=timeout, allow_redirects=False)

            # Check if response looks like an AVR
            # (This is a basic check - can be enhanced with manufacturer-specific detection)
            if response.status_code in [200, 301, 302, 401, 403]:
                logger.debug(f"HTTP device found at {ip}:{port}")
                return True

        except (requests.Timeout, requests.ConnectionError):
            pass
        except Exception as e:
            logger.debug(f"Probe error for {ip}:{port}: {str(e)}")

        return False

    def add_discovered_device(
        self,
        ip_address: str,
        port: int,
        hostname: str = None,
        mac_address: str = None,
        discovery_method: str = 'manual'
    ):
        """
        Add a discovered device to the database.

        Args:
            ip_address: Device IP address
            port: Device port
            hostname: Device hostname (optional)
            mac_address: MAC address (optional)
            discovery_method: How the device was discovered
        """
        with self._lock:
            try:
                # Check if already discovered
                existing = self.session.query(DiscoveredReceiver).filter_by(
                    ip_address=ip_address
                ).first()

                if existing:
                    # Update last seen time
                    existing.last_seen = datetime.utcnow()
                    existing.is_active = True
                    logger.debug(f"Updated existing device: {ip_address}")
                else:
                    # Try to identify the receiver model
                    receiver_id = self._identify_receiver(ip_address, port)

                    # Create new discovered receiver
                    discovered = DiscoveredReceiver(
                        receiver_id=receiver_id,
                        ip_address=ip_address,
                        port=port,
                        hostname=hostname,
                        mac_address=mac_address,
                        friendly_name=hostname or f"AVR at {ip_address}",
                        discovery_method=discovery_method,
                        last_seen=datetime.utcnow()
                    )

                    self.session.add(discovered)
                    logger.info(f"Added new discovered device: {ip_address}")

                self.session.commit()

            except Exception as e:
                logger.error(f"Error adding discovered device: {str(e)}", exc_info=True)
                self.session.rollback()

    def _identify_receiver(self, ip: str, port: int) -> Optional[int]:
        """
        Try to identify the receiver model by probing it.

        Args:
            ip: IP address
            port: Port number

        Returns:
            Receiver ID if identified, None otherwise
        """
        try:
            # Try to fetch device info page
            url = f"http://{ip}:{port}/"
            response = requests.get(url, timeout=2)

            if response.status_code == 200:
                content = response.text.lower()

                # Look for manufacturer/model indicators
                # Denon detection
                if 'denon' in content:
                    # Try to find model number
                    model_match = re.search(r'(avr-x?\d{3,4}w?)', content, re.IGNORECASE)
                    if model_match:
                        model = model_match.group(1).upper()
                        receiver = self.session.query(Receiver).filter_by(
                            manufacturer='Denon',
                            model=model
                        ).first()
                        if receiver:
                            logger.info(f"Identified {ip} as Denon {model}")
                            return receiver.id

                # Add more manufacturer detection here (Yamaha, Onkyo, etc.)

        except Exception as e:
            logger.debug(f"Could not identify receiver at {ip}: {str(e)}")

        return None

    def get_discovered_receivers(self, active_only: bool = True) -> List[Dict]:
        """
        Get list of discovered receivers.

        Args:
            active_only: Only return active receivers

        Returns:
            List of receiver dictionaries
        """
        try:
            query = self.session.query(DiscoveredReceiver)

            if active_only:
                query = query.filter_by(is_active=True)

            receivers = query.order_by(DiscoveredReceiver.last_seen.desc()).all()

            return [{
                'id': r.id,
                'ip_address': r.ip_address,
                'port': r.port,
                'hostname': r.hostname,
                'friendly_name': r.friendly_name,
                'model': r.receiver_model.model if r.receiver_model else 'Unknown',
                'manufacturer': r.receiver_model.manufacturer if r.receiver_model else 'Unknown',
                'last_seen': r.last_seen.isoformat(),
                'discovery_method': r.discovery_method
            } for r in receivers]

        except Exception as e:
            logger.error(f"Error retrieving discovered receivers: {str(e)}", exc_info=True)
            return []

    def cleanup_stale_devices(self, max_age_hours: int = 24):
        """
        Mark devices as inactive if not seen recently.

        Args:
            max_age_hours: Max age in hours before marking inactive
        """
        try:
            from datetime import timedelta

            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)

            stale = self.session.query(DiscoveredReceiver).filter(
                DiscoveredReceiver.last_seen < cutoff_time,
                DiscoveredReceiver.is_active == True
            ).all()

            for device in stale:
                device.is_active = False
                logger.info(f"Marked device {device.ip_address} as inactive")

            self.session.commit()

        except Exception as e:
            logger.error(f"Error cleaning up stale devices: {str(e)}", exc_info=True)
            self.session.rollback()
