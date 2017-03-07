"""A setuptools based setup module.
"""

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='pyowm-micro',
    version='1.0.0',
    description='Python bindings for OpenWeatherMap API with special attention to conciseness and ease of use',
    long_description=long_description,
    url='https://github.com/ola-ct/pyowm-micro',
    author='Oliver Lau',
    author_email='oliver@ersatzworld.net',
    license='GPLv3',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6'
    ],
    keywords='openweathermap api weather forecast',
    packages=find_packages(exclude=['contrib', 'docs', 'tests', 'tools']),
    install_requires=['urllib3']
)