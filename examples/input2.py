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
Connects to the interactively selected input device and any time a button is
pressed on that device it will turn on the selected LED.
"""
import mio
import sys

if sys.version_info[0] == 3:
    raw_input = input

def main():
    leds = mio.LED.enumerate()
    print("\n".join(leds))

    led_name = raw_input("Which led name? ")
    led = mio.LED(led_name)

    devices = mio.Input.enumerate()
    print "Available input devices"
    for d in devices:
        print d, "(", mio.Input.desc(d), ")"

    device = raw_input("Which input name? ")

    i = mio.Input(device)
    print "Press input for", device, "now"
    while True:
        (tv_sec, tv_usec, evtype, code, value) = i.read()
        if evtype == mio.Input.TYPE_EV_KEY:
            if value == 1:
                print "On"
                led.brightness = True
            elif value == 0:
                print "Off"
                led.brightness = False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print("Usage: ./input2.py")
        sys.exit(1)

    main()
