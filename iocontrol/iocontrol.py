#!/usr/bin/python
#
# I/O Control Demo Application
#
# Copyright (C) 2017 Microchip Technology Inc.  All rights reserved.
# Joshua Henderson <joshua.henderson@microchip.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
"""
PyQt demo application using mio to control and view hardware peripherals.
"""
import argparse
import sys
import os
import signal
import time
import threading
from functools import partial

try:
    from PyQt4.QtGui import *
    from PyQt4.QtCore import *
    from PyQt4 import uic
    from .pyqt_style_rc import *
except:
    from PyQt5.QtGui import *
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5 import uic
    from .pyqt5_style_rc import *

import mio

_version = "1.0"

def readonly(widget, state):
    """Special definition of setting a widget to readonly, without graying it out.
    """
    widget.setAttribute(Qt.WA_TransparentForMouseEvents, state)
    widget.setFocusPolicy(Qt.NoFocus if state else Qt.StrongFocus)

class AsyncHandler(QThread):
    """
    This is wrapper that will handle asynchronously calling a function and then
    emit() an event when the function returns True.
    """
    event = pyqtSignal(float)

    def __init__(self, function, delay=None):
        super(AsyncHandler, self).__init__()
        self.delay = delay
        self._function = function
        self._stop_event = threading.Event()
        self._stop_event.set()

    def start(self):
        self._stop_event.clear()
        super(AsyncHandler, self).start()

    def run(self):
        while not self.stopped():
            value = self._function()
            if value is not None:
                self.event.emit(value)
            if self.delay is not None:
                time.sleep(self.delay)

    def stopped(self):
        return self._stop_event.is_set()

    def stop(self):
        """Stop the capture thread from running.
        """
        self._stop_event.set()
        self.wait()

class LEDWidget(QWidget):
    def __init__(self, led, parent=None):
        super(LEDWidget, self).__init__(parent)

        self.led = led
        slider = QSlider(Qt.Horizontal, self)
        slider.setMinimum(0)
        slider.setValue(led.brightness)
        slider.setMaximum(led.max_brightness)

        layout = QHBoxLayout()
        layout.addWidget(slider)
        self.setLayout(layout)

        slider.valueChanged.connect(self.sliderChanged)

    def sliderChanged(self, value):
        self.led.brightness = value

class GPIOHeaderWidget(QWidget):
    def __init__(self, parent=None):
        super(GPIOHeaderWidget, self).__init__(parent)

        layout = QHBoxLayout()
        layout.addWidget(QLabel("GPIO"))
        layout.addWidget(QLabel("None"))
        layout.addWidget(QLabel("Input"))
        layout.addWidget(QLabel("Output"))
        layout.addWidget(QLabel("State"))
        self.setLayout(layout)

class GPIOWidget(QWidget):
    def __init__(self, pin, parent=None):
        super(GPIOWidget, self).__init__(parent)

        self.handler = None
        self.gpio = None
        self.pin = pin
        self.label = QLabel(mio.GPIO.pin_to_name(pin))
        self.none = QRadioButton()
        self.none.setChecked(True)
        self.input = QRadioButton()
        self.out = QRadioButton()
        self.state = QCheckBox()
        readonly(self.state, True)

        layout = QHBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.none)
        layout.addWidget(self.input)
        layout.addWidget(self.out)
        layout.addWidget(self.state)
        self.setLayout(layout)

        self.none.toggled.connect(lambda: self.setNone() if self.none.isChecked() else None)
        self.input.toggled.connect(lambda: self.setInput() if self.input.isChecked() else None)
        self.out.toggled.connect(lambda: self.setOutput() if self.out.isChecked() else None)
        self.state.stateChanged.connect(lambda: self.setValue(self.state.isChecked()))

    def setNone(self):
        readonly(self.state, False)
        self.state.setChecked(False)
        if self.handler:
            self.handler.stop()
        if self.gpio:
            self.gpio.close()
            self.gpio = None

    def setOutput(self):
        readonly(self.state, False)
        if self.handler:
            self.handler.stop()
        if self.gpio is not None:
            self.gpio.close()
        self.gpio = mio.GPIO(self.pin, mio.GPIO.OUT, force_own=True)

    def setInput(self):
        readonly(self.state, True)
        if self.gpio is not None:
            self.gpio.close()
        self.gpio = mio.GPIO(self.pin, mio.GPIO.IN, force_own=True)
        if self.gpio.interrupts_available:
            self.handler = AsyncHandler(function=partial(self.gpio.poll, timeout=0.5))
            self.handler.event.connect(self.onValueChange)
            self.handler.start()

    def setValue(self, value):
        if self.gpio:
            if self.gpio.mode == mio.GPIO.OUT:
                self.gpio.set(value)

    def onValueChange(self, value):
        if self.gpio:
            self.state.setChecked(value)

    def __del__(self):
        if self.handler:
            self.handler.stop()

class ADCWidget(QWidget):
    def __init__(self, adc, channel, parent=None):
        super(ADCWidget, self).__init__(parent)

        self.adc = adc
        self.channel = channel
        group = QGroupBox("ADC {}, Channel {}".format(adc.device, self.channel), self)
        self.value_label = QLabel("{0:.2f}v".format(0.0))
        self.value_label.setFont(QFont('SansSerif', 18))

        layout = QVBoxLayout()
        layout.addWidget(self.value_label)
        layout.addStretch(1)
        group.setLayout(layout)

        layout2 = QHBoxLayout()
        layout2.addWidget(group)
        self.setLayout(layout2)

        self.handler = AsyncHandler(function=partial(self.adc.volts, self.channel), delay=0.5)
        self.handler.event.connect(self.onValueChange)
        self.handler.start()

    def onValueChange(self, value):
        self.value_label.setText("{0:.2f}v".format(value))

    def __del__(self):
        if self.handler:
            self.handler.stop()

class PWMWidget(QWidget):
    def __init__(self, pwm, parent=None):
        super(PWMWidget, self).__init__(parent)

        self.pwm = pwm
        group = QGroupBox("PWM {}, Channel {}".format(pwm.chip, pwm.channel))

        self.enabled = QCheckBox("Enabled")

        PERIOD_MAX = 1000000

        self.period_slider = QSlider(Qt.Horizontal)
        self.period_slider.setMinimum(0)
        self.period_slider.setValue(pwm.period)
        self.period_slider.setMaximum(PERIOD_MAX)

        self.duty_slider = QSlider(Qt.Horizontal)
        self.duty_slider.setMinimum(0)
        self.duty_slider.setValue(pwm.duty_cycle * pwm.period)
        self.duty_slider.setMaximum(PERIOD_MAX)

        self.enabled.setChecked(pwm.enabled)

        layout = QVBoxLayout()
        layout.addWidget(self.enabled)
        layout.addWidget(QLabel("Period"))
        layout.addWidget(self.period_slider)
        layout.addWidget(QLabel("Duty Cycle"))
        layout.addWidget(self.duty_slider)
        layout.addStretch(1)
        group.setLayout(layout)

        layout2 = QHBoxLayout()
        layout2.addWidget(group)
        self.setLayout(layout2)

        self.enabled.stateChanged.connect(lambda: self.setEnabled(self.enabled.isChecked()))
        self.period_slider.valueChanged.connect(self.periodSliderChanged)
        self.duty_slider.valueChanged.connect(self.dutySliderChanged)

    def setEnabled(self, value):
        self.pwm.enabled = value

    def periodSliderChanged(self, value):
        # prevent period from being smaller than duty_cycle
        if value < self.duty_slider.value():
            self.period_slider.setValue(self.duty_slider.value())
            value = self.duty_slider.value()
        self.pwm.period = value

    def dutySliderChanged(self, value):
        # prevent duty_cycle from being larger than period
        if value > self.period_slider.value():
            self.duty_slider.setValue(self.period_slider.value())
            value = self.period_slider.value()
        if self.pwm.period > 0:
            self.pwm.duty_cycle = float(float(value) / float(self.pwm.period))

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'iocontrol.ui'), self)

        self.btn_exit.clicked.connect(self.close)

        self.setupLEDTab(self.tab_led)
        self.setupGPIOTab(self.tab_gpio)
        self.setupADCTab(self.tab_adc)
        self.setupPWMTab(self.tab_pwm)

    def setupDefaultTabLayout(self, tab):
        tab.scrollLayout = QFormLayout()
        tab.scrollWidget = QWidget()
        tab.scrollWidget.setLayout(tab.scrollLayout)
        tab.scrollArea = QScrollArea()
        tab.setContentsMargins(0, 0, 0, 0)
        tab.scrollArea.setWidgetResizable(True)
        tab.scrollArea.setWidget(tab.scrollWidget)
        tab.mainLayout = QVBoxLayout()
        tab.mainLayout.setContentsMargins(0, 0, 0, 0)
        tab.mainLayout.addWidget(tab.scrollArea)
        tab.setLayout(tab.mainLayout)

    def setupGPIOTab(self, tab):
        self.setupDefaultTabLayout(tab)

        tab.scrollLayout.addRow(GPIOHeaderWidget())

        for pin in range(0, 160):
            tab.scrollLayout.addRow(GPIOWidget(pin))

    def setupLEDTab(self, tab):
        self.setupDefaultTabLayout(tab)

        leds = mio.LED.enumerate()
        for name in leds:
            led = mio.LED(name)
            tab.scrollLayout.addRow(QLabel(led.name), LEDWidget(led))

    def setupADCTab(self, tab):
        self.setupDefaultTabLayout(tab)

        devices = mio.ADC.enumerate()
        for device in devices:
            adc = mio.ADC(device)
            channels = adc.available_channels
            for channel in channels:
                tab.scrollLayout.addRow(ADCWidget(adc, channel))

    def setupPWMTab(self, tab):
        self.setupDefaultTabLayout(tab)

        chips = mio.PWM.enumerate()
        for chip in chips:
            for channel in range(mio.PWM.num_channels(chip)):
                try:
                    pwm = mio.PWM(chip, channel, enable=False, force_own=True)
                    tab.scrollLayout.addRow(PWMWidget(pwm))
                except:
                    pass

def excepthook(exc_type, exc_value, traceback_obj):
    separator = '-' * 80
    notice = "An unhandled exception occurred:\n"
    version_info = '\n'.join((separator, "Version: %s" % _version))
    time_string = time.strftime("%Y-%m-%d, %H:%M:%S")
    errmsg = '%s: \n%s' % (str(exc_type), str(exc_value))
    sections = [separator, time_string, separator, errmsg, separator]
    msg = '\n'.join(sections)
    errorbox = QMessageBox()
    errorbox.setWindowTitle("Exception")
    errorbox.setText(str(notice) + str(msg) + str(version_info))
    errorbox.exec_()

def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)
    sys.excepthook = excepthook

    with open(os.path.join(os.path.dirname(__file__),"style.qss"), 'r') as f:
        app.setStyleSheet(f.read())

    win = MainWindow()

    parser = argparse.ArgumentParser(description='Microchip I/O Control')
    parser.add_argument('--fullscreen', dest='fullscreen', action='store_true',
                        help='show the main window in fullscreen')
    parser.set_defaults(fullscreen=False)
    args = parser.parse_args()

    if args.fullscreen:
        win.showFullScreen()
    else:
        win.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
