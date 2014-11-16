"""

"""

from whoosh.fields import SchemaClass, TEXT, KEYWORD, ID, STORED, DATETIME
import os

class AmbrySchema(SchemaClass):
    vid = ID(stored=True, unique=True)
    fqname = ID(stored=True)
    names = KEYWORD(stored=True, scorable=True, field_boost=2.0)
    title = TEXT(stored=True, field_boost=2.0)
    summary = TEXT(stored=True, field_boost=2.0)
    keywords = KEYWORD(field_boost=2.0)
    groups = KEYWORD
    text = TEXT
    time = DATETIME
    space = ID
    grain = ID

class Search(object):

    index_name = 'search_index'

    def __init__(self, doc_cache):
        from whoosh.index import create_in, open_dir
        self.doc_cache = doc_cache
        self.cache = self.doc_cache.cache

        self.index_dir = self.cache.path(self.index_name, propagate = False, missing_ok=True) # Return root directory

        if not os.path.exists(self.index_dir):
            os.makedirs(self.index_dir)
            self.ix = create_in(self.index_dir, AmbrySchema)
        else:
            self.ix = open_dir(self.index_dir)


    def reset(self):
        from whoosh.index import create_in

        if os.path.exists(self.index_dir):
            from shutil import rmtree
            rmtree(self.index_dir)

        os.makedirs(self.index_dir)

        self.ix = create_in(self.index_dir, AmbrySchema)

    def index(self, reset=False):

        if reset:
            self.reset()

        writer = self.ix.writer()

        #self.index_library(writer)

        self.index_tables(writer)

        writer.commit()

    def index_library(self, writer):

        l = self.doc_cache.get_library()

        for k, v in l['bundles'].items():
            print '------------'
            b = self.doc_cache.get_bundle(k)
            a = b['meta'].get('about', {})
            print b['identity'].values()
            print "'{}'".format(b['meta'].get('documentation', {}).get('main', ''))

            d = dict(
                vid=b['identity']['vid'],
                fqname=b['identity']['fqname'],
                names=u'{} {} {}'.format(b['identity']['name'], b['identity']['name'], b['identity']['fqname']),
                title=a.get('title', u'') or u'',
                summary=a.get('summary', u'') or u'',
                keywords=u' '.join(a.get('keywords', [])) or u'',
                groups=u' '.join(x for x in a.get('groups', []) if x) or u'',
                text=b['meta'].get('documentation', {}).get('main', u'') or u''
            )

            writer.add_document(**d)

    def index_tables(self, writer):

        l = self.doc_cache.get_library()

        for k, v in l['bundles'].items():
            s = self.doc_cache.get_schema(k)

            for t_vid, t in s.items():
                summary = '{} {}\n'.format(t['name'], t.get('description',''))
                columns = ''
                columns_names  = []
                for c_vid, c in t['columns'].items():
                    columns += '{} {}\n'.format(c['name'], c.get('description',''))
                    columns_names.append(c['name'])



            print '---------'
            print summary
            print columns



    def search(self, term):

        from whoosh.qparser import QueryParser, MultifieldParser

        with self.ix.searcher() as searcher:
            qp = MultifieldParser(['vid','name','names','title','summary','keywords'], self.ix.schema)

            query = qp.parse(term)

            results = searcher.search(query)

            for r in  results:
                print r

    def dump(self):

        for x in self.ix.searcher().documents():
            print x
