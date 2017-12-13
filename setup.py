#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""dkconfig - command line access to ConfigParser
"""

classifiers = """\
Development Status :: 4 - Beta
Intended Audience :: Developers
License :: OSI Approved :: MIT License
Programming Language :: Python
Programming Language :: Python :: 2
Programming Language :: Python :: 2.7
Programming Language :: Python :: 3
Programming Language :: Python :: 3.4
Programming Language :: Python :: 3.5
Programming Language :: Python :: 3.6
Topic :: Software Development :: Libraries
"""
import sys
import setuptools
from distutils.core import setup, Command
from setuptools.command.test import test as TestCommand

version = '0.2.0'


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


setup(
    name='dkconfig',
    version=version,
    license='MIT',
    url='https://github.com/datakortet/dkconfig',
    install_requires=[
        'lockfile>=0.10.2',
    ],
    description=__doc__.strip(),
    classifiers=[line for line in classifiers.split('\n') if line],
    long_description=open('README.rst').read(),
    cmdclass={'test': PyTest},
    packages=['dkconfig'],
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'dkconfig=dkconfig:main'
        ]
    }
)
