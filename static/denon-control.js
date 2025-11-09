/**
 * denon-control.js
 * JavaScript control module for Denon AVR-X2300W Web GUI
 *
 * This module handles all API communication and UI updates for the Denon receiver control interface.
 */

class DenonController {
    constructor() {
        // API configuration
        this.API_BASE_URL = window.location.origin + '/api';

        // State management
        this.state = {
            power: 'OFF',
            volume: -40,
            mute: false,
            input: '--',
            soundMode: '--',
            connection: 'disconnected',
            lastUpdate: null,
            settings: {
                dynamicEq: false,
                dynamicVol: false,
                ecoMode: false,
                sleepTimer: false
            },
            selectedZone: 'main',
            config: null
        };

        // Polling interval for status updates
        this.statusInterval = null;

        // Debounce timers
        this.debounceTimers = {};

        // Initialize on DOM load
        this.init();
    }

    /**
     * Initialize the controller
     */
    init() {
        console.log('Initializing Denon Controller...');

        // Load configuration
        this.loadConfig();

        // Check initial connection
        this.checkConnection();

        // Start status polling
        this.startStatusPolling();

        // Add event listeners
        this.attachEventListeners();

        console.log('Denon Controller initialized');
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Volume slider input event
        const volumeSlider = document.getElementById('volumeSlider');
        if (volumeSlider) {
            volumeSlider.addEventListener('input', (e) => {
                document.getElementById('volumeValue').textContent = e.target.value;
            });
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Only handle shortcuts if not typing in an input
            if (e.target.tagName === 'INPUT') return;

            switch(e.key) {
                case 'ArrowUp':
                    e.preventDefault();
                    this.volume('up');
                    break;
                case 'ArrowDown':
                    e.preventDefault();
                    this.volume('down');
                    break;
                case 'm':
                case 'M':
                    e.preventDefault();
                    this.mute();
                    break;
                case ' ':
                    e.preventDefault();
                    this.power(this.state.power === 'ON' ? 'off' : 'on');
                    break;
            }
        });
    }

    /**
     * Load configuration from API
     */
    async loadConfig() {
        try {
            const response = await fetch(`${this.API_BASE_URL}/config`);
            const data = await response.json();

            this.state.config = data;

            // Update UI with config info
            if (data.receiver_host) {
                document.getElementById('ipInfo').textContent = data.receiver_host;
            }

            // Enable/disable features based on config
            this.updateFeatureAvailability(data.features);

            console.log('Configuration loaded:', data);
        } catch (error) {
            console.error('Failed to load configuration:', error);
            this.showToast('Failed to load configuration', 'error');
        }
    }

    /**
     * Update feature availability based on config
     */
    updateFeatureAvailability(features) {
        // Enable/disable controls based on available features
        if (!features.volume) {
            document.querySelectorAll('.volume-controls button, #volumeSlider').forEach(el => {
                el.disabled = true;
            });
        }

        if (!features.input_selection) {
            document.querySelectorAll('.input-btn').forEach(el => {
                el.disabled = true;
            });
        }

        if (!features.sound_modes) {
            document.querySelectorAll('.sound-mode-btn').forEach(el => {
                el.disabled = true;
            });
        }

        if (!features.zone_control) {
            document.querySelectorAll('.zone-tab:not(.active)').forEach(el => {
                el.disabled = true;
            });
        }
    }

    /**
     * Check connection to API and receiver
     */
    async checkConnection() {
        try {
            const response = await fetch(`${this.API_BASE_URL}/health`);
            const data = await response.json();

            if (data.status === 'healthy') {
                this.updateConnectionStatus('connected');
                document.getElementById('apiStatus').textContent = 'Online';

                // Get current status
                await this.getStatus();
            } else {
                this.updateConnectionStatus('disconnected');
                document.getElementById('apiStatus').textContent = 'Error';
            }
        } catch (error) {
            console.error('Connection check failed:', error);
            this.updateConnectionStatus('disconnected');
            document.getElementById('apiStatus').textContent = 'Offline';
        }
    }

    /**
     * Update connection status display
     */
    updateConnectionStatus(status) {
        this.state.connection = status;
        const dot = document.getElementById('connectionDot');
        const text = document.getElementById('connectionText');

        dot.className = 'status-dot';

        switch(status) {
            case 'connected':
                dot.classList.add('connected');
                text.textContent = 'Connected';
                break;
            case 'disconnected':
                dot.classList.add('disconnected');
                text.textContent = 'Disconnected';
                break;
            case 'connecting':
                text.textContent = 'Connecting...';
                break;
            default:
                text.textContent = status;
        }
    }

    /**
     * Get current receiver status
     */
    async getStatus() {
        try {
            const response = await fetch(`${this.API_BASE_URL}/status`);
            const data = await response.json();

            if (data.success) {
                this.updateStatus(data.status);
                this.state.lastUpdate = new Date();
                document.getElementById('lastUpdate').textContent =
                    new Date().toLocaleTimeString();
            }
        } catch (error) {
            console.error('Failed to get status:', error);
        }
    }

    /**
     * Update UI with status data
     */
    updateStatus(status) {
        // Update power status
        if (status.power !== undefined) {
            this.state.power = status.power;
            const powerEl = document.getElementById('powerStatus');
            powerEl.textContent = status.power;
            powerEl.className = `power-status-value ${status.power.toLowerCase()}`;

            // Enable/disable controls based on power state
            const isPowerOn = status.power === 'ON';
            this.setControlsEnabled(isPowerOn);
        }

        // Update volume
        if (status.volume !== undefined) {
            this.state.volume = status.volume;
            document.getElementById('volumeValue').textContent = status.volume;
            document.getElementById('volumeSlider').value = status.volume;
        }

        // Update mute status
        if (status.mute !== undefined) {
            this.state.mute = status.mute;
            const muteBtn = document.getElementById('muteBtn');
            if (muteBtn) {
                muteBtn.textContent = status.mute ? 'Unmute' : 'Mute';
                muteBtn.classList.toggle('active', status.mute);
            }
        }

        // Update input
        if (status.input !== undefined) {
            this.state.input = status.input;
            this.updateInputSelection(status.input);
        }

        // Update connection status
        if (status.connection !== undefined) {
            this.updateConnectionStatus(status.connection === 'Connected' ? 'connected' : 'disconnected');
        }
    }

    /**
     * Enable/disable controls based on power state
     */
    setControlsEnabled(enabled) {
        // Only enable controls if power is on and feature is available
        const features = this.state.config?.features || {};

        // Volume controls
        if (features.volume !== false) {
            document.querySelectorAll('.volume-controls button, #volumeSlider').forEach(el => {
                el.disabled = !enabled;
            });
        }

        // Input controls
        if (features.input_selection !== false) {
            document.querySelectorAll('.input-btn').forEach(el => {
                el.disabled = !enabled;
            });
        }

        // Sound mode controls
        if (features.sound_modes !== false) {
            document.querySelectorAll('.sound-mode-btn').forEach(el => {
                el.disabled = !enabled;
            });
        }
    }

    /**
     * Update input button selection
     */
    updateInputSelection(input) {
        document.querySelectorAll('.input-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.input === input) {
                btn.classList.add('active');
            }
        });
    }

    /**
     * Start polling for status updates
     */
    startStatusPolling() {
        // Poll every 5 seconds when connected
        this.statusInterval = setInterval(() => {
            if (this.state.connection === 'connected') {
                this.getStatus();
            }
        }, 5000);

        // Also check connection every 30 seconds
        setInterval(() => {
            this.checkConnection();
        }, 30000);
    }

    /**
     * Send API command
     */
    async sendCommand(endpoint, method = 'POST', body = null) {
        console.log(`Sending command: ${method} ${endpoint}`);

        try {
            const options = {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                }
            };

            if (body) {
                options.body = JSON.stringify(body);
            }

            const response = await fetch(`${this.API_BASE_URL}${endpoint}`, options);
            const data = await response.json();

            if (data.success) {
                // Update status if included in response
                if (data.status) {
                    this.updateStatus(data.status);
                }

                // Show success message if provided
                if (data.message) {
                    this.showToast(data.message, 'success');
                }
            } else {
                // Show error message
                this.showToast(data.error || 'Command failed', 'error');
            }

            return data;

        } catch (error) {
            console.error('Command failed:', error);
            this.showToast('Failed to send command', 'error');
            throw error;
        }
    }

    /**
     * Power control
     */
    async power(action) {
        console.log(`Power ${action}`);

        // Disable buttons during request
        document.getElementById('powerOnBtn').disabled = true;
        document.getElementById('powerOffBtn').disabled = true;

        try {
            // Send command with receiver info
            await this.sendCommand(`/power/${action}`, 'POST', {
                receiver_ip: '192.168.1.182',
                receiver_model: 'AVR-X2300W'
            });

            // Update local state immediately for responsiveness
            this.state.power = action === 'on' ? 'ON' : 'OFF';
            this.updateStatus({power: this.state.power});

        } catch (error) {
            console.error('Power control failed:', error);
        } finally {
            // Re-enable buttons
            document.getElementById('powerOnBtn').disabled = false;
            document.getElementById('powerOffBtn').disabled = false;
        }
    }

    /**
     * Volume control
     */
    async volume(action) {
        if (this.state.power !== 'ON') return;

        console.log(`Volume ${action}`);
        await this.sendCommand(`/volume/${action}`);
    }

    /**
     * Set specific volume level
     */
    async setVolume(value) {
        if (this.state.power !== 'ON') return;

        // Debounce volume changes
        clearTimeout(this.debounceTimers.volume);
        this.debounceTimers.volume = setTimeout(async () => {
            console.log(`Setting volume to ${value}`);
            await this.sendCommand(`/volume/set`, 'POST', {value: value});
        }, 100);
    }

    /**
     * Mute toggle
     */
    async mute() {
        if (this.state.power !== 'ON') return;

        console.log('Toggling mute');
        await this.sendCommand('/volume/mute');
    }

    /**
     * Input selection
     */
    async setInput(input) {
        if (this.state.power !== 'ON') return;

        console.log(`Setting input to ${input}`);

        // Update UI immediately for responsiveness
        this.updateInputSelection(input);

        await this.sendCommand(`/input/${input}`);
    }

    /**
     * Sound mode selection
     */
    async setSoundMode(mode) {
        if (this.state.power !== 'ON') return;

        console.log(`Setting sound mode to ${mode}`);

        // Update UI
        document.querySelectorAll('.sound-mode-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.textContent.toUpperCase().includes(mode)) {
                btn.classList.add('active');
            }
        });

        await this.sendCommand(`/sound-mode/${mode}`);
    }

    /**
     * Toggle settings
     */
    async toggleSetting(setting) {
        if (this.state.power !== 'ON') return;

        console.log(`Toggling ${setting}`);

        // Toggle UI immediately
        const toggle = document.querySelector(`[data-setting="${setting}"]`);
        if (toggle) {
            toggle.classList.toggle('active');
        }

        // Update state
        this.state.settings[setting] = !this.state.settings[setting];

        await this.sendCommand(`/settings/${setting}/toggle`);
    }

    /**
     * Zone selection
     */
    selectZone(zone) {
        console.log(`Selecting zone: ${zone}`);

        this.state.selectedZone = zone;

        // Update UI
        document.querySelectorAll('.zone-tab').forEach(tab => {
            tab.classList.remove('active');
            if (tab.textContent.toLowerCase().includes(zone)) {
                tab.classList.add('active');
            }
        });

        // Load zone-specific status
        this.getStatus();
    }

    /**
     * Show toast notification
     */
    showToast(message, type = 'info', duration = 3000) {
        const container = document.getElementById('toastContainer');

        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;

        // Add icon based on type
        const icons = {
            success: '✓',
            error: '✗',
            info: 'ℹ',
            warning: '⚠'
        };

        toast.innerHTML = `
            <span style="font-size: 1.2rem;">${icons[type] || ''}</span>
            <span>${message}</span>
        `;

        container.appendChild(toast);

        // Trigger animation
        setTimeout(() => toast.classList.add('show'), 10);

        // Remove after duration
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }

    /**
     * Format time for display
     */
    formatTime(date) {
        if (!date) return '--';
        return date.toLocaleTimeString();
    }
}

// Initialize controller when DOM is ready
const DenonControl = new DenonController();

// Export for global access
window.DenonControl = DenonControl;

// Log initialization
console.log('Denon Control Module loaded successfully');