Changelog
---------

1.8 (Jun  3, 2024)
==================

- utils: add support for sama7d65 curiosity


1.7 (October 3, 2023)
=====================

- gpio: fix file descriptor close
- utils: add support for sama5d29 curiosity
- utils: add support for sam9x75 curiosity
- fix url in documentation


1.6 (July 21, 2023)
====================

- fix link for sam9x75-eb
- add .readthedocs.yaml file


1.5 (April 12, 2023)
====================

- fix warnings with setup.py (pypandoc) & setup.cfg (description_file)
- utils: add support sam9x60 curiosity board


1.4 (July 6, 2022)
==================

- utils: add support for sam9x7 and sam9x7-eb
- utils: add support for sama7g5 and sama7g5-ek
- utils: add support for sama5d27 wlsom1 ek


1.3 (August 31, 2020)
=======================

- mpio: more fixes to Python 3 incompatibility (pwm, gpio, devmem)
- utils: add support for sam9x60-ek


1.2 (June 18, 2019)
=======================

- mpio: fix Python 3 incompatibility


1.1 (September 6, 2018)
=======================

- test: spi: add loopback test
- mpio: fix close() on uninitialized objects
- gpio: return None instead of "unknown" when not found
- utils: add support for two environment variables to override cpu and board
- utils: add support for at91sam9x5


1.0 (February 22, 2018)
=======================

- Initial stable release.
