from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.conf import settings

from protocol import crypto_utils
from protocol import api
from device import models


def get_device(device_id: str) -> models.Device:
    device_id = device_id.lower()
    device = list(filter(
                lambda device: crypto_utils.md5(device.device_id) == device_id,
                models.Device.objects.all())
            )
    return device[0] if len(device) > 0 else None


def device_exists(device_id: str) -> User:
    return get_device(device_id) is not None


def requires_device_auth(func: callable):
    """ Decorator to ensure that the device message is authenticated. """

    @csrf_exempt
    def wrapper(request: HttpRequest, device_id: str):
        if device_exists(device_id):
            # Get device from the id.
            device = get_device(device_id)

            # Try to decrypt the packet
            packet = api.decode_packet(request.body, device.device_key)


            # TODO: Handle these errors better.
            if packet is None:
                print('Incorrect authorization')
                return HttpResponse('Incorrect authorization')

            if packet.device_id == device.device_id:
                print(f'Device id {packet.device_id} authorized')

                # Call the view function.
                return func(request, device, packet)

            else:
                print('Incorrect authorization')
                return HttpResponse('Incorrect authorization')
        else:
            print(f'No owner for device id {device_id}')
            return HttpResponse('No such device exists.')

    return wrapper
