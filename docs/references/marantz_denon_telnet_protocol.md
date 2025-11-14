# Marantz AVR Control Protocol Documentation

**Manufacturer**: Marantz
**Protocol Type**: Telnet (Port 23) / HTTP
**Source URLs**:
- https://github.com/k3erg/marantz-denon-telnet
- https://www.scribd.com/document/478884952/Marantz-FY21-SR8015-SR7015-PROTOCOL-V01
- Marantz Official Protocol Documentation (FY21 Series)

---

## Protocol Overview

Marantz AV receivers use the same control protocol as Denon (shared engineering), with support for:

### Telnet Control (Port 23)
- Single connection at a time
- Bidirectional communication
- Status feedback available
- Most stable and documented method

### HTTP Control
- Undocumented API
- Multiple simultaneous connections
- Requires reverse-engineering

### RS-232 Serial
- Legacy control method via serial port
- Full-sized AVR models include DB-9 connector
- Same command structure as telnet

---

## Connection Details

### Telnet Connection
```
Host: <receiver-ip>
Port: 23
Protocol: ASCII commands with CRLF termination
Baud: N/A (Ethernet-based)
```

### Important Settings
- "Network Control" must be enabled
- Network communication: Port 23 (telnet)
- Standby mode: Receiver remains controllable if network control enabled

---

## Core Command Structure

Commands follow the same format as Denon AVR receivers (Marantz and Denon share platform):

### ASCII Command Format
```
<COMMAND><VALUE>CRLF
```

- Commands are uppercase ASCII strings
- Parameters follow command code
- All commands end with CRLF (`\r\n`)
- Responses confirm command execution

### Command Categories

#### Power Management
| Command | Function | Response |
|---------|----------|----------|
| `PWON` | Power On | `PWON` |
| `PWSTANDBY` | Power Standby | `PWSTANDBY` |
| `PW?` | Query Power | `PWON` or `PWSTANDBY` |
| `ECOON` | ECO Mode On | `ECOON` |
| `ECOOFF` | ECO Mode Off | `ECOOFF` |

#### Volume Control
| Command | Parameter | Function | Notes |
|---------|-----------|----------|-------|
| `MVUP` | - | Volume Up | Increments 0.5 dB |
| `MVDOWN` | - | Volume Down | Decrements 0.5 dB |
| `MV` | `00-98` | Set Volume | ASCII format |
| `MVMAX` | `00-98` | Set Max Volume | Limit volume ceiling |
| `MV?` | - | Query Volume | Returns `MVnn` |
| `MUON` | - | Mute On | Enables mute |
| `MUOFF` | - | Mute Off | Disables mute |
| `MU?` | - | Query Mute | Returns `MUON` or `MUOFF` |

**Volume Reference**:
- Scale: 0-98 (ASCII numeric)
- 80 = 0 dB (reference level)
- 00 = -80 dB
- 98 = +18 dB

#### Input Selection
| Command | Function | Notes |
|---------|----------|-------|
| `SICD` | CD Input | |
| `SIPHONO` | Phono Input | |
| `SITUNER` | Tuner Input | AM/FM Radio |
| `SIDVD` | DVD Input | |
| `SIBD` | Blu-ray Input | BD |
| `SITV` | TV Input | |
| `SISAT/CBL` | Satellite/Cable | SAT/CBL |
| `SIDVR` | DVR Input | Digital Video Recorder |
| `SIGAME` | Game Input | Gaming console |
| `SIAUX` | Auxiliary Input | AUX |
| `SIDOCK` | iPod Dock | Dock connector |
| `SIIPOD` | iPod | Wireless/USB |
| `SINET/USB` | Net/USB | Network/USB input |
| `SIBT` | Bluetooth | BT wireless |
| `SI?` | Query Input | Returns current input |

#### Zone Control (Multi-Zone Models)

**Zone 2**:
- `Z2ON` / `Z2OFF` - Zone 2 power
- `Z2UP` / `Z2DOWN` - Zone 2 volume up/down
- `Z2MU` / `Z2MF` - Zone 2 mute on/off
- `Z2MV` - Zone 2 volume set (same scale as main)
- `Z2CD` / `Z2DVD` / `Z2SITUNER` - Zone 2 input selection
- `Z2?` - Query Zone 2 status

**Zone 3**:
- `Z3ON` / `Z3OFF` - Zone 3 power
- `Z3UP` / `Z3DOWN` - Zone 3 volume up/down
- `Z3MU` / `Z3MF` - Zone 3 mute on/off
- `Z3MV` - Zone 3 volume set
- `Z3CD` / `Z3DVD` / `Z3SITUNER` - Zone 3 input selection
- `Z3?` - Query Zone 3 status

#### Sound Processing
| Command | Function | Parameters |
|---------|----------|------------|
| `PSCINEMA` | Cinema EQ | ON/OFF |
| `PSDYNVOL` | Dynamic Volume | ON/OFF/MID/MAX |
| `PSPANORAMA` | Panorama | ON/OFF |
| `PSTONECTRL` | Tone Control | ON/OFF |
| `PSDEQ` | Dynamic EQ | ON/OFF |
| `PSDEC` | Dynamic Compressor | ON/OFF |
| `PSDELAY` | Speaker Distance | 0-24 feet |

#### Surround Modes
| Command | Mode |
|---------|------|
| `PSMCHSTEREO` | Multi-Channel Stereo |
| `PSSTEREO` | Stereo |
| `PSSTANDARD` | Standard Surround |
| `PSDOLBY` | Dolby Surround |
| `PSDTS` | DTS |

---

## Available Models

**SR Series** (Marantz standard):
- SR5006, SR5007, SR5009, SR5010, SR5011
- SR6006, SR6007, SR6009, SR6010, SR6011
- SR7006, SR7007, SR7009, SR7010, SR7011
- SR8015

**NR Series** (Marantz budget/compact):
- NR1504 through NR1609

**AV Series** (Marantz processor/amp):
- AV7005, AV8802

---

## Connection Example

### Python Example
```python
import socket
import time

class MarantzAVR:
    def __init__(self, host, port=23):
        self.host = host
        self.port = port
        self.sock = None

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        time.sleep(0.5)  # Wait for connection

    def send_command(self, cmd):
        """Send command and get response"""
        if not self.sock:
            self.connect()

        self.sock.send((cmd + '\r\n').encode('ascii'))
        time.sleep(0.1)  # Wait for processing

        try:
            response = self.sock.recv(1024).decode('ascii').strip()
            return response
        except:
            return None

    def power_on(self):
        return self.send_command('PWON')

    def power_off(self):
        return self.send_command('PWSTANDBY')

    def set_volume(self, level):
        """Set volume 0-98"""
        return self.send_command(f'MV{level:02d}')

    def volume_up(self):
        return self.send_command('MVUP')

    def volume_down(self):
        return self.send_command('MVDOWN')

    def set_input(self, input_name):
        """Set input: SIDVD, SITUNER, SICD, etc."""
        return self.send_command(f'SI{input_name}')

    def get_volume(self):
        return self.send_command('MV?')

    def get_power(self):
        return self.send_command('PW?')

    def get_input(self):
        return self.send_command('SI?')

    def mute_on(self):
        return self.send_command('MUON')

    def mute_off(self):
        return self.send_command('MUOFF')

    def query_mute(self):
        return self.send_command('MU?')

    def close(self):
        if self.sock:
            self.sock.close()


# Usage Example
avr = MarantzAVR('192.168.1.100')
avr.connect()

# Control receiver
print("Powering on...")
avr.power_on()

print("Setting volume to 50...")
avr.set_volume(50)

print("Selecting DVD input...")
avr.set_input('DVD')

print("Querying current status...")
print(f"Power: {avr.get_power()}")
print(f"Volume: {avr.get_volume()}")
print(f"Input: {avr.get_input()}")

avr.close()
```

### JavaScript (Node.js) Example
```javascript
const net = require('net');

class MarantzAVR {
  constructor(host, port = 23) {
    this.host = host;
    this.port = port;
    this.socket = null;
  }

  connect() {
    return new Promise((resolve, reject) => {
      this.socket = net.createConnection(this.port, this.host, () => {
        setTimeout(resolve, 500); // Wait for connection
      });
      this.socket.on('error', reject);
    });
  }

  sendCommand(cmd) {
    return new Promise((resolve) => {
      if (!this.socket) {
        this.connect().then(() => this.sendCommand(cmd)).then(resolve);
        return;
      }

      const dataListener = (data) => {
        this.socket.removeListener('data', dataListener);
        resolve(data.toString('ascii').trim());
      };

      this.socket.on('data', dataListener);
      this.socket.write(`${cmd}\r\n`);
    });
  }

  async powerOn() {
    return this.sendCommand('PWON');
  }

  async powerOff() {
    return this.sendCommand('PWSTANDBY');
  }

  async setVolume(level) {
    return this.sendCommand(`MV${String(level).padStart(2, '0')}`);
  }

  async volumeUp() {
    return this.sendCommand('MVUP');
  }

  async volumeDown() {
    return this.sendCommand('MVDOWN');
  }

  async setInput(input) {
    return this.sendCommand(`SI${input}`);
  }

  async getVolume() {
    return this.sendCommand('MV?');
  }

  async getPower() {
    return this.sendCommand('PW?');
  }

  async getInput() {
    return this.sendCommand('SI?');
  }

  async muteOn() {
    return this.sendCommand('MUON');
  }

  async muteOff() {
    return this.sendCommand('MUOFF');
  }

  close() {
    if (this.socket) {
      this.socket.destroy();
    }
  }
}

// Usage Example
(async () => {
  const avr = new MarantzAVR('192.168.1.100');
  await avr.connect();

  console.log('Powering on...');
  await avr.powerOn();

  console.log('Setting volume to 50...');
  await avr.setVolume(50);

  console.log('Selecting DVD...');
  await avr.setInput('DVD');

  console.log('Query status...');
  console.log('Power:', await avr.getPower());
  console.log('Volume:', await avr.getVolume());
  console.log('Input:', await avr.getInput());

  avr.close();
})();
```

---

## Important Notes

1. **Single Connection Limit**: Port 23 only allows one telnet connection; use HTTP for multiple simultaneous connections

2. **Network Control Required**: Must be enabled in receiver settings

3. **Volume Encoding**:
   - 80 = 0 dB reference
   - 00 = -80 dB (minimum)
   - 98 = +18 dB (maximum)

4. **Command Termination**: Always end with `\r\n` (CRLF)

5. **Response Format**: Receiver echoes command with value (e.g., `MV50` → response `MV50`)

6. **Case Sensitive**: All commands must be uppercase

7. **Shared Platform**: Marantz and Denon AVRs use identical control protocols

---

## Recommended Libraries

- **Node.js**: `marantz-denon-telnet` - Full API wrapper
- **Node.js**: `marantz-avr` - HTTP control library
- **Python**: `aiomadeavr` - Async Python control (tested with SR7013)
- **Home Assistant**: Denon/Marantz integration via `denonavr` library

---

## References

- GitHub marantz-denon-telnet: https://github.com/k3erg/marantz-denon-telnet
- Marantz Official Support: https://support.marantz.com
- OpenHAB Binding: https://www.openhab.org/addons/bindings/denonmarantz/
- FY21 Protocol: https://www.scribd.com/document/478884952/Marantz-FY21-SR8015-SR7015-PROTOCOL-V01
