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
from os import path

# read the README.md contents
pkg_dir = path.abspath(path.dirname(__file__))
with open(path.join(pkg_dir, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='batchmp',
    version='1.0',

    url='https://github.com/akpw/batch-mp-tools',

    author='Arseniy Kuznetsov',
    author_email='k.arseniy@gmail.com',

    long_description=long_description,
    long_description_content_type='text/markdown',

    description=('Command-line tools for batch media processing'),
    license='GNU General Public License v2 (GPLv2)',

    packages=find_packages(exclude=['test*']),
    keywords = 'batch processing media video audio CLI rename tags ID3',

    install_requires = ['mutagen>=1.27', 'pygtrie>=2.3.2'], ##, 'profilehooks>=1.11.0'],

    test_suite = 'tests.batch_mp_test_suite',

    entry_points={'console_scripts': [
        'batchmp = batchmp.cli.base.bmp_dispatch:main',
        'renamer = batchmp.cli.renamer.renamer_dispatch:main',
        'tagger = batchmp.cli.tagger.tagger_dispatch:main',
        'bmfp = batchmp.cli.bmfp.bmfp_dispatch:main',
    ]},
    zip_safe=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3 :: Only',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Information Technology',
        'Operating System :: OS Independent',
        'Topic :: Multimedia :: Sound/Audio',
        'Topic :: Multimedia :: Sound/Audio :: Analysis',
        'Topic :: Multimedia :: Sound/Audio :: Conversion',
        'Topic :: Multimedia :: Video',
        'Topic :: Multimedia :: Video :: Conversion',
        'Topic :: Software Development :: Libraries',
        'Topic :: Utilities',
    ]
)



