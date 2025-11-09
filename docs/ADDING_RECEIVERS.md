# Adding New Receiver Models to Sugartalking

This guide explains how to add support for new AVR receiver models to the Sugartalking system.

## Overview

Sugartalking uses a database-driven architecture where receiver commands are stored in the database rather than hardcoded. This makes it easy to add new receiver models without changing the application code.

## Prerequisites

- Access to the receiver's API documentation or protocol specification
- Ability to test commands against the physical receiver
- Basic knowledge of SQL or Python

## Step-by-Step Guide

### 1. Research the Receiver's API

Gather the following information:

- **Manufacturer**: e.g., "Denon", "Yamaha", "Onkyo"
- **Model**: e.g., "AVR-X2300W", "RX-V685"
- **Protocol**: http, https, telnet, serial, etc.
- **Default Port**: Usually 80 for HTTP, 23 for telnet
- **API Endpoints**: Where commands are sent
- **Command Format**: How commands are structured
- **Available Commands**: List of all supported operations

### 2. Test Commands Manually

Before adding to the database, test commands manually:

```bash
# Example for HTTP-based receiver
curl "http://192.168.1.182/MainZone/index.put.asp?cmd0=PutZone_OnOff/ON"

# Example for telnet-based receiver
telnet 192.168.1.182 23
# Then send commands according to protocol
```

Document which commands work and their exact format.

### 3. Add Receiver to Database

#### Option A: Using Python Script (Recommended)

Create a new seeding script in `scripts/seed_<manufacturer>_<model>.py`:

```python
"""
Seed script for <Manufacturer> <Model>
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import Receiver, Command, CommandParameter, init_db, get_session
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_receiver(session):
    """Seed the receiver and its commands."""

    # Create receiver
    receiver = Receiver(
        manufacturer='<Manufacturer>',
        model='<Model>',
        protocol='http',  # or telnet, serial, etc.
        default_port=80,
        description='<Full description of receiver>'
    )
    session.add(receiver)
    session.flush()

    # Add power on command
    power_on = Command(
        receiver_id=receiver.id,
        action_type='power',
        action_name='power_on',
        endpoint='/path/to/endpoint',
        http_method='GET',
        command_template='?cmd=POWER_ON',  # Adjust based on your protocol
        description='Turn the receiver on'
    )
    session.add(power_on)

    # Add power off command
    power_off = Command(
        receiver_id=receiver.id,
        action_type='power',
        action_name='power_off',
        endpoint='/path/to/endpoint',
        http_method='GET',
        command_template='?cmd=POWER_OFF',
        description='Turn the receiver off'
    )
    session.add(power_off)

    # Add more commands as needed...

    session.commit()
    logger.info(f"✓ {receiver.manufacturer} {receiver.model} seeded successfully")


if __name__ == '__main__':
    engine = init_db()
    session = get_session(engine)
    try:
        seed_receiver(session)
    finally:
        session.close()
```

Run the script:
```bash
python scripts/seed_<manufacturer>_<model>.py
```

#### Option B: Using SQL Directly

Connect to the database:
```bash
sqlite3 /data/sugartalking.db
```

Insert the receiver:
```sql
INSERT INTO receivers (manufacturer, model, protocol, default_port, description)
VALUES ('Yamaha', 'RX-V685', 'http', 80, 'Yamaha RX-V685 7.2 Channel AV Receiver');
```

Get the receiver ID:
```sql
SELECT id FROM receivers WHERE model = 'RX-V685';
-- Let's say it returns 2
```

Insert commands:
```sql
INSERT INTO commands (receiver_id, action_type, action_name, endpoint, http_method, command_template, description)
VALUES
(2, 'power', 'power_on', '/YamahaRemoteControl/ctrl', 'POST', '<YAMAHA_AV cmd="PUT"><Main_Zone><Power_Control><Power>On</Power></Power_Control></Main_Zone></YAMAHA_AV>', 'Power on'),
(2, 'power', 'power_off', '/YamahaRemoteControl/ctrl', 'POST', '<YAMAHA_AV cmd="PUT"><Main_Zone><Power_Control><Power>Standby</Power></Power_Control></Main_Zone></YAMAHA_AV>', 'Power off');
```

#### Option C: Using Admin Panel

1. Access the admin panel at `http://localhost:5000/admin`
2. (Future feature) Use the web UI to add receivers and commands

### 4. Add Commands with Parameters

For commands that take parameters (like volume level or input selection):

```python
# Create the command
volume_set = Command(
    receiver_id=receiver.id,
    action_type='volume',
    action_name='volume_set',
    endpoint='/MainZone/index.put.asp',
    http_method='GET',
    command_template='?cmd0=PutMasterVolumeSet/{level}',
    description='Set volume to specific level'
)
session.add(volume_set)
session.flush()

# Add parameter definition
volume_param = CommandParameter(
    command_id=volume_set.id,
    param_name='level',
    param_type='integer',
    required=True,
    min_value=-80,
    max_value=18,
    description='Volume level in dB'
)
session.add(volume_param)
```

The `{level}` in the command template will be replaced with the actual value when the command is executed.

### 5. Test the New Receiver

#### Via API:

```bash
# List available commands
curl http://localhost:5000/api/commands/RX-V685

# Test power on
curl -X POST http://localhost:5000/api/power/on \
  -H "Content-Type: application/json" \
  -d '{"receiver_ip": "192.168.1.100", "receiver_model": "RX-V685"}'
```

#### Via Admin Panel:

1. Go to `http://localhost:5000/admin`
2. Verify the receiver appears in the list
3. Check that all commands are present

### 6. Document the Receiver

Update this file with information about the new receiver:

```markdown
## Supported Receivers

### Denon AVR-X2300W
- Protocol: HTTP
- Port: 80
- Commands: Power, Volume, Input, Mute
- Documentation: [Denon Control Protocol](...)

### Yamaha RX-V685
- Protocol: HTTP (XML-based)
- Port: 80
- Commands: Power, Volume, Input, Sound Modes
- Documentation: [Yamaha YNC Protocol](...)
```

## Command Types

Standard action types for consistency:

- `power`: Power on/off
- `volume`: Volume control (up, down, set, mute)
- `input`: Input source selection
- `sound_mode`: Sound mode/preset selection
- `zone`: Multi-zone control
- `tuner`: Radio tuner control
- `network`: Network/streaming functions
- `display`: Display settings
- `custom`: Manufacturer-specific features

## Parameter Types

Supported parameter types:

- `string`: Text values
- `integer`: Whole numbers
- `float`: Decimal numbers
- `boolean`: true/false
- `enum`: Fixed set of values (use `valid_values` field)

## Common Protocols

### HTTP GET with Query Parameters
```python
endpoint='/control/command',
http_method='GET',
command_template='?action={action}&value={value}'
```

### HTTP POST with XML Body
```python
endpoint='/control',
http_method='POST',
command_template='<Command><Action>{action}</Action><Value>{value}</Value></Command>'
```

### HTTP POST with JSON Body
```python
endpoint='/api/command',
http_method='POST',
command_template='{"action": "{action}", "value": {value}}'
```

## Troubleshooting

### Command Not Working

1. Test the command manually with `curl` or browser
2. Check logs: `kubectl logs -l app=sugartalking -f`
3. Verify the receiver is reachable on the network
4. Check the command template for typos
5. Ensure parameter placeholders match parameter names

### Receiver Not Auto-Detected

1. Verify the receiver advertises via mDNS
2. Check if the receiver responds to HTTP probes
3. Update `_identify_receiver()` in `app/services/discovery.py`

### Adding Custom Identification Logic

Edit `app/services/discovery.py`:

```python
def _identify_receiver(self, ip: str, port: int) -> Optional[int]:
    # Your custom detection logic
    response = requests.get(f"http://{ip}:{port}/device_info")
    if 'YourManufacturer' in response.text:
        model = extract_model_from_response(response.text)
        receiver = self.session.query(Receiver).filter_by(
            manufacturer='YourManufacturer',
            model=model
        ).first()
        if receiver:
            return receiver.id
    return None
```

## Contributing

If you add support for a new receiver model, consider contributing it back:

1. Create a seed script in `scripts/`
2. Update this documentation
3. Test thoroughly
4. Submit a pull request

## Getting Help

If you need help adding a receiver:

1. Check existing seed scripts in `scripts/` for examples
2. Consult the receiver's API documentation
3. Ask on GitHub Issues
4. Use the Claude AI prompt guide in `docs/CONTEXT_PROMPT.md`

---

## Example: Complete Receiver Addition

Here's a complete example for adding a fictional "Onkyo TX-NR696":

```python
# scripts/seed_onkyo_txnr696.py

from app.models import Receiver, Command, CommandParameter, init_db, get_session

def seed_onkyo_txnr696(session):
    receiver = Receiver(
        manufacturer='Onkyo',
        model='TX-NR696',
        protocol='http',
        default_port=60128,
        description='Onkyo TX-NR696 7.2 Channel Network AV Receiver'
    )
    session.add(receiver)
    session.flush()

    # Power commands
    commands = [
        Command(receiver_id=receiver.id, action_type='power', action_name='power_on',
                endpoint='/eiscp/command', http_method='POST',
                command_template='PWR01', description='Power on'),

        Command(receiver_id=receiver.id, action_type='power', action_name='power_off',
                endpoint='/eiscp/command', http_method='POST',
                command_template='PWR00', description='Power off'),

        Command(receiver_id=receiver.id, action_type='volume', action_name='volume_up',
                endpoint='/eiscp/command', http_method='POST',
                command_template='MVLUP', description='Volume up'),

        Command(receiver_id=receiver.id, action_type='volume', action_name='volume_down',
                endpoint='/eiscp/command', http_method='POST',
                command_template='MVLDOWN', description='Volume down'),
    ]

    for cmd in commands:
        session.add(cmd)

    session.commit()
    print(f"✓ Onkyo TX-NR696 added successfully!")

if __name__ == '__main__':
    engine = init_db()
    session = get_session(engine)
    try:
        seed_onkyo_txnr696(session)
    finally:
        session.close()
```

Run it:
```bash
python scripts/seed_onkyo_txnr696.py
```

That's it! The receiver is now fully integrated.
