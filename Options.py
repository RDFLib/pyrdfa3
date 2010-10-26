# -*- coding: utf-8 -*-
"""

Options class: collect the possible options that govern the parsing possibilities. It also includes a reference and
handling of the extra Graph for warnings, informations, errors.


@summary: RDFa parser (distiller)
@requires: U{RDFLib<http://rdflib.net>}
@requires: U{html5lib<http://code.google.com/p/html5lib/>} for the HTML5 parsing; note possible dependecies on Python's version on the project's web site
@organization: U{World Wide Web Consortium<http://www.w3.org>}
@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}

"""

"""
$Id: Options.py,v 1.9 2010-10-26 14:32:10 ivan Exp $ $Date: 2010-10-26 14:32:10 $
"""

import sys, datetime

import rdflib
from rdflib	import URIRef
from rdflib	import Literal
from rdflib	import BNode
from rdflib	import Namespace
if rdflib.__version__ >= "3.0.0" :
	from rdflib	import Graph
	from rdflib	import RDF  as ns_rdf
	from rdflib	import RDFS as ns_rdfs
else :
	from rdflib.Graph	import Graph
	from rdflib.RDFS	import RDFSNS as ns_rdfs
	from rdflib.RDF		import RDFNS  as ns_rdf

from pyRdfa.Utils	import MediaTypes, HostLanguage, content_to_host_language
from pyRdfa			import ns_xsd, ns_distill

from pyRdfa 		import RDFA_Error, RDFA_Warning, RDFA_Info

ns_dc = Namespace("http://purl.org/dc/terms/")
ns_ht = Namespace("http://www.w3.org/2006/http#")

class ProcessorGraph :
	"""Wrapper around the 'processor graph', ie, the (RDF) Graph containing the warnings,
	error messages, and informational messages.
	"""
	def __init__(self) :
		"""
		@param warnings: whether a graph should effectively be set up, or whether this
		should just be an empty shell for the various calls to work (without effect)
		"""
		self.graph = Graph()
		self.graph.bind("dc", ns_dc)
		self.graph.bind("pyrdfa", ns_distill)
		self.graph.bind("rdf", ns_rdf)
		
	def add_triples(self, msg, top_class, info_class, context) :
		"""
		Add an error structure to the processor graph: a bnode with a number of predicates as defined by the RDFa
		document
		@param msg: the core error message, added as an object to a dc:description
		@param top_class: Error, Warning, or Info; an explicit rdf:type added to the bnode
		@type top_class: URIRef
		@param info_class: An additional error class, added as an rdf:type to the bnode in case it is not None
		@type info_class: URIRef
		@param context: An additional information added, if not None, as an object with rdfa:context as a predicate
		@type context: either an URIRef or a URI String (an URIRef will be created in the second case)
		@return: the bnode that serves as a subject for the errors. The caller may add additional information
		@rtype: BNode
		"""
		bnode = BNode()
		
		self.graph.add((bnode, ns_rdf["type"], top_class))
		if info_class :
			self.graph.add((bnode, ns_rdf["type"], info_class))
		self.graph.add((bnode, ns_dc["description"], Literal(msg)))
		self.graph.add((bnode, ns_dc["date"], Literal(datetime.datetime.utcnow().isoformat(),datatype=ns_xsd["dateTime"])))
		if context :
			if not isinstance(context,URIRef) :
				context = URIRef(context)
			self.graph.add((bnode, ns_distill["context"], context))
			
		return bnode
	
	def add_http_context(self, subj, http_code) :
		self.graph.bind("ht",ns_ht)
		bnode = BNode()
		self.graph.add((subj, ns_distill["context"], bnode))
		self.graph.add((bnode, ns_rdf["type"], ns_ht["Response"]))
		self.graph.add((bnode, ns_ht["sc"], URIRef("http://www.w3.org/2008/http-statusCodes/statusCode%s" % http_code)))


class Options :
	"""Settable options. An instance of this class is stored in
	the L{execution context<ExecutionContext>} of the parser.

	@ivar space_preserve: whether plain literals should preserve spaces at output or not
	@type space_preserve: Boolean
	@ivar output_default_graph: whether the 'default' graph should be returned to the user
	@type output_default_graph: Boolean
	@ivar output_processor_graph: whether the 'processor' graph should be returned to the user
	@type output_processor_graph: Boolean
	@ivar processor_graph: the 'processor' Graph
	@type processor_graph: L{CommentGraph}
	@ivar transformers: extra transformers
	@type transformers: list
	@ivar host_language: the host language for the RDFa attributes. Default is HostLanguage.xhtml_rdfa, but it can be HostLanguage.rdfa_core and HostLanguage.html_rdfa
	@type host_language: integer (logically: an enumeration)
	@ivar content_type: the content type of the host file. Default is None
	@type content_type: string (logically: an enumeration)
	"""
	def __init__(self, output_default_graph = True, output_processor_graph = False, space_preserve = True, transformers=[], host_language = HostLanguage.rdfa_core) :
		"""
		@keyword space_preserve: whether plain literals should preserve spaces at output or not
		@type space_preserve: Boolean
		@keyword output_default_graph: whether the 'default' graph should be returned to the user
		@type output_default_graph: Boolean
		@keyword output_processor_graph: whether the 'processor' graph should be returned to the user
		@type output_processor_graph: Boolean
		@keyword transformers: extra transformers
		@type transformers: list
		@keyword host_language: default host language
		@type host_language: string
		"""
		self.space_preserve 		= space_preserve
		self.transformers   		= transformers
		self.processor_graph  		= ProcessorGraph() 
		self.output_default_graph	= output_default_graph
		self.output_processor_graph	= output_processor_graph
		self.host_language 			= host_language
			
	def set_host_language(self, content_type) :
		"""
		Set the host language for processing, based on the recognized types. What this means is that everything is considered to be
		'core' RDFa, except if XHTML or HTML is used; indeed, no other language defined a deviation to core (yet...)
		@param content_type: content type
		@type content_type: string
		"""
		if content_type in content_to_host_language :
			self.host_language = content_to_host_language[content_type]
		else :
			self.host_language = HostLanguage.rdfa_core
		
	def __str__(self) :
		retval = """Current options:
		preserve space         : %s
		output processor graph : %s
		output default graph   : %s
		host language          : %s
		"""
		return retval % (self.space_preserve, self.output_processor_graph, self.output_default_graph, self.host_language)
		
	def reset_processor_graph(self):
		"""Empty the processor graph. This is necessary if the same options is reused
		for several RDFa sources, and new error messages should be generated.
		"""
		self.processor_graph.graph.remove((None,None,None))

	def add_warning(self, txt, warning_type=None, context=None) :
		"""Add a warning to the processor graph.
		@param txt: the warning text. 
		@keyword warning_type: Warning Class
		@type warning_type: URIRef
		@keyword context: possible context to be added to the processor graph
		@type context: URIRef or String
		"""
		return self.processor_graph.add_triples(txt, RDFA_Warning, warning_type, context)

	def add_info(self, txt, info_type=None) :
		"""Add an informational comment to the processor graph.
		@param txt: the information text. 
		@keyword info_type: Info Class
		@type info_type: URIRef
		@keyword context: possible context to be added to the processor graph
		@type context: URIRef or String
		"""
		return self.processor_graph.add_triples(txt, RDFA_Info, info_type, context)

	def add_error(self, txt, err_type=None, context=None) :
		"""Add an error  to the processor graph.
		@param txt: the information text. 
		@keyword err_type: Error Class
		@type err_type: URIRef
		@keyword context: possible context to be added to the processor graph
		@type context: URIRef or String
		"""
		return self.processor_graph.add_triples(txt, RDFA_Error, err_type, context)

