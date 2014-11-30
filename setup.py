#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""dkconfig - command line access to ConfigParser
"""

classifiers = """\
Development Status :: 3 - Alpha
Intended Audience :: Developers
License :: OSI Approved :: MIT License
Programming Language :: Python
Programming Language :: Python :: 2
Programming Language :: Python :: 2.7
Topic :: Software Development :: Libraries
"""

from setuptools import setup, Command

version = '0.1.0'


class PyTest(Command):
    user_options = []
    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import sys,subprocess
        errno = subprocess.call([sys.executable, 'runtests.py'])
        raise SystemExit(errno)


setup(
    name='dkconfig',
    version=version,
    license='MIT',
    url='https://github.com/datakortet/dkconfig',
    requires=[],
    install_requires=['lockfile', 'mock'],
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
