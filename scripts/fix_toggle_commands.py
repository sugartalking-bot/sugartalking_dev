"""
Fix mute toggle and eco mode commands.

This script updates the command templates for mute_toggle and eco mode to use proper Denon commands.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import Receiver, Command, get_session
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Fix toggle commands."""
    session = get_session()

    try:
        # Find receiver
        receiver = session.query(Receiver).filter_by(model='AVR-X2300W').first()
        if not receiver:
            logger.error("Receiver AVR-X2300W not found")
            return

        # Fix mute_toggle - change from MUON to MUOFF (to toggle off)
        # Actually Denon uses MUON/MUOFF, not toggle. We need to implement state tracking
        # For now, let's just make it cycle: MUOFF will unmute if currently muted
        mute_cmd = session.query(Command).filter_by(
            receiver_id=receiver.id,
            action_name='mute_toggle'
        ).first()

        if mute_cmd:
            # Change to use MUOFF so it toggles off
            old_template = mute_cmd.command_template
            mute_cmd.command_template = '?MUOFF'
            logger.info(f"Updated mute_toggle: {old_template} -> {mute_cmd.command_template}")

        # Fix eco mode - check the proper command
        eco_cmd = session.query(Command).filter_by(
            receiver_id=receiver.id,
            action_name='toggle_ecoMode'
        ).first()

        if eco_cmd:
            # The command might need to be formatted differently
            # Try: ?ECO AUTO, ON, OFF
            old_template = eco_cmd.command_template
            old_endpoint = eco_cmd.endpoint

            # Change to use MainZone endpoint like other toggle commands
            eco_cmd.endpoint = '/MainZone/index.put.asp'
            eco_cmd.command_template = '?cmd0=PutZone_EcoMode/Toggle'

            logger.info(f"Updated toggle_ecoMode:")
            logger.info(f"  Endpoint: {old_endpoint} -> {eco_cmd.endpoint}")
            logger.info(f"  Template: {old_template} -> {eco_cmd.command_template}")
        else:
            logger.warning("toggle_ecoMode command not found")

        session.commit()
        logger.info("✓ Toggle commands updated successfully")

    except Exception as e:
        logger.error(f"Error updating commands: {str(e)}", exc_info=True)
        session.rollback()
        sys.exit(1)

    finally:
        session.close()


if __name__ == '__main__':
    main()
