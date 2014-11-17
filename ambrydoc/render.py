"""
Support for creating web pages and text representations of schemas.
"""

import os

from  flask.json import JSONEncoder as FlaskJSONEncoder


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

def table_path(b, t):
    return "/bundles/{}/tables/{}.html".format(resolve(b), resolve(t))

def partition_path(b, p):
    return "/bundles/{}/partitions/{}.html".format(resolve(b), resolve(p))

def manifest_path(m):
    return "/manifests/{}.html".format(m)

def store_path(s):
    return "/stores/{}.html".format(s)




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

        return FlaskJSONEncoder.default(self, o)




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
            'table_path' :  table_path,
            'partition_path': partition_path,
            'manifest_path':  manifest_path,
            'store_path':  store_path,
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


    def index(self):

        template = self.env.get_template('index.html')

        return self.render(template, l = self.doc_cache.get_library(), **self.cc())


    def bundles_index(self):
        """Render the bundle Table of Contents for a library"""
        template = self.env.get_template('toc/bundles.html')

        return self.render(template, **self.cc())

    def tables_index(self):

        template = self.env.get_template('toc/tables.html')

        tables = []

        return self.render(template, tables=tables, **self.cc())

    def bundle(self, vid):
        """Render documentation for a single bundle """

        template = self.env.get_template('bundle/index.html')

        b = self.doc_cache.get_bundle(vid)

        lj = self.doc_cache.get_library()

        b['in_manifests'] = { muid:lj['manifests'][muid]
                              for muid in self.doc_cache.get('manifest_map.json').get(vid, [])}


        return self.render(template, b = b , **self.cc())

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

    def store(self, uid):

        template = self.env.get_template('store/index.html')

        l = self.doc_cache.get_library()
        store = l['stores'][uid]

        store['manifests'] = { uid:self.doc_cache.get_manifest(uid) for uid in store['manifests']}

        # Now collect the partitions and tables from all of the naifests.

        tables = {}

        for uid, m in store['manifests'].items():
            for t_vid, t in m['tables'].items():
                t['from_manifest'] = [dict(uid = uid, title = m['title'])]
                k = t_vid

                if k in tables:
                    tables[k]['from_manifest'] += t['from_manifest']
                    tables[k]['installed_names'] = list(set(tables[k]['installed_names'] + t['installed_names']))
                else:
                    tables[k] = t


        store['tables'] = tables


        return self.render(template, l=l, s=store, **self.cc())

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
