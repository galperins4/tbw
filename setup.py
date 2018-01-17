#!/usr/bin/env python

try:
    from setuptools import setup
    import wheel
except ImportError:
    from distutils.core import setup

setup(
    name='Python TBW',
    description='A Python True Block Weight Script',
    version='0.5.0',
    author='goose',
    author_email='goosenode@gmail.com',
    url='https://github.com/galperins4/tbw',
    packages=['config', 'snek', 'snek.db'],
    install_requires=['psycopg2']
)