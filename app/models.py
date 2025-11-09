"""
Database models for Sugartalking AVR control system.

This module defines the database schema for storing receiver information,
commands, and parameters to support multi-receiver control.
"""

from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import os

Base = declarative_base()


class Receiver(Base):
    """
    Represents an AVR receiver model.

    Stores information about different receiver models and their capabilities.
    """
    __tablename__ = 'receivers'

    id = Column(Integer, primary_key=True)
    manufacturer = Column(String(100), nullable=False)  # e.g., "Denon", "Yamaha", "Onkyo"
    model = Column(String(100), nullable=False, unique=True)  # e.g., "AVR-X2300W"
    firmware_version = Column(String(50), nullable=True)
    protocol = Column(String(50), nullable=False, default='http')  # http, telnet, serial, etc.
    default_port = Column(Integer, default=80)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    commands = relationship("Command", back_populates="receiver", cascade="all, delete-orphan")
    discovered_instances = relationship("DiscoveredReceiver", back_populates="receiver_model", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Receiver {self.manufacturer} {self.model}>"


class Command(Base):
    """
    Represents a command that can be sent to a receiver.

    Stores command templates with placeholders for parameters.
    """
    __tablename__ = 'commands'

    id = Column(Integer, primary_key=True)
    receiver_id = Column(Integer, ForeignKey('receivers.id'), nullable=False)
    action_type = Column(String(50), nullable=False)  # power, volume, input, zone, sound_mode, etc.
    action_name = Column(String(100), nullable=False)  # power_on, power_off, volume_up, etc.
    endpoint = Column(String(255), nullable=False)  # e.g., "/MainZone/index.put.asp"
    http_method = Column(String(10), default='GET')  # GET, POST, PUT
    command_template = Column(Text, nullable=False)  # e.g., "?cmd0=PutZone_OnOff/{state}"
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    receiver = relationship("Receiver", back_populates="commands")
    parameters = relationship("CommandParameter", back_populates="command", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Command {self.action_name} for {self.receiver.model}>"


class CommandParameter(Base):
    """
    Represents a parameter for a command.

    Stores validation rules and possible values for command parameters.
    """
    __tablename__ = 'command_parameters'

    id = Column(Integer, primary_key=True)
    command_id = Column(Integer, ForeignKey('commands.id'), nullable=False)
    param_name = Column(String(100), nullable=False)  # e.g., "state", "volume_level", "input_source"
    param_type = Column(String(50), nullable=False)  # string, integer, float, boolean, enum
    required = Column(Boolean, default=False)
    default_value = Column(String(255), nullable=True)
    valid_values = Column(Text, nullable=True)  # JSON array of valid values for enum types
    min_value = Column(Float, nullable=True)  # For numeric types
    max_value = Column(Float, nullable=True)  # For numeric types
    description = Column(Text, nullable=True)

    # Relationships
    command = relationship("Command", back_populates="parameters")

    def __repr__(self):
        return f"<CommandParameter {self.param_name} for {self.command.action_name}>"


class DiscoveredReceiver(Base):
    """
    Represents a physical receiver instance discovered on the network.

    Stores information about actual receivers found via auto-discovery.
    """
    __tablename__ = 'discovered_receivers'

    id = Column(Integer, primary_key=True)
    receiver_id = Column(Integer, ForeignKey('receivers.id'), nullable=True)  # Link to model if identified
    hostname = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=False)  # IPv4 or IPv6
    port = Column(Integer, default=80)
    mac_address = Column(String(17), nullable=True)  # MAC address if available
    friendly_name = Column(String(255), nullable=True)  # User-friendly name
    is_active = Column(Boolean, default=True)
    last_seen = Column(DateTime, default=datetime.utcnow)
    discovered_at = Column(DateTime, default=datetime.utcnow)
    discovery_method = Column(String(50), nullable=True)  # mdns, http_probe, manual

    # Relationships
    receiver_model = relationship("Receiver", back_populates="discovered_instances")

    def __repr__(self):
        return f"<DiscoveredReceiver {self.friendly_name or self.ip_address}>"


class ErrorLog(Base):
    """
    Stores error logs for debugging and auto-reporting.

    Tracks errors to categorize them as user errors vs bugs.
    """
    __tablename__ = 'error_logs'

    id = Column(Integer, primary_key=True)
    error_type = Column(String(100), nullable=False)  # ConfigError, NetworkError, ProcessingError, etc.
    error_category = Column(String(50), nullable=False)  # user_error, bug, unknown
    error_message = Column(Text, nullable=False)
    stack_trace = Column(Text, nullable=True)
    request_path = Column(String(255), nullable=True)
    user_agent = Column(String(255), nullable=True)
    reported_to_github = Column(Boolean, default=False)
    github_issue_number = Column(Integer, nullable=True)
    occurred_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ErrorLog {self.error_type} at {self.occurred_at}>"


# Database initialization
def init_db(db_url=None):
    """
    Initialize the database with tables.

    Args:
        db_url: Database URL (defaults to SQLite in data directory)
    """
    if db_url is None:
        # Default to SQLite in data directory
        data_dir = os.getenv('DATA_DIR', '/data')
        os.makedirs(data_dir, exist_ok=True)
        db_url = f'sqlite:///{data_dir}/sugartalking.db'

    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)
    return engine


def get_session(engine=None):
    """
    Get a database session.

    Args:
        engine: SQLAlchemy engine (creates default if None)

    Returns:
        SQLAlchemy session
    """
    if engine is None:
        engine = init_db()

    Session = sessionmaker(bind=engine)
    return Session()
