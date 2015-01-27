__author__ = 'eric'

def index_doc(vid):

    from ambrydoc.search import Search

    from ambrydoc.cache import DocCache
    from ambrydoc import fscache

    cache = fscache()
    doc_cache = DocCache(cache)
    s = Search(doc_cache)

    b = doc_cache.get_bundle(vid)

    lines = []

    for v in b['meta']['about'].values():
        if v:
            lines.append(str(v))

    for v in b['identity'].values():
        if v:
            lines.append(str(v))

    sk = doc_cache.get_schema(vid)

    for t in sk.values():
        for k, v in t.items():
            if v and k != 'columns':
                lines.append(v)

        for c in t['columns'].values():
            v = ' '.join([c['name'],c['vid'],c['id_'],c.get('description','')])
            lines.append(v)

    import pprint
    pprint.pprint(lines)
    return '\n'.join(lines)

def test():


    vid = 'd024004' #vid = 'd034003'

    print index_doc(vid)




