#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name = 'simhash',
    version = '2.1.2',
    keywords = ('simhash'),
    description = 'A Python implementation of Simhash Algorithm',
    license = 'MIT License',

    url = 'http://leons.im/posts/a-python-implementation-of-simhash-algorithm/',
    project_urls = {
        'Source': 'https://github.com/1e0ng/simhash',
    },
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
