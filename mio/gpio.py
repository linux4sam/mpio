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
"""gpio module"""
import os
import time
import select
import logging
import threading

from mio import utils

def _pin_to_name(pin):
    if utils.cpu() == "sama5d4":
        return 'pio' + str(chr(ord('A') + int(pin / 32))) + str(pin % 32)
    elif utils.cpu() == "sama5d2":
        return 'P' + str(chr(ord('A') + int(pin / 32))) + str(pin % 32)
    else:
        return 'gpio{}'.format(pin)

_GPIO_ROOT = '/sys/class/gpio'
_GPIO_PATH = lambda pin: os.path.join(_GPIO_ROOT, _pin_to_name(pin))
_GPIO_FILE = lambda pin, filename: os.path.join(_GPIO_PATH(pin), filename)

def _is_exported(pin):
    """Check if the pin was already exported on sysfs.
    """
    return os.path.isdir(_GPIO_PATH(pin))

class AsyncPoll(threading.Thread):
    """Asynchronous polling thread.
    """
    def __init__(self, gpio, callback, edge):
        super(AsyncPoll, self).__init__()
        self.gpio = gpio
        self.callback = callback
        self.edge = edge
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            if self.gpio.poll(self.edge, 0.1):
                self.callback()

    def stop(self):
        """Stop the capture thread from running.
        """
        self.running = False

class GPIO(object):
    """Create a GPIO object to control and monitor an input or output pin.

    Provides an interface to configure and use pins as general purpose digital
    inputs and outputs.

    Pin Numbering Scheme
        This interface uses pin numbers to identify pins that range from 0 to N. The
        pin numbering scheme involves groups of 32 pins.  The first group is 'A',
        the second group is 'B', and so on.  So, pin 0 is effectively A0. Pin 32 is
        B0, and so on.  This means if you want to use CPU pin PD15, you would use
        pin number `(('D'-'A') * 32) + 15 = 111` where ASCII `'D' - 'A' = 3`.

    Warning:
        Because internally the mode is set and then the value is set, there
        may be a flicker of the unintended value while configuring the pin.

    Args:
        pin (int): The pin number of the GPIO.
        mode (GPIO.IN, GPIO.OUT, None): The mode of the GPIO. ``None`` for don't change.
        pullup (None): Unsupported.  Must be None.
        initial (GPIO.LOW, GPIO.HIGH, bool): When the mode is ``GPIO.OUT``,
            this will be the initial value of the output.
        force_own (bool): When ``True``, steal ownership as necessary.
            However, this means that multiple objects are potentially
            controlling the pin.
    """

    IN, OUT = 'in', 'out'
    """Mode defines to specify the direction of the pin."""

    LOW, HIGH = False, True
    """Easy to use defines for the state of an input or output pin."""

    RISING, FALLING, BOTH = "rising", "falling", "both"
    """Defines for the edge interrupt type of the pin."""

    def __init__(self, pin, mode=None, pullup=None, initial=False, force_own=False):
        self._fd = None
        self._pin = None
        self._logger = logging.getLogger(__name__)

        if not isinstance(pin, int):
            raise TypeError("Invalid pin type, must be int.")

        if pullup is not None:
            raise ValueError("sysfs does not support pullups")

        if mode not in (self.IN, self.OUT, None):
            raise ValueError("Invalid mode value.")

        if _is_exported(pin) and not force_own:
            raise RuntimeError("Pin already owned.  Use force_own=True to override.")

        if not _is_exported(pin):
            utils.writestr_all(os.path.join(_GPIO_ROOT, 'export'), pin)

        # There's a bit of a race condition waiting for potential udev rules
        # to adjust the permissions on the files.  So, if we are getting a
        # permission denied error retry before aborting with the actual
        # exception.
        retries = 0
        while True:
            retries += 1
            try:
                self._fd = os.open(_GPIO_FILE(pin, 'value'), os.O_RDWR)
                break
            except OSError as error:
                if error.errno != 13 or retries > 20:
                    raise error
                else:
                    self._logger.debug("retrying gpio setup")
                    time.sleep(0.1)

        self._pin = pin
        if mode is not None:
            self._set_mode(mode, initial)

    def __del__(self):
        self.close()

    def __enter__(self):
        pass

    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

    @property
    def fd(self):
        """Get the file descriptor of the underlying gpio value file.

        :type: int
        """
        return self._fd

    @property
    def pin(self):
        """GPIO pin number.

        :type: int
        """
        return self._pin

    @property
    def name(self):
        """GPIO pin name.

        :type: str
        """
        return _pin_to_name(self._pin)

    @property
    def interrupts_available(self):
        """Whether or not this GPIO supports edge interrupts.

        :type: bool
        """

        if not _is_exported(self._pin):
            raise IOError("GPIO is not exported.")

        return os.path.isfile(_GPIO_FILE(self._pin, "edge"))

    def close(self):
        """Close the device and release any system resources."""
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
            utils.writestr_all(os.path.join(_GPIO_ROOT, 'unexport'), self._pin)

    @property
    def mode(self):
        """The mode of the pin.

        :type: bool
        """
        return utils.readstr_all(_GPIO_FILE(self._pin, 'direction'))

    def _set_mode(self, mode, initial=False):
        """Set the mode of the pin.

        Args:
            mode (GPIO.IN, GPIO.OUT): The mode of the GPIO.
            initial (bool): If the mode is ``GPIO.OUT``, then this will be the initial value.

        Warning:
            Because internally the mode is set and then the value is set, there
            may be a flicker of the unintended value while configuring the pin.
        """
        utils.writestr_all(_GPIO_FILE(self._pin, 'direction'), mode)

        if mode == self.OUT:
            self.set(initial)

    def get(self):
        """Read the boolean value of the pin.

        Note:
            This is really only valuable if the pin is actually configured as an
            input.

        Returns:
            bool
        """
        return bool(int(utils.readstr(self._fd)))

    def set(self, value):
        """Set the boolean output value of the pin.

        Note:
            This is really only valuable if the pin is actually configured as an
            output.
        """

        if not isinstance(value, (bool, int)):
            raise TypeError("value must be a bool or int.")

        if self.mode != self.OUT:
            raise RuntimeError("Cannot set value on pin that is not output mode.")

        value = int(bool(value))
        utils.writestr(self._fd, value)

    input = get
    """This is an alias for ``get()``."""

    output = set
    """This is an alias for ``set(value)``."""

    def poll(self, edge=BOTH, timeout=None):
        """Block and wait for an edge interrupt or the timeout to occur.

        Args:
            edge (GPIO.RISING, GPIO.FALLING, GPIO.BOTH, str): The edge to interrupt on.
            timeout (int, float, None): timeout duration in seconds.
        Returns:
            mixed: value if an edge event occurred, ``None`` on timeout.
        """
        if not isinstance(timeout, (int, float, type(None))):
            raise TypeError("Invalid timeout type, must be int, float, or None.")

        if edge not in (self.RISING, self.FALLING, self.BOTH):
            raise ValueError("Invalid edge value.")

        if not self.interrupts_available:
            raise RuntimeError("Interrupts not configurable on pin.")

        utils.writestr_all(_GPIO_FILE(self._pin, 'edge'), edge)

        epoll = select.epoll()
        epoll.register(self._fd, select.EPOLLIN | select.EPOLLET | select.EPOLLPRI)

        events = epoll.poll(timeout)

        result = None
        for _, event in events:
            if not event & (select.EPOLLPRI | select.EPOLLET):
                continue
            else:
                result = self.get()

        return result

    def async_poll(self, callback, edge=BOTH):
        """Returns a thread that invokes the specified callback when an interrupt
        is detected asynchronously.

        Args:
            callback: Function to call when interrupt occurs.
            edge (GPIO.RISING, GPIO.FALLING, GPIO.BOTH, str): The edge to interrupt on.
        Returns:
            thread
        """
        handler = AsyncPoll(self, callback, edge)
        handler.start()
        while not handler.running:
            time.sleep(0.001)
        return handler

    @staticmethod
    def pin_to_name(pin):
        return _pin_to_name(pin)

    def __str__(self):
        return ("GPIO (fd=%d, pin=%d, name=%s, interrupts_available=%r, mode=%s)") % (
            self.fd,
            self.pin,
            self.name,
            self.interrupts_available,
            self.mode)
