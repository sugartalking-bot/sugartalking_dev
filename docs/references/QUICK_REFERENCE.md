# AVR Control Protocol - Quick Reference

## Connection Strings

### Denon AVR-X2300W (Recommended for this project)
```
Telnet: telnet 192.168.1.<ip> 23
HTTP:   http://192.168.1.<ip>
```

### Other Common Receivers
```
Yamaha:   http://192.168.1.<ip>/YamahaExtendedControl/v1/
Onkyo:    telnet 192.168.1.<ip> 60128
Marantz:  telnet 192.168.1.<ip> 23
Pioneer:  telnet 192.168.1.<ip> 8102
```

---

## Most Common Commands by Manufacturer

### Denon / Marantz
```
PWON            Power On
PWSTANDBY       Power Off
MVUP / MVDOWN   Volume Up/Down
MV50            Set Volume to 50
MUON / MUOFF    Mute On/Off
SIDVD           Select DVD Input
SITUNER         Select Tuner Input
SI?             Query Current Input
PW?             Query Power State
```

### Yamaha
```
POST /main/setPower?power=on
POST /main/setPower?power=standby
POST /main/setVolume?volume=50
GET  /main/getVolume
POST /main/setInput?input=hdmi1
GET  /main/getInput
POST /main/setMute?enable=true
```

### Onkyo (eISCP)
```python
receiver.power = 'on'
receiver.power = 'off'
receiver.volume = 30
receiver.input = 'hdmi1'
receiver.mute = 'on'
print(receiver.power)
```

### Pioneer
```
PO              Power On
PF              Power Off
VU / VD         Volume Up/Down
19FN            Select HDMI 1 (source code 19)
?V              Query Volume (returns VOLnnn)
?F              Query Input
?M              Query Mute Status
```

---

## Volume Reference

| Manufacturer | Min | Reference (0 dB) | Max | Type |
|---|---|---|---|---|
| Denon/Marantz | 0 | 80 | 98 | ASCII scale |
| Yamaha | 0 | Varies | 100 | Percentage |
| Onkyo | 0x00 | 0x60 | 0x60 | Hexadecimal |
| Pioneer | 0 | Varies | 131 | Relative |

---

## Input Code Reference

### Denon / Marantz
```
SICD      CD
SIDVD     DVD
SIBD      Blu-ray
SITUNER   Tuner
SITV      TV
SIBT      Bluetooth
SINET/USB Net/USB
```

### Pioneer Source IDs
```
00  Phono
01  CD
02  Tuner
04  DVD
05  TV
19  HDMI 1
20  HDMI 2
21  HDMI 3
22  HDMI 4
25  Blu-ray
38  Internet Radio
53  Spotify
```

### Yamaha
```
hdmi1     HDMI 1
hdmi2     HDMI 2
hdmi3     HDMI 3
tuner     Tuner
netusb    Net/USB
spotify   Spotify
airplay   AirPlay
```

### Onkyo (eISCP)
```
phono          Phono
cd             CD
tuner          Tuner
net-usb        Net/USB
hdmi1-8        HDMI inputs
av1-3          Composite A/V
bluetooth      Bluetooth
```

---

## Python Connection Examples

### Denon (Telnet)
```python
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('192.168.1.100', 23))
sock.send(b'PWON\r\n')
response = sock.recv(1024)
print(response)  # b'PWON\r\n'
sock.close()
```

### Pioneer (Telnet)
```python
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('192.168.1.100', 8102))
sock.send(b'PO\r\n')
response = sock.recv(1024)
print(response)  # b'PO\r\n'
sock.close()
```

### Onkyo (eISCP)
```python
from onkyoeiscp import Receiver

receiver = Receiver('192.168.1.100')
receiver.power = 'on'
receiver.input = 'hdmi1'
receiver.volume = 30
print(receiver.power)
receiver.close()
```

### Yamaha (HTTP)
```python
import requests

url = 'http://192.168.1.100/YamahaExtendedControl/v1'

# Power on
requests.post(f'{url}/main/setPower?power=on')

# Set volume
requests.post(f'{url}/main/setVolume?volume=50')

# Get current input
response = requests.get(f'{url}/main/getInput')
print(response.json())
```

---

## JavaScript/Node.js Examples

### Denon (Telnet)
```javascript
const net = require('net');

const client = new net.Socket();
client.connect(23, '192.168.1.100', () => {
  client.write('PWON\r\n');
});

client.on('data', (data) => {
  console.log(data.toString());
  client.destroy();
});
```

### Pioneer (Telnet)
```javascript
const net = require('net');

const client = new net.Socket();
client.connect(8102, '192.168.1.100', () => {
  client.write('PO\r\n');
});

client.on('data', (data) => {
  console.log(data.toString());
});
```

### Yamaha (HTTP)
```javascript
const axios = require('axios');

const base = 'http://192.168.1.100/YamahaExtendedControl/v1';

// Power on
axios.post(`${base}/main/setPower?power=on`);

// Set volume
axios.post(`${base}/main/setVolume?volume=50`);

// Get volume
axios.get(`${base}/main/getVolume`)
  .then(res => console.log(res.data));
```

---

## Important Settings

### Denon / Marantz
- [ ] Enable "Network Control" in receiver settings
- [ ] Set to "Always On" to ensure control in standby
- [ ] Single connection on port 23 (use HTTP for multiple)

### Yamaha
- [ ] Enable network control
- [ ] Verify port 80 HTTP access
- [ ] Supports multiple simultaneous connections

### Onkyo
- [ ] Enable "Setup → Hardware → Network → Network Control"
- [ ] Required for standby control
- [ ] Port 60128 must be accessible

### Pioneer
- [ ] Default settings usually work
- [ ] May need to enable network control for standby
- [ ] Monitor port 8102 for status broadcasts

---

## Debugging Checklist

### Connection Issues
- [ ] Correct IP address? (`ping 192.168.1.100`)
- [ ] Correct port? (23 for Denon/Marantz, 8102 for Pioneer, 60128 for Onkyo, 80 for Yamaha)
- [ ] Network control enabled in receiver?
- [ ] Firewall blocking connection?
- [ ] Receiver powered on?

### Command Not Working
- [ ] Commands uppercase only? (for telnet protocols)
- [ ] CRLF termination included? (`\r\n`)
- [ ] Correct parameter format?
- [ ] Single connection limit exceeded? (telnet)
- [ ] Syntax matches documentation?

### Volume Not Changing
- [ ] Correct volume scale for manufacturer?
- [ ] Parameter in valid range?
- [ ] Mute status preventing changes?
- [ ] Zone specified correctly?

---

## Testing Commands

### Test Power (all telnet-based)
```bash
# Denon/Marantz
echo -e "PW?" | nc 192.168.1.100 23

# Pioneer
echo -e "?P" | nc 192.168.1.100 8102

# Onkyo (requires binary wrapper - use library)
python -c "from onkyoeiscp import Receiver; r=Receiver('192.168.1.100'); print(r.power)"
```

### Test HTTP (Yamaha)
```bash
curl http://192.168.1.100/YamahaExtendedControl/v1/main/getVolume
```

---

## Recommended Libraries

### Python
- **Denon/Marantz**: Custom socket or `aiomadeavr`
- **Pioneer**: `aiopioneer` (asyncio)
- **Onkyo**: `onkyo-eiscp`
- **Yamaha**: `requests` + custom HTTP

### Node.js
- **Denon**: `denon-avr`
- **Marantz**: `marantz-denon-telnet`
- **Pioneer**: Custom socket or community wrapper
- **Yamaha**: `yamaha-receiver-api`

### Home Assistant
- All manufacturers have built-in integrations
- Configuration examples available in integration docs

---

## Common Pitfalls

1. **Port confusion**: Pioneer uses 8102 (not 23), Onkyo uses 60128
2. **Volume scale**: Each manufacturer uses different scale (0-98, 0-100, 0-131, etc.)
3. **CRLF termination**: Required for telnet; HTTP methods use JSON
4. **Single connection**: Denon/Marantz port 23 only allows one client at a time
5. **Network control**: Must be explicitly enabled, especially for standby control
6. **Input naming**: Different manufacturers use different input codes/names
7. **Capitalization**: Telnet commands uppercase only

---

## Performance Tips

- **Reuse connections**: Keep socket open rather than reconnect for each command
- **Add delays**: 100-200ms between rapid commands to allow processing
- **Use HTTP for concurrent**: When multiple simultaneous commands needed
- **Batch operations**: Combine related commands in single connection
- **Monitor broadcasts**: Pioneer broadcasts status ~every 30 seconds

---

For complete protocol specifications, see the individual documentation files in this directory.
