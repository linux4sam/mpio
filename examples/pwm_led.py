#!/usr/bin/env python
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

from mio import PWM
import sys
import time

def main(device, channel):

    # 100 Hz
    pwm = PWM(device, channel, 10000, 0, polarity=PWM.INVERSED)

    while True:
        for i in range(0.1, 0.9, 0.01):
            pwm.duty_cycle = i
            time.sleep(0.001)

        for i in range(0.9, 0.0, -0.01):
            pwm.duty_cycle = i
            time.sleep(0.001)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: ./pwm_led.py DEVICE CHANNEL")
        sys.exit(1)

    main(int(sys.argv[1]), int(sys.argv[2]))
