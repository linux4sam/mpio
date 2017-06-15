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
"""
Monitor and print the ADC value of a specific channel.
"""
import mio
import sys
import time

def main(device, channel):
    adc = mio.ADC(device);
    value = None
    while True:
        current = adc.value(channel)
        if value != current:
            sys.stdout.write("\rADC value: {0}".format(current))
            sys.stdout.flush()
            value = current
            time.sleep(0.5)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: ./adc1.py DEVICE CHANNEL")
        sys.exit(1)

    main(int(sys.argv[1]), int(sys.argv[2]))
