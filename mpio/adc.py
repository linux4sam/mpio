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
"""adc module"""
import glob
import os
import re
import select
import threading
import time

from mpio import utils

_ADC_ROOT = '/sys/bus/iio/devices'
_DEVICE_PATH = lambda device: os.path.join(_ADC_ROOT, 'iio:device{0}'.format(device))
_VOLTAGE_RAW_PATH = lambda device, channel: os.path.join(_DEVICE_PATH(device),
                                                         'in_voltage{0}_raw'.format(channel))

class AsyncCapture(threading.Thread):
    """Asynchronous capture thread.
    """
    def __init__(self, adc, callback):
        super(AsyncCapture, self).__init__()
        self.adc = adc
        self.callback = callback
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            data = self.adc.get_capture(1000)
            if data:
                self.callback(data)

    def stop(self):
        """Stop the capture thread from running.
        """
        self.running = False
        self.adc.stop_capture()


class ADC(object):
    """An Analog to Digital Converter (ADC) object to configure and read ADC
    values.

    Once an ADC device has been identified, channels on that device can be
    configured to trigger by hardware or software to generate digital values from
    analog inputs.

    See Also:
        http://www.at91.com/linux4sam/bin/view/Linux4SAM/IioAdcDriver
        http://www.at91.com/linux4sam/bin/view/Linux4SAM/UsingSAMA5D2ADCDevice

    Args:
        device (int): The ADC device.
    """

    def __init__(self, device):
        self._device = None

        if not isinstance(device, int):
            raise TypeError("device must be int.")

        if not os.path.isdir(_DEVICE_PATH(device)):
            raise OSError("ADC device %s not found" % _DEVICE_PATH(device))

        self._device = device

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

    @property
    def device(self):
        """Device ID of the ADC.

        :type: int
        """
        return self._device

    @property
    def name(self):
        """Linux name of the ADC device.

        :type: str
        """
        return utils.readstr_all(os.path.join(_DEVICE_PATH(self._device), 'name'))

    def value(self, channel):
        """
        Perform a software trigger and get the raw ADC value.

        Calling this function causes a software trigger of the ADC.  The ADC
        will do a conversion and then return the value.

        Args:
            channel (int): The ADC channel.

        Returns:
            int
        """
        if not isinstance(channel, (int)):
            raise TypeError("channel must be an int.")

        return int(utils.readstr_all(os.path.join(_VOLTAGE_RAW_PATH(self._device,
                                                                    channel))))

    @property
    def scale(self):
        """Get the ADC value scale.

        The value you have to multiply the ADC value by to get microvolts.

        :type: float, None
        """
        if not os.path.isfile(os.path.join(_DEVICE_PATH(self._device),
                                           'in_voltage_scale')):
            return None

        return float(utils.readstr_all(os.path.join(_DEVICE_PATH(self._device),
                                                    'in_voltage_scale')))

    def microvolts(self, channel):
        """Perform a software trigger and get the microvolts value.

        The same as calling ``value(channel)`` * ``scale()``.

        Returns:
            float
        """
        if not isinstance(channel, (int)):
            raise TypeError("channel must be an int.")

        if not self.scale:
            raise RuntimeError("Scale not supported.")

        return float(self.value(channel) * self.scale)

    def volts(self, channel):
        """Perform a software trigger and get the volts value.

        The same as calling ``value(channel)`` * ``scale`` / 1000.0.

        Returns:
            float
        """
        if not isinstance(channel, (int)):
            raise TypeError("channel must be an int.")

        return float(self.microvolts(channel) / 1000.0)

    @property
    def available_channels(self):
        """Get a list of available channels for the device.

        :type: list: A list of channel ids available.
        """
        channels = []
        for f in os.listdir(_DEVICE_PATH(self._device)):
            if re.match(r'in_voltage[0-9]+_raw', f):
                for match in re.finditer(r'\d+', f):
                    channels.append(int(match.group()))
        return sorted(channels)

    @property
    def available_triggers(self):
        """List of available trigger names for the device.

        One of the names returned here can then be used when calling
        ``start_capture()`` to specify the trigger.

        :type: list: A list of trigger names available.
        """
        names = []

        triggers = [f for f in os.listdir(_ADC_ROOT) if \
                    os.path.isdir(os.path.join(_ADC_ROOT, f)) and 'trigger' in f]
        for trigger in triggers:
            names.append(utils.readstr_all(os.path.join(_ADC_ROOT, trigger, 'name')))

        return sorted(names)

    def _set_trigger(self, name):
        """Set the trigger for the device.
        """
        if name not in self.available_triggers:
            raise ValueError("Trigger name not supported.")

        utils.writestr_all(os.path.join(_DEVICE_PATH(self._device), 'trigger',
                                        'current_trigger'), name)

    def start_capture(self, channels, trigger, buffer_size=100):
        """Start a capture.

        Examples:
            The typical usage example for performing a triggered capture is as
            follows.

            >>> a.start_capture()
            >>> while CONDITION: data = a.get_capture()
            >>> a.stop_capture()

        Args:
            channels (list): Array of channels to capture for.
            trigger (str): The trigger to be used.
            buffer_size (int): The buffer size to store.
        """
        self._set_trigger(trigger)

        # disable all channels
        for f in os.listdir(os.path.join(_ADC_ROOT, 'scan_elements')):
            if os.path.isdir(os.path.join(_ADC_ROOT, 'scan_elements', f)) and '_en' in f:
                utils.writestr_all(os.path.join(_ADC_ROOT, 'scan_elements', f), 0)

        # enable specified channels
        for channel in channels:
            utils.writestr_all(os.path.join(_DEVICE_PATH(self._device), \
                                          'scan_elements',
                                            'in_voltage{0}_en'.format(channel)), 1)

        # set buffer length
        utils.writestr_all(os.path.join(_DEVICE_PATH(self._device), 'buffer',
                                        'length'), buffer_size)

        # start capture
        utils.writestr_all(os.path.join(_DEVICE_PATH(self._device), 'buffer',
                                        'enable'), 1)

    def get_capture(self, timeout=None):
        """Block for up to the specified timeout and read the capture data.

        Args:
            timeout (int, float, None): timeout duration in seconds.
        """
        if not isinstance(timeout, (int, float, type(None))):
            raise TypeError("Invalid timeout type, must be int, float, or None.")

        fd = os.open('/dev/iio:device{0}'.format(self._device), os.O_RDWR)

        epoll = select.epoll()
        epoll.register(fd, select.EPOLLIN | select.EPOLLET | select.EPOLLPRI)

        for _ in range(2):
            events = epoll.poll(timeout)

        data = None

        if events:
            data = os.read(fd, 1024)

        os.close(fd)

        return data

    def stop_capture(self):
        """Stop any pending capture."""
        utils.writestr_all(os.path.join(_DEVICE_PATH(self._device), 'buffer',
                                        'enable'), 0)

    def async_start_capture(self, channels, trigger, callback, buffer_size=100):
        """Returns a thread that invokes the specified callback when data is
        captured asynchronously.

        Args:
            channels (list): Array of channels to capture for.
            trigger (str): The trigger to be used.
            buffer_size (int): The buffer size to store.
            callback: Function to call when interrupt occurs.
        Returns:
            thread
        """
        self.start_capture(channels, trigger, buffer_size)
        handler = AsyncCapture(self, callback)
        handler.start()
        while not handler.running:
            time.sleep(0.001)
        return handler

    @property
    def sampling_frequency(self):
        """Get the sampling frequency of the ADC.

        :type: int
        """
        return int(utils.readstr_all(os.path.join(_DEVICE_PATH(self._device),
                                                  'sampling_frequency')))

    def close(self):
        """Close the device and release any system resources."""
        self._device = None

    @staticmethod
    def enumerate():
        """Enumerate a list of ADC devices available on the system.

        Returns:
            list
        """
        ids = [utils.get_trailing_number(f) for f in \
               glob.glob(os.path.join(_ADC_ROOT, 'iio:device*')) if \
               os.path.isdir(f)]
        return sorted(ids)

    def __str__(self):
        return ("ADC (device=%d, name=%d, scale=%d, sampling_frequency=%d)") % (
            self.name,
            self.device,
            self.scale,
            self.sampling_frequency)
