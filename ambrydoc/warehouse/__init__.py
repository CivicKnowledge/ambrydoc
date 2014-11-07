"""Documentation, file and login server for Ambry warehouses
"""

import logging
from flask import Flask, current_app

import os
import functools


app = Flask(__name__)

# Default configuration
app_config = {'host': os.getenv('AMBRYDOC_HOST', 'localhost'),
              'port': os.getenv('AMBRYDOC_PORT', 8081),
              'cache': os.getenv('AMBRYDOC_CACHE', '/tmp/ambrydoc'),
              'use_proxy': bool(os.getenv('AMBRYDOC_USE_PROXY', False)),
              'debug ': bool(os.getenv('AMBRYDOC_HOST', False))
}

def configure_application(command_args = {}):

    app_config.update(command_args)

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
    cache_config = parse_cache_string(current_app.app_config['cache'])
    return new_cache(cache_config, run_config=current_app.run_config)

@memoize
def renderer():
    return Renderer(cache(), library=library(), warehouse = warehouse(), root_path = '/')


import views
configure_application() # May get run again in __main__, when running in develop mode.
