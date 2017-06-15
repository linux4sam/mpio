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
#
import sys
import os
import threading
import time
import unittest
from mio import GPIO

if sys.version_info[0] == 3:
    raw_input = input
    import queue
else:
    import Queue as queue

pin_input = int(os.environ.get('GPIO_INPUT', "121"))
pin_output = int(os.environ.get('GPIO_OUTPUT', "123"))

class TestGeneral(unittest.TestCase):

    def test_open_close(self):

        gpio = GPIO(pin_output, "in")
        self.assertTrue(gpio.mode == "in")
        self.assertTrue(gpio.pin == pin_output)
        self.assertTrue(gpio.fd > 0)

        gpio.mode = "out"
        self.assertTrue(gpio.mode == "out")

        gpio.mode = "in"
        self.assertTrue(gpio.mode == "in")

        self.assertTrue(gpio.interrupts_available)

        gpio.edge = "rising"
        self.assertTrue(gpio.edge == "rising")
        gpio.edge = "falling"
        self.assertTrue(gpio.edge == "falling")
        gpio.edge = "both"
        self.assertTrue(gpio.edge == "both")

        gpio.close()

    # this test requires PD25 and PD27 to be tied together
    def test_loopback(self):

        gpio_in = GPIO(pin_input, "in")
        gpio_out = GPIO(pin_output, "out")

        gpio_out.set(False)
        self.assertTrue(gpio_in.get() == False)

        gpio_out.set(True)
        self.assertTrue(gpio_in.get() == True)

        gpio_out.set(False)
        self.assertTrue(gpio_in.get() == False)

        gpio_in.close()
        gpio_out.close()

    # this test requires PD25 and PD27 to be tied together
    def test_loopback_async(self):

        gpio_in = GPIO(pin_input, "in")
        gpio_out = GPIO(pin_output, "out")

        # Wrapper for running poll() in a thread
        def threaded_poll(gpio, timeout):
            ret = queue.Queue()
            def f():
                ret.put(gpio.poll(timeout))
            thread = threading.Thread(target=f)
            thread.start()
            return ret

        # gpio_in.edge = "falling"
        # poll_ret = threaded_poll(gpio_in, 5)
        # time.sleep(1)
        # gpio_out.set(False)
        # self.assertTrue(poll_ret.get() == True)
        # self.assertTrue(gpio_in.get() == False)

        # poll_ret = threaded_poll(gpio_in, 2)
        # time.sleep(1)
        # gpio_out.set(False)
        # self.assertTrue(poll_ret.get() == False)
        # self.assertTrue(gpio_in.get() == False)

        # gpio_in.edge = "rising"
        # poll_ret = threaded_poll(gpio_in, 5)
        # time.sleep(1)
        # gpio_out.set(True)
        # self.assertTrue(poll_ret.get() == True)
        # self.assertTrue(gpio_in.get() == True)

        # poll_ret = threaded_poll(gpio_in, 2)
        # time.sleep(1)
        # gpio_out.set(True)
        # self.assertTrue(poll_ret.get() == False)
        # self.assertTrue(gpio_in.get() == True)

        # gpio_in.edge = "both"
        # poll_ret = threaded_poll(gpio_in, 5)
        # time.sleep(1)
        # gpio_out.set(False)
        # self.assertTrue(poll_ret.get() == True)
        # self.assertTrue(gpio_in.get() == False)
        # poll_ret = threaded_poll(gpio_in, 5)
        # time.sleep(1)
        # gpio_out.set(True)
        # self.assertTrue(poll_ret.get() == True)
        # self.assertTrue(gpio_in.get() == True)
        # self.assertTrue(gpio_in.poll(1) == False)


    @unittest.skipIf(os.environ.get('NOINTERACTIVE', False), "interactive disabled")
    def test_interactive(self):
        gpio = GPIO(pin_output, "out")

        gpio.set(False)
        self.assertTrue(raw_input("GPIO out is low? y/n ") == "y")

        gpio.set(True)
        self.assertTrue(raw_input("GPIO out is high? y/n ") == "y")

        gpio.set(False)
        self.assertTrue(raw_input("GPIO out is low? y/n ") == "y")

        gpio.close()


if __name__ == '__main__':
    unittest.main()
