"""

"""

from whoosh.fields import SchemaClass, TEXT, KEYWORD, ID, STORED, DATETIME
import os

class AmbrySchema(SchemaClass):
    vid = ID(stored=True, unique=True)
    d_vid = ID(stored=True, unique=False)
    type = ID(stored=True)
    fqname = ID(stored=True)
    source = ID(stored=True)
    names = KEYWORD(stored=True, scorable=True, field_boost=2.0)
    title = TEXT(stored=True, field_boost=2.0)
    summary = TEXT(stored=True, field_boost=2.0)
    keywords = KEYWORD(field_boost=2.0)
    groups = KEYWORD
    text = TEXT
    time = DATETIME
    space = ID
    grain = ID

search_fields = ['fqname','source', 'names','title','summary','keywords', 'groups','text','time','space','grain']

class Search(object):

    index_name = 'search_index'

    def __init__(self, doc_cache):

        self.doc_cache = doc_cache
        self.cache = self.doc_cache.cache

        self.index_dir = self.cache.path(self.index_name, propagate = False, missing_ok=True) # Return root directory

        self._ix = None

    def reset(self):

        if os.path.exists(self.index_dir):
            from shutil import rmtree
            rmtree(self.index_dir)

        self._ix = None

    @property
    def ix(self):
        from whoosh.index import create_in, open_dir

        if not self._ix:

            if not os.path.exists(self.index_dir):
                os.makedirs(self.index_dir)
                self._ix = create_in(self.index_dir, AmbrySchema)

            else:
                self._ix = open_dir(self.index_dir)


        return self._ix

    def index(self, reset=False):

        if reset:
            self.reset()

        writer = self.ix.writer()

        self.index_library(writer)

        self.index_tables(writer)

        writer.commit()

    def index_library(self, writer):

        l = self.doc_cache.get_library()

        for k, v in l['bundles'].items():

            b = self.doc_cache.get_bundle(k)
            a = b['meta'].get('about', {})

            keywords = a.get('keywords', []) + [b['identity']['source']]

            d = dict(
                type=u'bundle',
                vid=b['identity']['vid'],
                d_vid=b['identity']['vid'],
                fqname=b['identity']['vname'],
                source=b['identity']['source'],
                names=u'{} {} {}'.format(b['identity']['name'], b['identity']['name'], b['identity']['fqname']),
                title=a.get('title', u'') or u'',
                summary=a.get('summary', u'') or u'',
                keywords=u' '.join(keywords),
                groups=u' '.join(x for x in a.get('groups', []) if x) or u'',
                text=b['meta'].get('documentation', {}).get('main', u'') or u''
            )

            writer.add_document(**d)

    def index_tables(self, writer):
        import json

        l = self.doc_cache.get_library()

        for i, (k, b) in enumerate(l['bundles'].items()):
            s = self.doc_cache.get_schema(k)

            for t_vid, t in s.items():

                columns = u''
                columns_names  = []
                for c_vid, c in t['columns'].items():
                    columns += u'{} {}\n'.format(c['name'], c.get('description',''))
                    columns_names.append(c['name'])

                d = dict(
                    vid=t_vid,
                    d_vid=b['identity']['vid'],
                    fqname=t['name'],
                    type=u'table',
                    title=b['about'].get('title',u''),
                    summary=unicode(t.get('description','')),
                    keywords=columns_names,
                    text=columns
                )

                writer.add_document(**d)


    def search(self, term):


        from whoosh.qparser import QueryParser, MultifieldParser

        with self.ix.searcher() as searcher:

            qp = MultifieldParser(search_fields, self.ix.schema)

            query = qp.parse(term)

            results = searcher.search(query, limit=600)

            entries = {}

            for hit in results:
                d_vid = hit['d_vid']

                d = dict(score = hit.score,**hit.fields())

                if d_vid not in entries:
                    entries[d_vid] = dict(score = 0, bundle = None, tables = [])

                entries[d_vid]['score'] += hit.score

                if hit['type'] == 'bundle':
                    entries[d_vid]['bundle'] = d
                elif hit['type'] == 'table':

                    entries[d_vid]['tables'].append(d)


                # When there are a bunch of tables returned, but not the bundle, we need to re-create the bundle.
                for vid, e in entries.items():

                    if not e['bundle']:
                        cb = self.doc_cache.get_bundle(vid)
                        about = cb ['meta']['about']
                        e['bundle'] = dict(
                            title = about.get('title'),
                            summary = about.get('summary'),
                            fqname = cb['identity']['fqname'],
                            vname = cb['identity']['vname'],
                            source=cb['identity']['source'],
                            vid = cb['identity']['vid'])


            return entries


    def dump(self):

        for x in self.ix.searcher().documents():
            print x
