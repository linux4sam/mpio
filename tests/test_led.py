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
import sys
import os
import unittest
from mio import LED

if sys.version_info[0] == 3:
    raw_input = input

class TestGeneral(unittest.TestCase):

    def test_exceptions(self):
        self.assertRaises(OSError, LED, "/invalid/path")

    def test_open_close(self):

        leds = LED.enumerate()
        self.assertTrue(len(leds) > 0)

        led_name = leds[0]

        led = LED(led_name, 0)
        self.assertEqual(led.name, led_name)
        self.assertTrue(led.max_brightness > 0)

        led.write(1)
        self.assertEqual(led.read(), 1)

        led.write(0)
        self.assertEqual(led.read(), 0)

        led.brightness = 1
        self.assertEqual(led.brightness, 1)

        led.brightness = 0
        self.assertEqual(led.brightness, 0)

        led.brightness = led.max_brightness
        self.assertEqual(led.brightness, led.max_brightness)

        led.write(True)
        self.assertEqual(led.read(), led.max_brightness)

        led.write(False)
        self.assertEqual(led.read(), 0)

        led.close()

    @unittest.skipIf(os.environ.get('NOINTERACTIVE', False), "interactive disabled")
    def test_interactive(self):

        leds = LED.enumerate()
        self.assertTrue(len(leds) > 0)

        led_name = leds[0]

        led = LED(led_name, False)

        led.write(False)
        self.assertEqual(raw_input("LED {} off? y/n ".format(led_name)), "y")

        led.write(True)
        self.assertEqual(raw_input("LED {} on? y/n ".format(led_name)), "y")

        led.write(False)
        self.assertEqual(raw_input("LED {} off? y/n ".format(led_name)), "y")

        led.close()

if __name__ == '__main__':
    unittest.main()
