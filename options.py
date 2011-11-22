# -*- coding: utf-8 -*-
"""
L{Options} class: collect the possible options that govern the parsing possibilities. The module also includes the L{ProcessorGraph} class that handles the processor graph, per RDFa 1.1 (i.e., the graph containing errors and warnings). 

@summary: RDFa parser (distiller)
@requires: U{RDFLib<http://rdflib.net>}
@organization: U{World Wide Web Consortium<http://www.w3.org>}
@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}
"""

"""
$Id: options.py,v 1.6 2011-11-22 13:09:43 ivan Exp $ $Date: 2011-11-22 13:09:43 $
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

from pyRdfa.host 	import HostLanguage, MediaTypes, content_to_host_language
from pyRdfa			import ns_xsd, ns_distill, ns_rdfa
from pyRdfa 		import RDFA_Error, RDFA_Warning, RDFA_Info

ns_dc = Namespace("http://purl.org/dc/terms/")
ns_ht = Namespace("http://www.w3.org/2006/http#")

class ProcessorGraph :
	"""Wrapper around the 'processor graph', ie, the (RDF) Graph containing the warnings,
	error messages, and informational messages.
	"""
	def __init__(self) :
		self.graph = Graph()
		self.graph.bind("dcterm", ns_dc)
		self.graph.bind("pyrdfa", ns_distill)
		self.graph.bind("rdf", ns_rdf)
		
	def add_triples(self, msg, top_class, info_class, context, node) :
		"""
		Add an error structure to the processor graph: a bnode with a number of predicates. The structure
		follows U{the processor graph vocabulary<http://www.w3.org/2010/02/rdfa/wiki/Processor_Graph_Vocabulary>} as described
		on the RDFa WG Wiki page.
		
		@param msg: the core error message, added as an object to a dc:description
		@param top_class: Error, Warning, or Info; an explicit rdf:type added to the bnode
		@type top_class: URIRef
		@param info_class: An additional error class, added as an rdf:type to the bnode in case it is not None
		@type info_class: URIRef
		@param context: An additional information added, if not None, as an object with rdfa:context as a predicate
		@type context: either an URIRef or a URI String (an URIRef will be created in the second case)
		@param node: The node's element name that contains the error
		@type node: string
		@return: the bnode that serves as a subject for the errors. The caller may add additional information
		@rtype: BNode
		"""
		bnode = BNode()
		
		if node != None:
			try :
				full_msg = "[In element '%s'] %s" % (node.nodeName, msg)
			except :
				full_msg = "[In element '%s'] %s" % (node, msg)
		else :
			full_msg = msg
		
		self.graph.add((bnode, ns_rdf["type"], top_class))
		if info_class :
			self.graph.add((bnode, ns_rdf["type"], info_class))
		self.graph.add((bnode, ns_dc["description"], Literal(full_msg)))
		self.graph.add((bnode, ns_dc["date"], Literal(datetime.datetime.utcnow().isoformat(),datatype=ns_xsd["dateTime"])))
		if context :
			if not isinstance(context,URIRef) :
				context = URIRef(context)
			self.graph.add((bnode, ns_rdfa["context"], context))
		return bnode
	
	def add_http_context(self, subj, http_code) :
		self.graph.bind("ht",ns_ht)
		bnode = BNode()
		self.graph.add((subj, ns_rdfa["context"], bnode))
		self.graph.add((bnode, ns_rdf["type"], ns_ht["Response"]))
		self.graph.add((bnode, ns_ht["responseCode"], URIRef("http://www.w3.org/2006/http#%s" % http_code)))

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
	@type processor_graph: L{ProcessorGraph}
	@ivar transformers: extra transformers
	@type transformers: list
	@ivar vocab_cache_report: whether the details of vocabulary file caching process should be reported as information (mainly for debug)
	@type vocab_cache_report: Boolean
	@ivar refresh_vocab_cache: whether the caching checks of vocabs should be by-passed, ie, if caches should be re-generated regardless of the stored date (important for vocab development)
	@type refresh_vocab_cache: Boolean
	@ivar hturtle: whether hturtle (ie, turtle in an HTML script element) should be extracted and added to the final graph. This is a non-standard option...
	@type hturtle: Boolean
	@ivar rdfa_sem: whether the @vocab elements should be expanded and a mini-RDFS processing should be done on the merged graph
	@type rdfa_sem: Boolean
	@ivar vocab_cache: whether the system should use the vocabulary caching mechanism when expanding via the mini-RDFS, or should just fetch the graphs every time
	@type vocab_cache: Boolean
	@ivar host_language: the host language for the RDFa attributes. Default is HostLanguage.xhtml, but it can be HostLanguage.rdfa_core and HostLanguage.html, or others...
	@type host_language: integer (logically: an enumeration)
	@ivar content_type: the content type of the host file. Default is None
	@type content_type: string (logically: an enumeration)
	"""
	def __init__(self, output_default_graph   = True,
					   output_processor_graph = False,
					   space_preserve         = True,
					   transformers           = [],
					   hturtle                = True,
					   vocab_expansion        = False,
					   vocab_cache            = True,
					   vocab_cache_report     = False,
					   refresh_vocab_cache    = False) :
		"""
		@keyword space_preserve: whether plain literals should preserve spaces at output or not
		@type space_preserve: Boolean
		@keyword output_default_graph: whether the 'default' graph should be returned to the user
		@type output_default_graph: Boolean
		@keyword output_processor_graph: whether the 'processor' graph should be returned to the user
		@type output_processor_graph: Boolean
		@keyword transformers: extra transformers
		@type transformers: list
		"""
		self.space_preserve 		= space_preserve
		self.transformers   		= transformers
		self.processor_graph  		= ProcessorGraph() 
		self.output_default_graph	= output_default_graph
		self.output_processor_graph	= output_processor_graph
		self.host_language 			= HostLanguage.rdfa_core
		self.vocab_cache_report		= vocab_cache_report
		self.refresh_vocab_cache	= refresh_vocab_cache
		self.hturtle				= hturtle
		self.vocab_expansion		= vocab_expansion
		self.vocab_cache			= vocab_cache
			
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
		preserve space                         : %s
		output processor graph                 : %s
		output default graph                   : %s
		host language                          : %s
		accept embedded turtle                 : %s
		perfom semantic postprocessing         : %s
		cache vocabulary graphs                : %s
		"""
		return retval % (self.space_preserve, self.output_processor_graph, self.output_default_graph, self.host_language, self.hturtle, self.rdfa_sem, self.vocab_cache)
		
	def reset_processor_graph(self):
		"""Empty the processor graph. This is necessary if the same options is reused
		for several RDFa sources, and new error messages should be generated.
		"""
		self.processor_graph.graph.remove((None,None,None))

	def add_warning(self, txt, warning_type=None, context=None, node=None) :
		"""Add a warning to the processor graph.
		@param txt: the warning text. 
		@keyword warning_type: Warning Class
		@type warning_type: URIRef
		@keyword context: possible context to be added to the processor graph
		@type context: URIRef or String
		"""
		return self.processor_graph.add_triples(txt, RDFA_Warning, warning_type, context, node)

	def add_info(self, txt, info_type=None, context=None, node=None) :
		"""Add an informational comment to the processor graph.
		@param txt: the information text. 
		@keyword info_type: Info Class
		@type info_type: URIRef
		@keyword context: possible context to be added to the processor graph
		@type context: URIRef or String
		"""
		return self.processor_graph.add_triples(txt, RDFA_Info, info_type, context, node)

	def add_error(self, txt, err_type=None, context=None, node=None) :
		"""Add an error  to the processor graph.
		@param txt: the information text. 
		@keyword err_type: Error Class
		@type err_type: URIRef
		@keyword context: possible context to be added to the processor graph
		@type context: URIRef or String
		"""
		return self.processor_graph.add_triples(txt, RDFA_Error, err_type, context, node)

