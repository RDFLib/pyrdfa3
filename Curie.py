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
$Id: Curie.py,v 1.11 2010-07-23 12:31:38 ivan Exp $
$Date: 2010-07-23 12:31:38 $

Changes:
	- the order in the @profile attribute should be right to left (meaning that the URI List has to be reversed first)
	- if a @profile cannot be dereferenced then a RDFaStopParsing exception is raised rather than just go on

"""

import re, sys
import xml.dom.minidom
import random
import urlparse, urllib2

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

from pyRdfa.Options		import Options
from pyRdfa.Utils 		import quote_URI, URIOpener, CachedURIOpener, MediaTypes, HostLanguage
from pyRdfa 			import FailedProfile
from pyRdfa				import IncorrectProfileDefinition, IncorrectPrefixDefinition
from pyRdfa				import ns_rdfa

#: Regular expression object for NCNAME
ncname = re.compile("^[A-Za-z][A-Za-z0-9._-]*$")

#: Regular expression object for a general XML application media type
xml_application_media_type = re.compile("application/[a-zA-Z0-9]+\+xml")

XHTML_PREFIX = "xhv"
XHTML_URI    = "http://www.w3.org/1999/xhtml/vocab#"

# Predefined terms for XHTML
# At the moment this is just hardcoded, we will see whether this can be handled as
# some form of a default profile mechanism.
_predefined_html_terms  = [
	'alternate', 'appendix', 'cite', 'bookmark', 'chapter', 'contents',
	'copyright', 'glossary', 'help', 'icon', 'index', 'meta', 'next',
	'p3pv1', 'prev', 'role', 'section', 'subsection', 'start', 'license',
	'up', 'last', 'stylesheet', 'first', 'top'
]

_XSD_NS = Namespace(u'http://www.w3.org/2001/XMLSchema#')

# list of namespaces that are considered as default, ie, the user should not be forced to declare:
# Not used at the moment, bound the to whole default setting issue of the WG which is still open
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

#### Managing blank nodes for CURIE-s: mapping from local names to blank nodes.
_bnodes = {}
_empty_bnode = BNode()

class ProfileRead :
	"""
	Wrapper around the "recursive" access to profile files. The main job of this class is to retrieve
	term and prefix definitions by accessing an RDF file stored in a URI as given by the
	values of the @profile attribute values. Each curie class has one instance of this class.
	
	(The main reason to put this into a separate class is to localize a caching mechanism, that
	ensures that the same vocabulary file is read only once.)
	
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

		# This is to store the local terms
		self.terms  = {}
		# This is to store the local Namespaces (a.k.a. prefixes)
		self.ns     = {}
		
		if state.rdfa_version < "1.1" :
			return
		# see what the @profile gives us...
		#for prof in self.state.getURI("profile") :
		# The right-most URI has a lower priority, so we have to go in reverse order
		profs = self.state.getURI("profile")
		profs.reverse()
		for prof in profs :
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
				if graph == None :
					#from pyRdfa import RDFaStopParsing
					#raise RDFaStopParsing()
					continue
				
				for (subj,uri) in graph.subject_objects(ns_rdfa["uri"]) :
					# subj is, usually, a bnode, and is used as a subject for either a term
					# or a prefix setting
					# extra check is done to see whether there are more than one settings
					# rdflib works with iterators and I need the whole set here to make the checks:-(
					term_list 	= [k for k in graph.objects(subj, ns_rdfa["term"])]
					prefix_list	= [k for k in graph.objects(subj, ns_rdfa["prefix"])]
					if len(term_list) > 0 and len(prefix_list) > 0 :
						self.state.options.add_warning("The same URI <%s> is used both for term and prefix mapping in <%s>" % (uri,prof), IncorrectProfileDefinition, prof)
					elif len(term_list) > 1 :
						self.state.options.add_warning("The same URI <%s> is used for several term mappings in <%s>" % (uri,prof), IncorrectProfileDefinition, prof)
					elif len(prefix_list) > 1 :
						self.state.options.add_warning("The same URI <%s> is used for several prefix mappings in <%s>" % (uri,prof), IncorrectProfileDefinition, prof)
					else :
						# everything seems to be o.k., though a check for literals and on the validity of the term is still to be done
						if len(term_list) > 0 :
							term = term_list[0]
							if isinstance(term, Literal) :
								if ncname.match(term) != None :
									self.terms[str(term).lower()] = URIRef(uri)
								else :
									self.state.options.add_warning("Term <%s> defined in <%s> for <%s> is invalid; ignored" % (term, prof, uri), IncorrectProfileDefinition, prof)
							else :
								self.state.options.add_warning("Non literal term <%s> defined in <%s> for <%s>; ignored" % (term, prof, uri), IncorrectProfileDefinition, prof)
						if len(prefix_list) > 0 :
							prefix = prefix_list[0]
							if isinstance(prefix, Literal) :
								if ncname.match(prefix) != None :
									self.ns[str(prefix).lower()] = Namespace(uri)
								else :
									self.state.options.add_warning("Prefix <%s> defined in <%s> for <%s> is invalid; ignored" % (prefix, prof, uri), IncorrectProfileDefinition, prof)
							else :
								self.state.options.add_warning("Non literal prefix <%s> defined in <%s> for <%s>; ignored" % (prefix, prof, uri), IncorrectProfileDefinition, prof)
				# store the cache value, avoid re-reading again...
				ProfileRead.profile_cache[prof] = (self.terms, self.ns)
			# Remove infinite anti-recursion measure
			ProfileRead.profile_stack.pop()
			
	def _get_graph(self, name) :
		"""
		Parse the vocabulary file, and return an RDFLib Graph. The URI's content type is checked and either one of
		RDFLib's parsers is invoked (for the Turtle, RDF/XML, and N Triple cases) or a separate RDFa processing is invoked
		on the RDFa content.
		
		@param name: URI of the vocabulary file
		@return: An RDFLib Graph instance; None if the dereferencing or the parsing was unsuccessful
		@raise: FailedProfile if the profile document could not be dereferenced or is not a known media type
		"""
		from pyRdfa import CACHED_PROFILES_ID, HTTPError, RDFaError
		content = None
		try :
			content = CachedURIOpener(name,
									  {'Accept' : 'text/html;q=0.7, application/xhtml+xml;q=0.7, text/turtle;q=1.0, application/rdf+xml;q=0.8'},
									  CACHED_PROFILES_ID)

		except HTTPError, e :
			raise FailedProfile("Profile document <%s> could not be dereferenced (%s)" % (name, e.msg), name, http_code = e.http_code)
		except RDFaError, e :
			raise FailedProfile("Profile document <%s> could not be dereferenced (%s)" % (name, e.msg), name)
		except Exception, e :
			(type,value,traceback) = sys.exc_info()
			raise FailedProfile("Profile document <%s> could not be dereferenced (%s)" % (name, value), name)
		
		if content.content_type == MediaTypes.turtle :
			retval = Graph()
			try :
				retval.parse(content.data,format="n3")
				return retval
			except :
				(type,value,traceback) = sys.exc_info()
				raise FailedProfile("Could not parse Turtle content content at <%s> (%s)" % (name,value), name)
		elif content.content_type == MediaTypes.rdfxml :
			try :
				retval = Graph()
				retval.parse(content.data)
				return retval
			except :
				(type,value,traceback) = sys.exc_info()
				raise FailedProfile("Could not parse RDF/XML content at <%s> (%s)" % (name,value), name)
		elif content.content_type == MediaTypes.nt :
			try :
				retval = Graph()
				retval.parse(content.data,format="nt")
				return retval
			except :
				(type,value,traceback) = sys.exc_info()
				raise FailedProfile("Could not parse N-Triple content at <%s> (%s)" % (name,value), name)
		elif content.content_type in [MediaTypes.xhtml, MediaTypes.html, MediaTypes.xml] or xml_application_media_type.match(content.content_type) != None :
			try :
				from pyRdfa import pyRdfa
				options = Options(warnings = False)
				return pyRdfa(options).graph_from_source(content.data)
			except :
				(type,value,traceback) = sys.exc_info()
				raise FailedProfile("Could not parse RDFa content at <%s> (%s)" % (name,value), name)
		else :
			raise FailedProfile("Unrecognized media type for the vocabulary file <%s>: '%s'" % (name,content.content_type), name)

class Curie :
	"""
	Wrapper around vocabulary management, ie, mapping a term to a URI, as well as a CURIE to a URI (typical
	examples for term are the "next", or "previous" as defined by XHTML). Each instance of this class belongs to a
	"state", instance of L{State.ExecutionContext}
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
		# Note that it is still an open issue whether the XHTML_URI should be used
		# for RDFa core, or whether it should be set to None.
		# This is a 1.1 feature, ie, should be ignored if the version is < 1.0
		if state.rdfa_version >= "1.1" :
			def_term_uri = self.state.getURI("vocab")
			if inherited_state == None :
				self.default_term_uri = def_term_uri
			else :
				if def_term_uri != None :
					self.default_term_uri = def_term_uri
				else :
					self.default_term_uri = inherited_state.curie.default_term_uri
		else :
			self.default_term_uri = None

		# --------------------------------------------------------------------------------
		# Get the recursive definitions, if any
		# Note that if the underlying file is 1.0 version, the returned structure will be, essentially, empty
		recursive_vocab = ProfileRead(self.state)
		
		# --------------------------------------------------------------------------------
		# The simpler case: terms, adding those that have been defined by a possible @profile file
		if inherited_state is None :
			# this is the vocabulary belonging to the top level of the tree!
			self.terms = {}
			# HTML has its own set of predefined terms. Though, conceptually, that can be done with @profile,
			# it is better that way...
			#if self.state.options.host_language in [HostLanguage.xhtml_rdfa, HostLanguage.html_rdfa] :
			#	for key in _predefined_html_terms : self.terms[key] = URIRef(XHTML_URI+key)

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
						state.options.add_warning("The '_' local CURIE prefix is reserved for blank nodes, and cannot be changed", IncorrectPrefixDefinition)
					elif prefix.find(':') != -1 :
						state.options.add_warning("The character ':' is not valid in a CURIE Prefix", IncorrectPrefixDefinition)
					else :					
						# quote the URI, ie, convert special characters into %.. This is
						# true, for example, for spaces
						uri = quote_URI(attr.value, state.options)
						# create a new RDFLib Namespace entry
						ns = Namespace(uri)
						# Add an entry to the dictionary if not already there (priority is left to right!)
						if state.rdfa_version >= "1.1" :
							pr = prefix.lower()
						else :
							pr = prefix
						dict[pr] = ns
						self.graph.bind(pr,ns)

		# Add the locally defined namespaces using the @prefix syntax
		# this may override the definition in @profile and @xmlns
		if state.rdfa_version >= "1.1" and state.node.hasAttribute("prefix") :
			pr = state.node.getAttribute("prefix")
			if pr != None :
				# separator character is whitespace
				pr_list = pr.strip().split()
				for i in range(0, len(pr_list), 2) :
					prefix = pr_list[i]
					# see if there is a URI at all
					if i == len(pr_list) - 1 :
						state.options.add_warning("Missing URI in prefix declaration for '%s' (in '%s')" % (prefix,pr), IncorrectPrefixDefinition)
						break
					else :
						value = pr_list[i+1]
					
					# see if the value of prefix is o.k., ie, there is a ':' at the end
					if prefix[-1] != ':' :
						state.options.add_warning("Invalid prefix declaration '%s' (in '%s')" % (prefix,pr), IncorrectPrefixDefinition)
						continue
					else :
						prefix = prefix[:-1]
						uri    = Namespace(quote_URI(value, state.options))
						if prefix == "" :
							#something to be done here
							self.default_curie_uri = uri
						elif prefix == "_" :
							state.options.add_warning("The '_' local CURIE prefix is reserved for blank nodes, and cannot be changed (in '%s')" % pr, IncorrectPrefixDefinition)				
						else :
							# last check: is the prefix an NCNAME?
							if ncname.match(prefix) :
								real_prefix = prefix.lower()
								# This extra check is necessary to allow for a left-to-right priority
								if real_prefix not in dict :
									dict[real_prefix] = uri
									self.graph.bind(real_prefix,uri)
							else :
								state.options.add_warning("Invalid prefix declaration (must be an NCNAME) '%s' (in '%s')" % (prefix,pr), IncorrectPrefixDefinition)

		# See if anything has been collected at all.
		# If not, the namespaces of the incoming state is
		# taken over by reference. Otherwise that is copied to the
		# the local dictionary
		self.ns = {}
		if len(dict) == 0 and inherited_state :
			self.ns = inherited_state.curie.ns
		else :
			if inherited_state :
				for key in inherited_state.curie.ns	: self.ns[key] = inherited_state.curie.ns[key]
				for key in dict						: self.ns[key] = dict[key]
			else :
				self.ns = dict

	def CURIE_to_URI(self, val) :
		"""CURIE to URI mapping. 
		
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
			if self.state.rdfa_version > "1.1" :
				prefix	= curie_split[0].lower()
			else :
				prefix	= curie_split[0]
			reference = curie_split[1]
			
			# first possibility: empty prefix
			if len(prefix) == 0 :
				return self.default_curie_uri[reference]
			else :
				# prefix is non-empty; can be a bnode
				if prefix == "_" :
					# yep, BNode processing. There is a difference whether the reference is empty or not...
					if len(reference) == 0 :
						return _empty_bnode
					else :
						# see if this variable has been used before for a BNode
						if reference in _bnodes :
							return _bnodes[reference]
						else :
							# a new bnode...
							retval = BNode()
							_bnodes[reference] = retval
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
				uri = self.terms[defined_term]
				if term.lower() == defined_term :
					return uri
	
			# check the default term uri, if any
			if self.default_term_uri != None :
				return URIRef(self.default_term_uri + term)

		# If it got here, it is all wrong...
		return None
		
