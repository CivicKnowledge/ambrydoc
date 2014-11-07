
import os
from . import app, library, warehouse, renderer, global_logger as logger



from flask import g, current_app, send_from_directory


@app.teardown_appcontext
def close_connection(exception):
    pass

@app.route('/css/<name>')
def css_file(name):

    return send_from_directory(renderer().css_dir, name)

@app.route('/')
@app.route('/index')
def index():
    return renderer().index()

@app.route('/bundles/<vid>.html')
def get_bundle(vid):


    return renderer()._bundle_main(vid)

@app.route('/bundles.html')
def get_bundles():

    return renderer().bundles_index()

@app.route('/tables.html')
def get_tables():

    return renderer().tables_index()

@app.route('/bundles/<bvid>/tables/<tvid>.html')
def get_table(bvid, tvid):

    return renderer().table(bvid, tvid)

@app.route('/bundles/<bvid>/partitions/<pvid>.html')
def get_partitions(bvid, pvid):

    return renderer().partition(bvid, pvid)

@app.route('/stores/<sid>.html')
def get_store(sid):
    s = library().store(sid)

    return renderer().store(s)

@app.route('/manifests/<mid>.html')
def get_manifest(mid):

    return renderer().manifest(mid)


@app.route('/test')
def test():
    return warehouse().database.dsn

@app.route('/info')
def info():
    return renderer().info(current_app.app_config, current_app.run_config)
