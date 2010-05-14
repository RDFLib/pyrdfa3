# -*- coding: utf-8 -*-
"""
Parser's execution context (a.k.a. state) object and handling. The state includes:

  - language, retrieved from C{@xml:lang}
  - URI base, determined by <base> (or set explicitly). This is a little bit superfluous, because the current RDFa syntax does not make use of C{@xml:base}; ie, this could be a global value.  But the structure is prepared to add C{@xml:base} easily, if needed.
  - options, in the form of an L{Options<pyRdfa.Options>} instance
  - a separate vocabulary/CURIE handling resource, in the form of an L{Curie<pyRdfa.CURIE>} instance

The execution context object is also used to handle URI-s, CURIE-s, terms, etc.

@summary: RDFa parser execution context
@requires: U{RDFLib package<http://rdflib.net>}
@organization: U{World Wide Web Consortium<http://www.w3.org>}
@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}
"""

"""
$Id: State.py,v 1.14 2010-05-14 11:26:56 ivan Exp $
$Date: 2010-05-14 11:26:56 $
"""

from rdflib.RDF			import RDFNS   as ns_rdf
from rdflib.RDFS		import RDFSNS  as ns_rdfs
from rdflib.RDFS		import comment as rdfs_comment
from rdflib.Namespace	import Namespace
from rdflib.URIRef		import URIRef
from rdflib.Literal		import Literal
from rdflib.BNode		import BNode
from pyRdfa.Options		import Options
from pyRdfa.Utils 		import quote_URI, HostLanguage
from pyRdfa.Curie		import Curie

import re
import random
import urlparse
import urllib


#: list of 'usual' URI schemes; if a URI does not fall into these, a warning may be issued (can be the source of a bug)
usual_schemes = ["doi", "file", "ftp", "gopher", "hdl", "http", "https", "imap", "isbn", "ldap", "lsid",
				 "mailto", "mms", "mstp", "news", "nntp", "prospero", "rsync", "rtmp", "rtsp", "rtspu", "sftp",
				 "shttp", "sip", "sips", "snews", "stp", "svn", "svn+ssh", "telnet", "tel", "urn", "wais"
				]

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
	@ivar curie: vocabulary management class instance
	@type curie: L{Curie.Curie}
	@ivar node: the node to which this state belongs
	@type node: DOM node instance
	"""

	#: list of attributes that allow for lists of values and should be treated as such	
	_list = [ "profile", "rel", "rev", "property", "typeof" ]
	#: mapping table from attribute name to the exact method to retrieve the URI(s).
	_resource_type = {}
	
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
				"href"		:	ExecutionContext._URI,
				"src"		:	ExecutionContext._URI,
				"profile"	:	ExecutionContext._URI,
				"vocab"	    :   ExecutionContext._URI,
			
				"about"		:	ExecutionContext._URIorCURIE, 
				"resource"	:	ExecutionContext._URIorCURIE, 
			
				"rel"		:	ExecutionContext._term_or_URIorCURIE,
				"rev"		:	ExecutionContext._term_or_URIorCURIE,
				"datatype"	:	ExecutionContext._term_or_URIorCURIE,
				"typeof"	:	ExecutionContext._term_or_URIorCURIE,
				"property"	:	ExecutionContext._term_or_URIorCURIE,
			}	
		#-----------------------------------------------------------------
		self.node = node
		
		#-----------------------------------------------------------------
		# Settling the base
		# It is done because it is prepared for a possible future change in direction of
		# accepting xml:base on each element.
		# At the moment, it is invoked with a 'None' at the top level of parsing, that is
		# when the <base> element is looked for (for the HTML cases, that is)
		if inherited_state :
			self.base		= inherited_state.base
			self.options	= inherited_state.options
			# for generic XML versions the xml:base attribute should be handled
			if self.options.host_language == HostLanguage.rdfa_core and node.hasAttribute("xml:base") :
				self.base = node.getAttribute("xml:base")
		else :
			# this is the branch called from the very top

			# this is just to play safe. I believe this should actually not happen...
			if options == None :
				from pyRdfa import Options
				self.options = Options()
			else :
				self.options = options

			self.base = ""
			# handle the base element case for HTML
			if self.options.host_language in [ HostLanguage.xhtml_rdfa, HostLanguage.html_rdfa ] :
				for bases in node.getElementsByTagName("base") :
					if bases.hasAttribute("href") :
						self.base = bases.getAttribute("href")
						continue

			# xml:base is not part of XHTML+RDFa, but it is a valid in core
			if self.options.host_language == HostLanguage.rdfa_core and node.hasAttribute("xml:base") :
				self.base = node.getAttribute("xml:base")		

			# If no local setting for base occurs, the input argument has it
			if self.base == "" :
				self.base = base	

			# This should be set once for the correct handling of warnings/errors
			self.options.comment_graph.set_base_URI(URIRef(quote_URI(base, self.options)))
								
		#-----------------------------------------------------------------
		# this will be used repeatedly, better store it once and for all...
		self.parsedBase = urlparse.urlsplit(self.base)

		#-----------------------------------------------------------------
		# generate and store the local CURIE handling class instance
		self.curie = Curie(self, graph, inherited_state)

		#-----------------------------------------------------------------
		# Settling the language tags
		# @lang has priority over @xml:lang
		# it is a bit messy: the three fundamental modes (xhtml, html, or xml) are all slightly different:-(
		# first get the inherited state's language, if any
		if inherited_state :
			self.lang = inherited_state.lang
		else :
			self.lang = None
			
		if node.hasAttribute("xml:lang") :
			self.lang = node.getAttribute("xml:lang").lower()
			if len(self.lang) == 0 : self.lang = None
		if self.options.host_language in [ HostLanguage.xhtml_rdfa, HostLanguage.html_rdfa ] :
			if node.hasAttribute("lang") :
				self.lang = node.getAttribute("lang").lower()

				# Also check a possible error, namely a clash with xml:lang		
				if node.hasAttribute("xml:lang") and self.lang != node.getAttribute("xml:lang").lower() :
					self.options.comment_graph.add_info("Both xml:lang and lang used on an element with different values; lang prevails. (%s and %s)" % (node.getAttribute("xml:lang"), node.getAttribute("lang")))			

				if len(self.lang) == 0 : self.lang = None
			
		#-----------------------------------------------------------------
		# Set the default namespace. Used when generating XML Literals
		if node.hasAttribute("xmlns") :
			self.defaultNS = node.getAttribute("xmlns")
		elif inherited_state and inherited_state.defaultNS != None :
			self.defaultNS = inherited_state.defaultNS
		else :
			self.defaultNS = None

	#------------------------------------------------------------------------------------------------------------

	def _URI(self, val) :
		"""Returns a URI for a 'pure' URI (ie, no CURIE). The method resolves possible relative URI-s. It also
		checks whether the URI uses an unusual URI scheme (and issues a warning); this may be the result of an
		uninterpreted CURIE...
		@param val: attribute value to be interpreted
		@type val: string
		@return: an RDFLib URIRef instance
		"""
		def check_create_URIRef(uri) :
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
		
		if val == "" :
			return URIRef(self.base)

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
				return check_create_URIRef(val)
		else :
			# Trust the python library...
			# Well, not quite:-) there is what is, in my view, a bug in the urljoin; in some cases it
			# swallows the '#' or '?' character at the end. This is clearly a problem with
			# Semantic Web URI-s
			joined = urlparse.urljoin(self.base, val)
			try :
				if val[-1] != joined[-1] :
					return check_create_URIRef(joined + val[-1])
				else :
					return check_create_URIRef(joined)
			except :
				return check_create_URIRef(joined)

	def _URIorCURIE(self, val) :
		"""Returns a URI for a (safe or not safe) CURIE. In case it is a safe CURIE but the CURIE itself
		is not defined, an error message is issued. 
		@param val: attribute value to be interpreted
		@type val: string
		@return: an RDFLib URIRef instance or None
		"""
		if val == "" :
			return URIRef(self.base)

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

		retval = self.curie.CURIE_to_URI(val)
		if retval == None :
			# the value could not be interpreted as a CURIE, ie, it did not produce any valid
			# URI.
			# The rule says that then the whole value should be considered as a URI
			# except if it was part of a safe Curie. In that case it should be ignored...
			if safe_curie :
				self.options.comment_graph.add_error("Safe CURIE was used but value does not correspond to a defined CURIE: [%s]" % val)
				return None
			else :
				return self._URI(val)
		else :
			# there is an unlikely case where the retval is actually a URIRef with a relative URI. Better filter that one out
			if isinstance(retval, BNode) == False and urlparse.urlsplit(str(retval))[0] == "" :
				# yep, there is something wrong, a new URIRef has to be created:
				return URIRef(self.base+str(retval))
			else :
				return retval

	def _term_or_URIorCURIE(self, val) :
		"""Returns a URI either for a term or for a CURIE. The value must be an NCNAME to be handled as a term; otherwise
		the method falls back on a URI or CURIE.
		@param val: attribute value to be interpreted
		@type val: string
		@return: an RDFLib URIRef instance or None
		"""
		# This case excludes the pure base, ie, the empty value
		if val == "" :
			return None
		from Curie import ncname
		if ncname.match(val) :
			# This is a term, must be handled as such...
			return self.curie.term_to_URI(val)
		else :
			return self._URIorCURIE(val)

	# -----------------------------------------------------------------------------------------------

	def getURI(self, attr) :
		"""Get the URI(s) for the attribute. The name of the attribute determines whether the value should be
		a pure URI, a CURIE, etc, and whether the return is a single element of a list of those. This is done
		using the L{ExecutionContext._resource_type} table.
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
		# should not happen if the code is correct, but it does not harm having it here...
		try :
			func = ExecutionContext._resource_type[attr]
		except :
			# Actually, this should not happen...
			func = ExecutionContext._URI
		
		if attr in ExecutionContext._list :
			# Allows for a list
			resources = [ func(self, v.strip()) for v in val.split() if v != None ]
			retval = [ r for r in resources if r != None ]
		else :
			retval = func(self, val.strip())
		return retval
