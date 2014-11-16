__author__ = 'eric'

import unittest

from ambrydoc import configure_application, fscache


class TestSearch(unittest.TestCase):


    def setUp(self):
        self.config = configure_application()

    def test_index(self):
        from ambrydoc.search import Search
        from ambrydoc.cache import DocCache

        s = Search(DocCache(fscache()))

        s.index(reset=True)

    def test_inc_index(self):
        from ambrydoc.search import Search
        from ambrydoc.cache import DocCache

        s = Search(DocCache(fscache()))

        s.index(reset=False)


    def test_search(self):
        from ambrydoc.search import Search
        from ambrydoc.cache import DocCache

        s = Search(DocCache(fscache()))

        s.search(u'd02j002')


    def test_dump(self):
        from ambrydoc.search import Search
        from ambrydoc.cache import DocCache

        s = Search(DocCache(fscache()))

        s.dump()


if __name__ == '__main__':
    unittest.main()
