# Onkyo/Integra eISCP Control Protocol Documentation

**Manufacturer**: Onkyo / Integra
**Protocol Type**: eISCP (Ethernet Integra Serial Control Protocol)
**Port**: 60128 (TCP)
**Source URLs**:
- https://github.com/miracle2k/onkyo-eiscp
- https://sudonull.com/post/9179-Onkyos-ISCP-eISCP-protocol-control-of-Onkyo-devices-over-the-network
- Official Onkyo ISCP/eISCP Protocol Documentation (v1.21 - 2011)

---

## Protocol Overview

The **eISCP** protocol (extended Integra Serial Control Protocol) is Onkyo's network control protocol for AV receivers and amplifiers. It evolved from the original ISCP serial protocol (RS-232) to support TCP/IP Ethernet communication.

### Protocol Characteristics
- Ethernet/TCP-IP based
- Supports bidirectional communication
- Self-contained message packets
- Parameter encoding in hexadecimal/ASCII or XML format
- Command-response communication pattern

---

## Connection Details

### Network Connection
```
Host: <receiver-ip>
Port: 60128
Protocol: TCP (not UDP)
```

### Important Configuration
The receiver's "Setup → Hardware → Network → Network Control" setting **must be enabled** for remote power-on and control to work while in standby mode.

---

## Message Format

### Basic ISCP Message Structure

```
!<Device><Command><Parameter>
```

- **Start**: `!` character (0x21)
- **Device**: Target device code (1 character)
  - `1` = Receiver
  - `2` = Tuner
  - `3` = Tape Deck
  - etc.
- **Command**: 3-letter command code (uppercase)
- **Parameter**: Variable-length parameter (hex, ASCII, or XML)
- **Termination**: CR (0x0D), LF (0x0A), or CR+LF

### eISCP Wrapper Format (Over Ethernet)

eISCP messages are wrapped in a binary packet structure:

```
Header: "ISCP" (4 bytes, ASCII)
Header Size: 16 (4 bytes, big-endian integer)
Data Size: <length> (4 bytes, big-endian integer)
Version: 0x01 (1 byte)
Reserved: 0x00 0x00 0x00 (3 bytes)
Payload: <ISCP message>
Terminator: LF (0x0A) or CR+LF
```

**Minimum packet size**: 22 bytes

### Complete eISCP Packet Example

```
Raw bytes (hexadecimal):
49 53 43 50        - "ISCP" header
00 00 00 10        - Header size (16 bytes)
00 00 00 0F        - Data size (15 bytes)
01                 - Version
00 00 00           - Reserved
21 31 50 57 4F 4E 0D 0A  - "!1PWN\r\n" (ISCP message)
```

---

## Core Commands

### Power Management

| Command | Parameter | Function | Response |
|---------|-----------|----------|----------|
| `PWR` | `00` | Standby | `PWR00` or `PWR01/02` |
| `PWR` | `01` | Power On | `PWR01` |
| `PWR` | `QSTN` | Query Power | Returns `PWR00/01/02` |

**Power States**:
- `00` = Standby
- `01` = On
- `02` = On (Eco mode variant)

### Volume Control

| Command | Parameter | Function | Example Response |
|---------|-----------|----------|---|
| `MVL` | `00-60` (hex) | Set Master Volume | `MVL20` (volume 0x20) |
| `MVL` | `QSTN` | Query Volume | `MVL45` |
| `MUT` | `00` | Mute Off | `MUT00` |
| `MUT` | `01` | Mute On | `MUT01` |
| `MUT` | `QSTN` | Query Mute | `MUT00` or `MUT01` |

**Volume Encoding**:
- Hexadecimal scale: `00` to `60` (0-96 in decimal)
- Typically: `60` = maximum (0 dB reference)
- Varies by model

### Input Selection

| Command | Parameter | Function |
|---------|-----------|----------|
| `SLI` | `00` | PHONO |
| `SLI` | `01` | CD |
| `SLI` | `02` | TUNER |
| `SLI` | `03` | TAPE |
| `SLI` | `04` | DOCK (iPod) |
| `SLI` | `05` | NET/USB |
| `SLI` | `06` | INTERNET RADIO |
| `SLI` | `07` | BLUETOOTH |
| `SLI` | `08` | HDMI 1 |
| `SLI` | `09` | HDMI 2 |
| `SLI` | `0A` | HDMI 3 |
| `SLI` | `0B` | HDMI 4 |
| `SLI` | `0C` | HDMI 5 |
| `SLI` | `0D` | HDMI 6 |
| `SLI` | `0E` | HDMI 7 |
| `SLI` | `0F` | HDMI 8 |
| `SLI` | `10` | AV 1 (Composite) |
| `SLI` | `11` | AV 2 (Composite) |
| `SLI` | `12` | AV 3 (Composite) |
| `SLI` | `QSTN` | Query Input | Returns current input code |

### Surround Mode

| Command | Parameter | Function |
|---------|-----------|----------|
| `LMD` | `00` | Stereo |
| `LMD` | `01` | Direct |
| `LMD` | `02` | Surround Decoder |
| `LMD` | `03` | DTS Surround |
| `LMD` | `04` | Dolby Digital |
| `LMD` | `05` | Dolby Surround Pro Logic |
| `LMD` | `06` | DTS-ES Discrete |
| `LMD` | `07` | DTS-ES Matrix |
| `LMD` | `QSTN` | Query Mode | |

### Tuner Control

| Command | Parameter | Function |
|---------|-----------|----------|
| `TUN` | Freq (hex) | Set frequency |
| `TUN` | `QSTN` | Query frequency |

---

## Zone Control (Multi-Zone)

Zone commands use the device code to distinguish zones:

- **Zone 1**: Device code `1` (example: `!1SLI02`)
- **Zone 2**: Device code `2` (example: `!2SLI02`)
- **Zone 3**: Device code `3` (example: `!3SLI02`)

---

## High-Level Python API (onkyo-eiscp)

The `onkyo-eiscp` library provides a simpler command interface:

### Command Format
```
zone.command=argument
```

### Examples
```
main.power=on               # Power on main zone
main.power=off              # Power off main zone
main.input=hdmi1            # Select HDMI 1
main.volume=30              # Set volume to 30
main.mute=on                # Mute on
zone2.power=on              # Zone 2 power on
zone2.input=net-usb         # Zone 2 input to Net/USB
main.listening_mode=stereo  # Set listening mode
```

### Discovery
```python
from onkyoeiscp import Receiver

# Discover receivers on network
receivers = Receiver.discover()
for ip in receivers:
    receiver = Receiver(ip)
    print(f"Found: {receiver.model}")
```

### Usage
```python
from onkyoeiscp import Receiver

receiver = Receiver('192.168.1.100')

# Power control
receiver.power = 'on'
receiver.power = 'off'
print(receiver.power)  # 'on' or 'off'

# Volume
receiver.volume = 25
print(receiver.volume)

# Mute
receiver.mute = 'on'
receiver.mute = 'off'

# Input selection
receiver.input = 'hdmi1'
receiver.input = 'hdmi2'
print(receiver.input)

# Listening mode
receiver.listening_mode = 'stereo'
print(receiver.listening_mode)

# Context manager (recommended)
with Receiver('192.168.1.100') as receiver:
    receiver.power = 'on'
    receiver.input = 'hdmi1'
    receiver.volume = 30
```

---

## Input Source Names

Human-readable input names for the Python library:

- `phono`
- `cd`
- `tuner`
- `tape`
- `dock`
- `net-usb`
- `internet-radio`
- `bluetooth`
- `hdmi1` through `hdmi8`
- `av1`, `av2`, `av3` (composite)

---

## Raw ISCP Message Examples

### Power On (Main Zone)
```
Message: !1PWN
Hex: 21 31 50 57 4E 0D
Description: Power main zone on
```

### Query Power Status
```
Message: !1PW?
Hex: 21 31 50 57 3F 0D
Response: !1PWN or !1PWF
```

### Select HDMI 1
```
Message: !1SLI08
Hex: 21 31 53 4C 49 30 38 0D
Description: Main zone input to HDMI 1
```

### Set Volume to 32 (0x20)
```
Message: !1MVL20
Hex: 21 31 4D 56 4C 32 30 0D
Description: Set master volume to hex 0x20
```

### Mute On
```
Message: !1MUT01
Hex: 21 31 4D 55 54 30 31 0D
Description: Enable mute
```

### Zone 2 Power On
```
Message: !2PWN
Hex: 21 32 50 57 4E 0D
Description: Power zone 2 on
```

---

## Connection Example

### Python Example (Low-Level)
```python
import socket
import struct

def send_eiscp_command(host, command):
    # Create socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, 60128))

    # Build eISCP message
    iscp_message = command.encode('ascii') + b'\r\n'

    # Build eISCP packet
    header = b'ISCP'
    header_size = struct.pack('>I', 16)
    data_size = struct.pack('>I', len(iscp_message))
    version = b'\x01'
    reserved = b'\x00\x00\x00'

    packet = header + header_size + data_size + version + reserved + iscp_message

    # Send
    sock.send(packet)

    # Receive response
    response = sock.recv(1024)
    sock.close()

    return response

# Usage
response = send_eiscp_command('192.168.1.100', '!1PWN')
print(response)
```

### Python Example (High-Level, onkyo-eiscp)
```python
from onkyoeiscp import Receiver

receiver = Receiver('192.168.1.100')

# Power on
receiver.power = 'on'

# Select HDMI 1
receiver.input = 'hdmi1'

# Set volume to 30
receiver.volume = 30

# Mute
receiver.mute = 'on'

# Query current settings
print(f"Power: {receiver.power}")
print(f"Input: {receiver.input}")
print(f"Volume: {receiver.volume}")
print(f"Mute: {receiver.mute}")
```

---

## Supported Models

Onkyo and Integra models supporting eISCP:

**High-End (Integra)**: TX-NR1009, TX-NR909, TX-NR808, TX-NR807, TX-NR906, TX-NR1010

**Mainstream**: TX-NR707, TX-NR606, TX-NR545, TX-NR444

**Budget**: TX-SR444, TX-SR343

**Amplifiers**: A-5701, A-9070

The protocol document (v1.21) specifically references models 3008 and 5008.

---

## Important Notes

1. **Network Control Enable**: Must be enabled in receiver settings for standby mode control
2. **Parameter Format**: Most parameters use hexadecimal encoding (0-9, A-F)
3. **Response Format**: Devices echo commands with parameters to confirm
4. **Single Query Parameter**: Use `QSTN` to query current state of any setting
5. **Termination**: Always use CR or CRLF at end of messages
6. **Device Codes**: Use `1` for main zone, `2` for zone 2, etc.

---

## Recommended Libraries

- **Python**: `onkyo-eiscp` - Best choice for Python integration
- **Node.js**: Multiple community libraries available
- **Java**: `jEISCP` implementation available
- **Home Assistant**: Built-in Onkyo integration via `onkyo-eiscp`

---

## References

- GitHub onkyo-eiscp: https://github.com/miracle2k/onkyo-eiscp
- Protocol Documentation: Official Onkyo ISCP/eISCP Protocol v1.21 (2011)
- eISCP Article: https://sudonull.com/post/9179-Onkyos-ISCP-eISCP-protocol-control-of-Onkyo-devices-over-the-network
- Home Assistant Integration: https://www.home-assistant.io/integrations/onkyo/
