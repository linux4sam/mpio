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

from mio import LED
import time

def main():
    red = LED("red")
    green = LED("green")
    blue = LED("blue")

    while True:
        red.brightness = True
        green.brightness = 0
        blue.brightness = 0
        time.sleep(1)

        red.brightness = 0
        green.brightness = True
        blue.brightness = 0
        time.sleep(1)

        red.brightness = 0
        green.brightness = 0
        blue.brightness = True
        time.sleep(1)

if __name__ == "__main__":
    main()
