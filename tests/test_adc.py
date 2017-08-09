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
from mpio import ADC

if sys.version_info[0] == 3:
    raw_input = input

device = int(os.environ.get('ADC_DEVICE', "0"), 0)
channel = int(os.environ.get('ADC_CHANNEL', "0"), 0)

class TestGeneral(unittest.TestCase):

    def test_arguments(self):
        self.assertRaises(TypeError, ADC, "invalid")
        self.assertRaises(OSError, ADC, 99)

    def test_open_close(self):

        adc = ADC(device);
        self.assertTrue(len(adc.name) > 0)
        self.assertTrue(adc.scale > 0)
        self.assertTrue(adc.microvolts > 0)
        self.assertTrue(adc.volts > 0)
        self.assertTrue(len(adc.available_channels) > 0)
        available_triggers = adc.available_triggers
        self.assertTrue(adc.sampling_frequency > 0)
        self.assertTrue(adc.value(channel) > 0)
        adc.close()

if __name__ == '__main__':
    unittest.main()
