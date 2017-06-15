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

import mio
import time

def main():
    leds = mio.LED.enumerate()
    for name in leds:
        print name
        l = mio.LED(name)
        l.brightness = l.max_brightness
        time.sleep(1)
        l.brightness = 0
        time.sleep(1)

if __name__ == "__main__":
    main()
