from unittest import TestCase

from pyRdfa import pyRdfa

class NonXhtmlTest(TestCase):
    """
    RDFa that is in not well-formed XHTML is passed through html5lib. 
    These tests make sure that this RDFa can be processed both from 
    a file, and from a URL.
    """
    target1 = '<og:isbn>9780596516499</og:isbn>'
    target2 = '<gr:typeOfGood rdf:resource="urn:x-domain:oreilly.com:product:9780596803391.EBOOK"/>'

    def test_url(self):
        g = pyRdfa().rdf_from_source('http://oreilly.com/catalog/9780596516499/')
        self.assert_(self.target1 in g)

    def test_file(self):
        g = pyRdfa().rdf_from_source('test/rdfa/oreilly.html')
        self.assert_(self.target2 in g)

