#!/usr/bin/env python
"""
Setup for sending netmem package to pypi.

Live:
    https://pypi.python.org/pypi/netmem
    https://pypi.python.org/pypi?%3Aaction=pkg_edit&name=netmem

Test:
    https://testpypi.python.org/pypi/netmem
    https://testpypi.python.org/pypi?%3Aaction=pkg_edit&name=netmem

"""
import os
import sys

from setuptools import setup

with open("./netmem/__version__.py") as version_file:
    version = version_file.read().split("\"")[1]

if sys.argv[-1] == 'test':
    print("TEST")
    os.system('python3 setup.py register -r pypitest')
    os.system('python3 setup.py sdist upload -r pypitest')
    sys.exit()

if sys.argv[-1] == 'publish':
    print("PUBLISH")
    os.system('python3 setup.py register -r pypi')
    os.system('python3 setup.py sdist upload -r pypi')
    sys.exit()

install_reqs = [
    "aiohttp"
]


def read(fname):
    try:
        with open(os.path.join(os.path.dirname(__file__), fname)) as f:
            return f.read()
    except IOError:
        return ""

setup(
    name = "netmem",
    version = version,
    author = "Robert Harder",
    author_email = "rob@iharder.net",
    description = ("A network-synchronized dictionary."),
    license = "Public Domain",
    keywords = "network, memory, synchronize",
    url = "https://github.com/rharder/netmem",
    download_url="https://github.com/rharder/netmem/tarball/" + version,
    # Be sure to do "git tag 0.1.0" or similar to support download linking
    packages=['netmem'],
    long_description=read('README.rst'),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Natural Language :: English",
        "License :: Public Domain",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities"
    ],
    install_requires=install_reqs
)
