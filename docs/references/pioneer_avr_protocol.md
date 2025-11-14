# Pioneer AVR Control Protocol Documentation

**Manufacturer**: Pioneer
**Protocol Type**: Telnet (Port 8102) / HTTP / RS-232
**Source URLs**:
- https://github.com/crowbarz/aiopioneer
- https://github.com/rwifall/pioneer-receiver-notes
- https://arnowelzel.de/en/control-av-receivers-by-pioneer-over-the-network
- Pioneer Official RS-232 & IP Protocol Documentation

---

## Protocol Overview

Pioneer Elite and VSX-series receivers support multiple control methods:

### Telnet Control (Port 8102)
- TCP socket communication
- Most reliable and stable method
- Bidirectional communication
- Status feedback available
- Recommended for custom integration

### HTTP Control
- Undocumented/reverse-engineered endpoints
- Multiple simultaneous connections
- Less stable than telnet
- Limited status feedback

### RS-232 Serial
- Legacy method via DB-9 serial connector
- Same command syntax as telnet
- Limited to serial port bandwidth

---

## Connection Details

### Telnet Connection
```
Host: <receiver-ip>
Port: 8102
Protocol: ASCII commands with CRLF termination
Connection: Persistent socket connection
```

### Important Configuration
By default, network connectivity **disconnects during standby mode**. To enable remote power-on capability:
1. Access receiver settings
2. Configure network to remain active during standby
3. Enables power control from standby state

---

## Core Command Structure

### ASCII Command Format
```
<COMMAND><PARAMETER>CRLF
```

- All commands are ASCII text
- Parameters follow command code
- Terminated with CR+LF (`\r\n`)
- Receiver provides status feedback

### Command Categories

#### Power Management
| Command | Function | Response | Notes |
|---------|----------|----------|-------|
| `PO` | Power On | `PO` | Activates receiver |
| `PF` | Power Off | `PF` | Enters standby |
| `?P` | Query Power | `PWR0` or `PWR2` | PWR0=On, PWR2=Standby |

#### Volume Control
| Command | Function | Parameter | Response |
|---------|----------|-----------|----------|
| `VU` | Volume Up | - | Next volume change |
| `VD` | Volume Down | - | Next volume change |
| `?V` | Query Volume | - | `VOLnnn` (000-131) |

**Volume Range**: 000-131 (relative scale)

#### Mute Control
| Command | Function | Response | Notes |
|---------|----------|----------|-------|
| `MO` | Mute On | `MUT0` | Enables mute |
| `MF` | Mute Off | `MUT1` | Disables mute |
| `?M` | Query Mute | `MUT0` or `MUT1` | MUT0=Mute on, MUT1=Mute off |

#### Input Selection
| Command | Function | Source ID |
|---------|----------|-----------|
| `19FN` | Select HDMI 1 | 19 |
| `20FN` | Select HDMI 2 | 20 |
| `21FN` | Select HDMI 3 | 21 |
| `22FN` | Select HDMI 4 | 22 |
| `23FN` | Select HDMI 5 | 23 |
| `25FN` | Select Blu-ray | 25 |
| `00FN` | Phono | 00 |
| `01FN` | CD | 01 |
| `02FN` | Tuner | 02 |
| `04FN` | DVD | 04 |
| `05FN` | TV | 05 |
| `06FN` | SAT/CBL | 06 |
| `38FN` | Internet Radio | 38 |
| `53FN` | Spotify | 53 |
| `?F` | Query Input | - |

### Input Source Reference

**Extended Source ID List (VSX-1021, SC-35, SC-37)**:

| ID | Source | ID | Source |
|---|---|---|---|
| 00 | Phono | 34 | Adapter Port |
| 01 | CD | 35 | HDMI 6 |
| 02 | Tuner | 36 | HDMI 7 |
| 03 | Cable/Sat | 38 | Internet Radio |
| 04 | DVD | 40 | Bluetooth |
| 05 | TV | 41 | USB Memory |
| 06 | Aux | 42 | Network Media Server |
| 19 | HDMI 1 | 53 | Spotify |
| 20 | HDMI 2 | 55 | Pandora |
| 21 | HDMI 3 | 57 | Airplay |
| 22 | HDMI 4 | 58 | MHL Mobile |
| 23 | HDMI 5 | 59 | Favorite |
| 24 | HDMI 6 | 60 | SiriusXM |
| 25 | Blu-ray | | |

#### Listening Mode
| Command | Mode | Notes |
|---------|------|-------|
| `0010SR` | Stereo | 2-channel stereo |
| `0011SR` | Dolby 2.0 | |
| `0012SR` | Dolby Surround | |
| `0013SR` | Neo:6 Cinema | |
| `0014SR` | Neo:6 Music | |
| `0015SR` | Dolby 5.1 | |
| `0016SR` | Dolby EX | |
| `0017SR` | DTS Surround | |
| `0018SR` | DTS-ES | |
| `0019SR` | DTS 96/24 | |
| `001ASR` | DTS-HD | |
| `001BSR` | Left/Center/Right | |
| `001CSR` | Dolby Atmos | |
| `?S` | Query Mode | Returns current mode code |

#### Volume Zone Control

**Multi-Zone Receivers** (VSX-821, VSX-921, VSX-1021):

Zone 2:
- `ZVU` - Zone 2 Volume Up
- `ZVD` - Zone 2 Volume Down
- `?ZV` - Zone 2 Query Volume
- `ZMO` - Zone 2 Mute On
- `ZMF` - Zone 2 Mute Off
- `?ZM` - Zone 2 Query Mute

Zone 3 (if supported):
- Similar commands with `HZVU`, `HZVD` prefix

#### Additional Commands

| Command | Function | Notes |
|---------|----------|-------|
| `PN` | Panel Toggle | Turn on/off receiver panel display |
| `R` | Ready Signal | Receiver broadcasts ~every 30 seconds |
| `E` | Error | Receiver broadcasts on invalid command |

---

## Supported Models

**VSX Series** (Mainstream):
- VSX-529, VSX-921, VSX-1021, VSX-1121, VSX-1131
- VSX-1221, VSX-1231

**Elite SC Series** (High-End):
- SC-35, SC-37, SC-57, SC-61, SC-67, SC-79, SC-89, SC-LX57, SC-LX87

**Other Models**:
- VSX-30, VSX-31, VSX-32, VSX-33 (older series)
- VSX-1120-K, VSX-1130 (specific variants)

---

## Connection Example

### Python Example (Synchronous)
```python
import socket
import time

class PioneerAVR:
    def __init__(self, host, port=8102):
        self.host = host
        self.port = port
        self.socket = None

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))

    def send_command(self, cmd):
        """Send command and receive response"""
        if not self.socket:
            self.connect()

        self.socket.send((cmd + '\r\n').encode('ascii'))
        time.sleep(0.1)  # Wait for processing

        try:
            response = self.socket.recv(1024).decode('ascii').strip()
            return response
        except Exception as e:
            print(f"Error: {e}")
            return None

    def power_on(self):
        return self.send_command('PO')

    def power_off(self):
        return self.send_command('PF')

    def get_power_status(self):
        response = self.send_command('?P')
        if response == 'PWR0':
            return 'on'
        elif response == 'PWR2':
            return 'standby'
        return response

    def volume_up(self):
        return self.send_command('VU')

    def volume_down(self):
        return self.send_command('VD')

    def get_volume(self):
        response = self.send_command('?V')
        if response.startswith('VOL'):
            return int(response[3:])
        return response

    def set_input(self, source_id):
        """Set input by source ID (e.g., '19' for HDMI 1)"""
        return self.send_command(f'{source_id}FN')

    def get_input(self):
        return self.send_command('?F')

    def mute_on(self):
        return self.send_command('MO')

    def mute_off(self):
        return self.send_command('MF')

    def get_mute_status(self):
        response = self.send_command('?M')
        if response == 'MUT0':
            return 'muted'
        elif response == 'MUT1':
            return 'unmuted'
        return response

    def set_listening_mode(self, mode_code):
        """Set listening mode by code (e.g., '0010SR' for Stereo)"""
        return self.send_command(f'{mode_code}')

    def get_listening_mode(self):
        return self.send_command('?S')

    def close(self):
        if self.socket:
            self.socket.close()


# Usage Example
avr = PioneerAVR('192.168.1.100')
avr.connect()

print("Powering on...")
avr.power_on()
time.sleep(1)

print(f"Power status: {avr.get_power_status()}")
print(f"Current volume: {avr.get_volume()}")

print("Volume up...")
avr.volume_up()

print("Selecting HDMI 1...")
avr.set_input('19')

print(f"Current input: {avr.get_input()}")
print(f"Mute status: {avr.get_mute_status()}")

avr.close()
```

### Python Example (Async with aiopioneer)
```python
import asyncio
from aiopioneer import PioneerAVR

async def main():
    avr = PioneerAVR('192.168.1.100')

    async with avr:
        # Power on
        await avr.turn_on()

        # Set volume
        await avr.set_volume(50)

        # Change input to HDMI 1
        await avr.select_input('19')

        # Set listening mode
        await avr.set_listening_mode('0010SR')

        # Query current state
        print(f"Power: {avr.power}")
        print(f"Volume: {avr.volume}")
        print(f"Input: {avr.input_source}")
        print(f"Mode: {avr.listening_mode}")

asyncio.run(main())
```

### JavaScript (Node.js) Example
```javascript
const net = require('net');

class PioneerAVR {
  constructor(host, port = 8102) {
    this.host = host;
    this.port = port;
    this.socket = null;
  }

  connect() {
    return new Promise((resolve, reject) => {
      this.socket = net.createConnection(this.port, this.host, () => {
        resolve();
      });
      this.socket.on('error', reject);
    });
  }

  sendCommand(cmd) {
    return new Promise((resolve) => {
      const dataListener = (data) => {
        this.socket.removeListener('data', dataListener);
        resolve(data.toString('ascii').trim());
      };

      this.socket.on('data', dataListener);
      this.socket.write(`${cmd}\r\n`);

      // Timeout after 500ms
      setTimeout(() => {
        this.socket.removeListener('data', dataListener);
        resolve(null);
      }, 500);
    });
  }

  async powerOn() {
    return this.sendCommand('PO');
  }

  async powerOff() {
    return this.sendCommand('PF');
  }

  async getPowerStatus() {
    const response = await this.sendCommand('?P');
    return response === 'PWR0' ? 'on' : response === 'PWR2' ? 'standby' : response;
  }

  async volumeUp() {
    return this.sendCommand('VU');
  }

  async volumeDown() {
    return this.sendCommand('VD');
  }

  async getVolume() {
    const response = await this.sendCommand('?V');
    return response?.startsWith('VOL') ? parseInt(response.substring(3)) : response;
  }

  async setInput(sourceId) {
    return this.sendCommand(`${sourceId}FN`);
  }

  async getInput() {
    return this.sendCommand('?F');
  }

  async muteOn() {
    return this.sendCommand('MO');
  }

  async muteOff() {
    return this.sendCommand('MF');
  }

  async getMuteStatus() {
    const response = await this.sendCommand('?M');
    return response === 'MUT0' ? 'muted' : response === 'MUT1' ? 'unmuted' : response;
  }

  close() {
    if (this.socket) {
      this.socket.destroy();
    }
  }
}

// Usage Example
(async () => {
  const avr = new PioneerAVR('192.168.1.100');
  await avr.connect();

  console.log('Power status:', await avr.getPowerStatus());
  await avr.powerOn();

  console.log('Volume:', await avr.getVolume());
  await avr.volumeUp();

  console.log('Setting HDMI 1...');
  await avr.setInput('19');

  console.log('Input:', await avr.getInput());

  avr.close();
})();
```

---

## HTTP Endpoints (Undocumented)

**Note**: HTTP API is reverse-engineered and less stable than telnet

### Status Handler
```
GET http://<receiver-ip>/StatusHandler.asp
```

Returns current receiver status including power, volume, input, etc.

### Event Handler
```
GET http://<receiver-ip>/EventHandler.asp?WebToHostItem=<command>
```

**Common WebToHostItem values**:
- `PO` - Power On
- `PF` - Power Off
- `VU` - Volume Up
- `VD` - Volume Down
- `19` - HDMI 1
- `20` - HDMI 2
- `25` - Blu-ray

---

## Important Notes

1. **Port Configuration**: Telnet uses port 8102 (not standard 23)

2. **Standby Network Control**: Network connectivity disabled in standby by default; must be configured in receiver settings

3. **Status Broadcast**: Receiver broadcasts ready signal `R` approximately every 30 seconds

4. **Command Feedback**: All commands receive response confirmation from receiver

5. **CRLF Termination**: All commands must end with `\r\n`

6. **Case Sensitive**: Commands are typically uppercase, parameters vary

7. **Volume Scale**: Range is 000-131 (relative, not absolute dB)

8. **Source ID Encoding**: Some sources use 2-digit codes (e.g., `19FN` for HDMI 1)

---

## Network Ports (VSX-1021 K)

The receiver opens multiple TCP ports:

| Port | Service | Usage |
|------|---------|-------|
| 23 | Telnet (legacy) | Basic telnet control |
| 80 | HTTP | Web interface |
| 443 | HTTPS | Secure web interface |
| 1900 | UPnP/SSDP | Device discovery |
| 8080 | HTTP Alt | Alternative HTTP |
| 8102 | Pioneer Control | Native telnet control (recommended) |
| 10100 | Proprietary | Proprietary service |
| 49152-49154 | Dynamic/RPC | Dynamic allocation |

---

## Recommended Libraries

- **Python**: `aiopioneer` (asyncio) - Best choice for Python
- **Node.js**: `pioneer-avr` wrappers available on npm
- **PHP/Node.js**: Multiple community implementations
- **Home Assistant**: Built-in Pioneer integration via `aiopioneer`

---

## References

- GitHub aiopioneer: https://github.com/crowbarz/aiopioneer
- GitHub pioneer-receiver-notes: https://github.com/rwifall/pioneer-receiver-notes
- Control Article: https://arnowelzel.de/en/control-av-receivers-by-pioneer-over-the-network
- Pioneer Custom Install: https://www.pioneerelectronics.com
- SnapAV Protocol: https://www.snapav.com
