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
from mio import PWM

if sys.version_info[0] == 3:
    raw_input = input

class TestGeneral(unittest.TestCase):

    def test_arguments(self):
        self.assertRaises(TypeError, PWM, "invalid", "invalid")
        self.assertRaises(TypeError, PWM, 0, 0, "invalid")
        self.assertRaises(TypeError, PWM, 0, 0, 0, "invalid")
        self.assertRaises(ValueError, PWM, 0, 0, 0, 0, False, "invalid")

    def test_open_close(self):
        pwms = PWM.enumerate()
        self.assertTrue(len(pwms) > 0)

        chip = int(os.environ.get('PWM_CHIP', str(pwms[0])), 0)

        num_channels = PWM.num_channels(chip)
        self.assertTrue(num_channels > 0)

        channel = int(os.environ.get('PWM_CHANNEL', "0"), 0)

        pwm = PWM(chip, channel, 10000, 0.5, polarity=PWM.INVERSED)

        self.assertEqual(pwm.period, 10000)
        self.assertEqual(pwm.duty_cycle, 0.5)
        self.assertEqual(pwm.polarity, "inversed")

        pwm.enabled = False
        self.assertFalse(pwm.enabled)

        pwm.period = 10100
        self.assertEqual(pwm.period, 10100)

        pwm.duty_cycle = 0.01
        self.assertEqual(pwm.duty_cycle, 0.01)

        pwm.enabled = True
        self.assertTrue(pwm.enabled)

        pwm.close()


if __name__ == '__main__':
    unittest.main()
