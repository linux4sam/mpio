#!/usr/bin/env python
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
"""
Given an ADC device, list the microvolts for all available channels.
"""
import mpio
import sys

def main(device):
    adc = mpio.ADC(device);
    for channel in adc.available_channels():
        print "Channel", channel, "microvolts:", adc.microvolts(channel)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ./adc1.py DEVICE")
        sys.exit(1)

    main(int(sys.argv[1]))
