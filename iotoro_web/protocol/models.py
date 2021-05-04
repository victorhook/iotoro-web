from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone

from device import models as device_models
from . import params
from iotoro_web import util


ACTIONS_CHOICES = [
    ('Pi', 'PING'),
    ('Wu', 'WRITE_UP'),
    ('Wd', 'WRITE_DOWN'),
    ('Po', 'PONG'),
    ('Ru', 'READ_UP'),
    ('Rd', 'READ_DOWN'),
]

ACTION_TABLE = [
    'PING',
    'WRITE_UP',
    'WRITE_UP_ACK',
    'WRITE_DOWN',
    'WRITE_DOWN_ACK',
    'PONG',
    'READ_UP',
    'READ_UP_ACK',
    'READ_DOWN',
    'READ_DOWN_ACK',
]

TYPE_CHOICES = [
    ('u8', 'unsigned int 8'),
    ('i8', 'signed int 8'),
    ('u16', 'unsigned int 16'),
    ('i16', 'signed int 16'),
    ('u32', 'unsigned int 32'),
    ('i32', 'signed int 32'),
    ('u64', 'unsigned int 64'),
    ('i64', 'signed int 64'),
    ('f', 'float'),
    ('d', 'double'),
    ('b', 'bool')
]

class Message(models.Model):
    # Recipients.
    device = models.ForeignKey(device_models.Device, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Version of the packet.
    version = models.IntegerField(default=settings.IOTORO_VERSION)
    
    # Type of packet.
    action = models.CharField(max_length=40, choices=ACTIONS_CHOICES)

    # Payload.
    data = models.BinaryField(max_length=settings.MAX_MESSAGE_DATA_SIZE,
                              blank=True, null=True)

    def __str__(self):
        return f'Device: {self.device.id} ' 

    def __len__(self) -> int:
        return settings.IOTORO_HEADER_SIZE + len(self.data)

    def get_action(self) -> str:
        return ACTION_TABLE[int(self.action)]

    def as_bytes(self) -> bytes:
        return self.data


class MessageUpStream(Message):
    sent = models.DateTimeField(default=timezone.now)


class MessageDownStream(Message):
    # Put in queue and actual sent can differ.
    put_in_queue = models.DateTimeField(default=timezone.now)
    sent = models.DateTimeField(null=True, blank=True)
    