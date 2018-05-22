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
"""input module"""
import os
import struct
import fcntl

from mpio import utils
from mpio.ioctl import IOC, IOR, IOC_READ

_INPUT_ROOT = '/dev/input'
_INPUT_PATH = lambda name: os.path.join(_INPUT_ROOT, name)

# From <linux/input.h>
_EVIOCGVERSION = IOR(ord('E'), 0x01, "i")
_EVIOCGID = IOR(ord('E'), 0x02, "hhhh")
_EVIOCGNAME = IOC(IOC_READ, 69, 0x06, 255)

class Input(object):
    """Input object to receive input device events.

    Provides an interface to input subsytem devices available on the system.
    For example, a mouse or keyboard or gpio buttons can generate input events
    this interface can relay.

    See Also:
        For a more complete way to read linux input events, see the `evdev
        <https://pypi.python.org/pypi/evdev/>`_ package.

    Args:
        name (str): For valid values of name, call enumerate().
    """

    _FORMAT = 'llHHI'
    _EVENT_SIZE = struct.calcsize(_FORMAT)

    TYPE_EV_SYN = 0x00
    TYPE_EV_KEY = 0x01
    TYPE_EV_REL = 0x02
    TYPE_EV_ABS = 0x03
    TYPE_EV_MSC = 0x04
    TYPE_EV_SW = 0x05
    TYPE_EV_LED = 0x11
    TYPE_EV_SND = 0x12
    TYPE_EV_REP = 0x14
    TYPE_EV_FF = 0x15
    TYPE_EV_PWR = 0x16
    TYPE_EV_FF_STATUS = 0x17

    def __init__(self, name):
        self._fd = None
        self._name = None

        if not isinstance(name, str):
            raise TypeError("Invalid name type, must be str.")

        if not os.path.exists(_INPUT_PATH(name)):
            raise OSError("Input %s not found." % _INPUT_PATH(name))

        self._fd = os.open(_INPUT_PATH(name), os.O_RDWR)
        self._name = name

    def __del__(self):
        self.close()

    def __enter__(self):
        pass

    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

    @property
    def name(self):
        """The name identifier for the device.

        :type: str
        """
        return self._name

    def close(self):
        """Close the device and release any system resources."""
        if hasattr(self, '_fd'):
            if self._fd is not None:
                os.close(self._fd)
                self._fd = None
        self._name = None

    def read(self):
        """Perform a blocking read forever until an event is returned or an error
        occurs.

        Returns:
            (tv_sec, tv_usec, evtype, code, value)
        """
        event = os.read(self._fd, self._EVENT_SIZE)
        (tv_sec, tv_usec, evtype, code, value) = struct.unpack(self._FORMAT, event)
        return (tv_sec, tv_usec, evtype, code, value)

    @staticmethod
    def enumerate():
        """Enumerate a list of input event devices available on the system.

        Returns:
            list
        """
        names = [f for f in os.listdir(_INPUT_ROOT) if not
                 os.path.isdir(os.path.join(_INPUT_ROOT, f))]
        return sorted(names)

    @staticmethod
    def desc(name):
        """Get the human readable description of the input device.

        Returns:
            str
        """

        # This includes several different methods to try and get the desc.  If
        # one fails, try the next.
        try:
            with open(os.path.join('/sys/class/input', name, 'device/name'), 'r') as f:
                return utils.readstr(f)
        except IOError as error:
            if error.errno == 2:
                with open(_INPUT_PATH(name), 'r') as f:
                    try:
                        name = fcntl.ioctl(f, _EVIOCGNAME, chr(0) * 256)
                        return name.replace(chr(0), '')
                    except: # pylint: disable=bare-except
                        pass
            else:
                raise error

        return None

    @property
    def driver_version(self):
        """Get the driver version of the device.

        :type: str
        """
        data = fcntl.ioctl(self._fd, _EVIOCGVERSION, '\x00\x00\x00\x00')
        return struct.unpack("i", data)[0]

    @property
    def device_id(self):
        """Get the device id.

        :type: str
        """
        data = fcntl.ioctl(self._fd, _EVIOCGID, '\x00\x00\x00\x00\x00\x00\x00\x00')
        idbus, idvendor, idproduct, idversion = struct.unpack("hhhh", data)
        return idbus, idvendor, idproduct, idversion

    def __str__(self):
        return ("Input (name=%s, driver_version=%s, device_id=%s)") % (self.name,
                                                                       self.driver_version,
                                                                       self.device_id)
