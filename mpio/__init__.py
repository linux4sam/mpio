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
"""mpio module"""

# Pull everything public into the module
from .utils import cpu, board
from .gpio import GPIO
from .led import LED
from .pwm import PWM
from .adc import ADC
from .input import Input
from .i2c import I2C
from .spi import SPI
from .serial import Serial
from .devmem import DevMem
from .smbus import SMBus

__version__ = '1.7'
"mpio module version string."
