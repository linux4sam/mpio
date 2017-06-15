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

def main():
    pwm = mio.PWM(0, 0, 10000, 10)

    while True:
        for i in range(1,10):
            pwm.duty_cycle = (i * 1000)

        for i in range(1,10):
            pwm.duty_cycle = (10000 - (i * 1000))

if __name__ == "__main__":
    main()
