# -*- coding: utf-8 -*-
"""
Wrapper around RDFLib's Graph object. The issue is that, in RDFLib 2.X, the turtle and the RDF/XML serialization has some issues (bugs and ugly output). As a result, the package’s own serializers should be registered and used. On the other hand, in RDFLib 3.X this becomes unnecessary, it is better to keep to the library’s own version. This wrapper provides a subclass of RDFLib’s Graph overriding the serialize method to register, if necessary, a different serializer and use that one.

As an extra bonus, some bindings (in the RDFLib sense) are done automatically, to ensure a nicer output for widely used schemas…

@summary: Shell around RDLib's Graph
@requires: Python version 2.5 or up
@requires: U{RDFLib<http://rdflib.net>}
@organization: U{World Wide Web Consortium<http://www.w3.org>}
@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}

@var _bindings: Default bindings. This is just for the beauty of things: bindings are added to the graph to make the output nicer. If this is not done, RDFlib defines prefixes like "_1:", "_2:" which is, though correct, ugly…
"""

"""
$Id: graph.py,v 1.1 2011/08/12 10:01:54 ivan Exp $ $Date: 2011/08/12 10:01:54 $

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

# Default bindings. This is just for the beauty of things: bindings are added to the graph to make the output nicer. If this is not done, RDFlib defines prefixes like "_1:", "_2:" which is, though correct, ugly...
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
	Wrapper around RDFLib's Graph object. The issue is that the serializers in RDFLib are buggy:-(
	
	In RDFLib 2.X both the Turtle and the RDF/XML serializations have issues (bugs and ugly output). In RDFLib 3.X
	the Turtle serialization seems to be fine, but the RDF/XML has problems:-(
	
	This wrapper provides a subclass of RDFLib’s Graph overriding the serialize method to register,
	if necessary, a different serializer and use that one.

	@cvar xml_serializer_registered_2: flag to avoid duplicate registration for RDF/XML for rdflib 2.*
	@type xml_serializer_registered_2: boolean
	@cvar xml_serializer_registered_3: flag to avoid duplicate registration for RDF/XML for rdflib 3.*
	@type xml_serializer_registered_3: boolean
	@cvar turtle_serializer_registered_2: flag to avoid duplicate registration for Turtle for rdflib 2.*
	@type turtle_serializer_registered_2: boolean
	"""
	xml_serializer_registered_2		= False
	xml_serializer_registered_3		= False
	turtle_serializer_registered_2	= False
	
	def __init__(self) :
		Graph.__init__(self)
		for (prefix,uri) in _bindings :
			self.bind(prefix,Namespace(uri))

	def _register_XML_serializer_3(self) :
		"""The default XML Serializer of RDFLib 3.X is buggy, mainly when handling lists. An L{own version<serializers.prettyXMLserializer_3>} is
		registered in RDFlib and used in the rest of the package. 
		"""
		if not MyGraph.xml_serializer_registered_3 :
			from rdflib.plugin import register
			from rdflib.serializer import Serializer
			register(_xml_serializer_name, Serializer,
					 "pyRdfa.serializers.prettyXMLserializer_3", "PrettyXMLSerializer")
			MyGraph.xml_serializer_registered_3 = True
				
	def _register_XML_serializer_2(self) :
		"""The default XML Serializer of RDFLib 2.X is buggy, mainly when handling lists.
		An L{own version<serializers.prettyXMLserializer>} is
		registered in RDFlib and used in the rest of the package. This is not used for RDFLib 3.X.
		"""
		if not MyGraph.xml_serializer_registered_2 :
			from rdflib.plugin import register
			from rdflib.syntax import serializer, serializers
			register(_xml_serializer_name, serializers.Serializer,
					 "pyRdfa.serializers.prettyXMLserializer", "PrettyXMLSerializer")
			MyGraph.xml_serializer_registered_2 = True

	def _register_Turtle_serializer_2(self) :
		"""The default Turtle Serializers of RDFLib 2.X is buggy and not very nice as far as the output is concerned.
		An L{own version<serializers.TurtleSerializer>} is registered in RDFLib and used in the rest of the package.
		This is not used for RDFLib 3.X.
		"""
		if not MyGraph.turtle_serializer_registered_2 :
			from rdflib.plugin import register
			from rdflib.syntax import serializer, serializers
			register(_turtle_serializer_name, serializers.Serializer,
					 "pyRdfa.serializers.turtleserializer", "TurtleSerializer")
			MyGraph.turtle_serialzier_registered_2 = True
			
	def add(self, triple) :
		"""Overriding the Graph's add method to filter out triples with possible None values. It may happen
		in case, for example, a host language is not properly set up for the distiller"""
		(s,p,o) = triple
		if s == None or p == None or o == None :
			return
		else :
			Graph.add(self, (s,p,o))
		
	def serialize(self, format = "xml") :
		"""Overriding the Graph's serialize method to adjust the output format"""
		if rdflib.__version__ >= "3.0.0" :
			# this is the easy case
			if format == "xml" or format == "pretty-xml" :
				#return Graph.serialize(self, format="pretty-xml")
				self._register_XML_serializer_3()
				return Graph.serialize(self, format=_xml_serializer_name)
			elif format == "nt" :
				return Graph.serialize(self, format="nt")
			elif format == "n3" or format == "turtle" :
				retval =""
				return Graph.serialize(self, format="n3")
		else :
			if format == "xml" or format == "pretty-xml" :
				self._register_XML_serializer_2()
				return Graph.serialize(self, format=_xml_serializer_name)
			elif format == "nt" :
				return Graph.serialize(self, format="nt")
			elif format == "n3" or format == "turtle" :
				self._register_Turtle_serializer_2()
				return Graph.serialize(self, format=_turtle_serializer_name)

"""
$Log: graph.py,v $
Revision 1.1  2011/08/12 10:01:54  ivan
*** empty log message ***

Revision 1.8  2011/04/05 06:37:22  ivan
*** empty log message ***

Revision 1.7  2011/03/11 14:30:39  ivan
*** empty log message ***

Revision 1.6  2011/03/11 14:12:12  ivan
*** empty log message ***

Revision 1.5  2011/03/11 13:08:18  ivan
*** empty log message ***

Revision 1.4  2011/03/08 10:49:49  ivan
*** empty log message ***

Revision 1.3  2010/11/02 14:56:35  ivan
*** empty log message ***

Revision 1.2  2010/10/29 16:30:22  ivan
*** empty log message ***

Revision 1.1  2010/10/29 15:39:13  ivan
Initial version


"""
