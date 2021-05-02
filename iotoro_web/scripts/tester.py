import binascii
import hashlib

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes


def asbin(data: bytes):
    print(' '.join(hex(a)[2:] for a in data))

def asord(data: bytes):
    print(' '.join(str(a) for a in data))

if __name__ == '__main__':
    id = get_random_bytes(8)
    a = binascii.hexlify(id).decode('utf-8')
    k = '13feffeb83805790'
    print(asord(binascii.unhexlify(k)))
    

    data = [0xe3, 0x64, 0xb9, 0x13, 0x5b, 0xf3, 0x32, 0x39, 0x2f, 0x6f, 0x58, 
    0xec, 0xc0, 0xa1, 0x9c, 0x97, 0x72, 0x4b, 0xbd, 0x40, 0x9b, 0x7c, 0x13,
     0xc8, 0x50, 0x8b, 0x3b, 0xa2, 0x02, 0xac, 0xc2, 0x8c, 0xc3, 0x65, 0xbb,
      0xf4, 0xd1, 0x36]

    #print(len(data))
    length = 35
    print(f'Length: {length}, rem: {length % 16}')
    length += 16 - (length % 16)
    print(f'Length: {length}, rem: {length % 16}')

      