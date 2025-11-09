"""
Command execution service for AVR receivers.

This module handles executing commands against receivers using database-stored
command templates, making it easy to support multiple receiver models.
"""

import requests
import logging
from typing import Dict, Any, Optional
from app.models import Receiver, Command, CommandParameter, DiscoveredReceiver, get_session

logger = logging.getLogger(__name__)


class CommandExecutor:
    """
    Executes commands against AVR receivers using database-driven templates.
    """

    def __init__(self, db_session=None):
        """
        Initialize the command executor.

        Args:
            db_session: SQLAlchemy session (creates new if None)
        """
        self.session = db_session or get_session()

    def execute_command(
        self,
        receiver_model: str,
        action_name: str,
        host: str,
        port: int = None,
        parameters: Dict[str, Any] = None,
        timeout: int = 5
    ) -> bool:
        """
        Execute a command against a receiver.

        Args:
            receiver_model: Receiver model name (e.g., "AVR-X2300W")
            action_name: Command action name (e.g., "power_on")
            host: Receiver hostname or IP address
            port: Port number (uses receiver default if None)
            parameters: Command parameters as key-value pairs
            timeout: Request timeout in seconds

        Returns:
            True if command succeeded, False otherwise
        """
        parameters = parameters or {}

        try:
            # Find the receiver model
            receiver = self.session.query(Receiver).filter_by(model=receiver_model).first()
            if not receiver:
                logger.error(f"Receiver model '{receiver_model}' not found in database")
                return False

            # Find the command
            command = self.session.query(Command).filter_by(
                receiver_id=receiver.id,
                action_name=action_name
            ).first()

            if not command:
                logger.error(f"Command '{action_name}' not found for {receiver_model}")
                return False

            # Use receiver default port if not specified
            if port is None:
                port = receiver.default_port

            # Build the command URL
            url = self._build_url(receiver.protocol, host, port, command.endpoint, command.command_template, parameters)

            logger.info(f"Executing {action_name} on {receiver_model} at {host}:{port}")
            logger.debug(f"URL: {url}")

            # Execute the HTTP request
            response = self._execute_http_request(
                method=command.http_method,
                url=url,
                timeout=timeout
            )

            if response and response.status_code == 200:
                logger.info(f"Command {action_name} executed successfully")
                return True
            else:
                status = response.status_code if response else "No response"
                logger.error(f"Command failed with status: {status}")
                return False

        except Exception as e:
            logger.error(f"Error executing command: {str(e)}", exc_info=True)
            return False

    def _build_url(
        self,
        protocol: str,
        host: str,
        port: int,
        endpoint: str,
        command_template: str,
        parameters: Dict[str, Any]
    ) -> str:
        """
        Build the full command URL with parameters.

        Args:
            protocol: Protocol (http, https)
            host: Hostname or IP
            port: Port number
            endpoint: API endpoint path
            command_template: Command template with placeholders
            parameters: Parameter values

        Returns:
            Full URL string
        """
        # Replace placeholders in command template
        command_string = command_template
        for key, value in parameters.items():
            placeholder = f"{{{key}}}"
            command_string = command_string.replace(placeholder, str(value))

        # Build full URL
        url = f"{protocol}://{host}:{port}{endpoint}{command_string}"
        return url

    def _execute_http_request(
        self,
        method: str,
        url: str,
        timeout: int,
        headers: Dict[str, str] = None,
        body: Any = None
    ) -> Optional[requests.Response]:
        """
        Execute an HTTP request.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            url: Full URL
            timeout: Timeout in seconds
            headers: Optional HTTP headers
            body: Optional request body

        Returns:
            Response object or None on failure
        """
        try:
            method = method.upper()
            if method == 'GET':
                response = requests.get(url, timeout=timeout, headers=headers)
            elif method == 'POST':
                response = requests.post(url, timeout=timeout, headers=headers, data=body)
            elif method == 'PUT':
                response = requests.put(url, timeout=timeout, headers=headers, data=body)
            elif method == 'DELETE':
                response = requests.delete(url, timeout=timeout, headers=headers)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None

            return response

        except requests.Timeout:
            logger.error(f"Request timeout after {timeout} seconds")
            return None
        except requests.ConnectionError as e:
            logger.error(f"Connection error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"HTTP request error: {str(e)}", exc_info=True)
            return None

    def get_available_commands(self, receiver_model: str) -> list:
        """
        Get all available commands for a receiver model.

        Args:
            receiver_model: Receiver model name

        Returns:
            List of command dictionaries
        """
        try:
            receiver = self.session.query(Receiver).filter_by(model=receiver_model).first()
            if not receiver:
                return []

            commands = self.session.query(Command).filter_by(receiver_id=receiver.id).all()

            return [{
                'action_type': cmd.action_type,
                'action_name': cmd.action_name,
                'description': cmd.description,
                'parameters': [
                    {
                        'name': param.param_name,
                        'type': param.param_type,
                        'required': param.required,
                        'valid_values': param.valid_values
                    }
                    for param in cmd.parameters
                ]
            } for cmd in commands]

        except Exception as e:
            logger.error(f"Error retrieving commands: {str(e)}", exc_info=True)
            return []
