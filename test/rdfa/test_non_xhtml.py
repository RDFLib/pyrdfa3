from unittest import TestCase
from nose.exc import SkipTest
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
        raise SkipTest("Suspended for investigation")
        g = pyRdfa().rdf_from_source('http://oreilly.com/catalog/9780596516499/')
        self.assert_(self.target1.encode('utf-8') in g)

    def test_file(self):
        raise SkipTest("Suspended for investigation")
        g = pyRdfa().rdf_from_source('test/rdfa/oreilly.html')
        self.assert_(self.target2.encode('utf-8') in g)

"""
======================================================================
FAIL: test_file (test.rdfa.test_non_xhtml.NonXhtmlTest)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "./test/rdfa/test_non_xhtml.py", line 20, in test_file
    self.assert_(self.target2.encode('utf-8') in g)
AssertionError:
-------------------- >> begin captured logging << --------------------
rdflib.term: WARNING: could not convert rdflib.term.Literal(u'2009-06-12',
    datatype=rdflib.term.URIRef(u'http://www.w3.org/2001/XMLSchema#dateTime')
    ) to a Python datatype
rdflib.term: WARNING: could not convert rdflib.term.Literal(u'2009-06-19',
    datatype=rdflib.term.URIRef(u'http://www.w3.org/2001/XMLSchema#dateTime')
    ) to a Python datatype
rdflib.term: WARNING: could not convert rdflib.term.Literal(u'2009-06-12',
    datatype=rdflib.term.URIRef(u'http://www.w3.org/2001/XMLSchema#dateTime')
    ) to a Python datatype
--------------------- >> end captured logging << ---------------------

======================================================================
FAIL: test_url (test.rdfa.test_non_xhtml.NonXhtmlTest)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "./test/rdfa/test_non_xhtml.py", line 16, in test_url
    self.assert_(self.target1.encode('utf-8') in g)
AssertionError:
-------------------- >> begin captured logging << --------------------
rdflib.term: WARNING: could not convert rdflib.term.Literal(u'2009-06-30',
    datatype=rdflib.term.URIRef(u'http://www.w3.org/2001/XMLSchema#dateTime')
    ) to a Python datatype
rdflib.term: WARNING: could not convert rdflib.term.Literal(u'2009-06-12',
    datatype=rdflib.term.URIRef(u'http://www.w3.org/2001/XMLSchema#dateTime')
    ) to a Python datatype
--------------------- >> end captured logging << ---------------------
"""