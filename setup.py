# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


deps = [line.strip() for line in open('requirements.txt')]


setup(
    name='share-bar-server',
    version='0.0.1',
    packages=find_packages(),
    install_requires=deps,
    classifiers=[
        'Private :: Do Not Upload',
    ]
)
