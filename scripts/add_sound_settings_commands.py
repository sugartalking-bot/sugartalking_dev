"""
Add sound mode and settings toggle commands to Denon AVR-X2300W.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import Receiver, Command, CommandParameter, get_session
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_commands():
    """Add sound mode and settings commands."""
    session = get_session()

    try:
        # Find the receiver
        receiver = session.query(Receiver).filter_by(model='AVR-X2300W').first()
        if not receiver:
            logger.error("AVR-X2300W receiver not found in database")
            return

        # Add sound mode command
        existing_sound = session.query(Command).filter_by(
            receiver_id=receiver.id,
            action_name='set_sound_mode'
        ).first()

        if not existing_sound:
            logger.info("Adding set_sound_mode command...")
            sound_mode_cmd = Command(
                receiver_id=receiver.id,
                action_type='sound',
                action_name='set_sound_mode',
                endpoint='/goform/formiPhoneAppDirect.xml',
                http_method='GET',
                command_template='?MS{mode}',
                description='Set sound mode'
            )
            session.add(sound_mode_cmd)
            session.flush()

            # Add parameter
            mode_param = CommandParameter(
                command_id=sound_mode_cmd.id,
                param_name='mode',
                param_type='string',
                required=True,
                valid_values='STEREO,MOVIE,MUSIC,GAME,AUTO,DIRECT,PURE DIRECT,MCH STEREO',
                description='Sound mode name'
            )
            session.add(mode_param)
        else:
            logger.info("set_sound_mode already exists")

        # Add Dynamic EQ toggle
        if not session.query(Command).filter_by(receiver_id=receiver.id, action_name='toggle_dynamicEq').first():
            logger.info("Adding toggle_dynamicEq command...")
            session.add(Command(
                receiver_id=receiver.id,
                action_type='setting',
                action_name='toggle_dynamicEq',
                endpoint='/goform/formiPhoneAppDirect.xml',
                http_method='GET',
                command_template='?PSDYNEQ TOGGLE',
                description='Toggle Dynamic EQ on/off'
            ))

        # Add Dynamic Volume toggle
        if not session.query(Command).filter_by(receiver_id=receiver.id, action_name='toggle_dynamicVol').first():
            logger.info("Adding toggle_dynamicVol command...")
            session.add(Command(
                receiver_id=receiver.id,
                action_type='setting',
                action_name='toggle_dynamicVol',
                endpoint='/goform/formiPhoneAppDirect.xml',
                http_method='GET',
                command_template='?PSDYNVOL TOGGLE',
                description='Toggle Dynamic Volume on/off'
            ))

        # Add Eco Mode toggle
        if not session.query(Command).filter_by(receiver_id=receiver.id, action_name='toggle_ecoMode').first():
            logger.info("Adding toggle_ecoMode command...")
            session.add(Command(
                receiver_id=receiver.id,
                action_type='setting',
                action_name='toggle_ecoMode',
                endpoint='/goform/formiPhoneAppDirect.xml',
                http_method='GET',
                command_template='?ECO TOGGLE',
                description='Toggle Eco Mode on/off'
            ))

        # Add Sleep Timer toggle (this is more of a set command, but we'll make it toggle off)
        if not session.query(Command).filter_by(receiver_id=receiver.id, action_name='toggle_sleepTimer').first():
            logger.info("Adding toggle_sleepTimer command...")
            session.add(Command(
                receiver_id=receiver.id,
                action_type='setting',
                action_name='toggle_sleepTimer',
                endpoint='/goform/formiPhoneAppDirect.xml',
                http_method='GET',
                command_template='?SLPOFF',
                description='Turn off sleep timer'
            ))

        session.commit()
        logger.info("✓ Sound and settings commands added successfully")

    except Exception as e:
        logger.error(f"Error adding commands: {str(e)}", exc_info=True)
        session.rollback()
    finally:
        session.close()


if __name__ == '__main__':
    add_commands()
