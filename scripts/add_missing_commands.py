"""
Add missing commands to existing Denon AVR-X2300W receiver.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import Receiver, Command, CommandParameter, get_session
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_missing_commands():
    """Add mute_toggle and change_input commands."""
    session = get_session()

    try:
        # Find the receiver
        receiver = session.query(Receiver).filter_by(model='AVR-X2300W').first()
        if not receiver:
            logger.error("AVR-X2300W receiver not found in database")
            return

        # Check if mute_toggle already exists
        existing_mute = session.query(Command).filter_by(
            receiver_id=receiver.id,
            action_name='mute_toggle'
        ).first()

        if not existing_mute:
            logger.info("Adding mute_toggle command...")
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
        else:
            logger.info("mute_toggle already exists")

        # Check if change_input already exists
        existing_input = session.query(Command).filter_by(
            receiver_id=receiver.id,
            action_name='change_input'
        ).first()

        if not existing_input:
            logger.info("Adding change_input command...")
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

            # Add parameter
            input_param = CommandParameter(
                command_id=change_input_cmd.id,
                param_name='input_source',
                param_type='string',
                required=True,
                valid_values='CD,DVD,BD,TV,SAT/CBL,MPLAY,GAME,TUNER,AUX1,NET,BT',
                description='Input source identifier'
            )
            session.add(input_param)
        else:
            logger.info("change_input already exists")

        session.commit()
        logger.info("✓ Missing commands added successfully")

    except Exception as e:
        logger.error(f"Error adding commands: {str(e)}", exc_info=True)
        session.rollback()
    finally:
        session.close()


if __name__ == '__main__':
    add_missing_commands()
