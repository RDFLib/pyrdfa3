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
$Id:$
$Date:$
"""

import re, sys

from rdflib.RDF			import RDFNS   as ns_rdf
from rdflib.RDFS		import RDFSNS  as ns_rdfs
from rdflib.RDFS		import comment as rdfs_comment
from rdflib.Namespace	import Namespace
from rdflib.URIRef		import URIRef
from rdflib.Literal		import Literal
from rdflib.BNode		import BNode
from rdflib.Graph		import Graph
from pyRdfa.Options		import Options, GENERIC_XML, XHTML_RDFA, HTML5_RDFA
from pyRdfa.Utils 		import quote_URI, URIOpener, RDFXML_MT, TURTLE_MT, HTML_MT, XHTML_MT, NT_MT
import xml.dom.minidom

debug = True

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

# list of namespaces that are considered as default, ie, the user should not be forced to declare:
# Not used at the moment, bound the to whole default setting issue which is still open
default_namespaces = {
	"xsd"		: "http://www.w3.org/2001/XMLSchema#",
	"rdf"		: "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
	"rdfs"		: "http://www.w3.org/2000/01/rdf-schema#",
	"dc"		: "http://purl.org/dc/terms/",
	"foaf"		: "http://xmlns.com/foaf/0.1/",
	"vcard"		: "http://www.w3.org/2001/vcard-rdf/3.0#",
	"geo"		: "http://www.w3.org/2003/01/geo/wgs84_pos#",
	"g"			: "http://rdf.data-vocabulary.org/#",
	"sioc"		: "http://rdfs.org/sioc/ns#",
	"owl"		: "http://www.w3.org/2002/07/owl#",
	"ical"		: "http://www.w3.org/2002/12/cal/icaltzd#",
	"openid"	: "http://xmlns.openid.net/auth#"
}

#: the namespace used in vocabulary management
ns_rdfa_profile = Namespace("http://www.w3.org/ns/rdfa#")

# This is a necessary optimization: we should avoid reading in the same vocabulary definition
# several times. Ie, some sort of a caching mechanism is necessary.

class ProfileRead :
	"""
	Wrapper around the "recursive" access to profile files. The main job of this task to retrieve
	keyword and namespace definitions by accessing an RDFa file stored in a URI as given by the
	values of the @profile attribute values. Each vocab class has one instance of this class.
	
	The main reason to put this into a separate class is to localize a caching mechanism, that
	ensures that the same vocabulary file is read only once.
	
	@ivar keywords: collection of all keyword mappings
	@type keywords: dictionary
	@ivar ns: namespace mapping
	@type ns: dictionary
	@cvar profile_cache: cache, maps a URI on a (keywords,ns) tuple
	@type profile_cache: dictionary
	"""
	profile_cache = {}
	profile_stack = []
	
	def __init__(self, state) :
		"""
		@param state: the state behind this keyword mapping
		@type state: L{State.ExecutionContext}
		"""
		self.state = state
		from pyRdfa import pyRdfa
		options = Options(warnings = False,
						  space_preserve = False,
						  transformers = [],
						  xhtml = (state.options.host_language == XHTML_RDFA),
						  lax = state.options.lax)
		options.host_language = state.options.host_language
		# this is the (recursive) RDFa processor:
		self.Rdfa_processor = pyRdfa(options)

		self.keywords  = {}
		self.ns        = {}
		
		# see what the @vocab gives us...
		for prof in self.state.getURI("profile") :

			# avoid infinite recursion here...
			if prof in ProfileRead.profile_stack :
				# That one has already been done, danger of recursion:-(
				continue
			else :
				ProfileRead.profile_stack.append(prof)			
			# check the cache...
			if prof in ProfileRead.profile_cache :
				(self.keywords, self.ns) = ProfileRead.profile_cache[prof]
			else :
				# this vocab value has not been seen yet...
				graph = self._get_graph(prof)
				if graph == None : continue
				
				for (subj,uri) in graph.subject_objects(ns_rdfa_profile["uri"]) :
					# subj is, usually, a bnode, and is used as a subject for either a keyword
					# or a prefix setting
					# extra check is done to see whether there are more than one settings
					# rdflib works with iterators and I need the whole set here to make the checks:-(
					keyword_list = [k for k in graph.objects(subj, ns_rdfa_profile["keyword"])]
					prefix_list  = [k for k in graph.objects(subj, ns_rdfa_profile["prefix"])]
					if len(keyword_list) > 0 and len(prefix_list) > 0 :
						self.state.options.comment_graph.add_warning("The same URI <%s> is used both for keyword and prefix mapping in <%s>" % (uri,prof))
					elif len(keyword_list) > 1 :
						self.state.options.comment_graph.add_warning("The same URI <%s> is used both for several keyword mappings in <%s>" % (uri,prof))
					elif len(prefix_list) > 1 :
						self.state.options.comment_graph.add_warning("The same URI <%s> is used both for several prefix mappings in <%s>" % (uri,prof))
					else :
						# everything seems to be o.k., though a check for literals is still to be done
						if len(keyword_list) > 0 :
							keyword = keyword_list[0]
							if isinstance(keyword, Literal) :
								self.keywords[str(keyword)] = (URIRef(uri),[])
							else :
								self.state.options.comment_graph.add_warning("Non literal keyword <%s> defined in <%s> for <%s>; ignored" % (keyword, prof, uri))
						if len(prefix_list) > 0 :
							prefix = prefix_list[0]
							if isinstance(prefix, Literal) :
								self.ns[str(prefix)] = Namespace(uri)
							else :
								self.state.options.comment_graph.add_warning("Non literal prefix <%s> defined in <%s> for <%s>; ignored" % (prefix, prof, uri))
				# store the cache value, avoid re-reading again...
				ProfileRead.profile_cache[prof] = (self.keywords, self.ns)
			# Remove infinite anti-recursion measure
			ProfileRead.profile_stack.pop()
			
	def _get_graph(self, name) :
		"""
		Parse the vocabulary file, and return an RDFLib Graph. The URI's content type is checked and either one of
		RDFLib's parsers is invoked (for the Turtle, RDF/XML, and N Triple cases) or the RDFa processing is invoked, recursively,
		on the RDFa content.
		
		@param name: URI of the vocabulary file
		@return: An RDFLib Graph instance; None if the dereferencing or the parsing was unsuccessful
		"""
		content = None
		try :
			content = URIOpener(name, {'Accept' : 'text/html, application/xhtml+xml, text/turtle, application/rdf+xml'})
		except  :
			(type,value,traceback) = sys.exc_info()
			self.state.options.comment_graph.add_warning("Profile document <%s> could not be dereferenced (%s)" % (name,value))
			return None
		
		if content.content_type == TURTLE_MT :
			retval = Graph()
			try :
				retval.parse(content.data,format="n3")
				return retval
			except :
				(type,value,traceback) = sys.exc_info()
				self.state.options.comment_graph.add_warning("Could not parse Turtle content content at <%s> (%s)" % (name,value))
				return None
		elif content.content_type == RDFXML_MT :
			try :
				retval = Graph()
				retval.parse(content.data)
				return retval
			except :
				(type,value,traceback) = sys.exc_info()
				self.state.options.comment_graph.add_warning("Could not parse RDF/XML content at <%s> (%s)" % (name,value))
				return None
		elif content.content_type == NT_MT :
			try :
				retval = Graph()
				retval.parse(content.data,format="nt")
				return retval
			except :
				(type,value,traceback) = sys.exc_info()
				self.state.options.comment_graph.add_warning("Could not parse N-Triple content at <%s> (%s)" % (name,value))
				return None
		elif content.content_type == HTML_MT or content.content_type == XHTML_MT :
			try :
				return self.Rdfa_processor.graph_from_source(content.data)		
			except :
				(type,value,traceback) = sys.exc_info()
				self.state.options.comment_graph.add_warning("Could not parse RDFa content at <%s> (%s)" % (name,value))
				return None
		else :
			self.state.options.comment_graph.add_warning("Unrecognized media type for the vocabulary file <%s>: '%s'" % (name,content.content_type))
			return None

class Vocab :
	"""
	Wrapper around vocabulary management, ie, mapping a keyword (a term) to a URI, as well as a CURIE to a URI (typical
	examples for keyword are the "next", or "previous" as defined by XHTML). Each instance of this class belongs to a
	"state", defined in State.py
	@ivar state: State to which this instance belongs
	@type state: L{State.ExecutionContext}
	@ivar graph: The RDF Graph under generation
	@type graph: rdflib.Graph
	@ivar keywords: mapping from keywords to URI-s
	@type keywords: dictionary
	@ivar ns: namespace declarations, ie, mapping from prefixes to URIs
	@type ns: dictionary
	@ivar xhtml_prefix: prefix used for the XHTML namespace
	"""
	def __init__(self, state, graph, inherited_state) :
		"""Initialize the vocab bound to a specific state. 
		@param state: the state to which this vocab instance belongs to
		@type state: L{State.ExecutionContext}
		@param graph: the RDF graph being worked on
		@type graph: rdflib.Graph
		@param inherited_state: the state inherited by the current state. 'None' if this is the top level state.
		@type inherited_state: L{State.ExecutionContext}
		"""
		self.state	= state
		self.graph	= graph
		
		# --------------------------------------------------------------------------------
		# Set the default keyword URI
		def_kw_uri = self.state.getURI("vocab")
		if inherited_state == None :
			# Note that this may result in storing None, which is fine
			self.default_keyword_uri = def_kw_uri
		else :
			if def_kw_uri != None :
				self.default_keyword_uri = def_kw_uri
			else :
				self.default_keyword_uri = inherited_state.vocab.default_keyword_uri
		
		# Get the recursive definitions, if any
		recursive_vocab = ProfileRead(self.state)
		
		# --------------------------------------------------------------------------------
		# The simpler case: keywords
		if inherited_state is None :
			# this is the vocabulary belonging to the top level of the tree!
			self.keywords = {}
			# TODO: remove this part at some point and exchange it against whatever is decided for the HTML case! 
			if state.options.host_language != GENERIC_XML :
				relrev = ["rel","rev"]
				for key in _predefined_rel : self.keywords[key] = (URIRef(XHTML_URI+key),relrev)
			# Until here...
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
				
		# Add the namespaces defined via a @profile
		for key in recursive_vocab.ns : dict[key] = recursive_vocab.ns[key]
		
		# Add the locally defined namespaces using the @prefix syntax
		# this may override the definition in @profile
		if state.node.hasAttribute("prefix") :
			pr = state.node.getAttribute("prefix")
			if pr != None :
				# '=' may be surrounded by whitespace characters.
				for item in re.sub("\s*=\s*","=",pr.strip()).split() :
					ns = item.strip().split('=')
					if len(ns) >= 3 :
						# this is the case when either the left hand or the right hand side of a 
						# '=' is empty and there are several declarations in @prefix
						state.options.comment_graph.add_error("Error in @prefix, ambiguous prefix declaration: %s" % ns)
						continue
					elif len(ns) <= 1 :
						# stand alone term without any '=' in @prefix
						state.options.comment_graph.add_error("Error in @prefix, uninterpretable prefix declaration: %s" % ns[0])
						continue
					elif len(ns) > 1 :
						# sorting out the cases when the left or the right hand side of '=' is empty and
						# this is the only declaration in @prefix (cumulated cases are handled by the case for len(ns)>=3
						if ns[1] == "" :
							state.options.comment_graph.add_error("Error in @prefix, missing URI in prefix declaration: %s" % ns[0])
							continue
						if ns[0] == "" :
							state.options.comment_graph.add_error("Error in @prefix, missing prefix for prefix declaration: %s" % ns[1])
							continue	
						(prefix,value) = (ns[0],ns[1])
						# I am not sure how this case will be handled, though; this was used in the Prefix hgrddl module
						# DEFAULTNS="DEFAULTNS"
						uri = quote_URI(value, state.options)
						ns  = Namespace(uri)
						dict[prefix] = ns
		
		# Add the locally defined namespaces using the xmlns: syntax
		# Note that the placement of this code means that the local definitions will override
		# the effects of a @profile or @prefix
		for i in range(0, state.node.attributes.length) :
			attr = state.node.attributes.item(i)
			if attr.name.find('xmlns:') == 0 :	
				# yep, there is a namespace setting
				prefix = attr.localName
				if prefix != "" : # exclude the top level xmlns setting...
					if prefix == "_" :
						state.options.comment_graph.add_error("The '_' local CURIE prefix is reserved for blank nodes, and cannot be changed" )
					elif prefix.find(':') != -1 :
						state.options.comment_graph.add_error("The character ':' is not valid in a CURIE Prefix" )
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
				
		#------------------------------------------------------------------------
				
		# see if the xhtml core vocabulary has been set
		# This whole code seems to be relevant for an XHTML case only if at all
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
		blank node management, ie, when the key is '_'; this is something that
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
		URI is defined via the @profile or the @vocab (ie, default keyword uri) mechanism. Returns None if keyword is not defined
		@param keyword: string
		@param attr: attribute name
		@type attr: string
		@return: an RDFLib URIRef instance (or None)
		"""
		if keyword in self.keywords :
			uri, attrs = self.keywords[keyword]
			if attrs == [] or attr in attrs :
				return uri
		elif self.default_keyword_uri != None :
			return URIRef(self.default_keyword_uri + keyword)
		return None
		
