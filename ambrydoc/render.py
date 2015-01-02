"""
Support for creating web pages and text representations of schemas.
"""

import os
from  flask.json import JSONEncoder as FlaskJSONEncoder
from . import memoize

import jinja2.tests

if not 'equalto' in jinja2.tests.TESTS:
    def test_equalto(value, other):
        return value == other

    jinja2.tests.TESTS['equalto'] = test_equalto

if not 'isin' in jinja2.tests.TESTS:
    def test_isin(value, other):
        return value in other

    jinja2.tests.TESTS['isin'] = test_isin


def resolve(t):

    from ambry.identity import Identity
    from ambry.orm import Table
    from ambry.warehouse.manifest import Manifest


    if isinstance(t, basestring):
        return t
    elif isinstance(t, (Identity, Table)):
        return t.vid
    elif isinstance(t, (Identity, Table)):
        return t.vid
    elif isinstance(t, Manifest):
        return t.uid
    elif isinstance(t, dict):
        if 'identity' in t:
            return t['identity'].get('vid',None)
        else:
            return t.get('vid', None)
    else:
        return None


# Path functions, for generating URL paths.
def bundle_path(b):
    return "/bundles/{}.html".format(resolve(b))

def schema_path(b, format):
    return "/bundles/{}/schema.{}".format(resolve(b), format)

def table_path(b, t):
    return "/bundles/{}/tables/{}.html".format(resolve(b), resolve(t))

def proto_vid_path(pvid):

    b,t,c  = deref_tc_ref(pvid)

    return table_path(str(b), str(t))

def deref_tc_ref(ref):
    """Given a column or table, vid or id, return the object"""
    from ambry.identity import ObjectNumber

    on = ObjectNumber.parse(ref)

    b = str(on.as_dataset)

    try:
        c = on
        t = on.as_table
    except AttributeError:
        t = on
        c = None

    if not on.revision:
        # The table does not have a revision, so we need to get one, just get the
        # latest one
        from . import renderer

        r = renderer()
        dc = r.doc_cache

        tm = dc.table_version_map()

        t_vid = reversed(sorted(tm.get(str(t)))).next()

        t = ObjectNumber.parse(t_vid)
        b = t.as_dataset

        if c:
            c = c.rev(t.revision)

    return b,t,c


def tc_obj(ref):
    """Return an object for a table or column"""
    from . import renderer

    b, t, c = deref_tc_ref(ref)

    dc = renderer().doc_cache

    table = dc.get_table(str(t))

    if c:
        try:
            return table['columns'][str(c.rev(0))]
        except KeyError:
            return None
    else:
        return table

def partition_path(b, p=None):

    if p is None:
        from ambry.identity import ObjectNumber
        p  = b
        on = ObjectNumber.parse(p)
        try:
            b = str(on.as_dataset)
        except AttributeError:
            b = str(on)
            raise
    return "/bundles/{}/partitions/{}.html".format(resolve(b), resolve(p))

def manifest_path(m):
    return "/manifests/{}.html".format(m)

def store_path(s):
    return "/stores/{}.html".format(s)

def store_table_path(s,t):
    return "/stores/{}/tables/{}.html".format(s,t)

def extract_url(base,s,t,format):
    return os.path.join(base,s,'extracts',t+'.'+format)

def extractor_list(t):
    from . import renderer

    return ['csv','json'] + ( ['kml','geojson'] if t.get('is_geo',False) else [] )

class extract_entry(object):
    def __init__(self, extracted, completed, rel_path, abs_path, data=None):
        self.extracted = extracted
        self.completed = completed  # For deleting files where exception thrown during generation
        self.rel_path = rel_path
        self.abs_path = abs_path
        self.data = data

    def __str__(self):
        return 'extracted={} completed={} rel={} abs={} data={}'.format(self.extracted,
                                                                        self.completed,
                                                                        self.rel_path, self.abs_path,
                                                                        self.data)

class JSONEncoder(FlaskJSONEncoder):

    def default(self, o):

        return str(type(o))

        #return FlaskJSONEncoder.default(self, o)


class Renderer(object):


    def __init__(self, cache,content_type='html'):

        from jinja2 import Environment, PackageLoader
        from cache import DocCache

        self.cache = cache

        self.doc_cache =  DocCache(self.cache)

        self.css_files = ['css/style.css', 'css/pygments.css' ]

        self.env = Environment(loader=PackageLoader('ambrydoc', 'templates'))

        self.extracts = []

        self.content_type = content_type # Set to true to get Render to return json instead

        # Monkey patch to get the equalto test



    def maybe_render(self, rel_path, render_lambda, metadata={}, force=False):
        """Check if a file exists and maybe render it"""

        if rel_path[0] == '/':
            rel_path = rel_path[1:]

        if rel_path.endswith('.html'):
            metadata['content-type'] = 'text/html'

        elif rel_path.endswith('.css'):
            metadata['content-type'] = 'text/css'

        try:
            if not self.cache.has(rel_path) or force:

                with self.cache.put_stream(rel_path, metadata=metadata) as s:
                    t = render_lambda()
                    if t:
                        s.write(t.encode('utf-8'))
                extracted = True
            else:
                extracted = False

            completed = True

        except:
            completed = False
            extracted = True
            raise

        finally:
            self.extracts.append(extract_entry(extracted, completed, rel_path, self.cache.path(rel_path)))

    def cc(self):
        """return common context values"""
        from functools import wraps

        # Add a prefix to the URLs when the HTML is generated for the local filesystem.
        def prefix_root(r,f):
            @wraps(f)
            def wrapper(*args, **kwds):
                return os.path.join(r,f(*args, **kwds))
            return wrapper

        return {
            'from_root': lambda x: x,
            'bundle_path': bundle_path,
            'schema_path': schema_path,
            'table_path' :  table_path,
            'partition_path': partition_path,
            'manifest_path':  manifest_path,
            'store_path':  store_path,
            'store_table_path': store_table_path,
            'proto_vid_path' : proto_vid_path,
            'extractors' : extractor_list,
            'tc_obj' : tc_obj,
            'extract_url' : extract_url,
            'bundle_sort': lambda l, key: sorted(l,key=lambda x: x['identity'][key])
        }

    def render(self, template, *args, **kwargs):

        from flask.json import dumps
        from flask import Response

        if self.content_type == 'json':
            return Response(dumps(dict(**kwargs), cls=JSONEncoder, indent=4), mimetype='application/json')

        else:
            return template.render(*args, **kwargs)

    def clean(self):
        '''Clean up the extracts on failures. '''
        for e in self.extracts:
            if e.completed == False and os.path.exists(e.abs_path):
                os.remove(e.abs_path)


    def error500(self,e):
        template = self.env.get_template('500.html')

        return self.render(template, e=e, **self.cc())


    def index(self, term=None):

        template = self.env.get_template('index.html')


        return self.render(template, l = self.doc_cache.get_library(), **self.cc())


    def bundles_index(self):
        """Render the bundle Table of Contents for a library"""
        template = self.env.get_template('toc/bundles.html')

        return self.render(template, **self.cc())

    def tables_index(self):

        template = self.env.get_template('toc/tables.html')

        tables = self.doc_cache.get_tables()

        return self.render(template, tables=tables, **self.cc())

    def bundle(self, vid):
        """Render documentation for a single bundle """

        template = self.env.get_template('bundle/index.html')

        b = self.doc_cache.get_bundle(vid)



        return self.render(template, b = b , **self.cc())

    def schemacsv(self, vid):
        """Render documentation for a single bundle """
        from flask import make_response

        response = make_response(self.doc_cache.get_schemacsv(vid))

        response.headers["Content-Disposition"] = "attachment; filename={}-schema.csv".format(vid)

        return response

    def schema(self, vid):
        """Render documentation for a single bundle """
        from csv import reader
        from StringIO import StringIO
        import json

        template = self.env.get_template('bundle/schema.html')

        b = self.doc_cache.get_bundle(vid)

        reader = reader(StringIO(self.doc_cache.get_schemacsv(vid)))

        schema = dict(header=reader.next(),rows= [x for x in reader])


        return self.render(template, b=b, schema=schema, **self.cc())

    def table(self, bvid, tid):

        template = self.env.get_template('table.html')

        b = self.doc_cache.get_bundle(bvid)

        t = self.doc_cache.get_table(tid)

        return self.render(template, b=b, t=t, **self.cc())

    def partition(self, bvid, pvid):

        template = self.env.get_template('bundle/partition.html')

        b = self.doc_cache.get_bundle(bvid)

        p = b['partitions'][pvid]

        return self.render(template, b=b, p=p, **self.cc())

    def store(self, uid, local_extract_url):

        template = self.env.get_template('store/index.html')

        store = self.doc_cache.get_store(uid)

        assert store

        if local_extract_url:
            store['url'] = local_extract_url

        # Update the manifest to get the whole object
        store['manifests'] = { uid:self.doc_cache.get_manifest(uid) for uid in store['manifests']}


        return self.render(template,  s=store, **self.cc())

    def store_table(self, uid, tid):

        template = self.env.get_template('store/table.html')

        store = self.doc_cache.get_store(uid)

        t = store['tables'][tid]

        del store['partitions']
        del store['manifests']
        del store['tables']


        return self.render(template, s=store, t=t, **self.cc())

    def info(self, app_config, run_config):

        template = self.env.get_template('info.html')

        return self.render(template,app_config = app_config,**self.cc())

    def manifest(self, muid):
        """F is the file object associated with the manifest"""
        from ambry.warehouse.manifest import Manifest
        from ambry.identity import ObjectNumber

        template = self.env.get_template('manifest/index.html')

        m_dict = self.doc_cache.get_manifest(muid)

        m = Manifest(m_dict['text'])


        return self.render(template, m=m,
                           md=m_dict,
                           **self.cc() )

    @property
    def css_dir(self):
        import ambrydoc.templates as tdir

        return os.path.join(os.path.dirname(tdir.__file__),'css')

    def css_path(self, name):
        import ambrydoc.templates as tdir

        return os.path.join(os.path.dirname(tdir.__file__), 'css', name)


    def search(self, term):
        from ambrydoc.search import Search

        if term:

            s = Search(self.doc_cache)

            bundles, stores =  s.search(term)

        else:

            bundles = []

        template = self.env.get_template('search.html')

        return self.render(template, term = term, bundles = bundles, stores = stores, **self.cc())


    def generate_sources(self):

        lj = self.doc_cache.get_library()

        sources = {}
        for vid, b in lj['bundles'].items():

            source = b['identity']['source']

            if not source in sources:
                sources[source] = {
                    'bundles': {}
                }

            sources[source]['bundles'][vid] = b

        return sources


    def sources(self):

        template = self.env.get_template('sources/index.html')

        sources = self.generate_sources()

        return self.render(template, sources=sources, **self.cc())