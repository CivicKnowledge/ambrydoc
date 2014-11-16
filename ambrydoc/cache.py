"""
Accessor class to produce dictionary representations of bundles, cached as json.
"""

class DocCache(object):

    templates = {
        'bundle' : 'bundles/{vid}/bundle.json',
        'schema' : 'bundles/{vid}/schema.json',
        'table' : 'bundles/{bvid}/tables/{tvid}.json',
        'library' : 'library.json',
        'manifest': 'manifests/{uid}.json',
        'stores': 'stores/{uid}.json',

    }

    def __init__(self, cache):

        assert bool(cache)

        self.cache = cache

    def path(self, t, **kwargs):

        return  t.format(**kwargs)

    def munge(self,n):
        import sys
        import re

        if sys.platform == 'darwin':
            # Mac OS has case-insensitive file systems which cause aliasing in vids,
            # so we add a '_' before the uppercase letters.

            return re.sub(r'([A-Z])', lambda p: '_' + p.group(1), n)
        else:

            return n

    def resolve_vid(self, vid):

        return self.munge(vid)

    def has(self, rel_path):

        return self.cache.has(rel_path)

    def put(self, rel_path, f, force=False):
        import json

        if self.cache.has(rel_path) and not force:
            return False

        with self.cache.put_stream(rel_path) as s:
            json.dump(f(), s, indent=2)

        return True

    def get(self, rel_path):
        import json

        if not self.cache.has(rel_path):

            return None

        with self.cache.get_stream(rel_path) as s:
            return json.load(s)

    ##
    ## Library

    def library_relpath(self):
        return self.path(self.templates['library'])

    def put_library(self, l, force=False):
        return self.put(self.library_relpath(), lambda:l.dict, force=force)

    def get_library(self):
        return self.get(self.library_relpath())





    ##
    ## Manifests

    def manifest_relpath(self, uid):
        return self.path(self.templates['manifest'], uid=self.resolve_vid(uid))

    def put_manifest(self, m,f, force=False):
        """WARNING! This method must be run after all of the bundles are already cached, or at least
        the bundles used in this manifest"""

        from ambry.identity import ObjectNumber

        d = m.dict
        d['file'] = f.dict
        d['text'] = str(m)

        d['files'] = f.dict['data'].get('files')

        del d['file']['data']

        # Update the partitions to include bundle references,
        # then add bundle information.

        partitions = {pvid: str(ObjectNumber.parse(pvid).as_dataset) for pvid in f.dict['data'].get('partitions',[])}

        d["partitions"] = partitions

        d['tables'] = {tvid:  {
                          k:v for k,v in (self.get_table(tvid).items()+[('installed_names',[])]) if k != 'columns'
                       } for tvid in f.dict['data'].get('tables',[])
                      }

        d['bundles'] = {vid: self.get_bundle(vid) for vid in partitions.values()}

        for vid, b in d['bundles'].items():
            b['installed_partitions'] = [pvid for pvid, pbvid in partitions.items() if vid == pbvid]

        ## Generate entries for the tables, using the names that they are installed with. These tables aren't
        ## nessiarily installed; this maps the instllation names to vids if they are installed.

        installed_table_names = {}

        def inst_table_entry(b, p, t):
            return dict(
                t_vid=t['vid'],
                t_name=t['name'],
                p_vid=p['vid'],
                p_vname=p['vname'],
                b_vid=b['identity']['vid'],
                b_vname=b['identity']['vname']
            )

        for vid, b in d['bundles'].items():
            for pvid, bvid in d['partitions'].items():
                b = d['bundles'][bvid]
                p = b['partitions'][pvid]
                for tvid in p['table_vids']:

                    t = b['tables'][tvid]
                    e = inst_table_entry(b, p, t)
                    # The versioned and unversioned install names, with the partition prefix.
                    nver_name = p['id'] + '_' + t['name']
                    ver_name =  p['vid'] + '_' + t['name']
                    if not nver_name in installed_table_names:
                        installed_table_names[nver_name] = e
                        installed_table_names[ver_name] = e

                    # Link the installed names into the tables dict
                    if tvid in d['tables'] and nver_name not in d['tables'][tvid]['installed_names']:
                        d['tables'][tvid]['installed_names'].append(nver_name)
                        d['tables'][tvid]['installed_names'].append(ver_name)

        d['installed_table_names'] = installed_table_names

        # Collect the views and mviews

        views = {}

        for s in d['sections']:
            if s['tag'] in ('view', 'mview'):
                views[s['args']] = dict(
                    tag=s['tag'],
                    tc_names=s.get('content', {}).get('tc_names'),
                    html=s.get('content', {}).get('html'),
                    text=s.get('content', {}).get('text'),
                )

        d['views'] = views


        return self.put(self.manifest_relpath(m.uid), lambda: d, force=force)

    def get_manifest(self, vid):
        return self.get(self.manifest_relpath(vid))

    ##
    ## Stores

    def store_relpath(self, vid):
        return self.path(self.templates['store'], vid=self.resolve_vid(vid))

    def put_store(self, b, force=False):
        return self.put(self.store_relpath(b.identity.vid), lambda: b.dict, force=force)

    def get_store(self, vid):
        return self.get(self.store_relpath(vid))

    ##
    ## Bundles

    def bundle_relpath(self, vid):
        return self.path(self.templates['bundle'], vid=self.resolve_vid(vid))

    def put_bundle(self, b, force=False):
        return self.put(self.bundle_relpath(b.identity.vid), lambda: b.dict)

    def get_bundle(self, vid):
        return self.get(self.bundle_relpath(vid))

    ##
    ## Schemas

    def schema_relpath(self, vid):
        return self.path(self.templates['schema'], vid=self.resolve_vid(vid))

    def put_schema(self, b, force=False):
        return self.put(self.schema_relpath(b.identity.vid), lambda: b.schema.dict)

    def get_schema(self, vid):
        return self.get(self.schema_relpath(vid))

    ##
    ## Tables

    def table_relpath(self, bvid, tvid):
        return self.path(self.templates['table'], bvid=self.resolve_vid(bvid), tvid=self.resolve_vid(tvid))

    def put_table(self, t, force=False):
        bvid = t.d_vid

        return self.put(self.table_relpath(bvid, t.vid), lambda: t.nonull_col_dict )

    def get_table(self, tvid):
        bvid = 'd'+tvid[1:-5]+tvid[-3:]
        return self.get(self.table_relpath(bvid,tvid))
