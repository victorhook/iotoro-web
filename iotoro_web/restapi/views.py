from device import models
from django.core.checks import messages
from django.http.response import HttpResponseBadRequest
from django.shortcuts import render, HttpResponse
from django.http import HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.contrib.auth.models import User
import logging
from iotoro_web import util

from protocol import api, crypto_utils
from device.models import Device

from . import utils
from . import models
from protocol import models as protocol_models
from protocol.models import MessageDownStream, MessageUpStream


# Create your views here.
@csrf_exempt
def index(request: HttpRequest):
    return HttpResponse('KHDASJKDHAJSHDJKASD')


def has_response_in_buffer(device: Device) -> bool:
    messages = MessageDownStream.objects.filter(device=device, sent=None)
    return len(messages) > 0


def get_response_in_buffer(device: Device) -> MessageDownStream:
    """ Returns a message from the database buffer.
        If the buffer is empty, None is returned.
    """
    buffer = MessageDownStream.objects.filter(device=device, sent=None)
    response = buffer[0]
    utils.mark_as_sent(response)
    return response


def get_response(device: Device, create_message: callable):
    """ Gets the appropiate response to send to the device.
        The process to get the right response is as follows:
            1. Check the message buffer in the database.
            2.1. If there's a packet in the buffer, that's the response.
                 This message is then deleted from the buffer.
            2.1. If the buffer is empty, create_message will be called
                 to created the response.
    """
    if has_response_in_buffer(device):
        response = get_response_in_buffer(device)
        logging.debug(f'Response from buffer: {response}')
    else:
        response = create_message(device)
        logging.debug(f'Default response: {response}')
        
    return response


def make_response(msg: MessageDownStream) -> bytes:
    return HttpResponse(msg.as_bytes(), content_type='application/octet-stream')


def pong(device: Device) -> HttpResponse:
    msg = get_response(device, api.make_pong)
    return make_response(msg)


def write_up(device: Device, packet: MessageUpStream) -> HttpResponse:
    packet.save()
    msg = get_response(device, api.make_write_ack)
    return make_response(msg)
    

def read_up(device: Device, packet: MessageUpStream) -> HttpResponse:
    packet.save()
    data = api.make_read_ack(device.device_key, device.device_id)
    return HttpResponse(data, content_type='application/octet-stream')


@utils.requires_device_auth
def device_push(request: HttpRequest, device: Device, packet: MessageUpStream):
    
    if packet.action == api.Action.PING:
        return pong(device)
    elif packet.action == api.Action.WRITE_UP:
        return write_up(device, packet)
    elif packet.action == api.Action.READ_UP:
        return read_up(device, packet)

    logging.warn(f'Failed to recognize command {packet.action}')
    return HttpResponse(f'Failed to recognize command {packet.action}')


