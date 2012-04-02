# -*- coding: utf-8 -*-
"""
RDFa 1.1 parser, also referred to as a “RDFa Distiller”. It is
deployed, via a CGI front-end, on the U{W3C RDFa Distiller page<http://www.w3.org/2007/08/pyRdfa/>}.



@summary: RDFa parser (distiller)
@requires: Python version 2.5 or up
@requires: U{RDFLib<http://rdflib.net>}; version 3.X is preferred, it has a more readable output serialization.
@requires: U{html5lib<http://code.google.com/p/html5lib/>} for the HTML5 parsing.
@requires: U{httpheader<http://deron.meranda.us/python/httpheader/>}; however, a small modification had to make on the original file, so for this reason and to make distribution easier this module (single file) is added to the distributed tarball.
@organization: U{World Wide Web Consortium<http://www.w3.org>}
@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}

"""

"""
$Id: __init__.py,v 1.1 2011/08/12 10:04:58 ivan Exp $ $Date: 2011/08/12 10:04:58 $

"""

__version__ = "3.0.2"
__author__  = 'Ivan Herman'
__contact__ = 'Ivan Herman, ivan@w3.org'
__license__ = u'W3C® SOFTWARE NOTICE AND LICENSE, http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231'


import rdflib
from rdflib	import URIRef
from rdflib	import Literal
from rdflib	import BNode
from rdflib	import Namespace
if rdflib.__version__ >= "3.0.0" :
	from rdflib	import RDF  as ns_rdf
	from rdflib	import RDFS as ns_rdfs
else :
	from rdflib.RDFS	import RDFSNS as ns_rdfs
	from rdflib.RDF		import RDFNS  as ns_rdf

from pyRdfa.graph import MyGraph as Graph

import xml.dom.minidom
import urlparse
from pyRdfa import RDFaError, pyRdfaError
from pyRdfa import ns_rdfa, ns_xsd, ns_distill

VocabCachingInfo = ns_distill["VocabCachingInfo"]


# Error message texts

err_outdated_cache  			= "Vocab document <%s> could not be dereferenced; using possibly outdated cache"
err_unreachable_vocab  			= "Vocab document <%s> could not be dereferenced"
err_unparsable_Turtle_vocab 	= "Could not parse vocab in Turtle at <%s> (%s)"
err_unparsable_xml_vocab 		= "Could not parse vocab in RDF/XML at <%s> (%s)"
err_unparsable_ntriples_vocab 	= "Could not parse vocab in N-Triple at <%s> (%s)"
err_unparsable_rdfa_vocab 		= "Could not parse vocab in RDFa at <%s> (%s)"
err_unrecognised_vocab_type		= "Unrecognized media type for the vocab file <%s>: '%s'"
