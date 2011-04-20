# -*- coding: utf-8 -*-
"""
Management of vocabularies, terms, and their mapping to URI-s. The main class of this module (L{TermOrCurie}) is,
conceptually, part of the overall state of processing at a node (L{State.ExecutionContext}) but putting it into a separate
module makes it easider to maintain.

@summary: Management of vocabularies, terms, and their mapping to URI-s.
@requires: U{RDFLib package<http://rdflib.net>}
@organization: U{World Wide Web Consortium<http://www.w3.org>}
@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}

@var XHTML_PREFIX: prefix for the XHTML vocabulary URI (set to 'xhv')
@var XHTML_URI: URI prefix of the XHTML vocabulary
@var ncname: Regular expression object for NCNAME
@var xml_application_media_type: Regular expression object for a general XML application media type
"""

"""
$Id: TermOrCurie.py,v 1.11 2011-04-20 11:02:21 ivan Exp $
$Date: 2011-04-20 11:02:21 $
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

from pyRdfa.Options			import Options
from pyRdfa.Utils 			import quote_URI, URIOpener
from pyRdfa.host 			import MediaTypes, HostLanguage, predefined_1_0_rel
from pyRdfa.ProfileCache	import CachedProfile
from pyRdfa 				import FailedProfile
from pyRdfa					import IncorrectProfileDefinition, IncorrectPrefixDefinition
from pyRdfa					import ns_rdfa, built_in_default_profiles

# Regular expression object for NCNAME
ncname = re.compile("^[A-Za-z][A-Za-z0-9._-]*$")

# Regular expression object for a general XML application media type
xml_application_media_type = re.compile("application/[a-zA-Z0-9]+\+xml")

XHTML_PREFIX = "xhv"
XHTML_URI    = "http://www.w3.org/1999/xhtml/vocab#"

#### Managing blank nodes for CURIE-s: mapping from local names to blank nodes.
_bnodes = {}
_empty_bnode = BNode()

####

class ProfileRead :
	"""
	Wrapper around the "recursive" access to profile files. The main job of this class is to retrieve
	term and prefix definitions as well as a default vocab value, by accessing an RDF file stored in a URI as given by the
	values of the @profile attribute values. Each L{TermOrCurie} class has one instance of this class.
	
	@ivar terms: collection of all term mappings
	@type terms: dictionary
	@ivar ns: namespace mapping
	@type ns: dictionary
	@ivar vocabulary: default vocabulary
	@type vocabulary: string
	@cvar profile_cache: cache, maps a URI on a (terms,ns) tuple
	@type profile_cache: dictionary
	@cvar excluded_profiles: list of profiles that are known to be used for other purposes but are either not dereferencable or do not contain RDFa information
	@type excluded_profiles: array of URI-s
	"""	
	excluded_profiles = [
		"http://www.w3.org/2005/11/profile",
		"http://www.w3.org/2003/g/data-view",
		"http://ns.inria.fr/grddl/rdfa/",
		"http://microformats.org/profile/hcalendar"
	]
	
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
		# Default vocabulary
		self.vocabulary = None
		
		if state.rdfa_version < "1.1" :
			return
		
		# see what the @profile gives us...
		profs = self.state.getURI("profile")
		# There was a persion when right-most URI had a lower priority, so we had to go in reverse order
		# kept it in the code for now, in case this is refersed again... for the time being the rule is
		# that the rightmost has a higher priority, ie, we simply have to go in normal order
		# At some point this comment has to be removed...
		# profs.reverse()
		for profuriref in profs :
			prof = str(profuriref)

			# jump over the excluded profiles
			if prof in self.excluded_profiles : continue
			
			# Get the profile data
			#
			if built_in_default_profiles :
				from DefaultProfiles import default_profiles
				if prof in default_profiles :
					data = default_profiles[prof]
				else :
					data = CachedProfile(prof, self.state.options, report = False)
			else :
					data = CachedProfile(prof, self.state.options, report = False)
			
			# Merge the profile data with the overall definition
			if data.vocabulary != "" :
				self.vocabulary = data.vocabulary
				
			for key in data.terms :
				if not isinstance(data.terms[key],URIRef) :
					self.terms[key] = URIRef(data.terms[key])
				else :
					self.terms[key] = data.terms[key]
			for key in data.ns :
				if not isinstance(data.ns[key], Namespace) :
					self.ns[key] = Namespace(data.ns[key])
				else :
					self.ns[key] = data.ns[key]

##################################################################################################################

class TermOrCurie :
	"""
	Wrapper around vocabulary management, ie, mapping a term to a URI, as well as a CURIE to a URI (typical
	examples for term are the "next", or "previous" as defined by XHTML). Each instance of this class belongs to a
	"state", instance of L{State.ExecutionContext}. Profile definitions are managed at initialization time.
	
	(In fact, this class is, conceptually, part of the overall state at a node, and has been separated here for an
	easier maintenance.)
	
	The class takes care of the stack-like behavior of vocabulary items, ie, inheriting everything that is possible
	from the "parent".
	
	@ivar state: State to which this instance belongs
	@type state: L{State.ExecutionContext}
	@ivar graph: The RDF Graph under generation
	@type graph: rdflib.Graph
	@ivar terms: mapping from terms to URI-s
	@type terms: dictionary
	@ivar ns: namespace declarations, ie, mapping from prefixes to URIs
	@type ns: dictionary
	@ivar default_curie_uri: URI for a default CURIE
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
		def check_prefix(pr) :
			from pyRdfa	import uri_schemes
			if pr in uri_schemes :
				# The prefix being defined is a registered URI scheme, better avoid it...
				state.options.add_warning("The '%s' prefix is also a registered or widely used URI scheme; is this a mistake?" % pr)
				
		self.state	= state
		self.graph	= graph
		
		# --------------------------------------------------------------------------------
		# Set the default CURIE URI
		if inherited_state == None :
			# This is the top level...
			# AFAIK there is no default setting for the URI-s
			# self.default_curie_uri = None
			self.default_curie_uri = Namespace(XHTML_URI)
			self.graph.bind(XHTML_PREFIX, self.default_curie_uri)				
		else :
			self.default_curie_uri = inherited_state.term_or_curie.default_curie_uri

		# --------------------------------------------------------------------------------
		# Get the recursive definitions, if any
		# Note that if the underlying file is 1.0 version, the returned structure will be, essentially, empty
		recursive_vocab = ProfileRead(self.state)
		
		# --------------------------------------------------------------------------------
		# Set the default term URI
		# Note that it is still an open issue whether the XHTML_URI should be used
		# for RDFa core, or whether it should be set to None.
		# This is a 1.1 feature, ie, should be ignored if the version is < 1.0
		if state.rdfa_version >= "1.1" :
			# that is the absolute default setup...
			if inherited_state == None :
				self.default_term_uri = None
			else :
				self.default_term_uri = inherited_state.term_or_curie.default_term_uri
				
			# see if the profile has defined a default profile:
			if recursive_vocab.vocabulary :
				self.default_term_uri = recursive_vocab.vocabulary
				
			# see if there is local vocab
			def_term_uri = self.state.getURI("vocab")
			if def_term_uri :			
				self.default_term_uri = def_term_uri
		else :
			self.default_term_uri = None
		
		# --------------------------------------------------------------------------------
		# The simpler case: terms, adding those that have been defined by a possible @profile file
		if inherited_state is None :
			# this is the vocabulary belonging to the top level of the tree!
			self.terms = {}
			if state.rdfa_version >= "1.1" :
				# Simply get the terms defined by the default vocabularies. There is no need for merging
				for key in recursive_vocab.terms :
					self.terms[key] = recursive_vocab.terms[key]
			else :
				# The terms are hardwired...
				for key in predefined_1_0_rel :
					self.terms[key] = URIRef(XHTML_URI + key)
				self.graph.bind(XHTML_PREFIX, XHTML_URI)
		else :
			if len(recursive_vocab.terms) == 0 :
				# just refer to the inherited terms
				self.terms = inherited_state.term_or_curie.terms
			else :
				self.terms = {}
				# tried to use python's 'update' operation for the dictionary and it failed. Why???
				for key in inherited_state.term_or_curie.terms 	: self.terms[key] = inherited_state.term_or_curie.terms[key]
				for key in recursive_vocab.terms 				: self.terms[key] = recursive_vocab.terms[key]

		#-----------------------------------------------------------------
		# the locally defined namespaces
		dict = {}
		# locally defined xmlns namespaces, necessary for correct XML Literal generation
		xmlns_dict = {}
				
		# Add the namespaces defined via a @profile
		for key in recursive_vocab.ns :
			dict[key] = recursive_vocab.ns[key]
			self.graph.bind(key, dict[key])

		# Add the locally defined namespaces using the xmlns: syntax
		# Note that the placement of this code means that the local definitions will override
		# the effects of a @profile, but these will be overriden by a possible @prefix
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
						dict[pr]       = ns
						xmlns_dict[pr] = ns
						self.graph.bind(pr,ns)
						check_prefix(pr)

		# Add the locally defined namespaces using the @prefix syntax
		# this may override the definition in @profile and @xmlns
		if state.rdfa_version >= "1.1" and state.node.hasAttribute("prefix") :
			pr = state.node.getAttribute("prefix")
			if pr != None :
				# separator character is whitespace
				pr_list = pr.strip().split()
				# range(0, len(pr_list), 2) 
				for i in range(len(pr_list) - 2, -1, -2) :
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
					elif prefix == ":" :
						state.options.add_warning("Default prefix cannot be changed (in '%s')" % pr, IncorrectPrefixDefinition)
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
								dict[real_prefix] = uri
								self.graph.bind(real_prefix,uri)
								# Additional warning: is this prefix overriding an existing xmlns statement with a different URI? if
								# so, that may lead to discrepancies between an RDFa 1.0 and RDFa 1.1 run...
								if (prefix in xmlns_dict and xmlns_dict[prefix] != uri) or (real_prefix in xmlns_dict and xmlns_dict[real_prefix] != uri) :
									state.options.add_warning("@prefix setting for '%s' overrides the 'xmlns:%s' setting; may be a source of problem if same file is run through RDFa 1.0" % (real_prefix,real_prefix))
								check_prefix(real_prefix)

							else :
								state.options.add_warning("Invalid prefix declaration (must be an NCNAME) '%s' (in '%s')" % (prefix,pr), IncorrectPrefixDefinition)

		# See if anything has been collected at all.
		# If not, the namespaces of the incoming state is
		# taken over by reference. Otherwise that is copied to the
		# the local dictionary
		self.ns = {}
		if len(dict) == 0 and inherited_state :
			self.ns = inherited_state.term_or_curie.ns
		else :
			if inherited_state :
				for key in inherited_state.term_or_curie.ns	: self.ns[key] = inherited_state.term_or_curie.ns[key]
				for key in dict								: self.ns[key] = dict[key]
			else :
				self.ns = dict
		
		# the xmlns prefixes have to be stored separately, again for XML Literal generation	
		self.xmlns = {}
		if len(xmlns_dict) == 0 and inherited_state :
			self.xmlns = inherited_state.term_or_curie.xmlns
		else :
			if inherited_state :
				for key in inherited_state.term_or_curie.xmlns	: self.xmlns[key] = inherited_state.term_or_curie.xmlns[key]
				for key in xmlns_dict							: self.xmlns[key] = xmlns_dict[key]
			else :
				self.xmlns = xmlns_dict
	# end __init__

	def CURIE_to_URI(self, val) :
		"""CURIE to URI mapping. 
		
		This method does I{not} take care of the last step of CURIE processing, ie, the fact that if
		it does not have a CURIE then the value is used a URI. This is done on the caller's side, because this has
		to be combined with base, for example. The method I{does} take care of BNode processing, though, ie,
		CURIE-s of the form "_:XXX".
		
		@param val: the full CURIE
		@type val: string
		@return: URIRef of a URI or None.
		"""
		# Just to be on the safe side:
		if val == "" :
			return None
		elif val == ":" :
			if self.default_curie_uri :
				return URIRef(self.default_curie_uri)
			else :
				return None
		
		# See if this is indeed a valid CURIE, ie, it can be split by a colon
		curie_split = val.split(':',1)
		if len(curie_split) == 1 :
			# there is no ':' character in the string, ie, it is not a valid CURIE
			return None
		else :
			if self.state.rdfa_version >= "1.1" :
				prefix	= curie_split[0].lower()
			else :
				prefix	= curie_split[0]
			reference = curie_split[1]
			if len(reference) > 0 and reference[0] == ":" :
				return None
			
			# first possibility: empty prefix
			if len(prefix) == 0 :
				if self.default_curie_uri :
					return self.default_curie_uri[reference]
				else :
					return None
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
	# end CURIE_to_URI

	def term_to_URI(self, term) :
		"""A term to URI mapping, where term is a simple string and the corresponding
		URI is defined via the @profile or the @vocab (ie, default term uri) mechanism. Returns None if term is not defined
		@param term: string
		@return: an RDFLib URIRef instance (or None)
		"""
		if len(term) == 0 : return None

		if ncname.match(term) :
			# It is a valid NCNAME
			# the algorithm is: first make a case sensitive match; if that fails than make a case insensive one
			# The first is easy, the second one is a little bit more convoluted
			
			# 1. simple, case sensitive test:
			if term in self.terms :
				# yep, term is a valid key as is
				return self.terms[term]
				
			# 2. the case insensitive test
			for defined_term in self.terms :
				uri = self.terms[defined_term]
				if term.lower() == defined_term.lower() :
					return uri
	
			# 3. check the default term uri, if any
			if self.default_term_uri != None :
				return URIRef(self.default_term_uri + term)

		# If it got here, it is all wrong...
		return None
		
#########################
"""
$Log: TermOrCurie.py,v $
Revision 1.11  2011-04-20 11:02:21  ivan
*** empty log message ***

Revision 1.10  2011/03/11 12:17:38  ivan
default prefix cannot be changed

Revision 1.9  2011/03/11 11:56:32  ivan
':' is a valid CURIE...

Revision 1.8  2011/03/08 10:49:50  ivan
*** empty log message ***

Revision 1.7  2011/01/14 12:43:32  ivan
xmlns values are stored separately for a proper generation of XML Literals


Revision 1.2  2010/09/03 13:12:51  ivan
Renamed CURIE to TermOrCurie everywhere, as a better name to reflect the functionality of the class

Revision 1.14  2010/07/27 13:19:19  ivan
Changed the profile term/prefix management to take care of all the errors and ignore entries with errors altogether

"""