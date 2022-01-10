#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name = 'simhash',
    version = '2.1.1',
    keywords = ('simhash'),
    description = 'A Python implementation of Simhash Algorithm',
    license = 'MIT License',

    url = 'http://leons.im/posts/a-python-implementation-of-simhash-algorithm/',
    author = '1e0n',
    author_email = 'i@leons.im',

    packages = find_packages(),
    include_package_data = True,
    platforms = 'any',
    install_requires = [
        'numpy',
    ],
    tests_require = [
        'nose2',
        'scipy',
        'scikit-learn',
        ],
    test_suite="tests",
)
