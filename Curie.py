# -*- coding: utf-8 -*-
"""
Management of vocabularies, terms, and their mapping to URI-s. The module's name is a slight misnomer because, beyond handling CURIE-s, it also handles terms...

@summary: RDFa core parser processing step
@requires: U{RDFLib package<http://rdflib.net>}
@organization: U{World Wide Web Consortium<http://www.w3.org>}
@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}

@var XHTML_PREFIX: prefix for the XHTML vocabulary URI
@var XHTML_URI: URI prefix of the XHTML vocabulary
@var usual_protocols: list of "usual" protocols (used to generate warnings when CURIES are not protected)
@var _predefined_rel: list of predefined C{@rev} and C{@rel} values that should be mapped onto the XHTML vocabulary URI-s.
"""

"""
$Id: Curie.py,v 1.2 2010-04-11 15:44:45 ivan Exp $
$Date: 2010-04-11 15:44:45 $
"""

import re, sys

#: Regular expression objects for NCNAME
ncname = re.compile("^[A-Za-z][A-Za-z0-9._-]*$")

#: Regular expression object for a general XML application media type
xml_application_media_type = re.compile("application/[a-zA-Z0-9]+\+xml")

from rdflib.RDF			import RDFNS   as ns_rdf
from rdflib.RDFS		import RDFSNS  as ns_rdfs
from rdflib.RDFS		import comment as rdfs_comment
from rdflib.Namespace	import Namespace
from rdflib.URIRef		import URIRef
from rdflib.Literal		import Literal
from rdflib.BNode		import BNode
from rdflib.Graph		import Graph
from pyRdfa.Options		import Options, RDFA_CORE, XHTML_RDFA, HTML5_RDFA
from pyRdfa.Utils 		import quote_URI, URIOpener, RDFXML_MT, TURTLE_MT, HTML_MT, XHTML_MT, NT_MT, XML_MT
import xml.dom.minidom

debug = True

import random
import urlparse

XHTML_PREFIX = "xhv"
XHTML_URI    = "http://www.w3.org/1999/xhtml/vocab#"

_WARNING_VERSION = "RDFa profile or RFDa version has not been set (for a correct identification of RDFa). This is not a requirement for RDFa, but it is advised to use one of those nevertheless. Note that in the case of HTML5, the DOCTYPE setting may not work..."

####Predefined @rel/@rev/@property values
# predefined values for the @rel and @rev values. These are considered to be part of a specific
# namespace, defined by the RDFa document.
_predefined_html_rel  = [
	'alternate', 'appendix', 'cite', 'bookmark', 'chapter', 'contents',
	'copyright', 'glossary', 'help', 'icon', 'index', 'meta', 'next',
	'p3pv1', 'prev', 'role', 'section', 'subsection', 'start', 'license',
	'up', 'last', 'stylesheet', 'first', 'top'
]

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


#### Managing blank nodes for CURIE-s
__bnodes = {}
__empty_bnode = BNode()

# This is a necessary optimization: we should avoid reading in the same vocabulary definition
# several times. Ie, some sort of a caching mechanism is necessary.

class ProfileRead :
	"""
	Wrapper around the "recursive" access to profile files. The main job of this task to retrieve
	term and namespace definitions by accessing an RDFa file stored in a URI as given by the
	values of the @profile attribute values. Each vocab class has one instance of this class.
	
	The main reason to put this into a separate class is to localize a caching mechanism, that
	ensures that the same vocabulary file is read only once.
	
	@ivar terms: collection of all term mappings
	@type terms: dictionary
	@ivar ns: namespace mapping
	@type ns: dictionary
	@cvar profile_cache: cache, maps a URI on a (terms,ns) tuple
	@type profile_cache: dictionary
	"""
	profile_cache = {}
	profile_stack = []
	
	def __init__(self, state) :
		"""
		@param state: the state behind this term mapping
		@type state: L{State.ExecutionContext}
		"""
		self.state = state

		# Terms are stored as tuples; the second element is a boolean, defining whether the term is case-sensitive (default) or not
		# at the moment, there are no rdfa vocabulary terms to set the latter, but it is important for the html cases
		self.terms  = {}
		self.ns     = {}
		
		# see what the @profile gives us...
		for prof in self.state.getURI("profile") :
			# avoid infinite recursion here...
			if prof in ProfileRead.profile_stack :
				# That one has already been done, danger of recursion:-(
				continue
			else :
				ProfileRead.profile_stack.append(prof)			
			# check the cache...
			if prof in ProfileRead.profile_cache :
				(self.terms, self.ns) = ProfileRead.profile_cache[prof]
			else :
				# this vocab value has not been seen yet...
				graph = self._get_graph(prof)
				if graph == None : continue
				
				for (subj,uri) in graph.subject_objects(ns_rdfa_profile["uri"]) :
					# subj is, usually, a bnode, and is used as a subject for either a term
					# or a prefix setting
					# extra check is done to see whether there are more than one settings
					# rdflib works with iterators and I need the whole set here to make the checks:-(
					term_list 	= [k for k in graph.objects(subj, ns_rdfa_profile["term"])]
					prefix_list	= [k for k in graph.objects(subj, ns_rdfa_profile["prefix"])]
					if len(term_list) > 0 and len(prefix_list) > 0 :
						self.state.options.comment_graph.add_warning("The same URI <%s> is used both for term and prefix mapping in <%s>" % (uri,prof))
					elif len(term_list) > 1 :
						self.state.options.comment_graph.add_warning("The same URI <%s> is used for several term mappings in <%s>" % (uri,prof))
					elif len(prefix_list) > 1 :
						self.state.options.comment_graph.add_warning("The same URI <%s> is used for several prefix mappings in <%s>" % (uri,prof))
					else :
						# everything seems to be o.k., though a check for literals and on the validity of the term is still to be done
						if len(term_list) > 0 :
							term = term_list[0]
							if isinstance(term, Literal) :
								if ncname.match(term) != None :
									self.terms[str(term)] = (URIRef(uri),True)
								else :
									self.state.options.comment_graph.add_warning("Term <%s> defined in <%s> for <%s> is invalid; ignored" % (term, prof, uri))
							else :
								self.state.options.comment_graph.add_warning("Non literal term <%s> defined in <%s> for <%s>; ignored" % (term, prof, uri))
						if len(prefix_list) > 0 :
							prefix = prefix_list[0]
							if isinstance(prefix, Literal) :
								if ncname.match(prefix) != None :
									self.ns[str(prefix)] = Namespace(uri)
								else :
									self.state.options.comment_graph.add_warning("Prefix <%s> defined in <%s> for <%s> is invalid; ignored" % (prefix, prof, uri))
							else :
								self.state.options.comment_graph.add_warning("Non literal prefix <%s> defined in <%s> for <%s>; ignored" % (prefix, prof, uri))
				# store the cache value, avoid re-reading again...
				ProfileRead.profile_cache[prof] = (self.terms, self.ns)
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
		elif content.content_type in [HTML_MT, XHTML_MT, XML_MT] or xml_application_media_type.match(content.content_type) != None :
			try :
				from pyRdfa import pyRdfa
				options = Options(warnings = False)
				return pyRdfa(options).graph_from_source(content.data)
			except :
				(type,value,traceback) = sys.exc_info()
				self.state.options.comment_graph.add_warning("Could not parse RDFa content at <%s> (%s)" % (name,value))
				return None
		else :
			self.state.options.comment_graph.add_warning("Unrecognized media type for the vocabulary file <%s>: '%s'" % (name,content.content_type))
			return None

class Curie :
	"""
	Wrapper around vocabulary management, ie, mapping a term (a term) to a URI, as well as a CURIE to a URI (typical
	examples for term are the "next", or "previous" as defined by XHTML). Each instance of this class belongs to a
	"state", defined in State.py
	@ivar state: State to which this instance belongs
	@type state: L{State.ExecutionContext}
	@ivar graph: The RDF Graph under generation
	@type graph: rdflib.Graph
	@ivar terms: mapping from terms to URI-s
	@type terms: dictionary
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
		# Set the default CURIE URI
		if inherited_state == None :
			self.default_curie_uri = Namespace(XHTML_URI)
			self.graph.bind(XHTML_PREFIX, self.default_curie_uri)
		else :
			self.default_curie_uri = inherited_state.curie.default_curie_uri
		
		# --------------------------------------------------------------------------------
		# Set the default term URI
		def_kw_uri = self.state.getURI("vocab")
		if inherited_state == None :
			# Note that this may result in storing None, which is fine
			# However, the HTML/XHTML case has to be handled in a somewhat different manner
			if def_kw_uri == None and (self.state.options.host_language == XHTML_RDFA or self.state.options.host_language) :
				self.default_term_uri = XHTML_URI
			else :
				self.default_term_uri = def_kw_uri
		else :
			if def_kw_uri != None :
				self.default_term_uri = def_kw_uri
			else :
				self.default_term_uri = inherited_state.curie.default_term_uri
		
		# --------------------------------------------------------------------------------
		# Get the recursive definitions, if any
		recursive_vocab = ProfileRead(self.state)
		
		# --------------------------------------------------------------------------------
		# The simpler case: terms, adding those that have been defined by a possible @profile file
		if inherited_state is None :
			# this is the vocabulary belonging to the top level of the tree!
			self.terms = {}
			# TODO: remove this part at some point and exchange it against whatever is decided for the HTML case! 
			if self.state.options.host_language == XHTML_RDFA or self.state.options.host_language :
				for key in _predefined_html_rel : self.terms[key] = (URIRef(XHTML_URI+key),False)
			# Until here...
			# add the terms defined locally
			for key in recursive_vocab.terms :
				self.terms[key] = recursive_vocab.terms[key]
		else :
			if len(recursive_vocab.terms) == 0 :
				# just refer to the inherited terms
				self.terms = inherited_state.curie.terms
			else :
				self.terms = {}
				# tried to use the 'update' operation for the dictionary and it failed. Why???
				for key in inherited_state.curie.terms 	: self.terms[key] = inherited_state.curie.terms[key]
				for key in recursive_vocab.terms 		: self.terms[key] = recursive_vocab.terms[key]

		#-----------------------------------------------------------------
		# the locally defined namespaces
		dict = {}
				
		# Add the namespaces defined via a @profile
		for key in recursive_vocab.ns : dict[key] = recursive_vocab.ns[key]

		# Add the locally defined namespaces using the xmlns: syntax
		# Note that the placement of this code means that the local definitions will override
		# the effects of a @profile
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

		# Add the locally defined namespaces using the @prefix syntax
		# this may override the definition in @profile and @xmlns
		if state.node.hasAttribute("prefix") :
			pr = state.node.getAttribute("prefix")
			if pr != None :
				# separator character is whitespace
				pr_list = pr.strip().split()
				for i in range(0,len(pr_list),2) :
					prefix = pr_list[i]
					# see if there is a URI at all
					if i == len(pr_list) - 1 :
						state.options.comment_graph.add_error("Missing URI in prefix declaration for %s in %s" % (prefix,pr))
						break
					else :
						value = pr_list[i+1]
					
					# see if the value of prefix is o.k., ie, there is a ':' at the end
					if prefix[-1] != ':' :
						state.options.comment_graph.add_error("Invalid prefix declaration %s in %s" % (prefix,pr))
						continue
					else :
						prefix = prefix[:-1]
						uri = Namespace(quote_URI(value, state.options))
						if prefix == "" :
							#something to be done here
							self.default_curie_uri = uri
						else :
							dict[prefix] = uri

		# See if anything has been collected at all.
		# If not, the namespaces of the incoming state is
		# taken over by reference. Otherwise that is copied to the
		# the local dictionary
		if len(dict) == 0 and inherited_state :
			self.ns = inherited_state.curie.ns
		else :
			self.ns = {}
			if inherited_state :
				for key in inherited_state.curie.ns	: self.ns[key] = inherited_state.curie.ns[key]
				for key in dict						: self.ns[key] = dict[key]
			else :
				self.ns = dict

	def CURIE_to_URI(self, val) :
		"""CURIE to URI mapping. Note that this method does not take care of the
		blank node management, ie, when the key is '_'; this is something that
		has to be taken care of summer higher up.
		
		Note that this method does I{not} take care of the last step of CURIE processing, ie, the fact that if
		it does not have a CURIE then the value is used a URI. This is done on the caller's side, because this has
		to be combined with base, for example. The method I{does} take care of BNode processing, though, ie,
		CURIE-s of the form "_:XXX".
		
		@param val: the full CURIE
		@type val: string
		@return: URIRef of a URI or None.
		"""
		# Just to be on the safe side:
		if val == "" or val == ":" : return None
		
		# See if this is indeed a valid CURIE, ie, it can be split by a colon
		curie_split = val.split(':',1)
		if len(curie_split) == 1 :
			# there is no ':' character in the string, ie, it is not a valid curie
			return None
		else :
			prefix    = curie_split[0]
			reference = curie_split[1]
			
			# first possibility: empty prefix
			if len(prefix) == 0 :
				return self.default_curie_uri[reference]
			else :
				# prefix is non-empty; can be a bnode
				if prefix == "_" :
					# yep, BNode processing. There is a difference whether the reference is empty or not...
					if len(reference) == 0 :
						return __empty_bnode
					else :
						# see if this variable has been used before for a BNode
						if reference in __bnodes :
							return __bnodes[reference]
						else :
							# a new bnode...
							retval = BNode()
							__bnodes[reference] = retval
							return retval
				# check if the prefix is a valid NCNAME
				elif ncname.match(prefix) :
					# see if there is a binding for this:
					if prefix in self.ns :
						# yep, a binding has been defined!
						if len(reference) == 0 :
							return URIRef(str(self.ns[prefix]))
						else :
							return self.ns[prefix][reference]
					else :
						# no definition for this thing...
						# the CURIE should be used as a URI, but that is handled by the caller (using base and stuff...)
						return None
				else :
					return None
				

	def term_to_URI(self, term) :
		"""A term to URI mapping, where term is a simple string and the corresponding
		URI is defined via the @profile or the @vocab (ie, default term uri) mechanism. Returns None if term is not defined
		@param term: string
		@return: an RDFLib URIRef instance (or None)
		"""
		if len(term) == 0 : return None

		if ncname.match(term) :
			# It is a valid NCNAME
			for defined_term in self.terms :
				uri, case_sensitive = self.terms[defined_term]
				if case_sensitive :
					if term == defined_term :
						return uri
				else :
					if term.lower() == defined_term.lower() :
						return uri
	
			# check the default term uri, if any
			if self.default_term_uri != None :
				return URIRef(self.default_term_uri + term)

		# If it got here, it is all wrong...
		return None
		
