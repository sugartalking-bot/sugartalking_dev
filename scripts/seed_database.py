"""
Database seeding script for Sugartalking.

This script populates the database with initial receiver models and commands,
starting with the Denon AVR-X2300W.
"""

import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import Receiver, Command, CommandParameter, init_db, get_session
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_denon_x2300w(session):
    """
    Seed database with Denon AVR-X2300W receiver and commands.

    Args:
        session: SQLAlchemy session
    """
    logger.info("Seeding Denon AVR-X2300W...")

    # Check if already exists
    existing = session.query(Receiver).filter_by(
        manufacturer='Denon',
        model='AVR-X2300W'
    ).first()

    if existing:
        logger.info("Denon AVR-X2300W already exists, skipping...")
        return existing

    # Create receiver
    receiver = Receiver(
        manufacturer='Denon',
        model='AVR-X2300W',
        protocol='http',
        default_port=80,
        description='Denon AVR-X2300W 7.2 Channel AV Receiver with HEOS'
    )
    session.add(receiver)
    session.flush()  # Get the receiver ID

    # Add power commands
    power_on = Command(
        receiver_id=receiver.id,
        action_type='power',
        action_name='power_on',
        endpoint='/MainZone/index.put.asp',
        http_method='GET',
        command_template='?cmd0=PutZone_OnOff/ON',
        description='Turn the receiver on (main zone)'
    )
    session.add(power_on)

    power_off = Command(
        receiver_id=receiver.id,
        action_type='power',
        action_name='power_off',
        endpoint='/MainZone/index.put.asp',
        http_method='GET',
        command_template='?cmd0=PutZone_OnOff/OFF',
        description='Turn the receiver off (standby mode)'
    )
    session.add(power_off)

    # Add volume commands
    volume_up = Command(
        receiver_id=receiver.id,
        action_type='volume',
        action_name='volume_up',
        endpoint='/goform/formiPhoneAppDirect.xml',
        http_method='GET',
        command_template='?MVUP',
        description='Increase volume by one step'
    )
    session.add(volume_up)

    volume_down = Command(
        receiver_id=receiver.id,
        action_type='volume',
        action_name='volume_down',
        endpoint='/goform/formiPhoneAppDirect.xml',
        http_method='GET',
        command_template='?MVDOWN',
        description='Decrease volume by one step'
    )
    session.add(volume_down)

    volume_set = Command(
        receiver_id=receiver.id,
        action_type='volume',
        action_name='volume_set',
        endpoint='/goform/formiPhoneAppDirect.xml',
        http_method='GET',
        command_template='?MV{level}',
        description='Set volume to specific level (00-98, where 00=-80dB, 98=+18dB)'
    )
    session.add(volume_set)
    session.flush()

    # Add parameter for volume_set
    volume_param = CommandParameter(
        command_id=volume_set.id,
        param_name='level',
        param_type='integer',
        required=True,
        min_value=0,
        max_value=98,
        description='Volume level (00-98, corresponds to -80dB to +18dB)'
    )
    session.add(volume_param)

    # Add mute commands
    mute_on = Command(
        receiver_id=receiver.id,
        action_type='mute',
        action_name='mute_on',
        endpoint='/MainZone/index.put.asp',
        http_method='GET',
        command_template='?cmd0=PutVolumeMute/on',
        description='Enable mute'
    )
    session.add(mute_on)

    mute_off = Command(
        receiver_id=receiver.id,
        action_type='mute',
        action_name='mute_off',
        endpoint='/MainZone/index.put.asp',
        http_method='GET',
        command_template='?cmd0=PutVolumeMute/off',
        description='Disable mute'
    )
    session.add(mute_off)

    mute_toggle = Command(
        receiver_id=receiver.id,
        action_type='mute',
        action_name='mute_toggle',
        endpoint='/goform/formiPhoneAppDirect.xml',
        http_method='GET',
        command_template='?MUON',
        description='Toggle mute on/off'
    )
    session.add(mute_toggle)

    # Add input selection commands
    input_sources = [
        ('CD', 'CD player'),
        ('DVD', 'DVD player'),
        ('BD', 'Blu-ray player'),
        ('TV', 'TV audio'),
        ('SAT/CBL', 'Satellite/Cable box'),
        ('MPLAY', 'Media player'),
        ('GAME', 'Game console'),
        ('TUNER', 'Radio tuner'),
        ('AUX1', 'Auxiliary input 1'),
        ('NET', 'Network/streaming'),
        ('BT', 'Bluetooth'),
    ]

    # Add generic change_input command with parameter
    change_input_cmd = Command(
        receiver_id=receiver.id,
        action_type='input',
        action_name='change_input',
        endpoint='/goform/formiPhoneAppDirect.xml',
        http_method='GET',
        command_template='?SI{input_source}',
        description='Change input source'
    )
    session.add(change_input_cmd)
    session.flush()

    # Add parameter for change_input
    input_param = CommandParameter(
        command_id=change_input_cmd.id,
        param_name='input_source',
        param_type='string',
        required=True,
        valid_values='CD,DVD,BD,TV,SAT/CBL,MPLAY,GAME,TUNER,AUX1,NET,BT',
        description='Input source identifier'
    )
    session.add(input_param)

    for source_id, description in input_sources:
        input_cmd = Command(
            receiver_id=receiver.id,
            action_type='input',
            action_name=f'input_{source_id.lower().replace("/", "_")}',
            endpoint='/goform/formiPhoneAppDirect.xml',
            http_method='GET',
            command_template=f'?SI{source_id}',
            description=f'Select input: {description}'
        )
        session.add(input_cmd)

    session.commit()
    logger.info(f"✓ Denon AVR-X2300W seeded with {len(receiver.commands)} commands")

    return receiver


def seed_additional_receivers(session):
    """
    Placeholder for seeding additional receiver models.

    This function demonstrates how to add more receivers in the future.
    """
    logger.info("Additional receivers can be added here in the future...")

    # Example structure for adding another receiver:
    # yamaha_rx = Receiver(
    #     manufacturer='Yamaha',
    #     model='RX-V685',
    #     protocol='http',
    #     default_port=80,
    #     description='Yamaha RX-V685 7.2 Channel AV Receiver'
    # )
    # session.add(yamaha_rx)
    # ... add commands ...


def main():
    """Main seeding function."""
    logger.info("=" * 60)
    logger.info("Sugartalking Database Seeding")
    logger.info("=" * 60)

    # Initialize database
    logger.info("Initializing database...")
    engine = init_db()
    session = get_session(engine)

    try:
        # Seed receivers
        seed_denon_x2300w(session)
        seed_additional_receivers(session)

        # Summary
        receiver_count = session.query(Receiver).count()
        command_count = session.query(Command).count()

        logger.info("=" * 60)
        logger.info(f"✓ Seeding complete!")
        logger.info(f"  Receivers: {receiver_count}")
        logger.info(f"  Commands: {command_count}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error seeding database: {str(e)}", exc_info=True)
        session.rollback()
        sys.exit(1)

    finally:
        session.close()


if __name__ == '__main__':
    main()
