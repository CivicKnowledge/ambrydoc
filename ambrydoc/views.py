
import os
from . import app, renderer


from flask import g, current_app, send_from_directory, request


@app.teardown_appcontext
def close_connection(exception):
    pass

@app.errorhandler(500)
def page_not_found(e):
    return renderer().error500(e)

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

@app.route('/search.<ct>')
def search(ct):
    return renderer(content_type=ct).search(term=request.args.get('term'))

@app.route('/bundles/<vid>.<ct>')
def get_bundle(vid, ct):
    return renderer(content_type=ct).bundle(vid)

@app.route('/bundles/<vid>/schema.<ct>')
def get_schema(vid, ct):

    if ct == 'csv':
        return renderer().schemacsv(vid)
    else:
        return renderer(content_type=ct).schema(vid)

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
    from flask import url_for

    return renderer(content_type=ct).store(sid)

@app.route('/stores/<sid>/tables/<tvid>.<ct>')
def get_store_table(sid, tvid, ct):

    return renderer(content_type=ct).store_table(sid, tvid)

@app.route('/manifests/<mid>.<ct>')
def get_manifest(mid, ct):

    return renderer(content_type=ct).manifest(mid)

@app.route('/sources.<ct>')
def get_sources(ct):

    return renderer(content_type=ct).sources()

@app.route('/test')
def test():
    pass

@app.route('/info')
def info():
    return renderer().info(current_app.app_config, current_app.run_config)
