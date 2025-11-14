"""
API routes for receiver control.

This module provides REST API endpoints for controlling AVR receivers.
"""

from flask import Blueprint, jsonify, request
import logging
import os

from app.services import CommandExecutor, DiscoveryService, ErrorReporter, ReceiverStatus
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

        logger.info(f"Getting status for {receiver_model} at {receiver_ip}")

        # Query actual receiver status
        status_service = ReceiverStatus()
        status = status_service.get_status(receiver_model, receiver_ip)

        return jsonify({
            'success': True,
            'status': status
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
        logger.info(f">>> API CALL: POST /power/{action}")
        if action not in ['on', 'off']:
            return jsonify({
                'success': False,
                'error': 'Invalid action. Use "on" or "off"'
            }), 400

        data = request.get_json(silent=True) or {}
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
        data = request.get_json(silent=True) or {}
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


@bp.route('/volume/<action>', methods=['POST'])
def control_volume(action):
    """
    Control receiver volume.

    Args:
        action: 'up', 'down', 'mute', or 'set'

    JSON body (for 'set' action):
        value: Volume level in dB
        receiver_ip: IP address (optional, defaults to env)
    """
    try:
        logger.info(f">>> API CALL: POST /volume/{action}")
        receiver_ip = os.getenv('RECEIVER_IP', '192.168.1.182')
        receiver_model = 'AVR-X2300W'

        data = request.get_json(silent=True) or {}
        logger.info(f"Request body: {data}")
        receiver_ip = data.get('receiver_ip', receiver_ip)

        if action == 'set':
            volume_value = data.get('value')
            if volume_value is None:
                return jsonify({
                    'success': False,
                    'error': 'value parameter is required for set action'
                }), 400

            # Convert dB (-80 to +18) to Denon format (0-98)
            # Formula: denon_value = dB + 80
            try:
                volume_db = int(volume_value)
                denon_value = volume_db + 80

                # Validate range
                if denon_value < 0 or denon_value > 98:
                    return jsonify({
                        'success': False,
                        'error': f'Volume {volume_db}dB is out of range (-80 to +18)'
                    }), 400

                # Format as 2-digit string (e.g., 40 -> "40", 5 -> "05")
                denon_level = f"{denon_value:02d}"

                logger.info(f"Setting volume to {volume_db}dB (Denon format: {denon_level}) for {receiver_ip}")
            except (ValueError, TypeError):
                return jsonify({
                    'success': False,
                    'error': 'Invalid volume value'
                }), 400

            executor = CommandExecutor()
            success = executor.execute_command(
                receiver_model=receiver_model,
                action_name='volume_set',
                host=receiver_ip,
                parameters={'level': denon_level}
            )
        elif action in ['up', 'down']:
            logger.info(f"Volume {action} for {receiver_ip}")
            executor = CommandExecutor()
            success = executor.execute_command(
                receiver_model=receiver_model,
                action_name=f'volume_{action}',
                host=receiver_ip
            )
        elif action == 'mute':
            # Get current mute state to toggle properly
            mute_state = data.get('mute_state', 'unknown')

            # Determine which command to use based on current state
            if mute_state == 'muted' or mute_state == True:
                action_cmd = 'mute_off'  # Unmute
                logger.info(f"Unmuting {receiver_ip}")
            else:
                action_cmd = 'mute_on'  # Mute
                logger.info(f"Muting {receiver_ip}")

            executor = CommandExecutor()
            success = executor.execute_command(
                receiver_model=receiver_model,
                action_name=action_cmd,
                host=receiver_ip
            )
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid action. Use "up", "down", "mute", or "set"'
            }), 400

        if success:
            response_data = {
                'success': True,
                'message': f'Volume {action} successful'
            }

            # Include volume value in response for 'set' action
            if action == 'set':
                response_data['volume'] = volume_db

            return jsonify(response_data)
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to {action} volume'
            }), 500

    except Exception as e:
        logger.error(f"Error in control_volume: {str(e)}", exc_info=True)

        error_reporter = ErrorReporter()
        error_reporter.handle_error(e, context={'endpoint': '/api/volume', 'action': action})

        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/input/<input_source>', methods=['POST'])
def set_input(input_source):
    """
    Set receiver input source.

    Args:
        input_source: Input source name (e.g., 'TV', 'CBL', 'DVD', 'BD', 'GAME', etc.)
    """
    try:
        logger.info(f">>> API CALL: POST /input/{input_source}")
        receiver_ip = os.getenv('RECEIVER_IP', '192.168.1.182')
        receiver_model = 'AVR-X2300W'

        logger.info(f"Setting input to {input_source} for {receiver_ip}")

        executor = CommandExecutor()
        success = executor.execute_command(
            receiver_model=receiver_model,
            action_name='change_input',
            host=receiver_ip,
            parameters={'input_source': input_source}
        )

        if success:
            return jsonify({
                'success': True,
                'message': f'Input changed to {input_source}'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to change input to {input_source}'
            }), 500

    except Exception as e:
        logger.error(f"Error in set_input: {str(e)}", exc_info=True)

        error_reporter = ErrorReporter()
        error_reporter.handle_error(e, context={'endpoint': '/api/input', 'input': input_source})

        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/sound-mode/<mode>', methods=['POST'])
def set_sound_mode(mode):
    """
    Set receiver sound mode.

    Args:
        mode: Sound mode name (e.g., 'STEREO', 'MOVIE', 'MUSIC', 'GAME', 'AUTO', 'DIRECT')
    """
    try:
        logger.info(f">>> API CALL: POST /sound-mode/{mode}")
        receiver_ip = os.getenv('RECEIVER_IP', '192.168.1.182')
        receiver_model = 'AVR-X2300W'

        logger.info(f"Setting sound mode to {mode} for {receiver_ip}")

        executor = CommandExecutor()
        success = executor.execute_command(
            receiver_model=receiver_model,
            action_name='set_sound_mode',
            host=receiver_ip,
            parameters={'mode': mode}
        )

        if success:
            return jsonify({
                'success': True,
                'message': f'Sound mode changed to {mode}'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to change sound mode to {mode}'
            }), 500

    except Exception as e:
        logger.error(f"Error in set_sound_mode: {str(e)}", exc_info=True)

        error_reporter = ErrorReporter()
        error_reporter.handle_error(e, context={'endpoint': '/api/sound-mode', 'mode': mode})

        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/settings/<setting>/toggle', methods=['POST'])
def toggle_setting(setting):
    """
    Toggle a receiver setting.

    Args:
        setting: Setting name (e.g., 'dynamicEq', 'dynamicVol', 'ecoMode', 'sleepTimer')
    """
    try:
        logger.info(f">>> API CALL: POST /settings/{setting}/toggle")
        receiver_ip = os.getenv('RECEIVER_IP', '192.168.1.182')
        receiver_model = 'AVR-X2300W'

        logger.info(f"Toggling {setting} for {receiver_ip}")

        executor = CommandExecutor()
        success = executor.execute_command(
            receiver_model=receiver_model,
            action_name=f'toggle_{setting}',
            host=receiver_ip
        )

        if success:
            return jsonify({
                'success': True,
                'message': f'{setting} toggled successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to toggle {setting}'
            }), 500

    except Exception as e:
        logger.error(f"Error in toggle_setting: {str(e)}", exc_info=True)

        error_reporter = ErrorReporter()
        error_reporter.handle_error(e, context={'endpoint': '/api/settings/toggle', 'setting': setting})

        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/config', methods=['GET'])
def get_config():
    """Get current API configuration."""
    return jsonify({
        'api_version': '2.0.0',
        'receiver_host': os.getenv('RECEIVER_IP', '192.168.1.182'),
        'features': {
            'power': True,
            'volume': True,
            'input_selection': True,
            'sound_modes': True,
            'zone_control': False,
            'discovery': True,
            'multi_receiver': True,
            'auto_error_reporting': os.getenv('AUTO_REPORT_ERRORS', 'true').lower() == 'true'
        }
    })
