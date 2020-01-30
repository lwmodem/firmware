#
# Modem-Shell (translate commands from stdin and exchange binary messages with modem)
#

from typing import List, Optional, Tuple, Union

import sys
import time
from serial import Serial
from struct import pack, unpack
from datetime import datetime, timedelta
from binascii import crc32
import string
import re
import os

def getopts(args):
    """ Validate command line arguments """

    if len(args) < 2:
        print ("Missing Parameters")
        print("Usage: python upgrade_fw.py <firmware_file> <UART port>")
        sys.exit()
    # first argument is the firmware file to be upgrade
    fw_file = args[0]
    ser_dev = args[1]
    return fw_file, ser_dev


# Print iterations progress
def printProgressBar (iteration, total, prefix = '', decimals = 1, length = 50):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = '█' * filledLength + '-' * (length - filledLength)
    print('\r%s [%s] %s%% %s' % (prefix, bar, percent, ''), end = '\r')
    # Print New Line on Complete
    if iteration == total:
        print()


def send_packet(pkt, cr):
    ser.write(pkt)
    if cr == 1:
        ser.write("\r\n".encode('utf-8'))
    #time.sleep(0.001)

# command:
def make_packet(cmd, payload:bytes=b'') -> bytes:
    #print(payload)
    pkt = pack('%ds' % len(cmd), cmd.encode('utf-8'))
    pkt += payload

    return pkt

# response:
def read_packet() -> Optional[Tuple]:
    while True:
        c = ser.readline().decode(errors='ignore')
        if c.find(">") >= 0:
            break

# send command / receive response
def command(pkt, cr, printdata=True) -> Optional[Tuple]:
    # send command packet
    send_packet(pkt, cr)
    # read response packet
    read_packet()

def upgradeFw(fw_file):
    with open(fw_file, "rb") as f:
        data = f.read()
        data += b'\x00' * ((128 - (len(data) & 0x7F)) & 0x7F)
        total = len(data) // 128
        block =0
        command(make_packet("firmwareupdate ", pack('<H', total)), 1)
        for block in range(total):
            #print("{} / {}".format(block, total))
            command(make_packet('', pack('<HH', block, total) + data[block*128:(block+1)*128]), 0)
            printProgressBar(block+1, total, prefix = 'Loading '+fw_file)


ser = Serial(baudrate=115200, timeout=1, inter_byte_timeout=0.010, rtscts=False)

if __name__ == '__main__':
    fw_file, ser_dev = getopts(sys.argv[1:])
    ser.port = ser_dev
    ser.rts = 0
    ser.open()
    upgradeFw(fw_file)
    print("\n\nFirmware {} upgrade done !!".format(fw_file))
    print("Reseting Device")
    time.sleep(2.5)
    send_packet("reset".encode(), 1)
    #time.sleep(2)
    print("Reset Done")
    ser.close()
