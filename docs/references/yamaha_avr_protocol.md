# Yamaha AVR Control Protocol Documentation

**Manufacturer**: Yamaha
**Protocol Type**: HTTP + XML (MusicCast) / HTTP + JSON (Extended Control API)
**Source URLs**:
- https://github.com/cps5155/yamaha-receiver-api
- Yamaha Extended Control API Specification (Advanced)
- https://forum.smartapfel.de/attachment/4358-yamaha-musiccast-http-simplified-api-for-controlsystems-pdf/

---

## Protocol Overview

Yamaha receivers support multiple control protocols depending on model and feature set:

### Yamaha Extended Control API (YXC)
- Modern approach using HTTP and XML/JSON
- Used for MusicCast-enabled devices
- Supports both basic and advanced features
- Multiple simultaneous connections

### MusicCast API
- REST-based control
- JSON-formatted responses
- Simplified API for control system integration

---

## Connection Details

### HTTP Connection
```
Host: <receiver-ip>
Port: 80 (standard HTTP)
Protocol: HTTP with XML or JSON payloads
Content-Type: application/x-www-form-urlencoded or application/json
```

### API Endpoint Base
```
http://<receiver-ip>/YamahaExtendedControl/v1/
```

---

## API Endpoints

### System Control
- `GET /system` - Get system information
- `GET /system/getFeatures` - Get device features
- `GET /system/getNetworkStatus` - Get network information
- `POST /system/setDeviceName` - Set device name
- `POST /system/setAutoPowerStandby` - Configure standby settings

### Power Management
- `GET /main/getPower` - Query main zone power state
- `POST /main/setPower?power=on` - Power on
- `POST /main/setPower?power=standby` - Power standby
- `GET /zone2/getPower` - Query Zone 2 power
- `POST /zone2/setPower?power=on` - Zone 2 power on

### Volume Control
- `GET /main/getVolume` - Get current volume
- `POST /main/setVolume?volume=50` - Set volume (0-100)
- `GET /main/getMute` - Query mute state
- `POST /main/setMute?enable=true` - Mute on
- `POST /main/setMute?enable=false` - Mute off

### Input Selection
- `GET /main/getInput` - Get current input
- `POST /main/setInput?input=hdmi1` - Select HDMI 1
- `POST /main/setInput?input=hdmi2` - Select HDMI 2
- `POST /main/setInput?input=hdmi3` - Select HDMI 3
- `POST /main/setInput?input=hdmi4` - Select HDMI 4
- `POST /main/setInput?input=av1` - Select AV 1
- `POST /main/setInput?input=av2` - Select AV 2
- `POST /main/setInput?input=audio1` - Select Audio 1
- `POST /main/setInput?input=audio2` - Select Audio 2
- `POST /main/setInput?input=tuner` - Select Tuner
- `POST /main/setInput?input=netusb` - Select Net/USB
- `POST /main/setInput?input=spotify` - Select Spotify
- `POST /main/setInput?input=airplay` - Select AirPlay
- `GET /main/getInputList` - Get available inputs

### Scene Control
- `GET /main/getScene` - Get current scene
- `POST /main/setScene?scene=scene1` - Activate scene
- `GET /main/getSceneList` - Get available scenes

### Surround/Sound
- `GET /main/getSoundProgram` - Get sound program
- `POST /main/setSoundProgram?program=stereo` - Set sound mode
- `GET /main/getEQ` - Get EQ settings
- `POST /main/setEQ?enable=true` - Enable EQ

### Tuner
- `GET /tuner/getFreq` - Get current frequency
- `POST /tuner/setFreq?freq=103.5` - Tune to frequency
- `GET /tuner/getPresetInfo` - Get preset information

### NetUSB (Network Audio)
- `GET /netusb/getPlayInfo` - Get playback information
- `POST /netusb/setPlayback?playback=play` - Play
- `POST /netusb/setPlayback?playback=pause` - Pause
- `POST /netusb/setPlayback?playback=stop` - Stop
- `POST /netusb/setPlayback?playback=next` - Next track
- `POST /netusb/setPlayback?playback=previous` - Previous track

---

## XML Message Format (Legacy)

### Volume Command Example
```xml
<?xml version="1.0" encoding="UTF-8"?>
<YAMAHA_AV>
  <Main_Zone>
    <Basic_Status>
      <Master_Volume>
        <Lvl Val="-50.0"/>
      </Master_Volume>
    </Basic_Status>
  </Main_Zone>
</YAMAHA_AV>
```

### Input Selection
```xml
<?xml version="1.0" encoding="UTF-8"?>
<YAMAHA_AV>
  <Main_Zone>
    <Basic_Status>
      <Input_Selector>
        <Sel>HDMI1</Sel>
      </Input_Selector>
    </Basic_Status>
  </Main_Zone>
</YAMAHA_AV>
```

---

## JSON Response Format (Modern)

### Power Status Response
```json
{
  "main": {
    "power": "on"
  }
}
```

### Volume Response
```json
{
  "main": {
    "volume": 50,
    "mute": false
  }
}
```

### Input Response
```json
{
  "main": {
    "input": "hdmi1"
  }
}
```

---

## Connection Example

### Python Example (HTTP + JSON)
```python
import requests

BASE_URL = "http://192.168.1.100/YamahaExtendedControl/v1"

# Power on
response = requests.post(f"{BASE_URL}/main/setPower?power=on")
print(response.status_code)

# Get volume
response = requests.get(f"{BASE_URL}/main/getVolume")
volume_data = response.json()
print(f"Current volume: {volume_data['main']['volume']}")

# Set volume to 60
response = requests.post(f"{BASE_URL}/main/setVolume?volume=60")

# Switch to HDMI 1
response = requests.post(f"{BASE_URL}/main/setInput?input=hdmi1")

# Mute
response = requests.post(f"{BASE_URL}/main/setMute?enable=true")

# Get current input
response = requests.get(f"{BASE_URL}/main/getInput")
input_data = response.json()
print(f"Current input: {input_data['main']['input']}")
```

### JavaScript (Node.js) Example
```javascript
const axios = require('axios');

const BASE_URL = 'http://192.168.1.100/YamahaExtendedControl/v1';

// Power on
await axios.post(`${BASE_URL}/main/setPower?power=on`);

// Get volume
const volumeResponse = await axios.get(`${BASE_URL}/main/getVolume`);
console.log(`Current volume: ${volumeResponse.data.main.volume}`);

// Set volume
await axios.post(`${BASE_URL}/main/setVolume?volume=60`);

// Select input
await axios.post(`${BASE_URL}/main/setInput?input=hdmi1`);

// Query current input
const inputResponse = await axios.get(`${BASE_URL}/main/getInput`);
console.log(`Current input: ${inputResponse.data.main.input}`);

// Mute
await axios.post(`${BASE_URL}/main/setMute?enable=true`);
```

---

## Available Input Sources

Common input source identifiers:

| Input | ID | Notes |
|-------|----|----|
| HDMI 1 | `hdmi1` | |
| HDMI 2 | `hdmi2` | |
| HDMI 3 | `hdmi3` | |
| HDMI 4 | `hdmi4` | |
| HDMI 5 | `hdmi5` | |
| HDMI 6 | `hdmi6` | |
| AV 1 | `av1` | Composite video |
| AV 2 | `av2` | Composite video |
| Audio 1 | `audio1` | Stereo audio |
| Audio 2 | `audio2` | Stereo audio |
| Tuner | `tuner` | AM/FM radio |
| Net/USB | `netusb` | Network audio services |
| Spotify | `spotify` | Spotify Connect |
| AirPlay | `airplay` | Apple AirPlay |
| MusicCast Link | `musiccast` | Yamaha MusicCast |

---

## Sound Programs

Available sound modes vary by model but typically include:

- `stereo` - Stereo reproduction
- `dolby_digital` - Dolby Digital
- `dts` - DTS surround
- `pcm_stereo` - PCM Stereo
- `surround_decoder` - Surround decoder
- `thx` - THX processing
- `dolby_surround` - Dolby Surround
- `neo6_cinema` - Neo:6 Cinema
- `neo6_music` - Neo:6 Music
- `dts_es` - DTS-ES
- `thx_cinema` - THX Cinema
- `thx_music` - THX Music

---

## Important Notes

1. **Protocol Variation**: Support for XML vs JSON depends on receiver model and firmware version
2. **Zone Support**: Main zone always supported; Zone 2/3 support varies by model
3. **Input Availability**: Available inputs depend on specific AVR model
4. **MusicCast ID**: Devices may require MusicCast ID (mcid) for certain operations
5. **Response Times**: Allow 100-500ms for command processing
6. **Status Polling**: Avoid excessive polling; use event notifications where available

---

## Supported Models

Yamaha Extended Control API support varies by series and firmware version:

- RX-V series (RX-V479, RX-V579, RX-V681, RX-V781, RX-V977, RX-V1, RX-V1A, RX-V2A)
- RX-A series (RX-A680, RX-A780, RX-A860, RX-A960, RX-A1060, RX-A2060, RX-A3060)
- TSR series (TSR-5810, TSR-6810, TSR-7810)
- MusicCast enabled amplifiers (WXA-50, A-S201)

---

## Recommended Libraries

- **Node.js**: `yamaha-receiver-api` - REST API wrapper
- **Node.js**: `yamaha-http` - HTTP control library
- **Python**: `pyyamaha` - Python Yamaha control
- **Home Assistant**: Built-in Yamaha integration

---

## References

- Yamaha Extended Control API: https://community.symcon.de/
- MusicCast API Documentation: https://forum.smartapfel.de/
- GitHub REST API Implementation: https://github.com/cps5155/yamaha-receiver-api
- Yamaha Official Support: https://support.yamaha.com
