Quick Start
-----------
These examples are about as simple as it gets and they don't attempt to cover
the complete API.  For more examples see the `examples` directory.

All of these examples can be run interactively right from the command line.  No
need to write a script and execute it.  This makes it very easy to start testing
and working with external hardware peripherals on the fly.

::

    $ python
    Python 2.7.12 (default, Nov 19 2016, 06:48:10)
    [GCC 5.4.0 20160609] on linux2
    Type "help", "copyright", "credits" or "license" for more information.
    >>> import mpio
    >>> g = mpio.LED("green")
    >>> g.brightness = True
    >>> g.brightness
    255


Set an output pin high
======================

::

    >>> from mpio import GPIO

    # create an output pin with an initial state of low
    >>> gpio = GPIO(107, GPIO.OUT, initial=GPIO.LOW)
    # set the pin state high
    >>> gpio.set(True)


Turn an LED on and off
======================

::

    >>> from mpio import LED

    # initialize the green LED as on
    >>> green = LED("green", True)
    # turn it off
    >>> green.brightness = False


Run a PWM output through a range of duty cycles
===============================================

::

    >>> from mpio import PWM

    # create a PWM with a period of 10000 and a duty cycle of 10
    >>> pwm = PWM(0, 0, 10000, 1000)
    >>> while True:
    ...    # sweep the duty cycle over 1000 increments
    ...    for i in range(1, 10):
    ...        pwm.set_duty(i * 1000)
    ...        time.sleep(1)


Read an analog input
====================

::

    >>> from mpio import ADC

    # initialize the ADC
    >>> adc = ADC(0)
    # read channel 0's level
    >>> print "ADC value: %d" % adc.voltage_raw(0)


Input events from gpio key buttons
==================================

::

    >>> from mpio import Input

    # initialize input
    >>> input = Input("event3")
    # read a single event from the input
    >>> print input.read()


Serial output
=============

::

    >>> from mpio import Serial

    # open /dev/ttyUSB0 with baudrate 115200
    >>> s = Serial("/dev/ttyUSB0", 115200)
    # write an ASCII string to it
    >>> s.write(b"Hello World!")


Read a hardware register
========================

::

    >>> from mpio import DevMem

    # read the CHIP ID register on SAMA5D2
    >>> print "0x{0:04x}".format(DevMem.read_reg(0xFC069000))
