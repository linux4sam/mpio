#
# Microchip IO
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
import sys
import os
import unittest
from mio import Input

if sys.version_info[0] == 3:
    raw_input = input

class TestGeneral(unittest.TestCase):

    def test_exceptions(self):
        self.assertRaises(OSError, Input, "/invalid/path")

    def test_open_close(self):

        inputs = Input.enumerate()
        self.assertTrue(len(inputs) > 0)

        name = os.environ.get('INPUT_NAME', inputs[0])

        Input.desc(name)

        i = Input(name)
        driver_version = i.driver_version
        device_id = i.device_id

        i.close()

    @unittest.skipIf(os.environ.get('NOINTERACTIVE', False), "interactive disabled")
    def test_interactive(self):
        inputs = Input.enumerate()
        self.assertTrue(len(inputs) > 0)

        name = os.environ.get('INPUT_NAME', inputs[0])

        i = Input(name)

        print ("Generate events on input {}...".format(Input.desc(name)))

        (tv_sec, tv_usec, evtype, code, value) = i.read()

        i.close()

if __name__ == '__main__':
    unittest.main()
