import binascii
from dataclasses import dataclass, field
import hashlib

from django.conf import settings

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes

import logging



@dataclass
class RawPacket:
    iv: field(default_factory=bytes)
    data: field(default_factory=bytes)

    def as_bytes(self) -> bytes:
        return self.data + self.iv


# -- Functions -- #

def md5(device_id: str) -> str:
    """ Returns md5 with HEX digest. """
    if type(device_id) is str:
        device_id = device_id.encode('utf-8')
    return hashlib.md5(device_id).hexdigest()


def ashex(data):
    return ' '.join(hex(a)[2:].zfill(2) for a in data)



def decrypt_packet(data: bytes, device_key: bytes) -> bytes:
    """ Decodes a packet using AES encryption, given the device key. """
    # Turn the data into a packet helper format.
    packet = _get_raw_packet(data)

    """
    logging.debug('OK')
    logging.debug(ashex(data[:3]))
    logging.debug(ashex(data[3:3+24]))
    logging.debug(ashex(data[3+24:3+24+8]))
    logging.debug(ashex(data[3+24+8:3+24+8+16]))
    logging.debug(f'Device key: {device_key}')
    logging.debug(f'Data: {ashex(packet.data)}')
    logging.debug(f'IV: {ashex(packet.iv)}')
    """


    if type(device_key) is str:
        device_key = binascii.unhexlify(device_key)

    # Create cypher from given iv and the device key.
    cipher = AES.new(device_key, AES.MODE_CBC, packet.iv)

    # Decrypt the data.
    try:
        decrypted = cipher.decrypt(packet.data)
    except ValueError as e:
        logging.warn(f'ValuError when decrypting packet: {e}')
        return None

    # Unpad the data.
    try:
        decrypted = unpad(decrypted, AES.block_size)
    except ValueError as e:
        logging.warn(f'{e}, might be incorrect key!')
        return None

    return decrypted


def encrypt_packet(device_key: bytes, device_id: bytes, data: bytes) -> bytes:
    """ Encrypts the given data with the device key and returns a packet. """
    device_key = binascii.unhexlify(device_key)
    device_id = binascii.unhexlify(device_id)

    iv = _generate_iv()
    cipher = AES.new(device_key, AES.MODE_CBC, iv)

    # Add device_id to data
    data += device_id

    # Add padding to ensure block size of 16 (with AES)
    data = pad(data, AES.block_size)

    # Encrypt the data
    encrypted = cipher.encrypt(data)
    return encrypted


def random_bytes(length: int) -> bytes:
    return get_random_bytes(length)


def get_default_key() -> str:
    bytes = random_bytes(settings.DEVICE_KEY_SIZE)
    return binascii.hexlify(bytes).decode('utf-8')


def get_default_id() -> str:
    """ Returns a new, completely unique id. """
    bytes = random_bytes(settings.DEVICE_ID_SIZE)
    return binascii.hexlify(bytes).decode('utf-8')


# -- Helper methods -- ##

def _get_raw_packet(raw_data: bytes) -> RawPacket:
    iv = raw_data[-16:]      # first 16 bytes is the initialization vector.
    data = raw_data[:-16]     # rest is the data
    return RawPacket(iv, data)


def _generate_iv() -> bytes:
    return random_bytes(AES.block_size)
