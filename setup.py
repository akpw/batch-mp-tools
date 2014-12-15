## Copyright (c) 2014 Arseniy Kuznetsov
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.

from setuptools import setup, find_packages

setup(
    name='BatchMediaProcessingTools',
    version="0.1",

    url='https://github.com/akpw/batch-mp-tools',

    author='Arseniy Kuznetsov',
    author_email='k.arseniy@gmail.com',

    description=('CLI tools for batch media processing'),
    license='GNU General Public License v2 (GPLv2)',

    packages=find_packages(exclude=['test*']),
    keywords = "batch processing media video audio CLI ",

    install_requires = ['mutagen>=1.27'],

    test_suite = "tests.batch_mp_test_suite",

    scripts=['scripts/denoiser.py'],
    entry_points={'console_scripts': [
        'denoiser = scripts.denoiser:main',
        'renamer = scripts.renamer:main',
    ]},
    zip_safe=True,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Multimedia :: Sound/Audio :: Analysis",
        "Topic :: Multimedia :: Sound/Audio :: Conversion",
        "Topic :: Multimedia :: Sound/Audio :: Noise reduction",
        "Topic :: Software Development :: Libraries",
        'Topic :: Utilities',
    ]
)



