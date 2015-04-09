# coding=utf8
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

import subprocess, shlex, time, tempfile, shutil
from functools import wraps
from urllib.parse import urlparse
import urllib.request, urllib.error
from contextlib import contextmanager

''' General-level utilities
'''

@contextmanager
def temp_dir():
    ''' Temp dir context manager
    '''
    tmp_dir = tempfile.mkdtemp()
    try:
        yield tmp_dir
    finally:
        # remove tmp dir
        shutil.rmtree(tmp_dir)


def timed(f):
    """ A timing decorator
    """
    @wraps(f)
    def wrapper(*args, **kwds):
        start = time.time()
        result = f(*args, **kwds)
        elapsed = time.time() - start
        return (result, elapsed)
    return wrapper


class CmdProcessingError(Exception):
    pass

@timed
def run_cmd(cmd, shell = False):
    ''' Runs shell commands in a separate process
    '''
    if not shell:
        cmd = shlex.split(cmd)
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell = shell)
    output = proc.communicate()[0].decode('utf-8')
    if proc.returncode != 0:
        raise CmdProcessingError(output)
    return output


class MiscHelpers:
    @staticmethod
    def int_num_digits(num):
        ''' Number of digits in an int number
        '''
        num_digits = 1
        while (int(abs(num)/(10**num_digits)) > 0):
            num_digits += 1
        return num_digits


class ImageLoader:
    @staticmethod
    def load_image_from_url(url):
        ''' Loads image from an URL
        '''
        img = None
        try:
            responce = urllib.request.urlopen(url, timeout = 5)
        except urllib.error.URLError as e:
            print('A problem while retrieving image: "{}"'.format(e))
        else:
            content_type = dict(responce.getheaders())['Content-Type']
            if content_type.split('/')[0] != 'image':
                print('URL did not seem to return a valid image')
                print('Received Content-Type: {}'.format(content_type))
            else:
                img = responce.read()

        return img

    @staticmethod
    def load_image_from_file(fpath):
        ''' Loads an image from disk via file path
        '''
        img = None
        if fpath:
            with open(fpath, 'rb') as f:
                img = f.read()

        return img

    @staticmethod
    def load_image(path_or_url):
        ''' Loads an image from an URL or a file path
        '''
        url_parts = urlparse(path_or_url)
        if url_parts.scheme in (None, '') and url_parts.netloc in (None, ''):
            return ImageLoader.load_image_from_file(path_or_url)

        if url_parts.scheme == 'file':
            fpath = format(url_parts.path)
            if url_parts.netloc == '~':
                fpath = '~{}'.format(fpath)
            return ImageLoader.load_image_from_file(path_or_url)

        return ImageLoader.load_image_from_url(path_or_url)



