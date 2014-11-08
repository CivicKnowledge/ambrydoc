
# Would use a relative import, but there is a problem realted to -m
# http://stackoverflow.com/a/18888854

import argparse
from ambrydoc import app, configure_application

parser = argparse.ArgumentParser(prog='python -mambry.server.documentation',
                                 description='Run an Ambry documentation server')

parser.add_argument('-H', '--host', help="Server host.")
parser.add_argument('-p', '--port', help="Server port")
parser.add_argument('-c', '--cache', help="Generated file cache. ")

parser.add_argument('-P', '--use-proxy', action='store_true',
                    help="Setup for using a proxy in front of server, using werkzeug.contrib.fixers.ProxyFix")

parser.add_argument('-d', '--debug',  action='store_true',  help="Set debugging mode")

args = parser.parse_args()


if args.use_proxy:
    from werkzeug.contrib.fixers import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app)

config = configure_application(vars(args))

import ambrydoc.views

app.run(host = config['host'], port = int(config['port']), debug = config['debug'])


