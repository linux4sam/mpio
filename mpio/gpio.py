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
"""gpio module"""
import array
import ctypes
import fcntl
import glob
import logging
import os
import select
import time

from mpio.ioctl import IOR, IOWR

# from <uapi/linux/gpio.h>
_GPIOHANDLES_MAX = 64

_GPIOHANDLE_GET_LINE_VALUES_IOCTL = IOWR(0xB4, 0x08, "=" + str(_GPIOHANDLES_MAX) + "B")
_GPIOHANDLE_SET_LINE_VALUES_IOCTL = IOWR(0xB4, 0x09, "=" + str(_GPIOHANDLES_MAX) + "B")

class _CGPIOGPIOChipInfo(ctypes.Structure):
    _fields_ = [
        ("name", ctypes.c_char * 32),
        ("label", ctypes.c_char * 32),
        ("lines", ctypes.c_uint),
    ]

_GPIO_GET_CHIPINFO_IOCTL = IOR(0xB4, 0x01, "=32s32sI")

class _CGPIOGPIOLineInfo(ctypes.Structure):
    _fields_ = [
        ("line_offset", ctypes.c_uint),
        ("flags", ctypes.c_uint),
        ("name", ctypes.c_char * 32),
        ("consumer", ctypes.c_char * 32),
    ]

_GPIO_GET_LINEINFO_IOCTL = IOWR(0xB4, 0x02, "=II32s32s")

_GPIOHANDLE_REQUEST_INPUT = 1 << 0
_GPIOHANDLE_REQUEST_OUTPUT = 1 << 1
_GPIOHANDLE_REQUEST_ACTIVE_LOW = 1 << 2
_GPIOHANDLE_REQUEST_OPEN_DRAIN = 1 << 3
_GPIOHANDLE_REQUEST_OPEN_SOURCE = 1 << 4

class _CGPIOGPIOHandleRequest(ctypes.Structure):
    _fields_ = [
        ("lineoffsets", ctypes.c_uint * _GPIOHANDLES_MAX),
        ("flags", ctypes.c_uint),
        ("default_values", ctypes.c_ubyte * _GPIOHANDLES_MAX),
        ("consumer_label", ctypes.c_char * 32),
        ("lines", ctypes.c_uint),
        ("fd", ctypes.c_int),
    ]

_GPIO_GET_LINEHANDLE_IOCTL = IOWR(0xB4, 0x03, "=" + str(_GPIOHANDLES_MAX) + "II"
                                  + str(_GPIOHANDLES_MAX) + "B32sII")

_GPIOEVENT_REQUEST_RISING_EDGE = 1 << 0
_GPIOEVENT_REQUEST_FALLING_EDGE = 1 << 1
_GPIOEVENT_REQUEST_BOTH_EDGES = _GPIOEVENT_REQUEST_RISING_EDGE | \
                                _GPIOEVENT_REQUEST_FALLING_EDGE

class _CGPIOGPIOEventRequest(ctypes.Structure):
    _fields_ = [
        ("lineoffset", ctypes.c_uint),
        ("handleflags", ctypes.c_uint),
        ("eventflags", ctypes.c_uint),
        ("consumer_label", ctypes.c_char * 32),
        ("fd", ctypes.c_int),
    ]

_GPIO_GET_LINEEVENT_IOCTL = IOWR(0xB4, 0x04, "=III32sI")

class _CGPIOGPIOEventData(ctypes.Structure):
    _fields_ = [
        ("timestamp", ctypes.c_ulonglong),
        ("id", ctypes.c_uint),
    ]

_GPIOEVENT_EVENT_RISING_EDGE = 0x01
_GPIOEVENT_EVENT_FALLING_EDGE = 0x02

_GPIO_ROOT = '/dev/gpiochip'

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
        mode (GPIO.IN, GPIO.OUT): The mode of the GPIO. ``None`` for don't change.
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

    def __init__(self, pin, mode, initial=False, force_own=False):
        self._fd = None
        self._pin = None
        self._line_offset = None
        self._name = None
        self._mode = None
        self._logger = logging.getLogger(__name__)

        if not isinstance(pin, (int, str)):
            raise TypeError("Invalid pin type, must be int.")

        if mode not in (self.IN, self.OUT):
            raise ValueError("Invalid mode value.")

        if isinstance(pin, str):
            pin = GPIO._name_lookup(pin)
            if pin is None:
                raise RuntimeError("Unknown pin name")

        self._name, self._line_offset = self._pin_lookup(pin)

        if self._name is None:
            raise ValueError("Invalid pin number.")

        # There's a bit of a race condition waiting for potential udev rules
        # to adjust the permissions on the files.  So, if we are getting a
        # permission denied error retry before aborting with the actual
        # exception.
        retries = 0
        while True:
            retries += 1
            try:
                self._fd = os.open(os.path.join("/dev", self._name), os.O_RDWR)
                break
            except OSError as error:
                if error.errno != 13 or retries > 20:
                    raise error
                else:
                    self._logger.debug("retrying gpio setup")
                    time.sleep(0.1)

        self._pin = pin
        self._mode = mode

        if self.mode == self.OUT and initial is not None:
            self.set(initial)

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
        return GPIO.pin_to_name(self._pin)

    @property
    def interrupts_available(self):
        """Whether or not this GPIO supports edge interrupts.

        :type: bool
        """
        return True

    def close(self):
        """Close the device and release any system resources."""
        if hasattr(self, '_fd'):
            if self._fd is not None:
                os.close(self._fd)
                self._fd = None

    @property
    def mode(self):
        """The mode of the pin.

        :type: bool
        """
        return self._mode

    def get(self):
        """Read the boolean value of the pin.

        Note:
            This is really only valuable if the pin is actually configured as an
            input.

        Returns:
            bool
        """
        if self.mode != self.IN:
            raise RuntimeError("Cannot get value on pin that is not input mode.")

        req = _CGPIOGPIOHandleRequest()
        req.lineoffsets[0] = self._line_offset
        req.default_values[0] = 0
        req.flags = _GPIOHANDLE_REQUEST_INPUT
        req.consumer_label = b'MPIO'
        req.lines = 1
        req.fd = 0

        fcntl.ioctl(self._fd, _GPIO_GET_LINEHANDLE_IOCTL, req, True)

        try:
            data = array.array('B', [0] * _GPIOHANDLES_MAX)
            fcntl.ioctl(req.fd, _GPIOHANDLE_GET_LINE_VALUES_IOCTL, data, True)
            return bool(data[0])
        except:
            raise
        finally:
            os.close(req.fd)

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

        req = _CGPIOGPIOHandleRequest()
        req.lineoffsets[0] = self._line_offset
        req.default_values[0] = 0
        req.flags = _GPIOHANDLE_REQUEST_OUTPUT
        req.consumer_label = b'MPIO'
        req.lines = 1
        req.fd = 0

        fcntl.ioctl(self._fd, _GPIO_GET_LINEHANDLE_IOCTL, req, True)

        try:
            data = array.array('B', [0] * _GPIOHANDLES_MAX)
            data[0] = int(bool(value))
            fcntl.ioctl(req.fd, _GPIOHANDLE_SET_LINE_VALUES_IOCTL, data, True)
        except:
            raise
        finally:
            os.close(req.fd)

    input = get
    """This is an alias for ``get()``."""

    output = set
    """This is an alias for ``set(value)``."""

    def poll(self, edge=BOTH, timeout=-1):
        """Block and wait for an edge interrupt or the timeout to occur.

        Args:
            edge (GPIO.RISING, GPIO.FALLING, GPIO.BOTH, str): The edge to interrupt on.
            timeout (int, float): timeout duration in seconds.
        Returns:
            mixed: value if an edge event occurred, ``None`` on timeout.
        """
        if not isinstance(timeout, (int, float)):
            raise TypeError("Invalid timeout type, must be int, float, or None.")

        if edge not in (self.RISING, self.FALLING, self.BOTH):
            raise ValueError("Invalid edge value.")

        if not self.interrupts_available:
            raise RuntimeError("Interrupts not configurable on pin.")

        req = _CGPIOGPIOEventRequest()
        req.lineoffset = self._line_offset
        req.handleflags = 0
        req.consumer_label = b'MPIO'
        if edge == self.BOTH:
            req.eventflags = _GPIOEVENT_REQUEST_RISING_EDGE | \
                             _GPIOEVENT_REQUEST_FALLING_EDGE
        elif edge == self.RISING:
            req.eventflags = _GPIOEVENT_REQUEST_RISING_EDGE
        elif edge == self.FALLING:
            req.eventflags = _GPIOEVENT_REQUEST_FALLING_EDGE
        req.fd = 0
        fcntl.ioctl(self._fd, _GPIO_GET_LINEEVENT_IOCTL, req, True)

        try:
            epoll = select.epoll()
            epoll.register(req.fd, select.EPOLLIN | select.EPOLLET | select.EPOLLPRI)
            events = epoll.poll(timeout)

            result = None
            for _, event in events:
                if not event & (select.EPOLLIN | select.EPOLLET):
                    continue
                else:
                    buf = os.read(req.fd, ctypes.sizeof(_CGPIOGPIOEventData))
                    event = _CGPIOGPIOEventData.from_buffer_copy(buf)
                    if event.id == _GPIOEVENT_EVENT_RISING_EDGE:
                        result = self.RISING
                    elif event.id == _GPIOEVENT_EVENT_FALLING_EDGE:
                        result = self.FALLING
                    else:
                        result = None
        except:
            raise
        finally:
            os.close(req.fd)

        return result

    @staticmethod
    def _pin_lookup(pin):
        """Lookup a pin and return the gpiochip name and line offset in that
        chip.

        Returns:
            tuple: Returns the str name and integer line offset.
        """
        offset = 0
        for devname in sorted(glob.glob(_GPIO_ROOT + "*")):
            fd = os.open(os.path.join("/dev", devname), os.O_RDONLY)
            info = _CGPIOGPIOChipInfo()
            fcntl.ioctl(fd, _GPIO_GET_CHIPINFO_IOCTL, info, True)
            for line_offset in range(info.lines):
                if offset == pin:
                    return devname, line_offset
                offset += 1
            os.close(fd)

        return None, None

    @staticmethod
    def _name_lookup(name):
        """Lookup a pin by name.

        Returns:
            integer: Returns the pin or None.
        """
        if name is None:
            return None

        offset = 0
        for devname in sorted(glob.glob(_GPIO_ROOT + "*")):
            fd = os.open(os.path.join("/dev", devname), os.O_RDONLY)
            info = _CGPIOGPIOChipInfo()
            fcntl.ioctl(fd, _GPIO_GET_CHIPINFO_IOCTL, info, True)
            for line_offset in range(info.lines):
                line = _CGPIOGPIOLineInfo()
                line.line_offset = line_offset
                fcntl.ioctl(fd, _GPIO_GET_LINEINFO_IOCTL, line, True)
                if line.name == name:
                    return offset
                offset += 1
            os.close(fd)

        return None

    @staticmethod
    def pin_to_name(pin):
        """Lookup the name of a pin.

        Returns:
            str: Returns the pin name or None.
        """
        devname, line_offset = GPIO._pin_lookup(pin)
        if devname is not None:
            fd = os.open(os.path.join("/dev", devname), os.O_RDONLY)
            line = _CGPIOGPIOLineInfo()
            line.line_offset = line_offset
            fcntl.ioctl(fd, _GPIO_GET_LINEINFO_IOCTL, line, True)
            os.close(fd)
            return line.name

        return None

    @staticmethod
    def enumerate():
        """Enumerate a list of gpio pins available on the system.

        Returns:
            list
        """
        pins = []
        pin = 0
        for devname in sorted(glob.glob(_GPIO_ROOT + "*")):
            fd = os.open(os.path.join("/dev", devname), os.O_RDONLY)
            info = _CGPIOGPIOChipInfo()
            fcntl.ioctl(fd, _GPIO_GET_CHIPINFO_IOCTL, info, True)
            for _ in range(info.lines):
                pins.append(pin)
                pin += 1
            os.close(fd)
        return pins

    def __str__(self):
        return ("GPIO (fd=%d, pin=%d, name=%s, interrupts_available=%r, mode=%s)") % (
            self.fd,
            self.pin,
            self.name,
            self.interrupts_available,
            self.mode)
