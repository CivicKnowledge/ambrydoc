#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

__version__ = None # "Declare", actually set in the execfile
__author__ = None
__email__ = None

# Load in the metadata.
execfile(os.path.join(os.path.dirname(__file__),'ambrydoc/_meta.py'))


if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()


with open(os.path.join(os.path.dirname(__file__), 'README.md')) as f:
    readme = f.read()

packages = [
    'ambrydoc'
]

scripts=[ ]

package_data = {"": ['*.html', '*.css', '*.rst']}

requires = [
    "flask",
    "Whoosh"
]

def find_package_data():
    """Return package_data, because setuptools is too stupid to handle nested directories """
    #
    #return {"ambry": ["support/*"]}

    l = list()

    import os
    for start in ("ambrydoc/static", "ambrydoc/templates"):
        for root, dirs, files in os.walk(start):

            for f in files:

                if f.endswith('.pyc'):
                    continue

                path = os.path.join(root,f).replace("ambrydoc/",'')

                l.append(path)

    return {"ambrydoc": l }

classifiers = [
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
]

setup(
    name='ambrydoc',
    version=__version__,
    description='Documentation server for Ambry',
    long_description=readme,
    packages=packages,
    package_data=find_package_data(),
    include_package_data=True,
    scripts=scripts,
    install_requires=requires,
    author='Eric Busboom',
    author_email='eric@sandiegodata.org',
    url='',
    license='LICENSE',
    classifiers=classifiers,
)