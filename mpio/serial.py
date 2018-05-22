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
"""serial module"""
import os
import fcntl
import array
import termios
import select

class Serial(object):
    """Serial object that opens the tty device at the specified path with the
    specified baudrate, and the defaults of 8 data bits, no parity, 1 stop bit,
    no software flow control (xonxoff), and no hardware flow control (rtscts).

    This can be used for simple bi-directional serial communication with connected
    devices.

    See Also:
        For an alternate package for interfacing with serial ports, see `pySerial
        <https://pythonhosted.org/pyserial/>`_.

    Args:
        devpath (str): tty device path.
        baudrate (int): baudrate.
        databits (int): data bits, can be 5, 6, 7, 8.
        parity (str): parity, can be "none", "even", "odd".
        stopbits (int): stop bits, can be 1 or 2.
        xonxoff (bool): software flow control.
        rtscts (bool): hardware flow control.

    Returns:
        Serial: Serial object.

    Raises:
        TypeError: if `devpath`, `baudrate`, `databits`, `parity`, `stopbits`,
                   `xonxoff`, or `rtscts` types are invalid.
        ValueError: if `baudrate`, `databits`, `parity`, or `stopbits`
                    values are invalid.
    """

    _DATABITS_TO_CFLAG = {
        5: termios.CS5, 6: termios.CS6, 7: termios.CS7, 8: termios.CS8
    }
    _CFLAG_TO_DATABITS = {v: k for k, v in _DATABITS_TO_CFLAG.items()}

    _BAUDRATE_TO_OSPEED = {
        50: termios.B50, 75: termios.B75, 110: termios.B110, 134: termios.B134,
        150: termios.B150, 200: termios.B200, 300: termios.B300,
        600: termios.B600, 1200: termios.B1200, 1800: termios.B1800,
        2400: termios.B2400, 4800: termios.B4800, 9600: termios.B9600,
        19200: termios.B19200, 38400: termios.B38400, 57600: termios.B57600,
        115200: termios.B115200, 230400: termios.B230400,
        # Linux baudrates bits missing in termios module included below
        460800: 0x1004, 500000: 0x1005, 576000: 0x1006,
        921600: 0x1007, 1000000: 0x1008, 1152000: 0x1009,
        1500000: 0x100A, 2000000: 0x100B, 2500000: 0x100C,
        3000000: 0x100D, 3500000: 0x100E, 4000000: 0x100F,
    }
    _OSPEED_TO_BAUDRATE = {v: k for k, v in _BAUDRATE_TO_OSPEED.items()}

    def __init__(self, devpath, baudrate, databits=8, parity="none", stopbits=1,
                 xonxoff=False, rtscts=False):
        self._fd = None
        self._devpath = None
        self._open(devpath, baudrate, databits, parity, stopbits, xonxoff, rtscts)

    def __del__(self):
        self.close()

    def __enter__(self):
        pass

    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

    def _open(self, devpath, baudrate, databits, parity, stopbits, xonxoff, rtscts):
        if not isinstance(devpath, str):
            raise TypeError("Invalid devpath type, must be str.")
        elif not isinstance(baudrate, int):
            raise TypeError("Invalid baud rate type, must be int.")
        elif not isinstance(databits, int):
            raise TypeError("Invalid data bits type, must be int.")
        elif not isinstance(parity, str):
            raise TypeError("Invalid parity type, must be str.")
        elif not isinstance(stopbits, int):
            raise TypeError("Invalid stop bits type, must be int.")
        elif not isinstance(xonxoff, bool):
            raise TypeError("Invalid xonxoff type, must be bool.")
        elif not isinstance(rtscts, bool):
            raise TypeError("Invalid rtscts type, must be bool.")

        if baudrate not in Serial._BAUDRATE_TO_OSPEED:
            raise ValueError("Unknown baud rate %d." % baudrate)
        elif databits not in [5, 6, 7, 8]:
            raise ValueError("Invalid data bits, can be 5, 6, 7, 8.")
        elif parity.lower() not in ["none", "even", "odd"]:
            raise ValueError("Invalid parity, can be: \"none\", \"even\", \"odd\".")
        elif stopbits not in [1, 2]:
            raise ValueError("Invalid stop bits, can be 1, 2.")

        # Open tty
        self._fd = os.open(devpath, os.O_RDWR | os.O_NOCTTY)

        self._devpath = devpath

        parity = parity.lower()

        (iflag, oflag, cflag, lflag, ispeed, ospeed, cc) = (0, 0, 0, 0, 0, 0, [0]*32)

        ### iflag

        # Ignore break characters
        iflag = termios.IGNBRK

        # Setup parity
        if parity != "none":
            iflag |= (termios.INPCK | termios.ISTRIP)

        # Setup xonxoff
        if xonxoff:
            iflag |= (termios.IXON | termios.IXOFF)

        ### oflag
        oflag = 0

        ### lflag
        lflag = 0

        ### cflag

        # Enable receiver, ignore modem control lines
        cflag = (termios.CREAD | termios.CLOCAL)

        # Setup data bits
        cflag |= Serial._DATABITS_TO_CFLAG[databits]

        # Setup parity
        if parity == "even":
            cflag |= termios.PARENB
        elif parity == "odd":
            cflag |= (termios.PARENB | termios.PARODD)

        # Setup stop bits
        if stopbits == 2:
            cflag |= termios.CSTOPB

        # Setup rtscts
        if rtscts:
            cflag |= termios.CRTSCTS

        # Setup baud rate
        cflag |= Serial._BAUDRATE_TO_OSPEED[baudrate]

        ### ispeed
        ispeed = Serial._BAUDRATE_TO_OSPEED[baudrate]

        ### ospeed
        ospeed = Serial._BAUDRATE_TO_OSPEED[baudrate]

        # Set tty attributes
        termios.tcsetattr(self._fd, termios.TCSANOW, [iflag, oflag, cflag, lflag,
                                                      ispeed, ospeed, cc])

    # Methods

    def read(self, length, timeout=None):
        """Read up to `length` number of bytes from the serial port with an
        optional timeout.

        `timeout` can be positive for a timeout in seconds, 0 for a
        non-blocking read, or negative or None for a blocking read that will
        block until `length` number of bytes are read. Default is a blocking
        read.

        For a non-blocking or timeout-bound read, read() may return data whose
        length is less than or equal to the requested length.

        Args:
            length (int): length in bytes.
            timeout (int, float, None): timeout duration in seconds.

        Returns:
            bytes: data read.
        """
        data = b""

        # Read length bytes if timeout is None

        # Read up to length bytes if timeout is not None
        while True:
            if timeout is not None:
                # Select
                (rlist, _, _) = select.select([self._fd], [], [], timeout)
                # If timeout
                if self._fd not in rlist:
                    break

            data += os.read(self._fd, length-len(data))

            if len(data) == length:
                break

        return data

    def write(self, data):
        """Write `data` to the serial port and return the number of bytes
        written.

        Args:
            data (bytes, bytearray, list): a byte array or list of 8-bit
                                           integers to write.

        Returns:
            int: number of bytes written.

        Raises:
            TypeError: if `data` type is invalid.
            ValueError: if data is not valid bytes.

        """
        if not isinstance(data, (bytes, bytearray, list)):
            raise TypeError("Invalid data type, must be bytes, bytearray, or list.")

        if isinstance(data, list):
            data = bytearray(data)

        return os.write(self._fd, data)

    def poll(self, timeout=None):
        """Poll for data available for reading from the serial port.

        `timeout` can be positive for a timeout in seconds, 0 for a
        non-blocking poll, or negative or None for a blocking poll. Default is
        a blocking poll.

        Args:
            timeout (int, float, None): timeout duration in seconds.

        Returns:
            bool: ``True`` if data is available for reading from the serial port,
                  ``False`` if not.
        """
        poll = select.poll()
        poll.register(self._fd, select.POLLIN | select.POLLPRI)
        events = poll.poll(int(timeout*1000))

        if len(events) > 0:
            return True

        return False

    def flush(self):
        """Flush the write buffer of the serial port, blocking until all bytes
        are written.
        """
        termios.tcdrain(self._fd)

    def input_waiting(self):
        """Query the number of bytes waiting to be read from the serial port.

        Returns:
            int: number of bytes waiting to be read.
        """
        # Get input waiting
        buf = array.array('I', [0])
        fcntl.ioctl(self._fd, termios.TIOCINQ, buf, True)

        return buf[0]

    def output_waiting(self):
        """Query the number of bytes waiting to be written to the serial port.

        Returns:
            int: number of bytes waiting to be written.
        """
        # Get input waiting
        buf = array.array('I', [0])
        fcntl.ioctl(self._fd, termios.TIOCOUTQ, buf, True)

        return buf[0]

    def close(self):
        """Close the tty device.
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
        """Get the device path of the underlying tty device.

        :type: str
        """
        return self._devpath

    # Mutable properties

    def _get_baudrate(self):
        # Get tty attributes
        (_, _, _, _, _, ospeed, _) = termios.tcgetattr(self._fd)

        if ospeed not in Serial._OSPEED_TO_BAUDRATE:
            raise ValueError(None, "Unknown baud rate: ospeed 0x%x." % ospeed)

        return Serial._OSPEED_TO_BAUDRATE[ospeed]

    def _set_baudrate(self, baudrate):
        if not isinstance(baudrate, int):
            raise TypeError("Invalid baud rate type, must be int.")

        if baudrate not in Serial._BAUDRATE_TO_OSPEED:
            raise ValueError("Unknown baud rate %d." % baudrate)

        # Get tty attributes
        (iflag, oflag, cflag, lflag, ispeed, ospeed, cc) = termios.tcgetattr(self._fd)

        # Modify tty attributes
        cflag &= ~(termios.CBAUD | termios.CBAUDEX)
        cflag |= Serial._BAUDRATE_TO_OSPEED[baudrate]
        ispeed = Serial._BAUDRATE_TO_OSPEED[baudrate]
        ospeed = Serial._BAUDRATE_TO_OSPEED[baudrate]

        # Set tty attributes
        termios.tcsetattr(self._fd, termios.TCSANOW, [iflag, oflag, cflag,
                                                      lflag, ispeed, ospeed, cc])

    baudrate = property(_get_baudrate, _set_baudrate)
    """Get or set the baudrate.

    Raises:
        TypeError: if `baudrate` type is not int.
        ValueError: if `baudrate` value is not supported.

    :type: int
    """

    def _get_databits(self):
        # Get tty attributes
        (_, _, cflag, _, _, _, _) = termios.tcgetattr(self._fd)

        csize = cflag & termios.CSIZE

        if csize not in Serial._CFLAG_TO_DATABITS:
            raise ValueError(None, "Unknown data bits setting: csize 0x%x." % csize)

        return Serial._CFLAG_TO_DATABITS[csize]

    def _set_databits(self, databits):
        if not isinstance(databits, int):
            raise TypeError("Invalid data bits type, must be int.")
        elif databits not in [5, 6, 7, 8]:
            raise ValueError("Invalid data bits, can be 5, 6, 7, 8.")


        # Get tty attributes
        (iflag, oflag, cflag, lflag, ispeed, ospeed, cc) = termios.tcgetattr(self._fd)

        # Modify tty attributes
        cflag &= ~termios.CSIZE
        cflag |= Serial._DATABITS_TO_CFLAG[databits]

        # Set tty attributes
        termios.tcsetattr(self._fd, termios.TCSANOW, [iflag, oflag, cflag, lflag,
                                                      ispeed, ospeed, cc])

    databits = property(_get_databits, _set_databits)
    """Get or set the data bits. Can be 5, 6, 7, 8.

    Raises:
        TypeError: if `databits` type is not int.
        ValueError: if `databits` value is invalid.

    :type: int
    """

    def _get_parity(self):
        # Get tty attributes
        (_, _, cflag, _, _, _, _) = termios.tcgetattr(self._fd)

        if (cflag & termios.PARENB) == 0:
            return "none"
        elif (cflag & termios.PARODD) == 0:
            return "even"
        else:
            return "odd"

    def _set_parity(self, parity):
        if not isinstance(parity, str):
            raise TypeError("Invalid parity type, must be str.")
        elif parity.lower() not in ["none", "even", "odd"]:
            raise ValueError("Invalid parity, can be: \"none\", \"even\", \"odd\".")

        parity = parity.lower()

        # Get tty attributes
        (iflag, oflag, cflag, lflag, ispeed, ospeed, cc) = termios.tcgetattr(self._fd)

        # Modify tty attributes
        iflag &= ~(termios.INPCK | termios.ISTRIP)
        cflag &= ~(termios.PARENB | termios.PARODD)
        if parity != "none":
            iflag |= (termios.INPCK | termios.ISTRIP)
            cflag |= termios.PARENB
        if parity == "odd":
            cflag |= termios.PARODD

        # Set tty attributes
        termios.tcsetattr(self._fd, termios.TCSANOW, [iflag, oflag, cflag, lflag,
                                                      ispeed, ospeed, cc])

    parity = property(_get_parity, _set_parity)
    """Get or set the parity. Can be "none", "even", "odd".

    Raises:
        TypeError: if `parity` type is not str.
        ValueError: if `parity` value is invalid.

    :type: str
    """

    def _get_stopbits(self):
        # Get tty attributes
        (_, _, cflag, _, _, _, _) = termios.tcgetattr(self._fd)

        if (cflag & termios.CSTOPB) != 0:
            return 2
        else:
            return 1

    def _set_stopbits(self, stopbits):
        if not isinstance(stopbits, int):
            raise TypeError("Invalid stop bits type, must be int.")
        elif stopbits not in [1, 2]:
            raise ValueError("Invalid stop bits, can be 1, 2.")

        # Get tty attributes
        (iflag, oflag, cflag, lflag, ispeed, ospeed, cc) = termios.tcgetattr(self._fd)

        # Modify tty attributes
        cflag &= ~termios.CSTOPB
        if stopbits == 2:
            cflag |= termios.CSTOPB

        # Set tty attributes
        termios.tcsetattr(self._fd, termios.TCSANOW, [iflag, oflag, cflag, lflag,
                                                      ispeed, ospeed, cc])

    stopbits = property(_get_stopbits, _set_stopbits)
    """Get or set the stop bits. Can be 1 or 2.

    Raises:
        TypeError: if `stopbits` type is not int.
        ValueError: if `stopbits` value is invalid.

    :type: int
    """

    def _get_xonxoff(self):
        # Get tty attributes
        (iflag, _, _, _, _, _, _) = termios.tcgetattr(self._fd)

        return bool(iflag & (termios.IXON | termios.IXOFF))

    def _set_xonxoff(self, enabled):
        if not isinstance(enabled, bool):
            raise TypeError("Invalid enabled type, must be bool.")

        # Get tty attributes
        (iflag, oflag, cflag, lflag, ispeed, ospeed, cc) = termios.tcgetattr(self._fd)

        # Modify tty attributes
        iflag &= ~(termios.IXON | termios.IXOFF | termios.IXANY)
        if enabled:
            iflag |= (termios.IXON | termios.IXOFF)

        # Set tty attributes
        termios.tcsetattr(self._fd, termios.TCSANOW, [iflag, oflag, cflag, lflag,
                                                      ispeed, ospeed, cc])

    xonxoff = property(_get_xonxoff, _set_xonxoff)
    """Get or set software flow control.

    Raises:
        TypeError: if `xonxoff` type is not bool.

    :type: bool
    """

    def _get_rtscts(self):
        # Get tty attributes
        (_, _, cflag, _, _, _, _) = termios.tcgetattr(self._fd)

        return bool(cflag & termios.CRTSCTS)

    def _set_rtscts(self, enabled):
        if not isinstance(enabled, bool):
            raise TypeError("Invalid enabled type, must be bool.")

        # Get tty attributes
        (iflag, oflag, cflag, lflag, ispeed, ospeed, cc) = termios.tcgetattr(self._fd)

        # Modify tty attributes
        cflag = ~termios.CRTSCTS
        if enabled:
            cflag |= termios.CRTSCTS

        # Set tty attributes
        termios.tcsetattr(self._fd, termios.TCSANOW, [iflag, oflag, cflag, lflag,
                                                      ispeed, ospeed, cc])

    rtscts = property(_get_rtscts, _set_rtscts)
    """Get or set hardware flow control.

    Raises:
        TypeError: if `rtscts` type is not bool.

    :type: bool
    """

    # String representation

    def __str__(self):
        return ("Serial (devpath=%s, fd=%d, baudrate=%d, databits=%d, parity=%s, "
                "stopbits=%d, xonxoff=%s, rtscts=%s)") % (self.devpath,
                                                          self.fd,
                                                          self.baudrate,
                                                          self.databits,
                                                          self.parity,
                                                          self.stopbits,
                                                          str(self.xonxoff),
                                                          str(self.rtscts))
