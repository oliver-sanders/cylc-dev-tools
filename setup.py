#!/usr/bin/env python

from setuptools import setup

install_requires = [
]
tests_require = [
]

extra_requires = {
    'all': [],
}
extra_requires['all'] = (
    tests_require
    + list({
        req
        for reqs in extra_requires.values()
        for req in reqs
    })
)


setup(
    version='0.1.0',
    long_description=open('README.rst').read(),
    long_description_content_type="text/rst",
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require=extra_requires
)
