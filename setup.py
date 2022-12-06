# -*- coding: utf-8 -*-
"""setup with setuptools."""

from setuptools import setup
from planner import __version__

setup(
    name='planner',
    version=__version__,
    description='A way to manage functions.',
    author='Logic',
    author_email='logic.irl@outlook.com',
    url='https://github.com/TheStar-LikeDust/planner',
    python_requires='>=3.8',
    # packages=find_packages(exclude=['tests*']),
    install_requires=[
    ],
    entry_points='''
        [console_scripts]
    ''',
    license='Apache License 2.0'
)
