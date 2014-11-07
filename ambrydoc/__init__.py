"""

Copyright 2014, Civic Knowledge. All Rights Reserved
"""

import os
import logging
import sys


__version__ = 0.1
__author__ = "Eric Busboom <eric@civicknowledge.com>"


# From https://wiki.python.org/moin/PythonDecoratorLibrary#Memoize
def memoize(obj):
    cache = obj.cache = {}
    import functools

    @functools.wraps(obj)
    def memoizer(*args, **kwargs):
        key = str(args) + str(kwargs)
        if key not in cache:
            cache[key] = obj(*args, **kwargs)
        return cache[key]

    return memoizer