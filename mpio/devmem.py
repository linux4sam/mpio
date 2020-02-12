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
"""devmem module"""
import os
import mmap
import struct

_MAP_SIZE = mmap.PAGESIZE
_MAP_MASK = _MAP_SIZE - 1

class DevMem(object):
    """Object to manage memory at the specified address.

    Provides an interface to read/write raw memory, like hardware registers.

    This allows you, for example, to manually shortcut any software and manually
    read and write hardware registers. This can be useful for debugging, but also
    useful for trivial setup and operation of hardware that is otherwise not
    exposed through a formal driver.

    See Also:
        This is losely similar in capability to the userspace command line tool
        `devmem2 <http://free-electrons.com/pub/mirror/devmem2.c>`_.

    Note:
        Running this requires root access by default.

    Note:
        This interface only maps one page at a time.

    Warning:
        Use with extreme caution. This can make the system unstable, especially
        when changing values in memory that currently running code (like the
        kernel itself) is using.  There is no error checking on values written.

    Args:
        addr (int): The starting address to manage.
        filename (str): The filename to mmap().
    """

    MODE8 = 1
    MODE16 = 2
    MODE32 = 4

    def __init__(self, addr, filename='/dev/mem'):
        self._fd = None
        self._addr = None
        self._filename = None
        self._mem = None

        if not isinstance(addr, int):
            raise TypeError("addr must be an int.")

        if addr <= 0:
            raise ValueError("addr cannot be less than 0")

        if not isinstance(filename, str):
            raise TypeError("filename must be a str.")

        self._addr = addr
        self._filename = filename

        self.base_addr = addr & ~(mmap.PAGESIZE - 1)
        self.base_addr_offset = addr - self.base_addr

        self._fd = os.open(self._filename, os.O_RDWR | os.O_SYNC)

        self._mem = mmap.mmap(self._fd, _MAP_SIZE, mmap.MAP_SHARED,
                              mmap.PROT_READ | mmap.PROT_WRITE,
                              offset=self.base_addr)

    def read(self, offset, mode=MODE32):
        """Read a value to the offset provided.

        Args:
            offset (int): The offset from the base address.
            mode (int): The mode of value.

        Returns:
            int
        """
        if not isinstance(offset, (int)):
            raise TypeError("offset must be an int.")

        if offset < 0:
            raise ValueError("offset must be >= 0")

        if mode not in (self.MODE8, self.MODE16, self.MODE32):
            raise ValueError("Invalid mode value.")

        mem = self._mem

        virt_addr = self.base_addr_offset & _MAP_MASK
        mem.seek(virt_addr + offset)

        if mode == self.MODE8:
            return struct.unpack('B', mem.read(mode))[0]
        elif mode == self.MODE16:
            return struct.unpack('H', mem.read(mode))[0]
        elif mode == self.MODE32:
            return struct.unpack('I', mem.read(mode))[0]

    def write(self, offset, value, mode=MODE32):
        """Write a value to the offset provided.

        Args:
            offset (int): The offset from the base address.
            value (int): The value to be written.
            mode (int): The mode of value.
        """
        if offset < 0:
            raise ValueError("offset must be >= 0")

        if mode not in (self.MODE8, self.MODE16, self.MODE32):
            raise ValueError("Invalid mode value.")

        mem = self._mem

        virt_addr = self.base_addr_offset & _MAP_MASK
        mem.seek(virt_addr + offset)

        if mode == self.MODE8:
            mem.write(struct.pack('B', value))
        elif mode == self.MODE16:
            mem.write(struct.pack('H', value))
        elif mode == self.MODE32:
            mem.write(struct.pack('I', value))

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

    @property
    def fd(self):
        """File descriptor of the underlying file.

        :type: int
        """
        return self._fd

    @property
    def addr(self):
        """Base address of the memory.

        :mode: int
        """
        return self._addr

    @property
    def filename(self):
        """Filename of the device mmap'd.

        :mode: str
        """
        return self._filename

    def close(self):
        """Close the device and release any system resources."""
        if hasattr(self, '_mem'):
            if self._mem is not None:
                self._mem.close()
                self._mem = None
        if hasattr(self, '_fd'):
            if self._fd is not None:
                os.close(self._fd)
                self._fd = None

    @staticmethod
    def write_reg(addr, value):
        """Utility function to write a 32 bit value.
        """
        mem = DevMem(addr)
        mem.write(0, value)

    @staticmethod
    def read_reg(addr):
        """Utility function to read a 32 bit value.
        """
        mem = DevMem(addr)
        return mem.read(0)

    def __str__(self):
        return ("DevMem (addr=%d, fd=%d, filename=%s)") % (self.addr,
                                                           self.fd,
                                                           self.filename)
