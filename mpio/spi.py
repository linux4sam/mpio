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
"""spi module"""
import os
import fcntl
import array
import ctypes

class _CSpiIocTransfer(ctypes.Structure):
    _fields_ = [
        ('tx_buf', ctypes.c_ulonglong),
        ('rx_buf', ctypes.c_ulonglong),
        ('len', ctypes.c_uint),
        ('speed_hz', ctypes.c_uint),
        ('delay_usecs', ctypes.c_ushort),
        ('bits_per_word', ctypes.c_ubyte),
        ('cs_change', ctypes.c_ubyte),
        ('tx_nbits', ctypes.c_ubyte),
        ('rx_nbits', ctypes.c_ubyte),
        ('pad', ctypes.c_ushort),
    ]

class SPI(object):
    """Instantiate a SPI object and open the spidev device at the specified
    path with the specified SPI mode, max speed in hertz, and the defaults
    of "msb" bit order and 8 bits per word.

    The SPI bus dev must exist at some path like /dev/spidev0. With
    that, this API can be used to communicate to any device connected to that
    bus.

    Note:
        This requires the kernel module ``spidev`` to be available.

    See Also:
        For an alternate package for interfacing with SPI devices, see
        `spidev <https://pypi.python.org/pypi/spidev>`_.

    Args:
        devpath (str): spidev device path.
        mode (int): SPI mode, can be 0, 1, 2, 3.
        max_speed (int, float): maximum speed in Hertz.
        bit_order (str): bit order, can be "msb" or "lsb".
        bits_per_word (int): bits per word.
        extra_flags (int): extra spidev flags to be bitwise-ORed with the SPI mode.

    Raises:
        TypeError: if `devpath`, `mode`, `max_speed`, `bit_order`, `bits_per_word`,
                   or `extra_flags` types are invalid.
        ValueError: if `mode`, `bit_order`, `bits_per_word`, or `extra_flags`
                    values are invalid.
    """

    # Constants scraped from <linux/spi/spidev.h>
    _SPI_CPHA = 0x1
    _SPI_CPOL = 0x2
    _SPI_LSB_FIRST = 0x8
    _SPI_IOC_WR_MODE = 0x40016b01
    _SPI_IOC_RD_MODE = 0x80016b01
    _SPI_IOC_WR_MAX_SPEED_HZ = 0x40046b04
    _SPI_IOC_RD_MAX_SPEED_HZ = 0x80046b04
    _SPI_IOC_WR_BITS_PER_WORD = 0x40016b03
    _SPI_IOC_RD_BITS_PER_WORD = 0x80016b03
    _SPI_IOC_MESSAGE_1 = 0x40206b00

    def __init__(self, devpath, mode, max_speed, bit_order="msb",
                 bits_per_word=8, extra_flags=0):
        self._fd = None
        self._devpath = None
        self._open(devpath, mode, max_speed, bit_order, bits_per_word, extra_flags)

    def __del__(self):
        self.close()

    def __enter__(self):
        pass

    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

    def _open(self, devpath, mode, max_speed, bit_order, bits_per_word, extra_flags):
        if not isinstance(devpath, str):
            raise TypeError("Invalid devpath type, must be str.")
        elif not isinstance(mode, int):
            raise TypeError("Invalid mode type, must be int.")
        elif not isinstance(max_speed, (int, float)):
            raise TypeError("Invalid max_speed type, must be int or float.")
        elif not isinstance(bit_order, str):
            raise TypeError("Invalid bit_order type, must be str.")
        elif not isinstance(bits_per_word, int):
            raise TypeError("Invalid bits_per_word type, must be int.")
        elif not isinstance(extra_flags, int):
            raise TypeError("Invalid extra_flags type, must be int.")

        if mode not in [0, 1, 2, 3]:
            raise ValueError("Invalid mode, can be 0, 1, 2, 3.")
        elif bit_order.lower() not in ["msb", "lsb"]:
            raise ValueError("Invalid bit_order, can be \"msb\" or \"lsb\".")
        elif bits_per_word < 0 or bits_per_word > 255:
            raise ValueError("Invalid bits_per_word, must be 0-255.")
        elif extra_flags < 0 or extra_flags > 255:
            raise ValueError("Invalid extra_flags, must be 0-255.")

        # Open spidev
        self._fd = os.open(devpath, os.O_RDWR)
        self._devpath = devpath

        bit_order = bit_order.lower()

        # Set mode, bit order, extra flags
        buf = array.array("B", [mode | (SPI._SPI_LSB_FIRST if \
                                        bit_order == "lsb" else 0) | extra_flags])
        fcntl.ioctl(self._fd, SPI._SPI_IOC_WR_MODE, buf, False)

        # Set max speed
        buf = array.array("I", [int(max_speed)])
        fcntl.ioctl(self._fd, SPI._SPI_IOC_WR_MAX_SPEED_HZ, buf, False)

        # Set bits per word
        buf = array.array("B", [bits_per_word])
        fcntl.ioctl(self._fd, SPI._SPI_IOC_WR_BITS_PER_WORD, buf, False)

    # Methods

    def transfer(self, data):
        """Shift out `data` and return shifted in data.

        Args:
            data (bytes, bytearray, list): a byte array or list of 8-bit integers
                                           to shift out.

        Returns:
            bytes, bytearray, list: data shifted in.

        Raises:
            TypeError: if `data` type is invalid.
            ValueError: if data is not valid bytes.

        """
        if not isinstance(data, (bytes, bytearray, list)):
            raise TypeError("Invalid data type, must be bytes, bytearray, or list.")

        # Create mutable array
        try:
            buf = array.array('B', data)
        except OverflowError:
            raise ValueError("Invalid data bytes.")

        buf_addr, buf_len = buf.buffer_info()

        # Prepare transfer structure
        spi_xfer = _CSpiIocTransfer()
        spi_xfer.tx_buf = buf_addr #pylint: disable=attribute-defined-outside-init
        spi_xfer.rx_buf = buf_addr #pylint: disable=attribute-defined-outside-init
        spi_xfer.len = buf_len #pylint: disable=attribute-defined-outside-init

        # Transfer
        fcntl.ioctl(self._fd, SPI._SPI_IOC_MESSAGE_1, spi_xfer)

        # Return shifted out data with the same type as shifted in data
        if isinstance(data, bytes):
            return bytes(bytearray(buf))
        elif isinstance(data, bytearray):
            return bytearray(buf)
        elif isinstance(data, list):
            return buf.tolist()

    def close(self):
        """
        Close the device and release any system resources.
        """
        if hasattr(self, '_fd'):
            if self._fd is not None:
                os.close(self._fd)
                self._fd = None

    # Immutable properties

    @property
    def fd(self):
        """File descriptor of the underlying file.

        :type: int
        """
        return self._fd

    @property
    def devpath(self):
        """Get the device path of the underlying spidev device.

        :type: str
        """
        return self._devpath

    # Mutable properties

    def _get_mode(self):
        buf = array.array('B', [0])

        # Get mode
        fcntl.ioctl(self._fd, SPI._SPI_IOC_RD_MODE, buf, True)

        return buf[0] & 0x3

    def _set_mode(self, mode):
        if not isinstance(mode, int):
            raise TypeError("Invalid mode type, must be int.")
        if mode not in [0, 1, 2, 3]:
            raise ValueError("Invalid mode, can be 0, 1, 2, 3.")

        # Read-modify-write mode, because the mode contains bits for other settings

        # Get mode
        buf = array.array('B', [0])
        fcntl.ioctl(self._fd, SPI._SPI_IOC_RD_MODE, buf, True)

        buf[0] = (buf[0] & ~(SPI._SPI_CPOL | SPI._SPI_CPHA)) | mode

        # Set mode
        fcntl.ioctl(self._fd, SPI._SPI_IOC_WR_MODE, buf, False)

    mode = property(_get_mode, _set_mode)
    """Get or set the SPI mode. Can be 0, 1, 2, 3.

    Raises:
        TypeError: if `mode` type is not int.
        ValueError: if `mode` value is invalid.

    :type: int
    """

    def _get_max_speed(self):
        # Get max speed
        buf = array.array('I', [0])
        fcntl.ioctl(self._fd, SPI._SPI_IOC_RD_MAX_SPEED_HZ, buf, True)

        return buf[0]

    def _set_max_speed(self, max_speed):
        if not isinstance(max_speed, (int, float)):
            raise TypeError("Invalid max_speed type, must be int or float.")

        # Set max speed
        buf = array.array('I', [int(max_speed)])
        fcntl.ioctl(self._fd, SPI._SPI_IOC_WR_MAX_SPEED_HZ, buf, False)

    max_speed = property(_get_max_speed, _set_max_speed)
    """Get or set the maximum speed in Hertz.

    Raises:
        TypeError: if `max_speed` type is not int or float.

    :type: int, float
    """

    def _get_bit_order(self):
        # Get mode
        buf = array.array('B', [0])
        fcntl.ioctl(self._fd, SPI._SPI_IOC_RD_MODE, buf, True)

        if (buf[0] & SPI._SPI_LSB_FIRST) > 0:
            return "lsb"

        return "msb"

    def _set_bit_order(self, bit_order):
        if not isinstance(bit_order, str):
            raise TypeError("Invalid bit_order type, must be str.")
        elif bit_order.lower() not in ["msb", "lsb"]:
            raise ValueError("Invalid bit_order, can be \"msb\" or \"lsb\".")

        # Read-modify-write mode, because the mode contains bits for other settings

        # Get mode
        buf = array.array('B', [0])
        fcntl.ioctl(self._fd, SPI._SPI_IOC_RD_MODE, buf, True)

        bit_order = bit_order.lower()
        buf[0] = (buf[0] & ~SPI._SPI_LSB_FIRST) | (SPI._SPI_LSB_FIRST if bit_order == "lsb" else 0)

        # Set mode
        fcntl.ioctl(self._fd, SPI._SPI_IOC_WR_MODE, buf, False)

    bit_order = property(_get_bit_order, _set_bit_order)
    """Get or set the SPI bit order. Can be "msb" or "lsb".

    Raises:
        TypeError: if `bit_order` type is not str.
        ValueError: if `bit_order` value is invalid.

    :type: str
    """

    def _get_bits_per_word(self):
        # Get bits per word
        buf = array.array('B', [0])
        fcntl.ioctl(self._fd, SPI._SPI_IOC_RD_BITS_PER_WORD, buf, True)

        return buf[0]

    def _set_bits_per_word(self, bits_per_word):
        if not isinstance(bits_per_word, int):
            raise TypeError("Invalid bits_per_word type, must be int.")
        if bits_per_word < 0 or bits_per_word > 255:
            raise ValueError("Invalid bits_per_word, must be 0-255.")

        # Set bits per word
        buf = array.array('B', [bits_per_word])
        fcntl.ioctl(self._fd, SPI._SPI_IOC_WR_BITS_PER_WORD, buf, False)

    bits_per_word = property(_get_bits_per_word, _set_bits_per_word)
    """Get or set the SPI bits per word.

    Raises:
        TypeError: if `bits_per_word` type is not int.
        ValueError: if `bits_per_word` value is invalid.

    :type: int
    """

    def _get_extra_flags(self):
        # Get mode
        buf = array.array('B', [0])
        fcntl.ioctl(self._fd, SPI._SPI_IOC_RD_MODE, buf, True)

        return buf[0] & ~(SPI._SPI_LSB_FIRST | SPI._SPI_CPHA | SPI._SPI_CPOL)

    def _set_extra_flags(self, extra_flags):
        if not isinstance(extra_flags, int):
            raise TypeError("Invalid extra_flags type, must be int.")
        if extra_flags < 0 or extra_flags > 255:
            raise ValueError("Invalid extra_flags, must be 0-255.")

        # Read-modify-write mode, because the mode contains bits for other settings

        # Get mode
        buf = array.array('B', [0])
        fcntl.ioctl(self._fd, SPI._SPI_IOC_RD_MODE, buf, True)

        buf[0] = (buf[0] & (SPI._SPI_LSB_FIRST | SPI._SPI_CPHA | SPI._SPI_CPOL)) | extra_flags

        # Set mode
        fcntl.ioctl(self._fd, SPI._SPI_IOC_WR_MODE, buf, False)

    extra_flags = property(_get_extra_flags, _set_extra_flags)
    """Get or set the spidev extra flags. Extra flags are bitwise-ORed with the SPI mode.

    Raises:
        TypeError: if `extra_flags` type is not int.
        ValueError: if `extra_flags` value is invalid.

    :type: int
    """

    # String representation

    def __str__(self):
        return ("SPI (device=%s, fd=%d, mode=%s, max_speed=%d, bit_order=%s, "
                "bits_per_word=%d, extra_flags=0x%02x)") % (self.devpath,
                                                            self.fd,
                                                            self.mode,
                                                            self.max_speed,
                                                            self.bit_order,
                                                            self.bits_per_word,
                                                            self.extra_flags)
