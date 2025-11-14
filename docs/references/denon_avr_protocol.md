# Denon AVR Control Protocol Documentation

**Manufacturer**: Denon
**Protocol Type**: Telnet (Port 23) / HTTP
**Source URLs**:
- https://github.com/Wolbolar/IPSymconDenon
- https://github.com/phillipsnick/denon-avr
- https://manuals.denon.com/avrx2300w/na/en/GFNFSYnkuzmnni.php
- https://github.com/bencouture/denon-rest-api

---

## Protocol Overview

Denon AVR receivers support two primary control methods:

### Telnet Control (Port 23)
- Single connection limitation—only one client can connect at a time
- Bidirectional status feedback available
- All documented commands return responses
- Network Control setting must be "Always On"

### HTTP Control
- Multiple simultaneous connections supported
- Automatic status updates every 10 seconds
- Feedback availability varies by model and manufacturing year
- Access via `http://<receiver-ip>`

---

## Supported Models

**Denon Series**: AVR-3310 through AVR-X7200WA series, including AVC-X8500H, AVR-S750H, DRA-N5, RCD-N8

**Specific Model**: AVR-X2300W (primary target)

---

## Connection Details

### Telnet Connection
```
Host: <receiver-ip>
Port: 23
Protocol: ASCII commands with CRLF termination
```

### HTTP Connection
```
URL: http://<receiver-ip>
Port: 80
Protocol: XML-based requests/responses
```

---

## Core Command Structure

### ASCII Command Format
Commands are uppercase ASCII strings typically 2-5 characters long, followed by parameter values or terminated with CRLF.

**Examples**:
- `PWON` - Power On
- `PWSTANDBY` - Power Standby
- `MVUP` - Master Volume Up
- `SIDVD` - Select DVD Input
- `PW?` - Query Power Status

### Response Format
Responses follow the pattern: `<COMMAND><VALUE>CRLF`

Examples:
- `PW0N` - Power is On (response)
- `VOL995` - Volume level 99.5 dB
- `SITV` - Input is TV

---

## Power Management Commands

| Command | Function | Response | Notes |
|---------|----------|----------|-------|
| `PWON` | Power On | `PWON` | Activates receiver |
| `PWSTANDBY` | Power Standby | `PWSTANDBY` | Enters standby mode |
| `PW?` | Query Power | `PWON` or `PWSTANDBY` | Returns current state |
| `ECOON` | ECO Mode On | `ECOON` | Energy saving mode |
| `ECOOFF` | ECO Mode Off | `ECOOFF` | Disables eco mode |
| `ECOAUTO` | ECO Auto | `ECOAUTO` | Automatic eco control |

---

## Volume Control Commands

| Command | Function | Parameter | Notes |
|---------|----------|-----------|-------|
| `MVUP` | Master Volume Up | - | Increments by 0.5 dB |
| `MVDOWN` | Master Volume Down | - | Decrements by 0.5 dB |
| `MV` | Set Master Volume | 00-98 (ASCII) | 0-98 dB scale (80 = 0 dB) |
| `MVMAX` | Maximum Volume | 00-98 (ASCII) | Sets max allowed volume |
| `MV?` | Query Volume | - | Returns current volume |
| `MUON` | Mute On | - | Enables mute |
| `MUOFF` | Mute Off | - | Disables mute |
| `MU?` | Query Mute | - | Returns `MUON` or `MUOFF` |

**Volume Conversion**:
- ASCII value 80 = 0 dB (reference level)
- Values above 80 = positive gain
- Values below 80 = negative gain
- Example: ASCII 98 = +18 dB, ASCII 00 = -80 dB

---

## Input Selection Commands

| Command | Function | Aliases |
|---------|----------|---------|
| `SICD` | CD Input | CD |
| `SIPHONO` | Phono Input | PHONO |
| `SITUNER` | Tuner Input | TUNER |
| `SIDVD` | DVD Input | DVD |
| `SIBD` | Blu-ray Input | BD |
| `SITV` | TV Input | TV |
| `SISAT/CBL` | Satellite/Cable | SAT/CBL |
| `SIDVR` | DVR Input | DVR |
| `SIGAME` | Game Input | GAME |
| `SIAUX` | Auxiliary Input | AUX |
| `SIDOCK` | iPod Dock | DOCK |
| `SIIPOD` | iPod | IPOD |
| `SINET/USB` | Net/USB | NET/USB |
| `SIBT` | Bluetooth | BT |
| `SI?` | Query Input | - |

---

## Zone Control (Multi-Zone)

Main Zone commands use `MV`, `MU`, `SI` prefixes.

Zone 2/Zone 3 commands:
- Zone 2 Power: `Z2ON` / `Z2OFF`
- Zone 2 Volume: `Z2UP` / `Z2DOWN`
- Zone 2 Mute: `Z2MU` / `Z2MF`
- Zone 2 Input: `Z2CD`, `Z2DVD`, etc.
- Zone 3 Power: `Z3ON` / `Z3OFF`
- Zone 3 Volume: `Z3UP` / `Z3DOWN`
- Zone 3 Mute: `Z3MU` / `Z3MF`
- Zone 3 Input: `Z3CD`, `Z3DVD`, etc.

---

## Sound Processing Commands

| Command | Function | Parameters |
|---------|----------|------------|
| `PSCINEMA` | Cinema EQ | ON/OFF |
| `PSDYNVOL` | Dynamic Volume | ON/OFF/MID/MAX |
| `PSPANORAMA` | Panorama | ON/OFF |
| `PSTONECTRL` | Tone Control | ON/OFF |
| `PSDEQ` | Dynamic EQ | ON/OFF |
| `PSDEC` | Dynamic Compressor | ON/OFF |
| `PSDRCOFF` / `PSDRCMID` / `PSDRCMAX` | Dynamic Range | OFF/MID/MAX |

---

## Display and System Commands

| Command | Function | Notes |
|----------|----------|-------|
| `NSA` | Display Update ASCII | Triggers status display update |
| `NSE` | Display Update Event | Event-based display update |
| `STBY` | Standby Auto Duration | 0, 15, 30, 60 minutes |
| `RES` | Reset | Factory reset |

---

## REST API Endpoints (Alternative HTTP Method)

Base URL: `http://<receiver-ip>:<port>/api/`

### Common REST Endpoints
```
GET /api/PWON           - Power On
GET /api/PWSTANDBY      - Power Standby
GET /api/SIDVD          - Select DVD Input
GET /api/SITUNER        - Select Tuner Input
GET /api/MVUP           - Volume Up
GET /api/MVDOWN         - Volume Down
GET /api/MUON           - Mute On
GET /api/MUOFF          - Mute Off
```

---

## Connection Example (Telnet)

### Python Example
```python
import socket

# Connect to receiver
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('192.168.1.100', 23))

# Send power on command
sock.send(b'PWON\r\n')

# Receive response
response = sock.recv(1024)
print(response)  # b'PWON\r\n'

# Set volume to 50
sock.send(b'MV50\r\n')
response = sock.recv(1024)

# Get current power status
sock.send(b'PW?\r\n')
response = sock.recv(1024)

sock.close()
```

### JavaScript (Node.js) Example
```javascript
const net = require('net');

const client = new net.Socket();
client.connect(23, '192.168.1.100', function() {
  console.log('Connected');

  // Power on
  client.write('PWON\r\n');

  // Set volume
  client.write('MV50\r\n');

  // Query power
  client.write('PW?\r\n');
});

client.on('data', function(data) {
  console.log('Response:', data.toString());
});

client.on('close', function() {
  console.log('Connection closed');
});
```

---

## Important Notes

1. **Single Connection Limit**: Telnet port 23 only allows one connection at a time. Use HTTP for multiple concurrent connections.

2. **Network Control Setting**: The receiver's "Network Control" setting must be set to "Always On" for telnet/HTTP to work.

3. **Volume Reference**: Volume value 80 = 0 dB (standard reference level)

4. **Status Feedback**: All commands except status queries provide feedback responses.

5. **Command Termination**: All commands must end with CRLF (`\r\n`)

6. **Case Sensitivity**: Commands are case-sensitive (uppercase only)

---

## Recommended Libraries

- **Node.js**: `denon-avr` (npm package) - Comprehensive telnet/RS232 support
- **Python**: `denonavr` - Python wrapper for Denon control
- **Node.js**: `denon-rest-api` - REST API wrapper for easier integration
- **Home Assistant**: Built-in Denon integration via `denonavr` library

---

## References

- Official Denon Manual: https://manuals.denon.com/avrx2300w/
- IP Symcon Integration: https://github.com/Wolbolar/IPSymconDenon
- Denon AVR Library: https://github.com/phillipsnick/denon-avr
- REST API Wrapper: https://github.com/bencouture/denon-rest-api
