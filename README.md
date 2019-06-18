![Microchip](https://raw.githubusercontent.com/linux4sam/mpio/master/docs/_static/microchip_logo.png)

# Microchip Peripheral I/O Python Package

This package provides easy access to various hardware peripherals found on
Microchip AT91/SAMA5 processors and Xplained boards running Linux.  The API is
clean, consistent, flexible, documented, and well tested to make navigating and
exercising even the most complex hardware peripherals a trivial task.


## Supported Interfaces

* ADC - Analog-to-Digital Converter
* DevMem - Read and Write System Memory
* GPIO - General Purpose I/O
* I2C - Inter-Integrated Circuit
* SMBus - System Management Bus
* Input - Input Subsystem (Mouse/Keyboard/Touchscreen)
* LED - Light Emitting Diode Light Sources
* PWM - Pulse Width Modulation
* SPI - Serial Peripheral Interface Bus
* Serial - RS-232
* CPU and Board Utilities


## Examples

Here's an example of how simple it is to fire up a Python interpreter and toggle
a GPIO.

    >>> from mpio import GPIO
    >>> gpio = GPIO(107, GPIO.OUT)
    >>> gpio.set(True)
    >>> gpio.set(False)


## Installation

You can install from PyPi by default with:

    pip install mpio

## License

Microchip Peripheral I/O is released under the terms of the `Apache License
Version 2`. See the `LICENSE` file for more information.  Parts of the code
originally provided under other licenses are noted in those source files,
including the MIT license and is reproduced in the `LICENSE.MIT` file.
