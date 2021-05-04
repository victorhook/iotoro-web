from django.db import models
from django.conf import settings
from django.utils import timezone


from device import models as device_models
from . import api
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
    device = models.ForeignKey(device_models.Device, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now)
    data = models.BinaryField(max_length=settings.MAX_MESSAGE_DATA_SIZE,
                              null=True)
    type = models.CharField(max_length=40, choices=api.get_action_choices())

    def __str__(self):
        return f'Device: {self.device.id} - {util.format_date(self.timestamp)}' + \
               f' - {self.get_type_display()}'


