from django.db import models
from django.conf import settings
from django.utils import timezone


from device import models as device_models
from . import api
from . import params
from iotoro_web import util


class Message(models.Model):
    device = models.ForeignKey(device_models.Device, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now)
    data = models.BinaryField(max_length=settings.MAX_MESSAGE_DATA_SIZE,
                              null=True)
    type = models.CharField(max_length=40, choices=api.get_action_choices())

    def __str__(self):
        return f'Device: {self.device.id} - {util.format_date(self.timestamp)}' + \
               f' - {self.get_type_display()}'


