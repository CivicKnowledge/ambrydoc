"""
Documentation, file and login server for Ambry warehouses


Copyright 2014, Civic Knowledge. All Rights Reserved
"""

import os
import logging
import sys


__version__ = 0.1
__author__ = "Eric Busboom <eric@civicknowledge.com>"

root_config = '/etc/ambrydoc/config.yaml'
user_config = '~/.ambrydoc/config.yaml'

config_paths = [root_config, os.path.expanduser(user_config) ]

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
              'use_proxy': bool(os.getenv('AMBRYDOC_USE_PROXY', False)),
              'debug': bool(os.getenv('AMBRYDOC_HOST', False))
}

def configure_application(command_args = {}):

    app_config.update(read_config())

    app_config.update({ k:v for k,v in command_args.items() if v is not None } )

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
def fscache():
    from ckcache import parse_cache_string, new_cache

    cache_config = parse_cache_string(app_config['cache'])
    return new_cache(cache_config)

@memoize
def renderer(content_type='html'):
    from render import Renderer
    return Renderer(fscache(), content_type=content_type)

def write_config(config):
    import yaml

    done = False
    for path in config_paths:
        try:

            c_dir = os.path.dirname(path)

            if not os.path.exists(c_dir):
                os.makedirs(c_dir)

            with open(path, 'wb') as f:
                yaml.dump(config, f, default_flow_style=False, indent=4, encoding='utf-8')

            return path


        except OSError:
            pass

    raise Exception("Failed to write config to any dir. Tried: {} ".format(config_paths))


def read_config():

    import yaml

    for path in config_paths:
        try:

            c_dir = os.path.dirname(path)

            if not os.path.exists(c_dir):
                os.makedirs(c_dir)

            with open(path, 'rb') as f:
                return yaml.load(f)

        except OSError:
            pass

    return {}



with app.app_context():
    current_app.app_config = configure_application() # May get run again in __main__, when running in develop mode.
