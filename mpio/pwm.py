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
"""pwm module"""
import os
import sys

from mpio import utils

_PWM_ROOT = '/sys/class/pwm'
_CHIP_PATH = lambda chip: os.path.join(_PWM_ROOT, 'pwmchip{0}'.format(chip))
_CHANNEL_PATH = lambda chip, channel: os.path.join(_PWM_ROOT,
                                                   'pwmchip{0}'.format(chip),
                                                   'pwm{0}'.format(channel))

def _is_exported(chip, channel):
    """ Check if the PWM was already exported on sysfs. """
    return os.path.isdir(_CHANNEL_PATH(chip, channel))

class PWM(object):
    """Pulse Width Modulation (PWM) object to generate signals on a pin.

    Provides an interface to Pulse Width Modulation (PWM) generators available
    on the system.

    To identify a specific PWM instance, a chip number and channel number is
    needed. The available chips can be retrieved with the enumerate() function.
    Then, with that you can call num_channels() to see how many channels the
    chip supports. However, you will have to reference CPU and board
    documentation to find out what physical pin the chip/channel number
    corresponds to.

    See Also:
        https://www.kernel.org/doc/Documentation/pwm.txt

    Args:
        chip (int): For valid values of chip, call enumerate().
        channel (int): For valid range of channel, call num_channels().
        period (int): Microsecond period value that is the sum of the active and
                      inactive time.
        duty_cycle (int, float): Percent of period between 0.0 and 1.0.
        enable (bool): Enable the PWM output after setup.
        polarity(self.NORMAL, self.INVERSED, None): Polarity of the output.
        force_own (bool): When ``True``, steal ownership as necessary.
            However, this means that multiple objects are potentially
            controlling the channel.
    """

    NORMAL, INVERSED = "normal", "inversed"

    def __init__(self, chip, channel, period=None, duty_cycle=None, enable=True,
                 polarity=None, force_own=False):
        self._chip = None
        self._channel = None

        if not isinstance(chip, int):
            raise TypeError("chip must be int.")

        if not isinstance(channel, int):
            raise TypeError("channel must be int.")

        if sys.version_info[0] == 2:
            if not isinstance(period, (int, long, type(None))):
                raise TypeError("period must be int, long, None.")
        else:
            if not isinstance(period, (int, type(None))):
                raise TypeError("period must be int, None.")

        if not isinstance(duty_cycle, (int, float, type(None))):
            raise TypeError("duty_cycle must be int, float, None.")

        if not isinstance(enable, bool):
            raise TypeError("enable must be bool.")

        if not isinstance(force_own, bool):
            raise TypeError("force_own must be bool.")

        if polarity not in (self.NORMAL, self.INVERSED, None):
            raise ValueError("Invalid polarity value.")

        if _is_exported(chip, channel) and not force_own:
            raise RuntimeError("Channel already owned.  Use force_own=True to override.")

        if not _is_exported(chip, channel):
            utils.writestr_all(os.path.join(_CHIP_PATH(chip), 'export'), channel)

        self._chip = chip
        self._channel = channel

        if self.enabled:
            self.enabled = False

        if period is not None:
            self.period = period
        if duty_cycle is not None:
            self.duty_cycle = duty_cycle

        # Crazy thing about setting polarity: this won't be allowed unless the
        # period is non-zero.
        if polarity is not None:
            utils.writestr_all(os.path.join(_CHANNEL_PATH(self._chip,
                                                          self._channel),
                                            'polarity'), polarity)

        if enable:
            self.enabled = True

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

    @property
    def chip(self):
        """The PWM chip.

        :type: int
        """
        return self._chip

    @property
    def channel(self):
        """The PWM chip channel.

        :type: int
        """
        return self._channel

    @property
    def enabled(self):
        """Enabled property of the PWM.

        :type: bool
        """
        return bool(int(utils.readstr_all(os.path.join(_CHANNEL_PATH(self._chip,
                                                                     self._channel),
                                                       'enable'))))

    @enabled.setter
    def enabled(self, enable):
        utils.writestr_all(os.path.join(_CHANNEL_PATH(self._chip,
                                                      self._channel),
                                        'enable'),
                           "1" if enable else "0")

    @property
    def duty_cycle(self):
        """Duty cycle of the PWM.

        :type: float
        """

        duty_cycle_ns = int(utils.readstr_all(os.path.join(_CHANNEL_PATH(self._chip,
                                                                         self._channel),
                                                           'duty_cycle')))
        if self.period > 0:
            return float(duty_cycle_ns / 1000.0 / float(self.period))
        else:
            return 0.0

    @duty_cycle.setter
    def duty_cycle(self, duty_cycle):
        if not isinstance(duty_cycle, (int, float)):
            raise TypeError("duty_cycle must be an int or float.")
        elif duty_cycle < 0.0 or duty_cycle > 1.0:
            raise ValueError("duty_cycle must be between 0.0 and 1.0.")

        duty_cycle = duty_cycle * self.period
        duty_cycle_ns = int(duty_cycle * 1000)

        utils.writestr_all(os.path.join(_CHANNEL_PATH(self._chip, self._channel),
                                        'duty_cycle'), duty_cycle_ns)

    @property
    def period(self):
        """Microsecond period of the PWM.

        :type: int
        """
        period_ns = int(utils.readstr_all(os.path.join(_CHANNEL_PATH(self._chip,
                                                                     self._channel),
                                                       'period')))
        return int(period_ns / 1000)

    @period.setter
    def period(self, period):
        if sys.version_info[0] == 2:
            if not isinstance(period, (int, long)):
                raise TypeError("period must be an int, long.")
        else:
            if not isinstance(period, int):
                raise TypeError("period must be an int.")

        period_ns = int(period * 1000)

        utils.writestr_all(os.path.join(_CHANNEL_PATH(self._chip, self._channel),
                                        'period'), period_ns)

    def close(self):
        """Close the channel and release any system resources."""
        if hasattr(self, '_chip') and hasattr(self, '_channel'):
            if self._chip is None or self._channel is None:
                return

            utils.writestr_all(os.path.join(_CHIP_PATH(self._chip), 'unexport'),
                               self._channel)

        self._chip = None
        self._channel = None

    @property
    def polarity(self):
        """Polarity setting of the PWM.

        Basically, this sets the "active high" or "active low" setting of the
        PWM.

        :type: PWM.NORMAL, PWM.INVERSED

        Note:
            This a readonly property because we set polarity in creation and
            there seems to be little value in changing it later.
        """
        return utils.readstr_all(os.path.join(_CHANNEL_PATH(self._chip,
                                                            self._channel),
                                              "polarity"))

    @staticmethod
    def enumerate():
        """Enumerate a list of PWM chips available on the system.

        Returns:
            list
        """
        chips = [utils.get_trailing_number(f) for f in os.listdir(_PWM_ROOT) \
                 if os.path.isdir(os.path.join(_PWM_ROOT, f))]
        return sorted(chips)

    @staticmethod
    def num_channels(chip):
        """Get the number of available PWM channels on the specified chip.

        Args:
            chip (int): The PWM chip id.

        Returns:
            int
        """
        return int(utils.readstr_all(os.path.join(_CHIP_PATH(chip), "npwm")))

    def __str__(self):
        return ("PWM (chip=%d, channel=%d, enabled=%r, duty_cycle=%f, "
                "period=%d, polarity=%s)") % (self.chip,
                                              self.channel,
                                              self.enabled,
                                              self.duty_cycle,
                                              self.period,
                                              self.polarity)
