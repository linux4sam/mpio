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
from mpio import I2C

if sys.version_info[0] == 3:
    raw_input = input

devpath1 = os.environ.get('SPI_DEVPATH1', "/dev/i2c-2")
eeprom_addr = int(os.environ.get('SPI_EEPROM_ADDR', "0x54"), 0)

class TestGeneral(unittest.TestCase):

    def test_arguments(self):
        self.assertRaises(OSError, I2C, "/invalid/path")

    def test_open_close(self):
        i2c = I2C(devpath1)

        # check default values
        self.assertTrue(i2c.fd > 0)

        i2c.close()

    def test_eeprom(self):

        NUM_BYTES = 256

        sysfs_path = "/sys/bus/i2c/devices/%s-00%02x/eeprom" % (devpath1[-1], eeprom_addr)
        with open(sysfs_path, "rb") as f:
            eeprom_data = f.read(NUM_BYTES)

        data = bytearray()
        i2c = I2C(devpath1)
        for addr in range(0, NUM_BYTES):
            msgs = [I2C.Message([addr]), I2C.Message([0x00], read=True)]
            i2c.transfer(eeprom_addr, msgs)
            data.append(msgs[1].data[0])

        self.assertEqual(eeprom_data, data)

        msgs = [I2C.Message(b"\x00"), I2C.Message(b"\x00", read=True)]
        i2c.transfer(eeprom_addr, msgs)
        self.assertTrue(isinstance(msgs[1].data, bytes))
        self.assertEqual(bytearray(msgs[1].data)[0], data[0])

        msgs = [I2C.Message(bytearray([0x00])), I2C.Message(bytearray([0x00]), read=True)]
        i2c.transfer(eeprom_addr, msgs)
        self.assertTrue(isinstance(msgs[1].data, bytearray))
        self.assertEqual(msgs[1].data[0], data[0])

        i2c.close()

    @unittest.skipIf(os.environ.get('NOINTERACTIVE', False), "interactive disabled")
    def test_interactive(self):
        devpath2 = os.environ.get('SPI_DEVPATH2', "/dev/i2c-1")
        i2c = I2C(devpath2)

        # S [ 0x52 W ] [0xaa] [0xbb] [0xcc] [0xdd] NA
        messages = [I2C.Message([0xaa, 0xbb, 0xcc, 0xdd])]

        raw_input("Press enter to start I2C transfer...")

        self.assertRaises(Exception, i2c.transfer, 0x52, messages)

        i2c.close()

        self.assertEqual(raw_input("I2C transfer OK? y/n "),  "y")

if __name__ == '__main__':
    unittest.main()
