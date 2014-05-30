#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name = 'simhash',
    version = '1.4.0',
    keywords = ('simhash'),
    description = 'A Python implementation of Simhash Algorithm',
    license = 'MIT License',

    url = 'http://liangsun.org/posts/a-python-implementation-of-simhash-algorithm/',
    author = 'Liang Sun',
    author_email = 'i@liangsun.org',

    packages = find_packages(),
    include_package_data = True,
    platforms = 'any',
    install_requires = [],
)
