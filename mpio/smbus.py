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
"""smbus module"""
import os
import ctypes
import struct
import fcntl

# from <linux/i2c-dev.h> and <linux/i2c.h>
_I2C_RETRIES = 0x0701
_I2C_SLAVE = 0x0703
_I2C_SLAVE_FORCE = 0x0706
_I2C_SMBUS = 0x0720
_I2C_SMBUS_WRITE = 0
_I2C_SMBUS_READ = 1
_I2C_SMBUS_BYTE_DATA = 2
_I2C_SMBUS_BLOCK_DATA = 5

# mimicks struct i2c_smbus_ioctl_data
class _CSMBMessage(ctypes.Structure):
    _fields_ = [
        ('read_write', ctypes.c_uint8),
        ('command', ctypes.c_uint8),
        ('size', ctypes.c_int),
        ('data', ctypes.POINTER(ctypes.c_uint8))]

POINTER_C_UINT8 = ctypes.POINTER(ctypes.c_uint8)

class SMBus(object):
    """SMBus object that opens the I2C device at the specified path.

    Similar to the I2C class, this provides simple System Management Bus (SMB)
    communications for performing byte and block transfers.

    See Also:
        For an alternate package for interfacing with smbus devices, see
        `smbus-cffi <https://pypi.python.org/pypi/smbus-cffi>`_.

    Args:
        devpath (str): Complete path to the I2C device.
    """

    def __init__(self, devpath):
        self._fd = None
        self._devpath = None
        self._addr = None
        self._open(devpath)

    def _open(self, devpath):
        self._fd = os.open(devpath, os.O_RDWR)
        self._devpath = devpath
        fcntl.ioctl(self._fd, _I2C_RETRIES, 3)

    def __del__(self):
        self.close()

    def __enter__(self):
        pass

    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

    @property
    def fd(self):
        """File descriptor of the underlying file.

        :type: int
        """
        return self._fd

    @property
    def devpath(self):
        """Path to the spidev.

        Returns:
            str
        """
        return self._devpath

    def _set_addr(self, addr):
        if self._addr != addr:
            #fcntl.ioctl(self._fd, _I2C_SLAVE, addr)
            fcntl.ioctl(self._fd, _I2C_SLAVE_FORCE, addr)
            self._addr = addr

    def write_byte(self, addr, command, value):
        """Write a byte of data.

        Args:
            addr (int): 7-bit slave address.
        """
        self._set_addr(addr)
        byte_value = ctypes.c_ubyte(value)
        data_pointer = POINTER_C_UINT8(byte_value)
        msg = _CSMBMessage(read_write=_I2C_SMBUS_WRITE,
                           command=command,
                           size=_I2C_SMBUS_BYTE_DATA,
                           data=data_pointer)
        fcntl.ioctl(self._fd, _I2C_SMBUS, msg)

    def read_byte(self, addr, command):
        """Read a byte of data.

        Args:
            addr (int): 7-bit slave address.
        """
        self._set_addr(addr)
        data_pointer = POINTER_C_UINT8(ctypes.c_uint8())
        msg = _CSMBMessage(read_write=_I2C_SMBUS_READ,
                           command=command,
                           size=_I2C_SMBUS_BYTE_DATA,
                           data=data_pointer)
        fcntl.ioctl(self._fd, _I2C_SMBUS, msg)
        [result] = struct.unpack("B", data_pointer.contents)
        return result

    def close(self):
        """Close the device and release any system resources.
        """
        if hasattr(self, '_fd'):
            if self._fd is not None:
                os.close(self._fd)
                self._fd = None

    def __str__(self):
        return ("SMBus (devpath=%s, fd=%d)") % (self.devpath, self.fd)
