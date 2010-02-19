# -*- coding: utf-8 -*-
"""
Management of vocabularies, keywords, etc.

@summary: RDFa core parser processing step
@requires: U{RDFLib package<http://rdflib.net>}
@organization: U{World Wide Web Consortium<http://www.w3.org>}
@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}

@var XHTML_PREFIX: prefix for the XHTML vocabulary namespace
@var XHTML_URI: URI prefix of the XHTML vocabulary
@var usual_protocols: list of "usual" protocols (used to generate warnings when CURIES are not protected)
@var _predefined_rel: list of predefined C{@rev} and C{@rel} values that should be mapped onto the XHTML vocabulary URI-s.
"""

"""
$Id: State.py,v 1.3 2010/01/29 12:42:59 ivan Exp $
$Date: 2010/01/29 12:42:59 $
"""

from rdflib.RDF			import RDFNS   as ns_rdf
from rdflib.RDFS		import RDFSNS  as ns_rdfs
from rdflib.RDFS		import comment as rdfs_comment
from rdflib.Namespace	import Namespace
from rdflib.URIRef		import URIRef
from rdflib.Literal		import Literal
from rdflib.BNode		import BNode
from rdflib.Graph		import Graph
from pyRdfa.Options		import Options, GENERIC_XML, XHTML_RDFA, HTML5_RDFA
from pyRdfa.Utils 		import quote_URI
import xml.dom.minidom

debug = True

import re
import random
import urlparse

_WARNING_VERSION = "RDFa profile or RFDa version has not been set (for a correct identification of RDFa). This is not a requirement for RDFa, but it is advised to use one of those nevertheless. Note that in the case of HTML5, the DOCTYPE setting may not work..."

####Predefined @rel/@rev/@property values
# predefined values for the @rel and @rev values. These are considered to be part of a specific
# namespace, defined by the RDFa document.
XHTML_PREFIX = "xhv"
XHTML_URI    = "http://www.w3.org/1999/xhtml/vocab#"
_predefined_rel  = ['alternate', 'appendix', 'cite', 'bookmark', 'chapter', 'contents',
					'copyright', 'glossary', 'help', 'icon', 'index', 'meta', 'next',
					'p3pv1', 'prev', 'role', 'section', 'subsection', 'start', 'license',
					'up', 'last', 'stylesheet', 'first', 'top']

_XSD_NS = Namespace(u'http://www.w3.org/2001/XMLSchema#')

#: list of namespaces that are considered as default, ie, the user should not be forced to declare:
default_namespaces = {
	"foaf"		: "http://xmlns.com/foaf/0.1/",
}
#default_namespaces = {
#	"xsd"		: "http://www.w3.org/2001/XMLSchema#",
#	"rdf"		: "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
#	"rdfs"		: "http://www.w3.org/2000/01/rdf-schema#",
#	"dc"		: "http://purl.org/dc/terms/",
#	"foaf"		: "http://xmlns.com/foaf/0.1/",
#	"vcard"		: "http://www.w3.org/2001/vcard-rdf/3.0#",
#	"geo"		: "http://www.w3.org/2003/01/geo/wgs84_pos#",
#	"g"			: "http://rdf.data-vocabulary.org/#",
#	"sioc"		: "http://rdfs.org/sioc/ns#",
#	"owl"		: "http://www.w3.org/2002/07/owl#",
#	"ical"		: "http://www.w3.org/2002/12/cal/icaltzd#",
#	"openid"	: "http://xmlns.openid.net/auth#"
#}



VOCABTERM = "vocab"

#: the namespace used in vocabulary management
ns_rdfa_vocab = Namespace("http://www.w3.org/2010/vocabs/rdfa")

# This is a necessary optimization: we should avoid reading in the same vocabulary definition
# several times. Ie, some sort of a caching mechanism is necessary.

class VocabularyRead :
	def __init__(self, state) :
		self.state = state
		from pyRdfa import pyRdfa
		options = Options(warnings = False,
						  space_preserve = False,
						  transformers = [],
						  xhtml = (state.options.host_language == XHTML_RDFA),
						  lax = state.options.lax)
		options.host_language = state.options.host_language
		self.processor = pyRdfa(options)
		self.keywords  = {}
		self.ns        = {}
		self._get_graphs()
		
	def _get_graphs(self) :
		if not self.state.node.hasAttribute(VOCABTERM) :
			return []
		else :
			vocabs = self.state.getURI(VOCABTERM)
			for vocab in vocabs :
				graph = self.processor.graph_from_source(vocab)
				for (uri,keyword) in graph.subject_objects(ns_rdfa_vocab["term"]) :
					if isinstance(keyword, Literal) :
						self.keywords[str(keyword)] = (URIRef(uri),[])
					else :
						self.state.options.comment_graph.add_warning("Non literal term <%s> defined in <%s> for <%s>; ignored" % (keyword, vocab, uri))
				for (uri,prefix) in graph.subject_objects(ns_rdfa_vocab["prefix"]) :
					if isinstance(prefix, Literal) :
						self.ns[str(prefix)] = Namespace(uri)
					else :
						self.state.options.comment_graph.add_warning("Non literal prefix <%s> defined in <%s> for <%s>; ignored" % (prefix, vocab, uri))

class Vocab :
	def __init__(self, state, graph, inherited_state) :
		"""Initialize the vocab bound to a specific state. 
		@param state: the state to which this vocab instance belongs to
		@param graph: the RDF graph being worked on
		@param inherited_state: the state inherited by the current state. 'None' if this is the top level state.
		"""
		self.state	= state
		self.graph	= graph
		
		# Get the recursive definitions, if any
		recursive_vocab = VocabularyRead(self.state)
		
		# --------------------------------------------------------------------------------
		# The simpler case: keywords
		if inherited_state is None :
			# this is the vocabulary belonging to the top level of the tree!
			self.keywords = {}
			if state.options.host_language != GENERIC_XML :
				relrev = ["rel","rev"]
				for key in _predefined_rel : self.keywords[key] = (URIRef(XHTML_URI+key),relrev)
			# add the keywords defined locally
			for key in recursive_vocab.keywords :
				self.keywords[key] = recursive_vocab.keywords[key]
		else :
			if len(recursive_vocab.keywords) == 0 :
				# just refer to the inherited keywords
				self.keywords = inherited_state.vocab.keywords
			else :
				self.keywords = {}
				# tried to use the 'update' operation for the dictionary and it failed. Why???
				for key in inherited_state.vocab.keywords 	: self.keywords[key] = inherited_state.vocab.keywords[key]
				for key in recursive_vocab.keywords 		: self.keywords[key] = recursive_vocab.keywords[key]

		#-----------------------------------------------------------------
		# the locally defined namespaces
		dict = {}
		# If this is the vocab on the top (signalled by inherited_state being None) then default namespaces
		# added to the vocabulary right away (subsequent namespace declarations and keyword
		# definition may override these)
		if inherited_state is None :
			for k in default_namespaces :
				ns  = Namespace(default_namespaces[k])
				dict[k] = ns
			self.keywords = {}
			if state.options.host_language != GENERIC_XML :
				relrev = ["rel","rev"]
				for key in _predefined_rel : self.keywords[key] = (URIRef(XHTML_URI+key),relrev)
				
		# Add the namespaces defined via a @vocab
		for key in recursive_vocab.ns : dict[key] = recursive_vocab.ns[key]				
		
		# Add the locally defined namespaces using the xmlns: syntax
		# Note that the placement of this code means that the local definitions will override
		# the effects of a @vocab
		for i in range(0, state.node.attributes.length) :
			attr = state.node.attributes.item(i)
			if attr.name.find('xmlns:') == 0 :	
				# yep, there is a namespace setting
				prefix = attr.localName
				if prefix != "" : # exclude the top level xmlns setting...
					if prefix == "_" :
						if warning: state.options.comment_graph.add_error("The '_' local CURIE prefix is reserved for blank nodes, and cannot be changed" )
					elif prefix.find(':') != -1 :
						if warning: state.options.comment_graph.add_error("The character ':' is not valid in a CURIE Prefix" )
					else :					
						# quote the URI, ie, convert special characters into %.. This is
						# true, for example, for spaces
						uri = quote_URI(attr.value, state.options)
						# create a new RDFLib Namespace entry
						ns = Namespace(uri)
						# Add an entry to the dictionary, possibly overriding an existing one
						dict[prefix] = ns

		# See if anything has been collected at all.
		# If not, the namespaces of the incoming state is
		# taken over by reference. Otherwise that is copied to the
		# the local dictionary
		if len(dict) == 0 and inherited_state :
			self.ns = inherited_state.vocab.ns
		else :
			self.ns = {}
			if inherited_state :
				for key in inherited_state.vocab.ns	: self.ns[key] = inherited_state.vocab.ns[key]
				for key in dict						: self.ns[key] = dict[key]
			else :
				self.ns = dict
				
		# see if the xhtml core vocabulary has been set
		# This whole code seems to be relevant for an XHTML case only
		self.xhtml_prefix = None
		for prefix in self.ns.keys() :
			if XHTML_URI == str(self.ns[prefix]) :
				self.xhtml_prefix = prefix
				break
		if self.xhtml_prefix == None :
			if XHTML_PREFIX not in self.ns :
				self.ns[XHTML_PREFIX] = Namespace(XHTML_URI)
				self.xhtml_prefix = XHTML_PREFIX
			else :
				# the most disagreeable thing, the user has used
				# the prefix for something else...
				self.xhtml_prefix = XHTML_PREFIX + '_' + ("%d" % random.randint(1,1000))
				self.ns[self.xhtml_prefix] = Namespace(XHTML_URI)

	def CURIE_to_URI(self, prefix, lname) :
		"""CURIE to URI mapping. Note that this method does not take care of the
		blank node management, ie, when the key is '_', this is something that
		has to be taken care of summer higher up.
		@param prefix: the prefix defined for the CURIE
		@param lname: local name
		"""
		if prefix in self.ns :
			# yep, we have a CURIE here!
			# ensure a nicer output...
			self.graph.bind(prefix, self.ns[prefix])
			if lname == "" :
				return URIRef(str(self.ns[prefix]))
			else :
				return self.ns[prefix][lname]
		else :
			return None

	def keyword_to_URI(self, attr, keyword) :
		"""A keyword to URI mapping, where keyword is a simple string and the corresponding
		URI is defined via the @vocab mechanism. Returns None if keyword is not defined
		@param keyword: string
		@param attr: attribute name
		@type attr: string
		@return: an RDFLib URIRef instance (or None)
		"""
		if keyword in self.keywords :
			uri, attrs = self.keywords[keyword]
			if attrs == [] or attr in attrs :
				return uri
		return None
		
