"""
API routes for receiver control.

This module provides REST API endpoints for controlling AVR receivers.
"""

from flask import Blueprint, jsonify, request
import logging
import os

from app.services import CommandExecutor, DiscoveryService, ErrorReporter
from app.models import get_session

logger = logging.getLogger(__name__)

bp = Blueprint('api', __name__, url_prefix='/api')


@bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Kubernetes probes."""
    return jsonify({
        'status': 'healthy',
        'version': '2.0.0'
    })


@bp.route('/status', methods=['GET'])
def get_status():
    """
    Get current receiver status.

    Query params:
        receiver_ip: IP address of the receiver (required)
        receiver_model: Model of the receiver (default: AVR-X2300W)
    """
    try:
        receiver_ip = request.args.get('receiver_ip')
        receiver_model = request.args.get('receiver_model', 'AVR-X2300W')

        if not receiver_ip:
            return jsonify({
                'success': False,
                'error': 'receiver_ip parameter is required'
            }), 400

        # For now, return a basic status
        # In the future, this would query the actual receiver
        return jsonify({
            'success': True,
            'status': {
                'power': 'UNKNOWN',
                'volume': -40,
                'input': 'UNKNOWN',
                'mute': False,
                'connection': 'Connected'
            }
        })

    except Exception as e:
        logger.error(f"Error in get_status: {str(e)}", exc_info=True)

        # Report error if it's a bug
        error_reporter = ErrorReporter()
        error_reporter.handle_error(e, context={'endpoint': '/api/status'})

        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@bp.route('/power/<action>', methods=['POST'])
def control_power(action):
    """
    Control receiver power.

    Args:
        action: 'on' or 'off'

    JSON body:
        receiver_ip: IP address of the receiver (required)
        receiver_model: Model of the receiver (default: AVR-X2300W)
        port: Port number (optional)
    """
    try:
        if action not in ['on', 'off']:
            return jsonify({
                'success': False,
                'error': 'Invalid action. Use "on" or "off"'
            }), 400

        data = request.get_json() or {}
        receiver_ip = data.get('receiver_ip')
        receiver_model = data.get('receiver_model', 'AVR-X2300W')
        port = data.get('port')

        if not receiver_ip:
            return jsonify({
                'success': False,
                'error': 'receiver_ip is required in request body'
            }), 400

        logger.info(f"Power {action} request for {receiver_model} at {receiver_ip}")

        # Execute command using database-driven executor
        executor = CommandExecutor()
        success = executor.execute_command(
            receiver_model=receiver_model,
            action_name=f'power_{action}',
            host=receiver_ip,
            port=port,
            timeout=5
        )

        if success:
            return jsonify({
                'success': True,
                'message': f'Receiver powered {action} successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to power {action} receiver'
            }), 500

    except Exception as e:
        logger.error(f"Error in control_power: {str(e)}", exc_info=True)

        # Report error
        error_reporter = ErrorReporter()
        error_reporter.handle_error(
            e,
            context={'endpoint': '/api/power', 'action': action},
            request_path=request.path
        )

        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/discover', methods=['POST'])
def discover_receivers():
    """
    Discover receivers on the network.

    JSON body (optional):
        method: 'mdns', 'http', or 'both' (default: 'both')
        duration: Discovery duration in seconds (default: 5)
    """
    try:
        data = request.get_json() or {}
        method = data.get('method', 'both')
        duration = data.get('duration', 5)

        logger.info(f"Starting receiver discovery: method={method}, duration={duration}s")

        discovery = DiscoveryService()

        if method in ['mdns', 'both']:
            discovery.start_mdns_discovery(duration=duration)

        if method in ['http', 'both']:
            discovery.scan_network_range()

        # Get discovered receivers
        receivers = discovery.get_discovered_receivers()

        return jsonify({
            'success': True,
            'receivers': receivers,
            'count': len(receivers)
        })

    except Exception as e:
        logger.error(f"Error in discover_receivers: {str(e)}", exc_info=True)

        error_reporter = ErrorReporter()
        error_reporter.handle_error(e, context={'endpoint': '/api/discover'})

        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/receivers', methods=['GET'])
def list_receivers():
    """Get list of discovered receivers."""
    try:
        discovery = DiscoveryService()
        receivers = discovery.get_discovered_receivers()

        return jsonify({
            'success': True,
            'receivers': receivers
        })

    except Exception as e:
        logger.error(f"Error in list_receivers: {str(e)}", exc_info=True)

        error_reporter = ErrorReporter()
        error_reporter.handle_error(e, context={'endpoint': '/api/receivers'})

        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/commands/<receiver_model>', methods=['GET'])
def get_commands(receiver_model):
    """
    Get available commands for a receiver model.

    Args:
        receiver_model: Model name (e.g., "AVR-X2300W")
    """
    try:
        executor = CommandExecutor()
        commands = executor.get_available_commands(receiver_model)

        return jsonify({
            'success': True,
            'model': receiver_model,
            'commands': commands
        })

    except Exception as e:
        logger.error(f"Error in get_commands: {str(e)}", exc_info=True)

        error_reporter = ErrorReporter()
        error_reporter.handle_error(e, context={'endpoint': '/api/commands', 'model': receiver_model})

        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/config', methods=['GET'])
def get_config():
    """Get current API configuration."""
    return jsonify({
        'api_version': '2.0.0',
        'features': {
            'power': True,
            'discovery': True,
            'multi_receiver': True,
            'auto_error_reporting': os.getenv('AUTO_REPORT_ERRORS', 'true').lower() == 'true'
        }
    })
