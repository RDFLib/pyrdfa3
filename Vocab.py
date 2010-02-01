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
from pyRdfa.Options		import Options, GENERIC_XML, XHTML_RDFA, HTML5_RDFA
from pyRdfa.Utils 		import quote_URI

debug = True

import re
import random
import urlparse

_WARNING_VERSION = "RDFa profile or RFDa version has not been set (for a correct identification of RDFa). This is not a requirement for RDFa, but it is advised to use one of those nevertheless. Note that in the case of HTML5, the DOCTYPE setting may not work..."

usual_protocols = ["http", "https", "mailto", "ftp", "urn", "gopher", "tel", "ldap", "doi",
				   "news", "file", "hdl", "imap", "mms" "nntp", "prospero", "rsync", "rtsp",
				   "rtspu", "sftp", "shttp", "sip", "sips", "snews", "svn", "svn+ssh", "tag", "telnet", "wais"]

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

_default_namespaces = {
	"xsd"	: 'http://www.w3.org/2001/XMLSchema#',
	"rdf"	: ns_rdf,
	"rdfs"	: ns_rdfs,
}


class Vocab :
	def __init__(self, state, graph, inherited_state) :
		"""Initialize the vocab bound to a specific state. 
		@param state: the state to which this vocab instance belongs to
		@param graph: the RDF graph being worked on
		@param inherited_state: the state inherited by the current state. 'None' if this is the top level state.
		"""
		self.state = state
		
		#-----------------------------------------------------------------
		# the locally defined namespaces
		dict = {}
		# If this is the vocab on the top (signalled by inherited_state being None) then default namespace
		# are added to the dictionary right away.
		if inherited_state is None :
			for k in _default_namespaces :
				val = _default_namespace[k]
				if isinstance(val, Namespace) :
					dict[k] = val
				else :
					dict[k] = Namespace(k)
		
		# handle the namespaces; at the moment using the xmlns: syntax
		# First get the local xmlns declarations/namespaces stuff.
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
						uri = quote_URI(attr.value, self.options)
						# 1. create a new RDFLib Namespace entry
						ns = Namespace(uri)
						# 2. 'bind' it in the current graph to
						# get a nicer output
						graph.bind(prefix, uri)
						# 3. Add an entry to the dictionary
						dict[prefix] = ns

		# See if anything has been collected at all.
		# If not, the namespaces of the incoming state is
		# taken over by reference. Otherwise that is copied to the
		# the local dictionary
		self.ns = {}
		if len(dict) == 0 and inherited_state :
			self.ns = inherited_state.vocab.ns
		else :
			if inherited_state :
				self.ns.update(inherited_state.vocab.ns)
				# copying the newly found namespace, possibly overwriting
				# incoming values
				self.ns.update(dict)
			else :
				self.ns = dict
				
		# see if the xhtml core vocabulary has been set
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
			graph.bind(self.xhtml_prefix, XHTML_URI)

		# extra tricks for unusual usages...
		# if the 'rdf' prefix is not used, it is artificially added...
		# Hm, this is illegal, so it is commented out...
		#if "rdf" not in self.ns :
		#	self.ns["rdf"] = ns_rdf
		#if "rdfs" not in self.ns :
		#	self.ns["rdfs"] = ns_rdfs

		# get the keyword list set up, and put the default XHTML elements onto it:
		self.keywords = {}
		if self.options.host_language != GENERIC_XML :
			relrev = ["rel","rev"]
			for key in _predefined_rel : self.keywords[key] = (URIRef(XHTML_URI+key),relrev)

	def CURIE_to_URI(self, prefix, lname) :
		"""CURIE to URI mapping. Note that this method does not take care of the
		blank node management, ie, when the key is '_', this is something that
		has to be taken care of summer higher up.
		@param prefix: the prefix defined for the CURIE
		@param lname: local name
		"""
		if prefix in self.ns :
			# yep, we have a CURIE here!
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
		
