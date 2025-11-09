"""
Admin routes for database management.

This module provides a simple web interface for managing receiver
models, commands, and parameters in the database.
"""

from flask import Blueprint, jsonify, request, render_template_string
import logging

from app.models import Receiver, Command, CommandParameter, DiscoveredReceiver, ErrorLog, get_session
from app.services import ErrorReporter

logger = logging.getLogger(__name__)

bp = Blueprint('admin', __name__, url_prefix='/admin')


# Simple admin page HTML template
ADMIN_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sugartalking Admin</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #1a1a2e; color: #eee; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: #00d4ff; margin-bottom: 30px; }
        h2 { color: #ff6b6b; margin: 30px 0 15px 0; border-bottom: 2px solid #ff6b6b; padding-bottom: 10px; }
        .card { background: #16213e; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #0f3460; }
        th { background: #0f3460; color: #00d4ff; font-weight: 600; }
        tr:hover { background: #1a2940; }
        .stat { display: inline-block; margin: 10px 20px 10px 0; }
        .stat-value { font-size: 24px; color: #00d4ff; font-weight: bold; }
        .stat-label { font-size: 14px; color: #999; }
        button { background: #00d4ff; color: #000; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-weight: 600; }
        button:hover { background: #00a8cc; }
        .error { color: #ff6b6b; }
        .success { color: #51cf66; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎛️ Sugartalking Admin Panel</h1>

        <div class="card">
            <h2>📊 Statistics</h2>
            <div id="stats">Loading...</div>
        </div>

        <div class="card">
            <h2>📡 Receiver Models</h2>
            <div id="receivers">Loading...</div>
        </div>

        <div class="card">
            <h2>🔍 Discovered Devices</h2>
            <button onclick="discover()">Scan Network</button>
            <div id="discovered">Loading...</div>
        </div>

        <div class="card">
            <h2>⚠️ Error Logs</h2>
            <div id="errors">Loading...</div>
        </div>
    </div>

    <script>
        async function loadData() {
            try {
                const [stats, receivers, discovered, errors] = await Promise.all([
                    fetch('/admin/stats').then(r => r.json()),
                    fetch('/admin/receivers').then(r => r.json()),
                    fetch('/admin/discovered').then(r => r.json()),
                    fetch('/admin/errors').then(r => r.json())
                ]);

                // Display stats
                document.getElementById('stats').innerHTML = `
                    <div class="stat">
                        <div class="stat-value">${stats.receiver_models || 0}</div>
                        <div class="stat-label">Receiver Models</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">${stats.total_commands || 0}</div>
                        <div class="stat-label">Total Commands</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">${stats.discovered_devices || 0}</div>
                        <div class="stat-label">Discovered Devices</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">${stats.total_errors || 0}</div>
                        <div class="stat-label">Total Errors</div>
                    </div>
                `;

                // Display receivers
                if (receivers.length > 0) {
                    document.getElementById('receivers').innerHTML = `
                        <table>
                            <tr>
                                <th>Manufacturer</th>
                                <th>Model</th>
                                <th>Protocol</th>
                                <th>Commands</th>
                            </tr>
                            ${receivers.map(r => `
                                <tr>
                                    <td>${r.manufacturer}</td>
                                    <td>${r.model}</td>
                                    <td>${r.protocol}</td>
                                    <td>${r.command_count}</td>
                                </tr>
                            `).join('')}
                        </table>
                    `;
                } else {
                    document.getElementById('receivers').innerHTML = '<p>No receiver models configured.</p>';
                }

                // Display discovered devices
                if (discovered.length > 0) {
                    document.getElementById('discovered').innerHTML = `
                        <table>
                            <tr>
                                <th>IP Address</th>
                                <th>Model</th>
                                <th>Last Seen</th>
                                <th>Method</th>
                            </tr>
                            ${discovered.map(d => `
                                <tr>
                                    <td>${d.ip_address}:${d.port}</td>
                                    <td>${d.model}</td>
                                    <td>${new Date(d.last_seen).toLocaleString()}</td>
                                    <td>${d.discovery_method}</td>
                                </tr>
                            `).join('')}
                        </table>
                    `;
                } else {
                    document.getElementById('discovered').innerHTML = '<p>No devices discovered yet. Click "Scan Network" to search.</p>';
                }

                // Display errors
                if (errors.length > 0) {
                    document.getElementById('errors').innerHTML = `
                        <table>
                            <tr>
                                <th>Time</th>
                                <th>Type</th>
                                <th>Category</th>
                                <th>Message</th>
                                <th>Reported</th>
                            </tr>
                            ${errors.map(e => `
                                <tr>
                                    <td>${new Date(e.occurred_at).toLocaleString()}</td>
                                    <td>${e.error_type}</td>
                                    <td>${e.error_category}</td>
                                    <td>${e.error_message.substring(0, 50)}...</td>
                                    <td>${e.reported_to_github ? '<span class="success">✓</span>' : ''}</td>
                                </tr>
                            `).join('')}
                        </table>
                    `;
                } else {
                    document.getElementById('errors').innerHTML = '<p class="success">No errors logged! 🎉</p>';
                }

            } catch (error) {
                console.error('Error loading data:', error);
            }
        }

        async function discover() {
            try {
                const response = await fetch('/api/discover', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ method: 'both', duration: 5 })
                });
                const data = await response.json();
                alert(`Discovery complete! Found ${data.count} devices.`);
                loadData();
            } catch (error) {
                alert('Discovery failed: ' + error.message);
            }
        }

        // Load data on page load
        loadData();
        // Refresh every 30 seconds
        setInterval(loadData, 30000);
    </script>
</body>
</html>
"""


@bp.route('/')
def admin_page():
    """Serve the admin interface."""
    return render_template_string(ADMIN_PAGE)


@bp.route('/stats', methods=['GET'])
def get_stats():
    """Get database statistics."""
    try:
        session = get_session()

        receiver_count = session.query(Receiver).count()
        command_count = session.query(Command).count()
        discovered_count = session.query(DiscoveredReceiver).filter_by(is_active=True).count()
        error_count = session.query(ErrorLog).count()

        return jsonify({
            'receiver_models': receiver_count,
            'total_commands': command_count,
            'discovered_devices': discovered_count,
            'total_errors': error_count
        })

    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@bp.route('/receivers', methods=['GET'])
def get_receivers():
    """Get all receiver models."""
    try:
        session = get_session()
        receivers = session.query(Receiver).all()

        return jsonify([{
            'id': r.id,
            'manufacturer': r.manufacturer,
            'model': r.model,
            'protocol': r.protocol,
            'default_port': r.default_port,
            'command_count': len(r.commands)
        } for r in receivers])

    except Exception as e:
        logger.error(f"Error getting receivers: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@bp.route('/discovered', methods=['GET'])
def get_discovered():
    """Get discovered devices."""
    try:
        session = get_session()
        devices = session.query(DiscoveredReceiver).filter_by(is_active=True).all()

        return jsonify([{
            'id': d.id,
            'ip_address': d.ip_address,
            'port': d.port,
            'model': d.receiver_model.model if d.receiver_model else 'Unknown',
            'last_seen': d.last_seen.isoformat(),
            'discovery_method': d.discovery_method
        } for d in devices])

    except Exception as e:
        logger.error(f"Error getting discovered devices: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@bp.route('/errors', methods=['GET'])
def get_errors():
    """Get recent error logs."""
    try:
        session = get_session()
        errors = session.query(ErrorLog).order_by(ErrorLog.occurred_at.desc()).limit(50).all()

        return jsonify([{
            'id': e.id,
            'error_type': e.error_type,
            'error_category': e.error_category,
            'error_message': e.error_message,
            'occurred_at': e.occurred_at.isoformat(),
            'reported_to_github': e.reported_to_github,
            'github_issue_number': e.github_issue_number
        } for e in errors])

    except Exception as e:
        logger.error(f"Error getting error logs: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
