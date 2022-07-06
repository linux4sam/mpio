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
"""utils module

This module provides miscellaneous functionality both used internally
and available for use externally.
"""
import os
import re

def writestr(f, value):
    """Write a value as a str to a file descriptor or file handle.
    """
    if isinstance(f, int):
        os.write(f, str(value))
        os.fsync(f)
    else:
        f.write(str(value))
        f.flush()

def writestr_all(path, value):
    """Write a value as a str to a file path.
    """
    with open(path, 'w') as f:
        writestr(f, value)

def readstr(f, maxsize=1024):
    """Read a str from a file descriptor or file handle.
    """
    if isinstance(f, int):
        os.lseek(f, 0, os.SEEK_SET)
        return os.read(f, maxsize).strip()
    else:
        f.seek(0)
        return f.read().strip()

def readstr_all(path):
    """Read a str from a file path.
    """
    with open(path, 'r') as f:
        return readstr(f)

def cpu():
    """Returns unique string identifying the current CPU.

    Returns:
        str
    """

    fixed = os.environ.get('MPIO_CPU')
    if fixed:
        return fixed

    cpus = [
        ("sam9x60", "sam9x60"),
        ("sam9x7", "sam9x7"),
        ("sama5d3", "sama5d3"),
        ("sama5d4", "sama5d4"),
        ("sama5d2", "sama5d2"),
        ("sama7g5", "sama7g5"),
        ("at91sam9x5", "at91sam9x5")
    ]

    for name, string in cpus:
        try:
            if string in open('/sys/firmware/devicetree/base/compatible').read():
                return name
        except: #pylint: disable=bare-except
            pass

    return None

def board():
    """Returns a unique string identifying the current board.

    Returns:
        str
    """

    fixed = os.environ.get('MPIO_BOARD')
    if fixed:
        return fixed

    boards = [
        ("sam9x60-ek", "microchip,sam9x60ek"),
        ("sam9x75-eb", "microchip,sam9x75eb"),
        ("sama5d3-xplained", "atmel,sama5d3-xplained"),
        ("sama5d4-xplained", "atmel,sama5d4-xplained"),
        ("sama5d2-xplained", "atmel,sama5d2-xplained"),
        ("sama5d27-som1-ek", "atmel,sama5d27-som1-ek"),
        ("sama5d27-wlsom1-ek", "microchip,sama5d27-wlsom1-ek"),
        ("sama5d2-ptc-ek", "atmel,sama5d2-ptc_ek"),
        ("sama7g5-ek", "microchip,sama7g5ek"),
        ("at91sam9x35-ek", "atmel,at91sam9g35ek")
    ]

    for name, string in boards:
        try:
            if string in open('/sys/firmware/devicetree/base/compatible').read():
                return name
        except: #pylint: disable=bare-except
            pass

    return None

def get_trailing_number(string):
    """Returns the trailing number from a string.

    Returns:
        int, None: Returns int if found, ``None`` otherwise.
    """
    matches = re.search(r'\d+$', string)
    return int(matches.group()) if matches else None
