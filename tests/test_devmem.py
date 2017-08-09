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
import sys
import os
import unittest
from mpio import DevMem

if sys.version_info[0] == 3:
    raw_input = input

class TestGeneral(unittest.TestCase):

    def test_arguments(self):
        self.assertRaises(ValueError, DevMem, -1)
        self.assertRaises(ValueError, DevMem, 0)

    def test_open_close(self):
        addr = int(os.environ.get('DEVMEM_ADDR', "0xFC069000"), 16)
        mem = DevMem(addr)
        self.assertTrue(mem.read(0, DevMem.MODE32) != 0)
        mem.close()

if __name__ == '__main__':
    unittest.main()
