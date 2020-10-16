#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name = 'simhash',
    version = '2.0.0',
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
        'nose',
        'scipy',
        'scikit-learn',
        ],
    test_suite = "nose.collector",
)
