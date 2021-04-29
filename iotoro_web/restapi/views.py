from device import models
from django.shortcuts import render, HttpResponse
from django.http import HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
import logging

from protocol import api
from device.models import Device

from . import utils
from . import models
from protocol import models as protocol_models


# Create your views here.
@csrf_exempt
def index(request: HttpRequest):
    return HttpResponse('Ok')


def pong(device: Device) -> HttpResponse:
    protocol_models.Message(device=device, type='PING').save()
    protocol_models.Message(device=device, type='PONG').save()
    return HttpResponse(utils.make_pong())


def write_up():
    return HttpResponse('Hello !')
    pass


def read_up():
    return HttpResponse('Hello !')
    pass


@utils.requires_device_auth
def device_push(request: HttpRequest, device: Device, packet: api.IotoroPacket):
    
    print(packet)

    if packet.action == api.Action.PING:
        return pong(device)
    elif packet.action == api.Action.WRITE_UP:
        return write_up()
    elif packet.action == api.Action.READ_UP:
        return read_up()

    logging.warn(f'Failed to recognize command {packet.action}')
    return HttpResponse(f'Failed to recognize command {packet.action}')


