#
# Copyright (c) 2015-2016 vsergeev / Ivan (Vanya) A. Sergeev
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
"""i2c module"""
import os
import ctypes
import array
import fcntl

class _CI2CMessage(ctypes.Structure):
    _fields_ = [
        ("addr", ctypes.c_ushort),
        ("flags", ctypes.c_ushort),
        ("len", ctypes.c_ushort),
        ("buf", ctypes.POINTER(ctypes.c_ubyte)),
    ]

class _CI2CIocTransfer(ctypes.Structure):
    _fields_ = [
        ("msgs", ctypes.POINTER(_CI2CMessage)),
        ("nmsgs", ctypes.c_uint),
    ]

class I2C(object):
    """Interface to I2C buses available on the system. This interface only
    supports being a master.

    The I2C bus dev must exist at some path like /dev/i2c-0. With that, this API
    can be used to communicate to any slave device connected to that bus. To
    communicate with the slave you must know the slave address and the format of
    messages the slave device expects.  There is no slave device driver
    involved, so you have to manually communicate with the device.

    Args:
        devpath (str): Complete path to the I2C device.
    """

    # Constants scraped from <linux/i2c-dev.h> and <linux/i2c.h>
    _I2C_IOC_FUNCS = 0x705
    _I2C_IOC_RDWR = 0x707
    _I2C_FUNC_I2C = 0x1
    _I2C_M_TEN = 0x0010
    _I2C_M_RD = 0x0001
    _I2C_M_STOP = 0x8000
    _I2C_M_NOSTART = 0x4000
    _I2C_M_REV_DIR_ADDR = 0x2000
    _I2C_M_IGNORE_NAK = 0x1000
    _I2C_M_NO_RD_ACK = 0x0800
    _I2C_M_RECV_LEN = 0x0400

    def __init__(self, devpath):
        self._fd = None
        self._devpath = None
        self._open(devpath)

    def __del__(self):
        self.close()

    def __enter__(self):
        pass

    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

    def _open(self, devpath):
        self._fd = os.open(devpath, os.O_RDWR)
        self._devpath = devpath

        buf = array.array('I', [0])
        try:
            fcntl.ioctl(self._fd, I2C._I2C_IOC_FUNCS, buf, True)
        except OSError as error:
            self.close()
            raise error

        if (buf[0] & I2C._I2C_FUNC_I2C) == 0:
            self.close()
            raise IOError("I2C device does not support I2C_RDWR")

    @property
    def fd(self):
        """File descriptor of the underlying file.

        :type: int
        """
        return self._fd

    def transfer(self, addr, messages):
        """Transfer `messages` to the specified I2C slave `addr`. Modifies the
        `messages` array with the results of any read transactions.

        Args:
            addr (int): I2C address.
            messages (list): list of I2C.Message messages.

        Raises:
            TypeError: if `messages` type is not list.
            ValueError: if `messages` length is zero, or if message data is not
                        valid bytes.
        """
        if not isinstance(messages, list):
            raise TypeError("Invalid messages type, should be list of I2C.Message.")
        elif len(messages) == 0:
            raise ValueError("Invalid messages data, should be non-zero length.")

        # Convert I2C.Message messages to _CI2CMessage messages
        cmessages = (_CI2CMessage * len(messages))()
        for i in range(len(messages)): #pylint: disable=consider-using-enumerate
            # Convert I2C.Message data to bytes
            if isinstance(messages[i].data, bytes):
                data = messages[i].data
            elif isinstance(messages[i].data, bytearray):
                data = bytes(messages[i].data)
            elif isinstance(messages[i].data, list):
                data = bytes(bytearray(messages[i].data))

            cmessages[i].addr = addr
            cmessages[i].flags = messages[i].flags | (I2C._I2C_M_RD if messages[i].read else 0)
            cmessages[i].len = len(data)
            cmessages[i].buf = ctypes.cast(ctypes.create_string_buffer(data, len(data)),
                                           ctypes.POINTER(ctypes.c_ubyte))

        # Prepare transfer structure
        i2c_xfer = _CI2CIocTransfer()
        i2c_xfer.nmsgs = len(cmessages) #pylint: disable=attribute-defined-outside-init
        i2c_xfer.msgs = cmessages #pylint: disable=attribute-defined-outside-init

        # Transfer
        fcntl.ioctl(self._fd, I2C._I2C_IOC_RDWR, i2c_xfer, False)

        # Update any read I2C.Message messages
        for i in range(len(messages)): #pylint: disable=consider-using-enumerate
            if messages[i].read:
                data = [cmessages[i].buf[j] for j in range(cmessages[i].len)]
                # Convert read data to type used in I2C.Message messages
                if isinstance(messages[i].data, list):
                    messages[i].data = data
                elif isinstance(messages[i].data, bytearray):
                    messages[i].data = bytearray(data) #pylint: disable=redefined-variable-type
                elif isinstance(messages[i].data, bytes):
                    messages[i].data = bytes(bytearray(data))

    def close(self):
        """Close the device and release any system resources.
        """
        if hasattr(self, '_fd'):
            if self._fd is not None:
                os.close(self._fd)
                self._fd = None

    @property
    def devpath(self):
        """Path to the spidev.

        Returns:
            str
        """
        return self._devpath

    def __str__(self):
        return ("I2C (devpath=%s, fd=%d)") % (self.devpath,
                                              self.fd)

    class Message(object):
        """Instantiate an I2C Message object.

        Args:
            data (bytes, bytearray, list): a byte array or list of 8-bit
                         integers to write.
            read (bool): specify this as a read message, where `data`
                         serves as placeholder bytes for the read.
            flags (int): additional i2c-dev flags for this message.

        Returns:
            Message: Message object.

        Raises:
            TypeError: if `data`, `read`, or `flags` types are invalid.
        """

        def __init__(self, data, read=False, flags=0):
            if not isinstance(data, (bytes, bytearray, list)):
                raise TypeError("Invalid data type, should be bytes, bytearray, or list.")
            if not isinstance(read, bool):
                raise TypeError("Invalid read type, should be boolean.")
            if not isinstance(flags, int):
                raise TypeError("Invalid flags type, should be integer.")

            self.data = data
            self.read = read
            self.flags = flags
