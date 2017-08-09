#
# Microchip Peripheral I/O
#
# Joshua Henderson <joshua.henderson@microchip.com>
# Copyright (C) 2017 Microchip Technology Inc.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import sys
import os
import unittest
import time
from mpio import SMBus

if sys.version_info[0] == 3:
    raw_input = input

devpath1 = os.environ.get('SMBUS_DEVPATH1', "/dev/i2c-2")
eeprom_addr = int(os.environ.get('SMBUS_EEPROM_ADDR', "0x54"), 0)

class TestGeneral(unittest.TestCase):

    def test_arguments(self):
        self.assertRaises(OSError, SMBus, "/invalid/path")

    def test_open_close(self):
        smbus = SMBus(devpath1)
        self.assertTrue(smbus.fd > 0)
        smbus.close()

    def test_eeprom(self):

        NUM_BYTES = 256

        sysfs_path = "/sys/bus/i2c/devices/%s-00%02x/eeprom" % (devpath1[-1], eeprom_addr)
        with open(sysfs_path, "rb") as f:
            eeprom_data = f.read(NUM_BYTES)

        data = bytearray()
        smbus = SMBus(devpath1)
        for addr in range(0, NUM_BYTES):
            byte = smbus.read_byte(eeprom_addr, addr)
            data.append(byte)

        self.assertEqual(eeprom_data, data)

        smbus.write_byte(eeprom_addr, 0x00, 0xDE)

        #
        # TODO: This is required otherwise we get a IOError: [Errno 121] Remote
        # I/O error when trying to do a read immediately after a write.
        #
        time.sleep(0.1)

        value = smbus.read_byte(eeprom_addr, 0x00)
        self.assertEqual(0xDE, value)

        smbus.write_byte(eeprom_addr, 0x00, data[0])

        smbus.close()

if __name__ == '__main__':
    unittest.main()
