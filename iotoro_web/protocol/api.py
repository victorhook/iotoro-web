import binascii
from dataclasses import dataclass, field
from datetime import datetime
from django.utils import timezone
import struct

from django.conf import settings
from . import crypto_utils
from . import models
from . import params
from .models import MessageDownStream
from iotoro_web import util
import logging
from device.models import Device


class Action:
    PING = 0
    WRITE_UP = 1
    WRITE_UP_ACK = 2
    WRITE_DOWN = 3
    WRITE_DOWN_ACK = 4
    PONG = 5
    READ_UP = 6
    READ_UP_ACK = 7
    READ_DOWN = 8
    READ_DOWN_ACK = 9


@dataclass
class IotoroPacket:
    version: int
    action: int
    payload_size: int
    device_id: str
    timestamp: datetime

    raw_content: field(default_factory=bytes)
    params: list = field(default_factory=list)


    def __repr__(self):
        return '---------------------------\n' + \
               f'Version: {self.version}\n' + \
               f'Action: {self.action}\n' + \
               f'Payload size: {self.payload_size}\n' + \
               f'Time: {util.format_date(self.timestamp)}\n' + \
               f'Params: {self.params}\n' + \
               '---------------------------\n'


# -- Helper methods -- #

def _make_message(device: Device, payload: bytes, action: Action) -> MessageDownStream:
    """ Returns a downstream message. """
    message = MessageDownStream(
        msg_to=device,
        msg_from=device.user,
        data=payload,
        type=action
    )
    return message


def _make_data_packet(version: int, action: int, content: bytes) -> tuple:
    """ Returns a tuple of: (payload, action) """
    first_byte = (version << 4) | action
    header = struct.pack('<BH', first_byte, len(content))
    return header + content, action


def _get_payload_size(data: bytes) -> int:
    return struct.unpack('<H', data[1:settings.IOTORO_PACKET_HEADER_SIZE])[0]


def _get_device_id(data: bytes) -> str:
    return binascii.hexlify(data[-settings.DEVICE_ID_SIZE:]).decode('utf-8')


def _get_packet_body(data: bytes) -> bytes:
    return data[settings.IOTORO_PACKET_HEADER_SIZE:-settings.DEVICE_ID_SIZE]


def _decode_packet(data: bytes) -> IotoroPacket:
    version = (data[0] & 0xf0) >> 4
    action = data[0] & 0x0f

    packet = IotoroPacket(
        version=version,
        action=action,
        payload_size=_get_payload_size(data),
        raw_content=_get_packet_body(data),
        timestamp=timezone.now(),
        params=params.get_parameters(_get_packet_body(data)),
        device_id=_get_device_id(data)
    )

    return packet


# -- Public -- #

def encrypt_packet(make_packet: callable):
    """ 
        Decorator that encrypts whatever packet-making method that
        uses it.
        Note: This requires device_key: str, device_id: str as args.
    """
    def wrapper(device_key: str, device_id: str, content: bytes = None):
        data = make_packet()
        data = crypto_utils.encrypt_packet(device_key, device_id, data)
        return data

    return wrapper


def make_message(make_packet_data: callable):
    """ 
        Decorator that encrypts whatever packet-making method that
        uses it.
        Note: This requires device_key: str, device_id: str as args.
    """
    # device_key: str, device_id: str, content: bytes = None
    def wrapper(device: Device):
        # Create the packet payload.
        data, action = make_packet_data(device)

        # Encrypt the payload.
        payload = crypto_utils.encrypt_packet(device.device_key, 
                                              device.device_id, data)

        # Create a message obj which we can save to database.
        message = _make_message(device, payload, action)

        return message

    return wrapper


@make_message
def make_pong(device: Device) -> MessageDownStream:
    return _make_data_packet(
        settings.IOTORO_VERSION,
        Action.PONG,
        b''
    )

@make_message
def make_write_ack(device: Device) -> bytes:
    return _make_data_packet(
        settings.IOTORO_VERSION,
        Action.WRITE_UP_ACK,
        b''
    )

@make_message
def make_read_ack(device: Device) -> bytes:
    return _make_data_packet(
        settings.IOTORO_VERSION,
        Action.READ_UP_ACK,
        b''
    )

def decode_packet(data: bytes, device_key: bytes) -> IotoroPacket:
    decrypted_data = crypto_utils.decrypt_packet(data, device_key)
    packet = _decode_packet(decrypted_data)
    return packet
