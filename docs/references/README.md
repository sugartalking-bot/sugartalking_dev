# AVR Receiver Control Protocol Documentation Index

This directory contains comprehensive technical documentation for controlling various AV receiver models via network protocols. Each file includes command specifications, connection methods, code examples, and integration recommendations.

---

## Quick Reference Table

| Manufacturer | Model(s) | Protocol | Port | Recommended | Status |
|---|---|---|---|---|---|
| **Denon** | AVR-X2300W, X-series, S-series | Telnet / HTTP | 23 / 80 | ✓ | Complete |
| **Marantz** | SR5000-SR8000 series, NR-series | Telnet / HTTP | 23 / 80 | ✓ | Complete |
| **Yamaha** | RX-V/A-series, TSR-series | HTTP + XML/JSON | 80 | ✓ | Complete |
| **Onkyo** | TX-NR series, Integra | eISCP | 60128 | ✓ | Complete |
| **Pioneer** | VSX-series, Elite SC-series | Telnet | 8102 | ✓ | Complete |

---

## Documentation Files

### Denon AVR Protocol
**File**: `denon_avr_protocol.md`
- **Manufacturer**: Denon
- **Primary Model**: AVR-X2300W
- **Protocol Type**: Telnet (Port 23) / HTTP (Port 80)
- **Connection Method**: ASCII commands with CRLF termination
- **Status Feedback**: Yes - all commands return responses
- **Multi-Zone Support**: Yes (Zone 2, Zone 3)
- **Key Features**:
  - Single connection limit on Telnet (23)
  - Multiple connections supported via HTTP
  - Volume control: 0-98 scale (80 = 0 dB)
  - Input selection: CD, DVD, Tuner, HDMI, Bluetooth, USB, etc.
  - Sound processing: Cinema EQ, Dynamic Volume, Panorama
  - Zone control for multi-zone receivers
- **Recommended Use**: Best choice for modern Denon receivers
- **Supported Libraries**: `denon-avr` (npm), `denonavr` (Python), Home Assistant integration

---

### Yamaha AVR Protocol
**File**: `yamaha_avr_protocol.md`
- **Manufacturer**: Yamaha
- **Protocol Type**: HTTP + XML (legacy) / HTTP + JSON (modern)
- **Port**: 80 (HTTP)
- **API Endpoint**: `/YamahaExtendedControl/v1/`
- **Multi-Zone Support**: Yes (Main, Zone 2, Zone 3)
- **Status Feedback**: JSON/XML responses
- **Key Features**:
  - Yamaha Extended Control API (YXC) for modern devices
  - MusicCast integration support
  - Volume: 0-100 scale
  - Multiple simultaneous connections supported
  - Input selection: HDMI 1-6, AV 1-2, Tuner, NetUSB, Spotify, AirPlay
  - Scene control for preset configurations
  - Surround mode selection
  - Tuner FM/AM control
- **Recommended Use**: Primary method for modern Yamaha receivers (RX-V/RX-A series)
- **Supported Libraries**: `yamaha-receiver-api` (npm), `pyyamaha` (Python), Home Assistant integration

---

### Onkyo eISCP Protocol
**File**: `onkyo_eiscp_protocol.md`
- **Manufacturer**: Onkyo / Integra
- **Protocol Type**: eISCP (Extended Integra Serial Control Protocol)
- **Port**: 60128 (TCP)
- **Connection Method**: Binary packet wrapper around ISCP messages
- **Multi-Zone Support**: Yes (Zones 1-3 via device codes)
- **Status Feedback**: Yes - command echoing and parameter responses
- **Key Features**:
  - eISCP packet format with binary wrapper
  - ISCP command structure: `!<device><command><parameter>`
  - Support for both hexadecimal and XML parameters
  - Power control, volume, mute, input selection
  - Listening mode selection (Stereo, DTS, Dolby Surround, etc.)
  - Network control must be enabled in settings
  - Discovery mechanism available
- **Recommended Use**: Best for Onkyo/Integra receivers, most documented protocol
- **Supported Libraries**: `onkyo-eiscp` (Python) - recommended, multiple Java implementations, Home Assistant integration

---

### Marantz Telnet Protocol
**File**: `marantz_denon_telnet_protocol.md`
- **Manufacturer**: Marantz
- **Model Series**: SR5000-SR8000, NR-series, AV-series
- **Protocol Type**: Telnet (Port 23) / HTTP (Port 80) / RS-232
- **Connection Method**: ASCII commands with CRLF termination
- **Multi-Zone Support**: Yes (Zone 2, Zone 3)
- **Status Feedback**: Yes - command confirmation responses
- **Key Features**:
  - Identical to Denon protocol (shared engineering)
  - Single connection on Port 23
  - Volume: 0-98 scale (80 = 0 dB reference)
  - Input selection: CD, DVD, Tuner, HDMI, Bluetooth, Net/USB
  - Sound processing: Cinema EQ, Dynamic Volume, Dynamic EQ, Panorama
  - RS-232 serial control available (legacy)
  - HTTP control (undocumented)
- **Recommended Use**: For Marantz receivers, particularly SR series
- **Supported Libraries**: `marantz-denon-telnet` (npm), `aiomadeavr` (Python), Home Assistant integration

---

### Pioneer AVR Protocol
**File**: `pioneer_avr_protocol.md`
- **Manufacturer**: Pioneer
- **Model Series**: VSX-529 through VSX-1231, Elite SC-series
- **Protocol Type**: Telnet (Port 8102) / HTTP (undocumented) / RS-232
- **Connection Method**: ASCII commands with CRLF termination
- **Multi-Zone Support**: Yes (Zone 2, Zone 3 variants)
- **Status Feedback**: Yes - response confirmation and status broadcasts
- **Key Features**:
  - Port 8102 (non-standard telnet)
  - Persistent socket connection recommended
  - Volume: 0-131 relative scale
  - Extensive HDMI input support (up to 8 HDMI ports)
  - Listening mode selection (Stereo, Dolby, DTS, Neo:6, etc.)
  - Source ID encoding (19-25 for HDMI, 38 for Internet Radio, 53 for Spotify)
  - Ready signal broadcast every 30 seconds
  - Network control disabled in standby by default
- **Recommended Use**: For Pioneer receivers, port 8102 is native protocol
- **Supported Libraries**: `aiopioneer` (Python asyncio), multiple npm wrappers, Home Assistant integration

---

## Protocol Comparison

### Connection Methods

| Protocol | Port | Type | Single Connection Limit | Feedback |
|---|---|---|---|---|
| Denon Telnet | 23 | Socket | Yes | Immediate |
| Denon HTTP | 80 | HTTP | No | Periodic (10s) |
| Yamaha | 80 | HTTP | No | JSON/XML |
| Onkyo eISCP | 60128 | TCP Binary | No | Command echo |
| Marantz Telnet | 23 | Socket | Yes | Immediate |
| Pioneer Telnet | 8102 | Socket | No | Status broadcast |

### Command Structure Comparison

| Manufacturer | Command Format | Parameter Type | Encoding |
|---|---|---|---|
| Denon | `<CMD><PARAM>` | ASCII | ASCII strings |
| Yamaha | HTTP GET/POST | JSON/XML | URL parameters |
| Onkyo | `!<DEVICE><CMD><PARAM>` | Hex/XML | Mixed |
| Marantz | `<CMD><PARAM>` | ASCII | ASCII strings |
| Pioneer | `<CMD><PARAM>` | ASCII | ASCII strings |

### Volume Control

| Manufacturer | Scale | Reference | Min | Max |
|---|---|---|---|---|
| Denon | 0-98 | 80 = 0 dB | 0 (-80 dB) | 98 (+18 dB) |
| Yamaha | 0-100 | Variable | 0 | 100 |
| Onkyo | 0-96 (hex) | 60 (0 dB) | 00 | 60 |
| Marantz | 0-98 | 80 = 0 dB | 0 (-80 dB) | 98 (+18 dB) |
| Pioneer | 0-131 | Relative | 0 | 131 |

---

## Implementation Recommendations

### For Custom Control Application

1. **If targeting Denon AVR-X2300W specifically**:
   - Use Denon Telnet protocol (port 23)
   - Reference: `denon_avr_protocol.md`
   - Recommended library: `denon-avr` npm package or custom socket implementation

2. **For multiple manufacturer support**:
   - Implement separate drivers for each protocol
   - Use abstraction layer for common operations (power, volume, input)
   - Consider: `denon-avr` (Denon), `aiopioneer` (Pioneer), `onkyo-eiscp` (Onkyo)

3. **For flexibility and future expansion**:
   - Implement telnet-based control (Denon, Marantz, Pioneer share ASCII format)
   - Add HTTP layer for Yamaha support
   - Plan for eISCP support for Onkyo

### Recommended Libraries by Language

**Python**:
- Denon/Marantz: Custom socket implementation or `aiomadeavr`
- Pioneer: `aiopioneer` (asyncio recommended)
- Onkyo: `onkyo-eiscp` (most feature-complete)
- Yamaha: Custom HTTP requests or `pyyamaha`

**JavaScript/Node.js**:
- Denon: `denon-avr` npm package
- Marantz: `marantz-denon-telnet`
- Pioneer: Custom socket implementation or community wrappers
- Yamaha: `yamaha-receiver-api`
- Onkyo: Community implementations available

**Home Assistant**:
- Built-in integrations available for all manufacturers
- Use via `custom_components` if needed

---

## Network Configuration Requirements

### Denon / Marantz
- Enable "Network Control" setting (set to "Always On")
- Port 23 for telnet or port 80 for HTTP
- Telnet single-connection limitation; use HTTP for multiple clients

### Yamaha
- Enable network control in receiver settings
- Port 80 HTTP access
- Supports multiple simultaneous connections

### Onkyo
- Enable "Setup → Hardware → Network → Network Control"
- Critical for standby mode control
- Port 60128 TCP

### Pioneer
- Network control typically enabled by default
- Port 8102 for telnet protocol
- Standby network control may need configuration
- Monitor port 8102 for ready signal broadcasts

---

## Testing Connectivity

### Quick Telnet Test (Denon/Marantz/Pioneer)

```bash
# Denon/Marantz (port 23)
telnet 192.168.1.100 23
> PW?
< PWON  (or PWSTANDBY)

# Pioneer (port 8102)
telnet 192.168.1.100 8102
> ?P
< PWR0  (or PWR2)
```

### HTTP Test (Yamaha)

```bash
# Query volume
curl -s http://192.168.1.100/YamahaExtendedControl/v1/main/getVolume

# Power on
curl -s -X POST http://192.168.1.100/YamahaExtendedControl/v1/main/setPower?power=on
```

### eISCP Test (Onkyo)

```python
from onkyoeiscp import Receiver

receiver = Receiver('192.168.1.100')
print(receiver.power)  # Check if connection works
```

---

## Additional Resources

### Official Documentation Sources
- Denon: https://manuals.denon.com/
- Yamaha: https://support.yamaha.com/
- Onkyo: https://support.onkyo.com/
- Marantz: https://support.marantz.com/
- Pioneer: https://www.pioneerelectronics.com/

### Home Automation Integrations
- Home Assistant: Built-in integrations for all manufacturers
- OpenHAB: Denon/Marantz binding available
- Homey: Support for Denon and others
- Pimatic: Community plugins available

### Community Projects
- **Denon**: https://github.com/bencouture/denon-rest-api
- **Onkyo**: https://github.com/miracle2k/onkyo-eiscp
- **Pioneer**: https://github.com/crowbarz/aiopioneer
- **Marantz**: https://github.com/k3erg/marantz-denon-telnet
- **Yamaha**: https://github.com/cps5155/yamaha-receiver-api

---

## Document Maintenance

These documents are based on:
- Official manufacturer protocols (where publicly available)
- Community reverse-engineered specifications
- Real-world implementation experience
- Open-source library documentation

Last updated: 2025-11-14

---

## Contributing

When adding new receiver models or protocols:
1. Create new markdown file: `{manufacturer}_{model}_protocol.md`
2. Follow the structure of existing documentation
3. Include: URL sources, protocol type, port, command reference, code examples
4. Update this README with summary information
