"""
Update volume commands to use modern Denon API endpoint.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import Receiver, Command, get_session
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def update_commands():
    """Update volume commands to modern API."""
    session = get_session()

    try:
        # Find the receiver
        receiver = session.query(Receiver).filter_by(model='AVR-X2300W').first()
        if not receiver:
            logger.error("AVR-X2300W receiver not found in database")
            return

        # Update volume_up command
        vol_up = session.query(Command).filter_by(
            receiver_id=receiver.id,
            action_name='volume_up'
        ).first()

        if vol_up:
            logger.info("Updating volume_up command...")
            vol_up.endpoint = '/goform/formiPhoneAppDirect.xml'
            vol_up.command_template = '?MVUP'

        # Update volume_down command
        vol_down = session.query(Command).filter_by(
            receiver_id=receiver.id,
            action_name='volume_down'
        ).first()

        if vol_down:
            logger.info("Updating volume_down command...")
            vol_down.endpoint = '/goform/formiPhoneAppDirect.xml'
            vol_down.command_template = '?MVDOWN'

        # Update volume_set command
        vol_set = session.query(Command).filter_by(
            receiver_id=receiver.id,
            action_name='volume_set'
        ).first()

        if vol_set:
            logger.info("Updating volume_set command...")
            vol_set.endpoint = '/goform/formiPhoneAppDirect.xml'
            # Denon uses absolute volume values like MV50 for 50, MV305 for 30.5
            # We'll need to convert dB to this format
            vol_set.command_template = '?MV{level}'
            vol_set.description = 'Set volume to specific level (00-98, where 00=-80dB, 98=+18dB)'

            # Update parameter to reflect the new range
            for param in vol_set.parameters:
                if param.param_name == 'level':
                    param.min_value = 0
                    param.max_value = 98
                    param.description = 'Volume level (00-98, corresponds to -80dB to +18dB)'

        session.commit()
        logger.info("✓ Volume commands updated successfully")

    except Exception as e:
        logger.error(f"Error updating commands: {str(e)}", exc_info=True)
        session.rollback()
    finally:
        session.close()


if __name__ == '__main__':
    update_commands()
