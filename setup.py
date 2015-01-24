#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from setuptools import setup
import urlpath as target


def readme():
    with open('README.txt') as f:
        return f.read()


install_requires = []
if sys.version[:3] < '3.4':
    install_requires.append('pathlib')
if sys.version[:3] < '3.3':
    install_requires.append('mock')

setup(
    py_modules=[target.__name__],
    name=target.__name__,
    version=target.__version__,
    author=target.__author__,
    author_email=target.__author_email__,
    url=target.__url__,
    download_url=target.__download_url__,
    description=target.__doc__.strip().splitlines()[0],
    long_description=readme(),
    classifiers=target.__classifiers__,
    license=target.__license__,
    install_requires=install_requires,
)
