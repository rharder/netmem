#!/usr/bin/env python
import os
import sys

from setuptools import setup

with open("./netmem/__version__.py") as version_file:
    version = version_file.read().split("\"")[1]

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
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
    description = ("A dictionary synchronized across a network."),
    license = "Public Domain",
    keywords = "network, memory, synchronize",
    url = "https://github.com/rharder/netmem",
    download_url="https://github.com/rharder/netmem/tarball/" + version,
    packages=['netmem'],
    long_description=read('readme.md'),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Natural Language :: English",
        "License :: OSI Approved :: Public Domain",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities"
    ],
    install_requires=install_reqs
)
