from datetime import timedelta, datetime
from django.contrib import messages
from django.shortcuts import render, redirect
from django.db.utils import IntegrityError
from django.utils import timezone
from django.http import HttpRequest
from django.contrib.auth.decorators import login_required
from protocol.models import MessageUpStream
from restapi.utils import get_device


from . import models
from . import forms
from . import utils
from iotoro_web import util as basic_utils


@login_required
def new_device(request: HttpRequest):
    if request.method == 'POST':
        device_obj = models.Device(user=request.user)
        device_form = forms.DeviceForm(request.POST, instance=device_obj)
        if device_form.is_valid():
            try:
                print('Trying to save...')
                device_form.save()
            except IntegrityError as e:
                messages.warning(request, 'You already have a device with this\
                                 name. Please choose a unique one.')
                return render(request, 'new_device.html', {'form': device_form})
            
            return redirect('device')
        else:
            #TODO: Handle error here?
            print('Not valid!...')
            return render(request, 'new_device.html', {'form': device_form})
    else:
        device_form = utils.get_device_form()
        return render(request, 'new_device.html', {'form': device_form})


@login_required
def device(request: HttpRequest):
    """ First page that the user gets linked to when pressing on Devices. """
    devices = utils.get_devices(request.user)
    selected_device = devices[0].name if len(devices) > 0 else None
    if selected_device is None:
        return render(request, 'no_devices.html')
    else:
        return redirect('overview', selected_device)


@login_required
def base_device_view(request: HttpRequest, endpoint: str, 
                     selected_device: str, data: dict):
    devices = utils.get_devices(request.user)
    selected_device = utils.get_device(request.user, selected_device)

    context = {
        'devices': devices,
        'selected_device': selected_device
    }
    context.update(data)

    return render(request, endpoint, context)

def data(request: HttpRequest, device_name: str):
    device = utils.get_device(request.user, device_name)
    packets = MessageUpStream.objects.filter(device=device)
    return base_device_view(request, 'data.html', device_name, 
                            {'packets': packets})


def attributes(request: HttpRequest, device_name: str):
    return base_device_view(request, 'attributes.html', device_name, {})

def settings(request: HttpRequest, device_name: str):
    if request.method == 'POST':
        # Save settings.
        device_obj = models.Device.objects.get(id=request.POST['id'])
        device_form = forms.DeviceForm(request.POST, instance=device_obj)
        if device_form.is_valid():
            device_form.save()
            device_form.clean()
            device_name = device_form.cleaned_data['name']
            return redirect('settings', device_name)
        else:
            #TODO: Handle error here?
            pass   
    else:
        device_form = utils.get_device_form(utils.get_device(request.user, 
                                            device_name))
        return base_device_view(request, 'settings.html', device_name, 
                            {'form': device_form})

def triggers(request: HttpRequest, device_name: str):
    return base_device_view(request, 'triggers.html', device_name, {})


def get_time_diff(t1: timezone, t2: timezone) -> str:
    return (t1 - t2).seconds


def packets_last_24_hours(device: models.Device) -> list:
    date_from = timezone.now() - timezone.timedelta(days=1)
    packets = MessageUpStream.objects.filter(device=device,
                                             sent__gte=date_from)
    labels = list(map(lambda pkt: basic_utils.format_date(pkt.sent), packets))
    values = list(map(lambda pkt: len(pkt), packets))
    return labels, values

    
@login_required
def overview(request: HttpRequest, device_name: str):
    device = utils.get_device(request.user, device_name)
    print(f'Overview: {device}')
    latest_packet = utils.get_latest_packet(device)
    latest_packet = None

    last_24_hour_labels, last_24_hour_values = packets_last_24_hours(device)

    if latest_packet is not None:
        latest_packet.time_diff = get_time_diff(timezone.now(),
                                                latest_packet.timestamp)

    total_data = utils.get_total_data_send(device)

    return base_device_view(request, 'overview.html', device_name,
                            {
                                'latest_packet': latest_packet,
                                'last_24_hour_labels': last_24_hour_labels,
                                'last_24_hour_values': last_24_hour_values
                            })
