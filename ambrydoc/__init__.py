"""
Documentation, file and login server for Ambry warehouses


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


import os
import functools

from flask import Flask, current_app


app = Flask(__name__)


# Default configuration
app_config = {'host': os.getenv('AMBRYDOC_HOST', 'localhost'),
              'port': os.getenv('AMBRYDOC_PORT', 8081),
              'cache': os.getenv('AMBRYDOC_CACHE', '/data/cache/documentation/'),
              'accounts': os.getenv('AMBRYDOC_ACOUNTS', '/etc/ambrydoc/accounts.yaml'),
              'use_proxy': bool(os.getenv('AMBRYDOC_USE_PROXY', False)),
              'debug': bool(os.getenv('AMBRYDOC_HOST', False))
}

def configure_application(command_args = {}):

    app_config.update({ k:v for k,v in command_args.items() if v is not None } )

    with app.app_context():
        current_app.app_config = app_config

    return app_config


# From https://wiki.python.org/moin/PythonDecoratorLibrary#Memoize
def memoize(obj):
    cache = obj.cache = {}

    @functools.wraps(obj)
    def memoizer(*args, **kwargs):
        key = str(args) + str(kwargs)
        if key not in cache:
            cache[key] = obj(*args, **kwargs)
        return cache[key]

    return memoizer


@memoize
def cache():
    from ckcache import parse_cache_string, new_cache

    if os.path.exists(current_app.app_config['accounts']):
        import yaml
        with open(current_app.app_config['accounts']) as f:
            accounts = yaml.load(f)
    else:
        accounts = None

    cache_config = parse_cache_string(current_app.app_config['cache'])
    return new_cache(cache_config, accounts = accounts)

@memoize
def renderer():
    from render import Renderer
    return Renderer(cache())


configure_application() # May get run again in __main__, when running in develop mode.
