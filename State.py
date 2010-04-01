# -*- coding: utf-8 -*-
"""
Parser's execution context (a.k.a. state) object and handling. The state includes:

  - dictionary for namespaces. Keys are the namespace prefixes, values are RDFLib Namespace instances
  - language, retrieved from C{@xml:lang}
  - URI base, determined by <base> (or set explicitly). This is a little bit superfluous, because the current RDFa syntax does not make use of C{@xml:base}; ie, this could be a global value.  But the structure is prepared to add C{@xml:base} easily, if needed.
  - options, in the form of an L{Options<pyRdfa.Options>} instance

The execution context object is also used to turn relative URI-s and CURIES into real URI references.

@summary: RDFa core parser processing step
@requires: U{RDFLib package<http://rdflib.net>}
@organization: U{World Wide Web Consortium<http://www.w3.org>}
@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}

@var RDFa_PROFILE: the official RDFa profile URI
@var RDFa_VERSION: the official version string of RDFa
@var __bnodes: dictionary of blank node names to real blank node
@var __empty_bnode: I{The} Bnode to be associated with the CURIE of the form "C{_:}".
"""

"""
$Id: State.py,v 1.7 2010-04-01 08:34:38 ivan Exp $
$Date: 2010-04-01 08:34:38 $
"""

from rdflib.RDF			import RDFNS   as ns_rdf
from rdflib.RDFS		import RDFSNS  as ns_rdfs
from rdflib.RDFS		import comment as rdfs_comment
from rdflib.Namespace	import Namespace
from rdflib.URIRef		import URIRef
from rdflib.Literal		import Literal
from rdflib.BNode		import BNode
from pyRdfa.Options		import Options, GENERIC_XML, XHTML_RDFA, HTML5_RDFA
from pyRdfa.Utils 		import quote_URI
from pyRdfa.Vocab		import Vocab

debug = True

import re
import random
import urlparse
import urllib


_WARNING_VERSION = "RDFa profile or RFDa version has not been set (for a correct identification of RDFa). This is not a requirement for RDFa, but it is advised to use one of those nevertheless. "

RDFa_VERSION    = "XHTML+RDFa 1.0"
RDFa_PublicID   = "-//W3C//DTD XHTML+RDFa 1.0//EN"
RDFa_SystemID   = "http://www.w3.org/MarkUp/DTD/xhtml-rdfa-1.dtd"

#: list of 'usual' URI schemes; if a URI does not fall into these, a warning may be issued (can be the source of a bug)
usual_schemes = ["doi", "file", "ftp", "gopher", "hdl", "http", "https", "imap", "ldap",
				 "mailto", "mms", "news", "nntp", "prospero", "rsync", "rtsp", "rtspu", "sftp",
				 "shttp", "sip", "sips", "snews", "svn", "svn+ssh", "telnet", "tel", "urn", "wais"
				]

#### Managing blank nodes for CURIE-s
__bnodes = {}
__empty_bnode = BNode()
def _get_bnode_from_Curie(var) :
	"""
	'Var' gives the string after the coloumn in a CURIE of the form C{_:XXX}. If this variable has been used
	before, then the corresponding BNode is returned; otherwise a new BNode is created and
	associated to that value.
	@param var: CURIE BNode identifier
	@return: BNode
	"""
	if len(var) == 0 :
		return __empty_bnode
	if var in __bnodes :
		return __bnodes[var]
	else :
		retval = BNode()
		__bnodes[var] = retval
		return retval	

#### Core Class definition
class ExecutionContext :
	"""State at a specific node, including the current set of namespaces in the RDFLib sense, current language,
	the base, vocabularies, etc. The class is also used to interpret URI-s and CURIE-s to produce
	URI references for RDFLib.
	
	@ivar options: reference to the overall options
	@type options: L{Options.Options}
	@ivar base: the 'base' URI
	@ivar defaultNS: default namespace
	@ivar lang: language tag (possibly None)
	@ivar vocab: vocabulary management class instance
	@type vocan: L{Vocab.Vocab}
	@ivar node: the node to which this state belongs
	@type node: DOM node instance
	"""

	#: list of attributes that allow for lists of values and should be treated as such	
	_list = [ "profile", "rel", "rev", "property", "typeof" ]
	#: mapping table from attribute name to the exact method to retrieve the URI(s). Note that this is a class variable that is initialized by the first instance
	_resource_type = {}
	#	"href"		:	ExecutionContext._pureURI,
	#	"src"		:	ExecutionContext._pureURI,
	#	"vocab"		:	ExecutionContext._pureURI,
	#
	#	"about"		:	ExecutionContext._CURIE_with_base,
	#	"resource"	:	ExecutionContext._CURIE_with_base,
	#
	#	"rel"		:	ExecutionContext._CURIE,
	#	"rev"		:	ExecutionContext._CURIE,
	#	"datatype"	:	ExecutionContext._CURIE,
	#	"typeof"	:	ExecutionContext._CURIE,
	#	"property"	:	ExecutionContext._CURIE,
	#}	
	
	def __init__(self, node, graph, inherited_state=None, base="", options=None) :
		"""
		@param node: the current DOM Node
		@param graph: the RDFLib Graph
		@keyword inherited_state: the state as inherited
		from upper layers. This inherited_state is mixed with the state information
		retrieved from the current node.
		@type inherited_state: L{State.ExecutionContext}
		@keyword base: string denoting the base URI for the specific node. This overrides the possible
		base inherited from the upper layers. The 
		current XHTML+RDFa syntax does not allow the usage of C{@xml:base}, but SVG1.2 does, so this is
		necessary for SVG (and other possible XML dialects that accept C{@xml:base})
		@keyword options: invocation options, and references to warning graphs
		@type options: L{Options<pyRdfa.Options>}
		"""
		# This additional class initialization that must be done run time, otherwise import errors show up
		if len(	ExecutionContext._resource_type ) == 0 :	
			ExecutionContext._resource_type = {
				"href"		:	ExecutionContext._pureURI,
				"src"		:	ExecutionContext._pureURI,
				"profile"	:	ExecutionContext._pureURI,
				"vocab"	    :   ExecutionContext._pureURI,
			
				"about"		:	ExecutionContext._CURIE_with_base,
				"resource"	:	ExecutionContext._CURIE_with_base,
			
				"rel"		:	ExecutionContext._CURIE,
				"rev"		:	ExecutionContext._CURIE,
				"datatype"	:	ExecutionContext._CURIE,
				"typeof"	:	ExecutionContext._CURIE,
				"property"	:	ExecutionContext._CURIE,
			}	
		#-----------------------------------------------------------------
		# This is not inherited:-)
		self.node = node
		
		#-----------------------------------------------------------------
		# settling the base
		# note that, strictly speaking, it is not necessary to add the base to the
		# context, because there is only one place to set it (<base> element of the <header>).
		# It is done because it is prepared for a possible future change in direction of
		# accepting xml:base on each element.
		# At the moment, it is invoked with a 'None' at the top level of parsing, that is
		# when the <base> element is looked for.
		if inherited_state :
			self.base		= inherited_state.base
			self.options	= inherited_state.options
			# for generic XML versions the xml:base attribute should be handled
			if self.options.host_language == GENERIC_XML and node.hasAttribute("xml:base") :
				self.base = node.getAttribute("xml:base")
		else :
			# this is the branch called from the very top
			self.base = ""
			for bases in node.getElementsByTagName("base") :
				if bases.hasAttribute("href") :
					self.base = bases.getAttribute("href")
					continue
			if self.base == "" :
				self.base = base
			
			# this is just to play safe. I believe this branch should actually not happen...
			if options == None :
				from pyRdfa import Options
				self.options = Options()
			else :
				self.options = options

			# xml:base is not part of XHTML+RDFa, but it is a valid setting for, say, SVG1.2
			if self.options.host_language == GENERIC_XML and node.hasAttribute("xml:base") :
				self.base = node.getAttribute("xml:base")		

			self.options.comment_graph.set_base_URI(URIRef(quote_URI(base, self.options)))

			# check the the presence of the @profile and or @version attribute for the RDFa profile...
			# This whole branch is, however, irrelevant if the host language is a generic XML one (eg, SVG)
			if self.options.host_language != GENERIC_XML :
				doctype = None
				try :
					# I am not 100% sure the HTML5 minidom implementation has this, so let us just be
					# cautious here...
					doctype = node.ownerDocument.doctype
				except :
					pass
				if doctype == None or not( doctype.publicId == RDFa_PublicID and doctype.systemId == RDFa_SystemID ) :
					# next level: check the version
					html = node.ownerDocument.documentElement
					if not( html.hasAttribute("version") and RDFa_VERSION == html.getAttribute("version") ):
						if self.options.host_language == HTML5_RDFA :
							self.options.comment_graph.add_info(_WARNING_VERSION + " Note that in the case of HTML5, the DOCTYPE setting may not work...")
						else :
							self.options.comment_graph.add_info(_WARNING_VERSION)
								
		#-----------------------------------------------------------------
		# this will be used repeatedly, better store it once and for all...
		self.parsedBase = urlparse.urlsplit(self.base)

		#-----------------------------------------------------------------
		# generate and store the local vocab class instance
		self.vocab = Vocab(self, graph, inherited_state)

		#-----------------------------------------------------------------
		# Settling the language tags
		# @lang has priority over @xml:lang
		# I just want to be prepared here...
		if node.hasAttribute("xml:lang") :
			self.lang = node.getAttribute("xml:lang")
			if len(self.lang) == 0 : self.lang = None
		elif node.hasAttribute("lang") :
			self.lang = node.getAttribute("lang")
			if len(self.lang) == 0 : self.lang = None
		elif inherited_state :
			self.lang = inherited_state.lang
		else :
			self.lang = None
			
		if node.hasAttribute("xml:lang") and node.hasAttribute("lang") and node.getAttribute("lang") != node.getAttribute("xml:lang") :
			self.options.comment_graph.add_info("Both xml:lang and lang used on an element with different values; xml:lang prevails. (%s and %s)" % (node.getAttribute("xml:lang"),node.getAttribute("lang")))			
			
		#-----------------------------------------------------------------
		# Set the default namespace. Used when generating XML Literals
		if node.hasAttribute("xmlns") :
			self.defaultNS = node.getAttribute("xmlns")
		elif inherited_state and inherited_state.defaultNS != None :
			self.defaultNS = inherited_state.defaultNS
		else :
			self.defaultNS = None

	def _check_create_URIRef(self, uri) :
		"""
		Mini helping function: it checks whether a uri is using a usual scheme before a URIRef is created. In case
		there is something unusual, a warning is generated (though the URIRef is created nevertheless)
		@param uri: (absolute) URI string
		@return: an RDFLib URIRef instance
		"""
		val = uri.strip()
		if urlparse.urlsplit(val)[0] not in usual_schemes :
			self.options.comment_graph.add_warning("Unusual URI scheme used <%s>; may that be a mistake?" % val.strip())
		return URIRef(val)

	def _pureURI(self, attr, val) :
		"""Returns a URI for a 'pure' URI (ie, no CURIE). The value should not be emtpy at this point.
		@param val: attribute value to be interpreted
		@type val: string
		@param attr: attribute name
		@type attr: string
		@return: an RDFLib URIRef instance
		"""
		assert val != ""
		# fall back on good old traditional URI-s.
		# To be on the safe side, let us use the Python libraries
		if self.parsedBase[0] == "" :
			# base is, in fact, a local file name
			# The following call is just to be sure that some pathological cases when
			# the ':' _does_ appear in the URI but not in a scheme position is taken
			# care of properly...
			key = urlparse.urlsplit(val)[0]
			if key == "" :
				# relative URI, to be combined with local file name:
				return URIRef(self.base + val.strip())
			else :
				# base should be forgotten
				return self._check_create_URIRef(val)
		else :
			# Trust the python library...
			# Well, not quite:-) there is what is, in my view, a bug in the urljoin; in some cases it
			# swallows the '#' or '?' character at the end. This is, clearly, a problem with
			# Semantic Web URI-s
			joined = urlparse.urljoin(self.base, val)
			try :
				if val[-1] != joined[-1] :
					return self._check_create_URIRef(joined + val[-1])
				else :
					return self._check_create_URIRef(joined)
			except :
				return self._check_create_URIRef(joined)

	def _pureURI_with_base(self, attr, val) :
		"""Returns a URI for a 'pure' URI (ie, no CURIE). An error is added to the graph is Safe CURIE is
		used. If the value is empty, the base is returned
		@param val: attribute value to be interpreted
		@type val: string
		@param attr: attribute name
		@type attr: string
		@return: an RDFLib URIRef instance or None if Safe Curis is used
		"""
		if val == "" :
			return URIRef(self.base)
		elif val[0] == '[' and val[-1] == ']' :
			self.options.comment_graph.add_error("Illegal usage of CURIE: %s" % val)
			return None
		else :
			return self._pureURI(attr, val)
		
	def _CURIE_with_base(self, attr, val) :
		"""Returns a URI for a CURIE; if the CURIE is empty, the base value returned.
		@param val: attribute value to be interpreted
		@type val: string
		@param attr: attribute name
		@type attr: string
		@return: an RDFLib URIRef instance 
		"""
		if len(val) == 0 :
			return URIRef(self.base)
		return self._CURIE(attr, val)

	def _CURIE(self, attr, val) :
		"""Returns a URI for a CURIE; if the CURIE is empty, None is returned (ie, I{not} the base)
		@param val: attribute value to be interpreted
		@type val: string
		@param attr: attribute name
		@type attr: string
		@return: an RDFLib URIRef instance or None
		"""
		val.strip()
		if val == "" :
			return None

		safe_curie = False
		if val[0] == '[' :
			# safe curies became almost optional, mainly for backward compatibility reasons
			# Note however, that if a safe curie is asked for, a pure URI is not acceptable.
			# Is checked below, and that is why the safe_curie flag is necessary
			if val[-1] != ']' :
				# that is certainly forbidden: an incomplete safe curie
				self.options.comment_graph.add_error("Illegal CURIE: %s" % val)
				return None
			else :
				val = val[1:-1]
				safe_curie = True
				
		# Get possible blank nodes out of the way
		if len(val) >= 2 and val[0] == "_" and val[1] == ":" :
			# this is a blank node...
			# However, RDF does not allow blank nodes in predicate position,
			# better check
			if attr in ["property", "rel", "rev"] :
				self.options.comment_graph.add_error("Blank node CURIE cannot be used in property position: %s" % val)
				return None
			else :
				return _get_bnode_from_Curie(val[2:])
		
		if val.find(":") == -1 :
			# this is not of a key:lname format. A possibility is that this is simply
			# a term defined via a @vocab/@profile mechanism (explicitly or implicitly)
			# This means that the string starts with a proper alphanumeric character...
			#
			# Note here that the rule for relative URIs is to preceed the name with '/' or something similar
			# hence the reliance on alphanumeric character...
			if val[0].isalpha() :
				return self.vocab.term_to_URI(attr, val.lower())
			else :
				key   = ""
				lname = val
		else :
			key   = val.split(":", 1)[0]
			lname = val.split(":", 1)[1]
			if key == "" :
				# This is the ":blabla" case
				key = self.vocab.xhtml_prefix
				
		# By now we know that
		#   - this is not a predefined term 
		#   - this is not a blank node
		# Consequently, it is either a well defined CURIE, or an absolute or relative URI		
		retval = self.vocab.CURIE_to_URI(key, lname)
		if retval :
			# yep, we got a real URI
			return retval
		elif safe_curie :
			# Oops. The author used a safe curie but the value was not
			# interpreted as such. This should not be the case if a safe curie was used, ie,
			# an error should be raised.
			self.options.comment_graph.add_error("Safe CURIE was used but value does not correspond to a defined CURIE: [%s]" % val)
			return None
		else :
			return self._pureURI(attr, val)

	# -----------------------------------------------------------------------------------------------

	def getURI(self, attr) :
		"""Get the URI(s) for the attribute. The value of the attribute determines whether the value should be
		a pure URI, a CURIE, etc, and whether the return is a single element of a list of those.
		@param attr: attribute name
		@type attr: string
		@return: an RDFLib URIRef instance (or None) or a list of those
		"""
		if self.node.hasAttribute(attr) :
			val = self.node.getAttribute(attr)
			val.strip()
		else :
			if attr in ExecutionContext._list :
				return []
			else :
				return None
		
		# This may raise an exception if the attr has no key. This, actually,
		# should not happen if the code is correct, so I leave this in for debugging purposes
		try :
			func = ExecutionContext._resource_type[attr]
		except :
			# Actually, this should not happen...
			func = ExecutionContext._pureURI
		
		if attr in ExecutionContext._list :
			# Allows for a list
			resources = [ func(self, attr, v) for v in val.split() if v != None ]
			retval = [ r for r in resources if r != None ]
		else :
			retval = func(self, attr, val)
		return retval
	