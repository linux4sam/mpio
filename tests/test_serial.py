#
# Microchip IO
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
from mio import Serial

if sys.version_info[0] == 3:
    raw_input = input

devpath = os.environ.get('SERIAL_DEVPATH', "/dev/ttyS0")

class TestGeneral(unittest.TestCase):

    def test_arguments(self):
        self.assertRaises(TypeError, Serial, 1, 115200)
        self.assertRaises(TypeError, Serial, devpath, "str")

    def test_open_close(self):
        s = Serial(devpath, 115200)

        # check default values
        self.assertTrue(s.fd > 0)
        self.assertEqual(s.devpath, devpath)
        self.assertEqual(s.baudrate, 115200)
        self.assertEqual(s.databits, 8)
        self.assertEqual(s.stopbits, 1)
        self.assertEqual(s.parity, "none")
        self.assertEqual(s.xonxoff, False)
        self.assertEqual(s.rtscts, False)

        for i in range(1,1024):
            s.write("hello ");
        self.assertTrue(s.output_waiting() > 0)
        s.flush()

        s.close()

    @unittest.skipIf(os.environ.get('NOINTERACTIVE', False), "interactive disabled")
    def test_interactive(self):
        s = Serial(devpath, 115200)

        expected = "test"
        print("Enter '{}' on serial console...".format(expected))
        data = s.read(len(expected))
        self.assertEqual(data, expected)

        s.close()

if __name__ == '__main__':
    unittest.main()
