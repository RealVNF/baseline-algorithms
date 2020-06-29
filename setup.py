# -*- coding: utf-8 -*-
import os

from setuptools import setup, find_packages

requirements = [
    'tqdm',
    'common-utils',
    'coord-sim'
]

test_requirements = [
    'flake8'
]

setup(
    name='baseline-algorithms',
    version='1.0.1',
    description="Baseline algorithms for coordination of chained VNFs",
    url='https://github.com/RealVNF/baseline-algorithms',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    install_requires=requirements + test_requirements,
    tests_require=test_requirements,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            "rs=algorithms.randomSchedule:main",
            "lb=algorithms.loadBalance:main",
            "sp=algorithms.shortestPath:main"
        ],
    },
)
