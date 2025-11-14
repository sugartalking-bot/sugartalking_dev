"""
Complete migration script to add and update all missing commands.
Run this after deployment to ensure all commands are up to date.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import Receiver, Command, CommandParameter, get_session
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_all():
    """Run all migrations."""
    session = get_session()

    try:
        # Find the receiver
        receiver = session.query(Receiver).filter_by(model='AVR-X2300W').first()
        if not receiver:
            logger.error("AVR-X2300W receiver not found in database")
            return

        logger.info("=== Starting command migrations ===\n")

        # 1. Add mute_toggle
        if not session.query(Command).filter_by(receiver_id=receiver.id, action_name='mute_toggle').first():
            logger.info("Adding mute_toggle command...")
            session.add(Command(
                receiver_id=receiver.id,
                action_type='mute',
                action_name='mute_toggle',
                endpoint='/goform/formiPhoneAppDirect.xml',
                http_method='GET',
                command_template='?MUON',
                description='Toggle mute on/off'
            ))

        # 2. Add change_input
        if not session.query(Command).filter_by(receiver_id=receiver.id, action_name='change_input').first():
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

            session.add(CommandParameter(
                command_id=change_input_cmd.id,
                param_name='input_source',
                param_type='string',
                required=True,
                valid_values='CD,DVD,BD,TV,SAT/CBL,MPLAY,GAME,TUNER,AUX1,NET,BT',
                description='Input source identifier'
            ))

        # 3. Add sound mode command
        if not session.query(Command).filter_by(receiver_id=receiver.id, action_name='set_sound_mode').first():
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

            session.add(CommandParameter(
                command_id=sound_mode_cmd.id,
                param_name='mode',
                param_type='string',
                required=True,
                valid_values='STEREO,MOVIE,MUSIC,GAME,AUTO,DIRECT,PURE DIRECT,MCH STEREO',
                description='Sound mode name'
            ))

        # 4. Add settings toggles
        settings_commands = [
            ('toggle_dynamicEq', '?PSDYNEQ TOGGLE', 'Toggle Dynamic EQ on/off'),
            ('toggle_dynamicVol', '?PSDYNVOL TOGGLE', 'Toggle Dynamic Volume on/off'),
            ('toggle_ecoMode', '?ECO TOGGLE', 'Toggle Eco Mode on/off'),
            ('toggle_sleepTimer', '?SLPOFF', 'Turn off sleep timer'),
        ]

        for action_name, cmd_template, desc in settings_commands:
            if not session.query(Command).filter_by(receiver_id=receiver.id, action_name=action_name).first():
                logger.info(f"Adding {action_name} command...")
                session.add(Command(
                    receiver_id=receiver.id,
                    action_type='setting',
                    action_name=action_name,
                    endpoint='/goform/formiPhoneAppDirect.xml',
                    http_method='GET',
                    command_template=cmd_template,
                    description=desc
                ))

        # 5. Update volume commands to modern API
        vol_up = session.query(Command).filter_by(receiver_id=receiver.id, action_name='volume_up').first()
        if vol_up and vol_up.endpoint != '/goform/formiPhoneAppDirect.xml':
            logger.info("Updating volume_up command to modern API...")
            vol_up.endpoint = '/goform/formiPhoneAppDirect.xml'
            vol_up.command_template = '?MVUP'

        vol_down = session.query(Command).filter_by(receiver_id=receiver.id, action_name='volume_down').first()
        if vol_down and vol_down.endpoint != '/goform/formiPhoneAppDirect.xml':
            logger.info("Updating volume_down command to modern API...")
            vol_down.endpoint = '/goform/formiPhoneAppDirect.xml'
            vol_down.command_template = '?MVDOWN'

        vol_set = session.query(Command).filter_by(receiver_id=receiver.id, action_name='volume_set').first()
        if vol_set and vol_set.endpoint != '/goform/formiPhoneAppDirect.xml':
            logger.info("Updating volume_set command to modern API...")
            vol_set.endpoint = '/goform/formiPhoneAppDirect.xml'
            vol_set.command_template = '?MV{level}'
            vol_set.description = 'Set volume to specific level (00-98, where 00=-80dB, 98=+18dB)'

            for param in vol_set.parameters:
                if param.param_name == 'level':
                    param.min_value = 0
                    param.max_value = 98
                    param.description = 'Volume level (00-98, corresponds to -80dB to +18dB)'

        session.commit()

        # Count commands
        total_commands = session.query(Command).filter_by(receiver_id=receiver.id).count()

        logger.info("\n=== Migration complete ===")
        logger.info(f"✓ AVR-X2300W now has {total_commands} commands")
        logger.info("✓ All commands updated to modern Denon API")

    except Exception as e:
        logger.error(f"Error in migration: {str(e)}", exc_info=True)
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == '__main__':
    migrate_all()
