#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from setuptools import setup
import urlpath as target

setup(
    py_modules=[target.__name__],
    name=target.__name__,
    version=target.__version__,
    author=target.__author__,
    author_email=target.__author_email__,
    url=target.__url__,
    download_url=target.__download_url__,
    description=target.__doc__.strip().splitlines()[0],
    long_description=open('README.txt').read(),
    classifiers=target.__classifiers__,
    license=target.__license__,
)
