# Licensed under the MIT License
# http://code.activestate.com/recipes/578225-linux-ioctl-numbers-in-python/

"""
Linux ioctl numbers made easy.

Size can be an integer or format string compatible with struct module

Example:

    For example include/linux/watchdog.h:

        #define WATCHDOG_IOCTL_BASE     'W'

        struct watchdog_info {
                __u32 options;          /* Options the card/driver supports */
                __u32 firmware_version; /* Firmware version of the card */
                __u8  identity[32];     /* Identity of the board */
        };

        #define WDIOC_GETSUPPORT  _IOR(WATCHDOG_IOCTL_BASE, 0, struct watchdog_info)

    becomes:

        WDIOC_GETSUPPORT = _IOR(ord('W'), 0, "=II32s")
"""
import struct
import sys

# pragma pylint: disable=locally-disabled,invalid-name,missing-docstring

# constant for linux portability
_IOC_NRBITS = 8
_IOC_TYPEBITS = 8

# architecture specific
_IOC_SIZEBITS = 14
_IOC_DIRBITS = 2

_IOC_NRMASK = (1 << _IOC_NRBITS) - 1
_IOC_TYPEMASK = (1 << _IOC_TYPEBITS) - 1
_IOC_SIZEMASK = (1 << _IOC_SIZEBITS) - 1
_IOC_DIRMASK = (1 << _IOC_DIRBITS) - 1

_IOC_NRSHIFT = 0
_IOC_TYPESHIFT = _IOC_NRSHIFT + _IOC_NRBITS
_IOC_SIZESHIFT = _IOC_TYPESHIFT + _IOC_TYPEBITS
_IOC_DIRSHIFT = _IOC_SIZESHIFT + _IOC_SIZEBITS

IOC_NONE = 0
IOC_WRITE = 1
IOC_READ = 2

def IOC(direction, itype, nr, size):
    if sys.version_info >= (3,0,0):
        if isinstance(size, str):
            size = struct.calcsize(size)
    else:
        if isinstance(size, basestring):
            size = struct.calcsize(size)
    return direction << _IOC_DIRSHIFT | \
        itype << _IOC_TYPESHIFT | \
        nr   << _IOC_NRSHIFT | \
        size << _IOC_SIZESHIFT

def IO(itype, nr):
    return IOC(IOC_NONE, itype, nr, 0)
def IOR(itype, nr, size):
    return IOC(IOC_READ, itype, nr, size)
def IOW(itype, nr, size):
    return IOC(IOC_WRITE, itype, nr, size)
def IOWR(itype, nr, size):
    return IOC(IOC_READ | IOC_WRITE, itype, nr, size)
