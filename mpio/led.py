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
"""led module"""
import os

from mpio import utils

_LED_ROOT = '/sys/class/leds'
_LED_PATH = lambda name: os.path.join(_LED_ROOT, name)
_LED_FILE = lambda name, filename: os.path.join(_LED_PATH(name), filename)

class LED(object):
    """LED object using the specified LED name.

    To determine what LED names are available on the system, the `enumerate()`
    function will return a list.  That name can then be used to contruct an LED
    object and control the LED.

    Note:
        In the case of a single physical RGB LED, this will usually show up as 3
        different LEDs in this interface.  This allows you to set the appropriate
        and independent R-G-B brightness values.

    Note:
        This API should not be confused with just connecting up a physical LED to a
        gpio. This is not a generic interface for working with any LED. Unless you
        configure an LED in the Linux LED subsystem using Device Tree or hard coded
        setup, that LED won't show up to this module. For that, you shoud use the
        GPIO class.

    Args:
        name (str): The name of the LED.  For valid values, call enumerate().
        value (int, bool): The brightness value or ``True`` for max
                           brightness and ``False`` for off.
    """

    def __init__(self, name, value=None):
        self._name = name

        if not os.path.isdir(_LED_PATH(name)):
            raise OSError("LED %s not found" % _LED_PATH(name))

        if value is not None:
            self.brightness = value

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

    @property
    def name(self):
        """The LED name."""
        return self._name

    @property
    def max_brightness(self):
        """Maximum brightness value supportd by the LED.

        Returns:
            int
        """
        return int(utils.readstr_all(_LED_FILE(self._name, 'max_brightness')))

    def write(self, value):
        """Set the output brightness of the LED.

        Args:
            value (int, bool): The brightness value or ``True`` for max
                               brightness and ``False`` for off.
        """
        if not isinstance(value, (bool, int)):
            raise TypeError("brightness must be a bool or int.")

        if isinstance(value, bool):
            value = self.max_brightness if value else 0
        else:
            value = int(value)

        utils.writestr_all(_LED_FILE(self._name, 'brightness'), value)

    def read(self):
        """Get the output brightness of the LED.

        Returns:
            int
        """
        return int(utils.readstr_all(_LED_FILE(self._name, 'brightness')))

    brightness = property(read, write)

    def close(self):
        """Close the device and release any system resources."""
        pass

    @staticmethod
    def enumerate():
        """Enumerate a list of LED names available on the system.

        Returns:
            list
        """
        names = [f for f in os.listdir(_LED_ROOT) if \
                 os.path.isdir(os.path.join(_LED_ROOT, f))]
        return sorted(names)

    def __str__(self):
        return ("LED (name=%s, brightness=%d, max_brightness=%d)") % (self.name,
                                                                      self.brightness,
                                                                      self.max_brightness)
