__all__ = ['get_param', 'IotoroParamType']


from dataclasses import dataclass
import struct

from django.conf import settings


@dataclass
class IotoroParamType:
    format: str
    size: int

    def __repr__(self):
        return f'{self.format}, {self.size}'

@dataclass
class IotoroParam:
    name: str
    type: IotoroParamType
    value: bytes

    def __repr__(self):
        return f'{self.name}: {self.value}'


class IotoroParamTypes:
    PARAM_BOOL = 0
    PARAM_UINT_8 = 1
    PARAM_INT_8 = 2
    PARAM_UINT_16 = 3
    PARAM_INT_16 = 4
    PARAM_UINT_32 = 5
    PARAM_INT_32 = 6
    PARAM_UINT_64 = 7
    PARAM_INT_64 = 8
    PARAM_FLOAT = 9
    PARAM_DOBULE = 10


IOTORO_PARAM_TYPES = {
    IotoroParamTypes.PARAM_BOOL: '?',
    IotoroParamTypes.PARAM_UINT_8: 'B',
    IotoroParamTypes.PARAM_INT_8: 'b',
    IotoroParamTypes.PARAM_UINT_16: 'H',
    IotoroParamTypes.PARAM_INT_16: 'h',
    IotoroParamTypes.PARAM_UINT_32: 'I',
    IotoroParamTypes.PARAM_INT_32: 'i',
    IotoroParamTypes.PARAM_UINT_64: 'L',
    IotoroParamTypes.PARAM_INT_64: 'l',
    IotoroParamTypes.PARAM_FLOAT: 'f',
    IotoroParamTypes.PARAM_DOBULE: 'd',
}

IOTORO_PARAM_SIZES = {
    IotoroParamTypes.PARAM_BOOL: 1,
    IotoroParamTypes.PARAM_UINT_8: 1,
    IotoroParamTypes.PARAM_INT_8: 1,
    IotoroParamTypes.PARAM_UINT_16: 2,
    IotoroParamTypes.PARAM_INT_16: 2,
    IotoroParamTypes.PARAM_UINT_32: 4,
    IotoroParamTypes.PARAM_INT_32: 4,
    IotoroParamTypes.PARAM_UINT_64: 8,
    IotoroParamTypes.PARAM_INT_64: 8,
    IotoroParamTypes.PARAM_FLOAT: 4,
    IotoroParamTypes.PARAM_DOBULE: 8,
}

def _get_param_value(data: bytes, param_type: IotoroParamType) -> str:
    return struct.unpack(param_type.format, data[:param_type.size])[0]


def _get_param(raw_type: int) -> IotoroParamType:
    return IotoroParamType(IOTORO_PARAM_TYPES[raw_type], 
                           IOTORO_PARAM_SIZES[raw_type])

def _get_param_name(data: bytes) -> str:
    # The names are c-style char-arrays, which are null-terminated. 
    c_style_name = data[:settings.IOTORO_PARAM_MAX_NAME_SIZE]
    return c_style_name.decode('ascii').split('\x00')[0]


def get_parameters(data: bytes) -> list:
    """ Returns a list of parameters from the payload data. 
        If no params exist, an empty list is returned.
    """
    param_list = []
    index = 0
    while index < len(data):
        name = _get_param_name(data[index:])
        index += settings.IOTORO_PARAM_MAX_NAME_SIZE
        type = _get_param(data[index])
        index += 1
        value = _get_param_value(data[index:], type)

        param_list.append(IotoroParam(
            name,
            type,
            value
        ))

        index += type.size


    return param_list
