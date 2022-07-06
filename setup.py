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
import codecs
import sys
import subprocess
from setuptools import setup, find_packages
from mpio import __version__

try:
    import pypandoc
    README = pypandoc.convert_file('README.md', 'rst')
except ImportError:
    with codecs.open('README.md', encoding='utf-8') as f:
        README = f.read()

setup(
    name='mpio',
    author='Joshua Henderson',
    author_email='joshua.henderson@microchip.com',
    version=__version__,
    packages=['mpio'],
    include_package_data=True,
    install_requires=[
    ],
    extras_require={
    },
    description="Hardware access for Microchip boards",
    long_description=README,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Embedded Systems',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
