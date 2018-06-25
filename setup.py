# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

INSTALL_REQUIREMENTS = [
    'Click>=6.0,<7.0',
    'requests>=2.18',
    'python-dateutil>=2.3.7',
]

setup(
    author='Jonas Ohrstrom',
    author_email='ohrstrom@gmail.com',
    url='https://github.com/ohrstrom/simple-timelog-client',
    name='simple timelog client',
    version='0.0.1',
    description='A simple timelog client',
    packages=find_packages(),
    install_requires=INSTALL_REQUIREMENTS,
    entry_points='''
        [console_scripts]
        tlc=timelog_client:cli
    ''',
)
