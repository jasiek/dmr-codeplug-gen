from lxml import etree

from .cache import FileCache


class LXMLCacheAdapter:
    __name__ = "xml"

    def loads(self, s):
        return etree.fromstring(s)

    def dumps(self, value):
        return etree.tostring(value, encoding="unicode")


class PrzemiennikiAPI(FileCache):
    def __init__(self):
        FileCache.__init__(self, "przemienniki", LXMLCacheAdapter())

    def repeaters_2m(self):
        return self.cached(
            "2m_fm",
            "https://przemienniki.net/export/rxf.xml?country=pl&band=2M&mode=FM&status=working",
        )

    def repeaters_70cm(self):
        return self.cached(
            "70cm_fm",
            "https://przemienniki.net/export/rxf.xml?country=pl&band=70CM&mode=FM&status=working",
        )
