
import os
from . import app, renderer



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

@app.route('/index.<ct>')
def index_ct(ct):
    return renderer(content_type=ct).index()

@app.route('/bundles/<vid>.<ct>')
def get_bundle(vid, ct):
    return renderer(content_type=ct).bundle(vid)

@app.route('/bundles.<ct>')
def get_bundles(ct):

    return renderer(content_type=ct).bundles_index()

@app.route('/tables.<ct>')
def get_tables(ct):

    return renderer(content_type=ct).tables_index()

@app.route('/bundles/<bvid>/tables/<tvid>.<ct>')
def get_table(bvid, tvid, ct):

    return renderer(content_type=ct).table(bvid, tvid)

@app.route('/bundles/<bvid>/partitions/<pvid>.<ct>')
def get_partitions(bvid, pvid, ct):

    return renderer(content_type=ct).partition(bvid, pvid)

@app.route('/stores/<sid>.<ct>')
def get_store(sid, ct):

    return renderer(content_type=ct).store(sid)

@app.route('/manifests/<mid>.<ct>')
def get_manifest(mid, ct):

    return renderer(content_type=ct).manifest(mid)


@app.route('/test')
def test():
    pass

@app.route('/info')
def info():
    return renderer().info(current_app.app_config, current_app.run_config)
