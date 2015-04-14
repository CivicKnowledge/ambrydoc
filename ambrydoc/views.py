
import os
from . import app, renderer


from flask import g, current_app, send_from_directory, request


def send_json(o):
    from flask import Response
    from flask.json import dumps
    from render import JSONEncoder

    return Response(dumps(o, cls=JSONEncoder, indent=4),mimetype='application/json')

@app.teardown_appcontext
def close_connection(exception):
    pass

@app.errorhandler(500)
def page_not_found(e):
    return renderer().error500(e)


# Really should be  serving this from a static directory, but this
# is easier for now.
@app.route('/css/<name>')
def css_file(name):
    return send_from_directory(renderer().css_dir, name)

@app.route('/js/<path:path>')
def js_file(path):
    import os.path

    dir, name = os.path.split(os.path.join(renderer().js_dir, path))


    return send_from_directory(dir, name)

@app.route('/')
@app.route('/index')
def index():
    return renderer().index()

@app.route('/index.<ct>')
def index_ct(ct):
    return renderer(content_type=ct).index()

@app.route('/databases.<ct>')
def databases_ct(ct):
    return renderer(content_type=ct).databases()

@app.route('/search.<ct>')
def search(ct):

    return renderer(content_type=ct).search(term=request.args.get('term'))

@app.route('/search/dataset')
def datasetsearch():
    """Search for a dataset, using a single term"""

    return renderer().dataset_search(term=request.args.get('term'))

@app.route('/search/place')
def place_search():
    """Search for a place, using a single term"""

    return renderer().place_search(term=request.args.get('term'))

@app.route('/search/bundle')
def bundle_search():
    """Search for a datasets and partitions, using a structured JSON term"""

    return renderer().bundle_search(terms=request.args)



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
def get_bundle_partitions(bvid, pvid, ct):

    return renderer(content_type=ct).partition(pvid)

@app.route('/collections.<ct>')
def get_collections(ct):

    return renderer(content_type=ct).collections_index()

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

@app.route('/test/times')
def test_times():

    return send_json(([x.__dict__ for x in renderer().compiled_times()]))

