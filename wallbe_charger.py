#!/usr/bin/env python

# import normal packages
from enum import IntEnum
import struct

import platform
import logging
import os
import sys

if sys.version_info.major == 2:
    import gobject
else:
    from gi.repository import GLib as gobject
import sys
import time
import requests  # for http GET
import configparser  # for config/ini file

# our own packages from victron
sys.path.insert(1, os.path.join(os.path.dirname(__file__), '/opt/victronenergy/dbus-systemcalc-py/ext/velib_python'))
from vedbus import VeDbusService

sys.path.insert(1, os.path.join(os.path.dirname(__file__), '/opt/victronenergy/dbus-modbus-client'))
import device
import mdns
import probe
from register import *

class WALLBE_MODE(IntEnum):
    MANUAL          = 0
    AUTO            = 1

class WALLBE_CHARGE(IntEnum):
    DISABLED = 0
    ENABLED  = 1

class WALLBE_STATUS(IntEnum):
    DISCONNECTED    = 0
    CONNECTED       = 1
    CHARGING        = 2
    CHARGED         = 3
    WAIT_SUN        = 4
    WAIT_RFID       = 5
    WAIT_START      = 6
    LOW_SOC         = 7
    GND_ERROR       = 8
    WELD_CON        = 9
    CP_SHORTED      = 10

class WALLBE_POSITION(IntEnum):
    OUTPUT = 0
    INPUT = 1

class Reg_ver(Reg, int):
    def __init__(self, base, name):
        Reg.__init__(self, base, 2, name)

    def __int__(self):
        v = self.value
        return v[1] << 16 | v[2] << 8 | v[3]

    def __str__(self):
        if self.value[3] == 0xFF:
            return '%x.%x' % self.value[1:3]
        return '%x.%x~%x' % self.value[1:4]

    def decode(self, values):
        return self.update(struct.unpack('4B', struct.pack('>2H', *values)))

class WALLBE_Charger(device.ModbusDevice):
    allowed_roles = None
    default_role = 'wallbecharger'
    default_instance = 40
    productid = 0xc024
    productname = 'WALLBE Charging Station'
    min_timeout = 0.5

    def __init__(self, *args):
        super(EV_Charger, self).__init__(*args)

        self.info_regs = [
            Reg_text(5001, 6, '/Serial', little=True),
            Reg_ver(5007, '/FirmwareVersion'),
        ]

        self.data_regs = [
            Reg_e16(5009, '/Mode', WALLBE_MODE, write=True),
            Reg_e16(5010, '/StartStop', WALLBE_CHARGE, write=True),
            Reg_u16(5011, '/Ac/L1/Power', 1, '%d W'),
            Reg_u16(5012, '/Ac/L2/Power', 1, '%d W'),
            Reg_u16(5013, '/Ac/L3/Power', 1, '%d W'),
            Reg_u16(5014, '/Ac/Power',    1, '%d W'),
            Reg_e16(5015, '/Status', WALLBE_STATUS),
            Reg_u16(5016, '/SetCurrent',  1, '%d A', write=True),
            Reg_u16(5017, '/MaxCurrent',  1, '%d A', write=True),
            Reg_u16(5018, '/Current',    10, '%.1f A'),
            Reg_u32b(5019, '/ChargingTime', 1, '%d s'),
            Reg_u16(5021, '/Ac/Energy/Forward', 100, '%.2f kWh'),
            Reg_e16(5026, '/Position', WALLBE_POSITION, write=True),
            Reg_text(5027, 22, '/CustomName', little=True, encoding='utf-8', write=True),
            Reg_u16(5049, '/AutoStart', write=(0,1))
        ]

    def device_init(self):
        # Firmware check, before 1.21~1 we could only fetch 50 registers
        if self.read_register(self.info_regs[1]) >= (0, 0x01, 0x21, 0x01):
            self.data_regs.append(
                Reg_u16(5050, '/EnableDisplay', write=(0, 1)))

    def get_ident(self):
        return 'evc_%s' % self.info['/Serial']

class WALLBE_Charger_AC22E(WALLBE_Charger):
    productid = 0xc025

class WALLBE_Charger_AC22NS(WALLBE_Charger):
    productid = 0xc026

models = {
    WALLBE_Charger.productid: {
        'model':    'AC22',
        'handler':  WALLBE_Charger,
    },
    WALLBE_Charger_AC22E.productid: {
        'model':    'AC22E',
        'handler':  WALLBE_Charger_AC22E,
    },
    WALLBE_Charger_AC22NS.productid: {
        'model':    'AC22NS',
        'handler':  WALLBE_Charger_AC22NS,
    },
}

probe.add_handler(probe.ModelRegister(5000, models,
                                      methods=['tcp'],
                                      units=[1]))
mdns.add_service('_victron-car-charger._tcp')
