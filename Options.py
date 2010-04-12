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
$Id: Options.py,v 1.5 2010-04-12 14:36:13 ivan Exp $ $Date: 2010-04-12 14:36:13 $
"""

import sys
from rdflib.Graph		import Graph
from rdflib.URIRef		import URIRef
from rdflib.Literal		import Literal
from rdflib.BNode		import BNode
from rdflib.Namespace	import Namespace
from rdflib.RDFS		import comment as rdfs_comment
from pyRdfa.Utils		import MediaTypes, HostLanguage

DIST_URI = "http://www.w3.org/2007/08/pyRdfa/distiller"
DIST_NS  = DIST_URI + '#'

ns_errors 		= Namespace(DIST_NS)
distillerURI	= URIRef(DIST_URI)

WARNING = 'warning'
ERROR   = 'error'
INFO    = 'info'
DEBUG   = 'debug'

_message_properties = {
	WARNING	: ns_errors["warning"],
	ERROR	: ns_errors["error"],
	INFO	: ns_errors["information"],
	DEBUG	: ns_errors["debug"]
}

def _add_to_comment_graph(graph, msg, prop, uri) :
	"""
	Add a distiller message to the graph.
	
	@param graph: RDFLib Graph
	@param msg: message of an exception
	@type msg: RDFLIb Literal
	@param prop: the property to be used
	@type prop: string, must be one of 'warning', 'error', 'info', 'debug'
	@param uri: the top URI used to invoke the distiller
	@type uri: URIRef
	"""
	bnode = BNode()
	graph.add((distillerURI, _message_properties[prop], bnode))
	graph.add((bnode, ns_errors["onURI"], uri))
	graph.add((bnode, ns_errors["message"], msg))		


class CommentGraph :
	"""Class to handle the 'comment graph', ie, the (RDF) Graph containing the warnings,
	error messages, and informational messages.
	"""
	def __init__(self, warnings = False) :
		"""
		@param warnings: whether a graph should effectively be set up, or whether this
		should just be an empty shell for the various calls to work (without effect)
		"""
		if warnings :
			self.graph = Graph()
		else :
			self.graph = None
		self.accumulated_literals = []
		self.baseURI              = None
		
	def _add_triple(self, msg, prop) :
		obj = Literal(msg)
		if self.baseURI == None :
			self.accumulated_literals.append((obj,prop))
		elif self.graph != None :
			_add_to_comment_graph(self.graph, obj, prop, self.baseURI) 
			
	def set_base_URI(self, URI) :
		"""Set the base URI for the comment triples.
		
		Note that this method I{must} be called at some point to complete the triples. Without it the triples
		added via L{add_warning<CommentGraph.add_warning>}, L{add_info<CommentGraph.add_info>}, etc, will not be added to the final graph.
		
		@param URI: URIRef for the subject of the comments
		"""
		self.baseURI = URI
		if self.graph != None :
			for obj, prop in self.accumulated_literals :
				_add_to_comment_graph(self.graph, obj, prop, self.baseURI) 
		self.accumulated_literals = []
				
	def add_warning(self, txt) :
		"""Add a warning. A comment triplet is added to the separate "warning" graph.
		@param txt: the warning text. It will be preceded by the string "==== pyRdfa Warning ==== "
		"""
		self._add_triple(txt, WARNING)

	def add_info(self, txt) :
		"""Add an informational comment. A comment triplet is added to the separate "warning" graph.
		@param txt: the information text. It will be preceded by the string "==== pyRdfa information ==== "
		"""
		self._add_triple(txt, INFO)

	def add_error(self, txt) :
		"""Add an error comment. A comment triplet is added to the separate "warning" graph.
		@param txt: the information text. It will be preceded by the string "==== pyRdfa information ==== "
		"""
		self._add_triple(txt, ERROR)
		
	def _add_debug(self, txt) :
		self._add_triple(txt, DEBUG)

class Options :
	"""Settable options. An instance of this class is stored in
	the L{execution context<ExecutionContext>} of the parser.

	@ivar space_preserve: whether plain literals should preserve spaces at output or not
	@type space_preserve: Boolean
	@ivar comment_graph: Graph for the storage of warnings
	@type comment_graph: L{CommentGraph}
	@ivar warnings: whether warnings should be generated or not
	@type warnings: Boolean
	@ivar transformers: extra transformers
	@type transformers: list
	@type host_language: the host language for the RDFa attributes. Default is HostLanguage.xhtml_rdfa, but it can be HostLanguage.rdfa_core and HostLanguage.html_rdfa
	@ivar host_language: integer (logically: an enumeration)	
	"""
	def __init__(self, warnings = False, space_preserve = True, transformers=[], host_language = HostLanguage.rdfa_core) :
		"""
		@keyword space_preserve: whether plain literals should preserve spaces at output or not
		@type space_preserve: Boolean
		@keyword warnings: whether warnings should be generated or not
		@type warnings: Boolean
		@keyword transformers: extra transformers
		@type transformers: list
		@keyword host_language: default host language
		@type host_language: string
		"""
		self.space_preserve 	= space_preserve
		self.transformers   	= transformers
		self.comment_graph  	= CommentGraph(warnings) 
		self.warnings			= warnings
		self.host_language 		= host_language
			
	def set_host_language(self, content_type) :
		"""
		Set the host language for processing, based on the recognized types. What this means is that everything is considered to be
		'core' RDFa, except if XHTML or HTML is used
		@param content_type: content type
		@type content_type: string
		"""
		if content_type == MediaTypes.xhtml :
			self.host_language = HostLanguage.xhtml_rdfa
		elif content_type == MediaTypes.html :
			self.host_language = HostLanguage.html_rdfa
		else :
			self.host_language = HostLanguage.rdfa_core		
		
	def __str__(self) :
		retval = """Current options:
		space_preserve : %s
		warnings       : %s
		lax parsing    : %s
		host language  : %s
		"""
		return retval % (self.space_preserve, self.warnings, self.lax, self.host_language)


