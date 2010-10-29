# -*- coding: utf-8 -*-
"""
Wrapper around RDFLib's Graph object. The issue is that, in RDFLib 2.X the turtle and the RDF/XML serialization has some issues (bugs and ugly output). So the package's own serializers should be registered. On the other hand, in RDFLib 3.X this becomes unnecessary, it is better to keep to the library's own version. So this wrapper provides a subclass of RDFLib's Graph overriding the serialize method to register, if necessary, a different serializer and use that.


@summary: Shell around RDLib's Graph
@requires: Python version 2.5 or up
@requires: U{RDFLib<http://rdflib.net>}
@requires: U{html5lib<http://code.google.com/p/html5lib/>} for the HTML5 parsing; note possible dependecies on Python's version on the project's web site
@requires: U{httpheader<http://deron.meranda.us/python/httpheader/>}. To make distribution easier this module (single file) is added to the distributed tarball.
@organization: U{World Wide Web Consortium<http://www.w3.org>}
@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}

"""

"""
$Id: MyGraph.py,v 1.2 2010-10-29 16:30:22 ivan Exp $ $Date: 2010-10-29 16:30:22 $

"""

__version__ = "3.0"
__author__  = 'Ivan Herman'
__contact__ = 'Ivan Herman, ivan@w3.org'
__license__ = u'W3C® SOFTWARE NOTICE AND LICENSE, http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231'

import rdflib
if rdflib.__version__ >= "3.0.0" :
	from rdflib	import Graph
else :
	from rdflib.Graph import Graph
from rdflib	import Namespace

_xml_serializer_name	= "my-rdfxml"
_turtle_serializer_name	= "my-turtle"

#: Default bindings. This is just for the beauty of things: bindings are added to the graph to make the output nicer. If this is not done, RDFlib defines prefixes like "_1:", "_2:" which is, though correct, ugly...
_bindings = [	
	("foaf", "http://xmlns.com/foaf/0.1/"),
	("xsd",  "http://www.w3.org/2001/XMLSchema#"),
	("rdf",  "http://www.w3.org/1999/02/22-rdf-syntax-ns#"),
	("rdfs", "http://www.w3.org/2000/01/rdf-schema#"),
	("skos", "http://www.w3.org/2004/02/skos/core#"),
	("cc",   "http://creativecommons.org/ns#")
]

	
#########################################################################################################
class MyGraph(Graph) :
	"""
	Wrapper around RDFLib's Graph object. The issue is that, in RDFLib 2.X the turtle and the RDF/XML serialization has some issues (bugs and ugly output). So the package's own serializers should be registered. On the other hand, in RDFLib 3.X this becomes unnecessary, it is better to keep to the library's own version. So this wrapper provides a subclass of RDFLib's Graph overriding the serialize method to register, if necessary, a different serializer and use that.

	@cvar xml_serializer_registered: flag to avoid duplicate registration for RDF/XML
	@type xml_serializer_registered: boolean
	@cvar turtle_serializer_registered: flag to avoid duplicate registration for Turtle
	@type turtle_serializer_registered: boolean
	"""
	xml_serializer_registered		= False
	turtle_serializer_registered	= False
	
	def __init__(self) :
		Graph.__init__(self)
		for (prefix,uri) in _bindings :
			self.bind(prefix,Namespace(uri))
				
	def _register_XML_serializer(self) :
		"""The default XML Serializer of RDFLib 2.X is buggy, mainly when handling lists. An L{own version<serializers.PrettyXMLSerializer>} is
		registered in RDFlib and used in the rest of the package. This is not used for RDFLib 3.X.
		"""
		if not MyGraph.xml_serializer_registered :
			from rdflib.plugin import register
			from rdflib.syntax import serializer, serializers
			register(_xml_serializer_name, serializers.Serializer, "pyRdfa.serializers.PrettyXMLSerializer", "PrettyXMLSerializer")
			MyGraph.xml_serializer_registered = True

	def _register_Turtle_serializer(self) :
		"""The default Turtle Serializers of RDFLib 2.X is buggy and not very nice as far as the output is concerned.
		An L{own version<serializers.TurtleSerializer>} is registered in RDFLib and used in the rest of the package.
		This is not used for RDFLib 3.X.
		"""
		if not MyGraph.turtle_serializer_registered :
			from rdflib.plugin import register
			from rdflib.syntax import serializer, serializers
			register(_turtle_serializer_name, serializers.Serializer, "pyRdfa.serializers.TurtleSerializer", "TurtleSerializer")
			MyGraph.turtle_serialzier_registered = True
		
	def serialize(self, format = "xml") :
		if rdflib.__version__ >= "3.0.0" :
			# this is the easy case
			if format == "xml" or format == "pretty-xml" :
				return Graph.serialize(self, format="pretty-xml")
			elif format == "nt" :
				return Graph.serialize(self, format="nt")
			elif format == "n3" or format == "turtle" :
				return Graph.serialize(self, format="n3")
		else :
			if format == "xml" or format == "pretty-xml" :
				self._register_XML_serializer()
				return Graph.serialize(self, format=_xml_serializer_name)
			elif format == "nt" :
				return Graph.serialize(self, format="nt")
			elif format == "n3" or format == "turtle" :
				self._register_Turtle_serializer()
				return Graph.serialize(self, format=_turtle_serializer_name)

"""
$Log: MyGraph.py,v $
Revision 1.2  2010-10-29 16:30:22  ivan
*** empty log message ***

Revision 1.1  2010/10/29 15:39:13  ivan
Initial version


"""
