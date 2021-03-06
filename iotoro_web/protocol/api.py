import binascii
from dataclasses import dataclass, field
from django.utils import timezone
import struct

from django.conf import settings
from . import crypto_utils
from . import models
from . import params
from .models import MessageDownStream, MessageUpStream
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
    timestamp: timezone

    raw_content: field(default_factory=bytes)       # Encrypted
    params: list = field(default_factory=list)


    def __repr__(self):
        return '---------------------------\n' + \
               f'Version: {self.version}\n' + \
               f'Action: {self.action}\n' + \
               f'Payload size: {self.payload_size}\n' + \
               f'Time: {util.format_date(self.timestamp)}\n' + \
               f'Params: {self.params}\n' + \
               '---------------------------\n'


    def to_message_upstream(self) -> MessageUpStream:
        device = _get_device_from_id(self.device_id)
        return MessageUpStream(
            device=device,
            user=device.user,
            version=self.version,
            action=self.action,
            data=self.raw_content,
            sent=self.timestamp
        )


# -- Helper methods -- #

def _get_device_from_id(device_id: str) -> Device:
    device = Device.objects.get(device_id=device_id)
    return device if device is not None else None

def _get_payload_size(data: bytes) -> int:
    return struct.unpack('<H', data[1:settings.IOTORO_PACKET_HEADER_SIZE])[0]


def _get_device_id(data: bytes) -> str:
    return binascii.hexlify(data[-settings.DEVICE_ID_SIZE:]).decode('utf-8')


def _get_packet_body(data: bytes) -> bytes:
    return data[settings.IOTORO_PACKET_HEADER_SIZE:-settings.DEVICE_ID_SIZE]


def _make_header(version: int, action: int, payload: bytes) -> bytes:
    """ Creates an IotorPacket header from the version, action and payload. """
    first_byte = (version << 4) | action
    header = struct.pack('<BH', first_byte, len(payload))
    return header + payload


def _make_packet(device: Device, action: Action, payload=None, 
                 version=settings.IOTORO_VERSION) -> MessageDownStream:
    """ Returns a downstream message. """
    if payload is None:
        payload = b''

    # Create header.
    header = _make_header(version, action, payload)

    # Encrypt the data.
    encrypted_data = crypto_utils.encrypt_packet(device.device_key, 
                                                 device.device_id,
                                                 header + payload)
    # Create a message object.
    message = MessageDownStream(
        device=device,
        user=device.user,
        version=version,
        action=action,
        data=encrypted_data,
    )

    return message


def _decode_header(data: bytes) -> tuple:
    version = (data[0] & 0xf0) >> 4
    action = data[0] & 0x0f
    return version, action


def _decode_packet(data: bytes) -> IotoroPacket:
    version, action = _decode_header(data)

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
def decode_packet(data: bytes, device_key: bytes) -> IotoroPacket:
    decrypted_data = crypto_utils.decrypt_packet(data, device_key)
    packet = _decode_packet(decrypted_data)
    return packet


def make_pong(device: Device) -> MessageDownStream:
    return _make_packet(device, Action.PONG)


def make_write_ack(device: Device) -> bytes:
    return _make_packet(device, Action.WRITE_UP_ACK)
