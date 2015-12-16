#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
import ast
from setuptools import setup


def readme():
    with open('README.rst') as f:
        return f.read()


def get_meta(filename):
    """Get top level module metadata without execution.
    """
    result = {
        '__file__': filename,
        '__name__': os.path.splitext(os.path.basename(filename))[0],
        '__package__': '',
    }

    with open(filename) as fp:
        root = ast.parse(fp.read(), fp.name)

    result['__doc__'] = ast.get_docstring(root)

    for node in ast.iter_child_nodes(root):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                try:
                    result[target.id] = ast.literal_eval(node.value)
                except ValueError:
                    pass

    return result


install_requires = ['requests']
if sys.version[:3] < '3.4':
    install_requires.append('pathlib')
if sys.version[:3] < '3.3':
    install_requires.append('mock')

meta = get_meta('urlpath.py')

setup(
    py_modules=[meta['__name__']],
    name=meta['__name__'],
    version=meta['__version__'],
    author=meta['__author__'],
    author_email=meta['__author_email__'],
    url=meta['__url__'],
    download_url=meta['__download_url__'],
    description=meta['__doc__'].strip().splitlines()[0],
    long_description=readme(),
    classifiers=meta['__classifiers__'],
    license=meta['__license__'],
    install_requires=install_requires,
    extras_require={
        'test': ['WebOb']
    },
)
