from django.forms import ModelForm

from . import models


class DeviceForm(ModelForm):
    class Meta:
        model = models.Device
        fields = ['name', 'type', 'device_key']
        labels = {
            'name': 'Device name',
            'type': 'Device type',
            'device_key': 'Device key',
        }
        help_texts = {
            'name': 'A unique name for the device. This could be anything!',
            'type': 'What type of device it is, eg ESP8266, ESP32 etc.',
            'device_key': 'A 16-byte long key that is used for ' + 
            'authenticating the device. Valid values are hex, so 0-f'
        }
