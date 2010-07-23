# -*- coding: utf-8 -*-
"""
Various utilities for pyRdfa.

Most of the utilities are straightforward, except for the caching module whose usage that is described in the class description. 

@summary: RDFa core parser processing step
@requires: U{RDFLib package<http://rdflib.net>}
@organization: U{World Wide Web Consortium<http://www.w3.org>}
@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}
"""

"""
$Id:$
$Date:$
"""
import os, os.path, sys, imp
import urllib, urlparse, urllib2
import httpheader

import rdflib
if rdflib.__version__ >= "3.0.0" :
	from rdflib	import RDF as ns_rdf
else :
	from rdflib.RDF	import RDFNS  as ns_rdf

class HostLanguage :
	"""An enumeration style class: recognized host language types for RDFa. Some processing details may also
	depend on these host languages."""
	(rdfa_core, xhtml_rdfa, html_rdfa) = range(0,3)
	
class MediaTypes :
	"""An enumeration style class: some common media types (better have them at one place to avoid misstyping...)"""
	rdfxml 	= 'application/rdf+xml'
	turtle 	= 'text/turtle'
	html	= 'text/html'
	xhtml	= 'application/xhtml+xml'
	svg		= 'application/svg+xml'
	smil	= 'application/smil+xml'
	xml		= 'application/xml'
	nt		= 'text/plain'
	
#: mapping from (some) content types to RDFa host languages. This may control the exact processing or at least the default profile (see below)...
content_to_host_language = {
	MediaTypes.html		: HostLanguage.html_rdfa,
	MediaTypes.xhtml	: HostLanguage.xhtml_rdfa,
	MediaTypes.xml		: HostLanguage.rdfa_core,
	MediaTypes.smil		: HostLanguage.rdfa_core,
	MediaTypes.svg		: HostLanguage.rdfa_core,
}
	
#: default profiles for some of the host languages
default_profiles = {
	HostLanguage.xhtml_rdfa	: "http://www.w3.org/1999/xhtml",
	HostLanguage.html_rdfa 	: "http://www.w3.org/1999/xhtml",
}

#: mapping preferred suffixes to media types...
preferred_suffixes = {
	".rdf"		: MediaTypes.rdfxml,
	".ttl"		: MediaTypes.turtle,
	".n3"		: MediaTypes.turtle,
	".owl"		: MediaTypes.rdfxml,
	".html"		: MediaTypes.html,
	".xhtml"	: MediaTypes.xhtml,
	".svg"		: MediaTypes.svg,
	".smil"		: MediaTypes.smil,
	".xml"		: MediaTypes.xml,
	".nt"		: MediaTypes.nt
}

#########################################################################################################
# Handling URIs
class URIOpener :
	"""A wrapper around the urllib2 method to open a resource. Beyond accessing the data itself, the class
	sets a number of instance variable that might be relevant for processing.
	The class also adds an accept header to the outgoing request, namely
	text/html and application/xhtml+xml (unless set explicitly by the caller).
	
	@ivar data: the real data, ie, a file-like object
	@ivar headers: the return headers as sent back by the server
	@ivar content_type: the 'CONTENT_TYPE' header or, if not set by the server, the empty string
	@ivar location: the real location of the data (ie, after possible redirection and content negotiation)
	"""
	CONTENT_LOCATION	= 'Content-Location'
	CONTENT_TYPE		= 'Content-Type'
	def __init__(self, name, additional_headers = {}) :
		"""
		@param name: URL to be opened
		@keyword additional_headers: additional HTTP request headers to be added to the call
		"""
		try :
			req = urllib2.Request(url=name)

			for key in additional_headers :
				req.add_header(key, additional_headers[key])
			if 'Accept' not in additional_headers :
				req.add_header('Accept', 'text/html, application/xhtml+xml')
				
			self.data		= urllib2.urlopen(req)
			self.headers	= self.data.info()
			
			if URIOpener.CONTENT_TYPE in self.headers :
				# The call below will remove the possible media type parameters, like charset settings
				self.content_type = httpheader.content_type(self.headers[URIOpener.CONTENT_TYPE]).media_type
			else :
				# check if the suffix can be used for the content type; this may be important
				# for file:// type URI or if the server is not properly set up to return the right
				# mime type
				self.content_type = ""
				for suffix in preferred_suffixes.keys() :
					if name.endswith(suffix) :
						self.content_type = preferred_suffixes[suffix]
						break
			
			if URIOpener.CONTENT_LOCATION in self.headers :
				self.location = urlparse.urljoin(self.data.geturl(),self.headers[URIOpener.CONTENT_LOCATION])
			else :
				self.location = name
		except urllib2.HTTPError, e :
			from pyRdfa import HTTPError
			raise HTTPError('%s' % e, e.code)
		except Exception, e :
			from pyRdfa import RDFaError
			raise RDFaError('%s' % e)

#########################################################################################################
# Handling Cached URIs
class CachedURIOpener(URIOpener) :
	"""
	Implementation of a simple chaching mechanism for opening URI-s. The fundamental idea is that some URI-s
	have a cached version (or an equivalent) version in the local file space, and that file is loaded instead of
	getting to the Web with another request.
	
	The essence is to find a dictionary that maps URI-s to local file names. Instead of hardcoding the
	location of the chached files, an environment variable isued; this environment variable is
	an input argument to the class' constructor (C{cached_env}).
	
	The environment variable plays two roles:
	
	 - the value of the environment variable provides a directory in the local file space to locate cached files
	 - the environment variable itself servers as a Python module name; that module, when imported, should include
	 the 'index' dictionary to map URI-s to cached files.
	 
	For example, if the cached environment variable is C{cached_profiles}", then
	
	 - the environment variable C{cached_profiles" may give C{/Users/ivan/W3C/WWW/2007/08/pyRdfa/profiles}
	 - the module C{/Users/ivan/W3C/WWW/2007/08/pyRdfa/profiles/cached_profile.py} is (dynamically) imported
	 - the index dictionary in that profile may contain the entry::
	"http://www.w3.org/2007/08/pyRdfa/profiles/cc.html" : "cc.html"
	
	meaning that if the requested URI is::
	"http://www.w3.org/2007/08/pyRdfa/profiles/cc.html"
	
	the class loads the following local file instead::
	/Users/ivan/W3C/WWW/2007/08/pyRdfa/profiles/cc.html
	
	Furthermore, the class may be initialized with additional (HTTP) Accept headers. This means that if the
	index dictionary does not contain an entry for the incoming URI, suffixes for the content types in the Accept
	headers will be used to check again (in case that content type is known). Ie, if the requested URI is::
	"http://www.w3.org/2007/08/pyRdfa/profiles/cc"
	
	and the additonal accept header includes 'text/html' then the::
	"http://www.w3.org/2007/08/pyRdfa/profiles/cc.html"
	
	is also checked. This is a crude local imitation of HTTP content negotiation.
	
	Obviously, if the cache mechanism fails at any place in finding a local copy, the superclass, ie, a proper
	HTTP request, is used.
	"""
	loaded_modules = {}
	def __init__(self, uri, additional_headers = {}, cached_env = "") :
		resolved = False
		if cached_env in CachedURIOpener.loaded_modules :
			# This module has already been imported once
			(self.index, self.base) = CachedURIOpener.loaded_modules[cached_env]
			resolved = self._resolve_cache(uri, additional_headers)
		else :
			# let us try to import the module
			if cached_env in os.environ :
				self.base = os.environ[cached_env]
				if self.base not in sys.path :
					sys.path.insert(0, self.base)
				try :
					# These calls do a dynamic import; ie, python magic is going on here...:-)
					(f,p,d) = imp.find_module(cached_env)	
					imp.load_module(cached_env,f,p,d)
					m = sys.modules[cached_env]
					self.index = m.__dict__['index']
					CachedURIOpener.loaded_modules[cached_env] = (self.index, self.base)
					resolved = self._resolve_cache(uri, additional_headers)
				except :
					pass
					#(type,value,traceback) = sys.exc_info()
					#print value
					# if anything happened here, just forget about caching...
							
		# If the resolved flag has been set then we do not have anything else to do
		# and the attributes for self.location, self.content_type, etc, have been set.
		# Otherwise we fall back on a real URI opening
		if not resolved :
			URIOpener.__init__(self, uri, additional_headers)
		else :
			self.location = uri
		
	def _resolve_cache(self, uri, additional_headers) :
		def headersort(x,y) :
			if x[1] < y[1] :
				return 1
			elif x[1] > y[1] :
				return -1
			else :
				return 0

		# There can be a bunch of exceptions raised by, eg, invalid headers; these are all simply swallowed for now
		try :
			# See which are the acceptable media types for the caller
			# Suffix type list is set to a ([suffixlist],media_type), highest priority first
			suffix_type_list = []
			if 'Accept' in additional_headers :
				# Get the accept headers, with possibly rearranging them based on the 'q' values
				headers = httpheader.parse_accept_header(additional_headers['Accept'])
				headers.sort(headersort)
				for ctype in [str(x[0]) for x in headers] :
					# Several suffixes may share media types, like owl and rdf...
					suffxs = []
					for sffx in preferred_suffixes.keys() :
						if preferred_suffixes[sffx] == ctype :
							suffxs.append(sffx)
					suffix_type_list.append((suffxs, ctype))
					
			# First, attempt to resolve the incoming URI as is
			if self._resolve_uri(uri, None) :
				# got it!
				return True
			else :
				for suffxs, ctype in suffix_type_list :
					for sufx in suffxs :
						retval = self._resolve_uri(uri+sufx, ctype)
						if retval == True :
							return True
			# Sadly, there is no cache
			return False
		except :
			return False

	def _resolve_uri(self, uri, content_type) :
		if uri in self.index :
			fname = self.index[uri]
			# This file name should be combined with the base
			try :
				self.data = file(os.path.join(self.base, fname))
				if content_type :
					self.content_type = content_type
				else :
					# try to guess based on the suffix
					# this should be the case when the original URI
					# included a suffix already
					for key in preferred_suffixes.keys() :
						if uri.endswith(key) :
							self.content_type = preferred_suffixes[key]
				return True
			except :
				return False
		else :
			return False

#########################################################################################################

# 'safe' characters for the URI quoting, ie, characters that can safely stay as they are. Other 
# special characters are converted to their %.. equivalents for namespace prefixes
_unquotedChars = ':/\?=#~'
_warnChars     = [' ','\n','\r','\t']

def quote_URI(uri, options) :
	"""
	'quote' a URI, ie, exchange special characters for their '%..' equivalents. Some of the characters
	may stay as they are (listed in L{_unquotedChars}. If one of the characters listed in L{_warnChars} 
	is also in the uri, an extra warning is also generated.
	@param uri: URI
	@param options: 
	@type options: L{Options<pyRdfa.Options>}
	"""
	suri = uri.strip()
	for c in _warnChars :
		if suri.find(c) != -1 :
			if options != None :
				options.processor_graph.add_warning('Unusual character in uri:%s; possible error?' % suri)
			break
	return urllib.quote(suri, _unquotedChars)

def traverse_tree(node, func) :
	"""Traverse the whole element tree, and perform the function C{func} on all the elements.
	@param node: DOM element node
	@param func: function to be called on the node. Input parameter is a DOM Element Node. If the function returns a boolean True, the recursion is stopped.
	"""
	if func(node) :
		return

	for n in node.childNodes :
		if n.nodeType == node.ELEMENT_NODE :
			traverse_tree(n, func)

def rdf_prefix(html) :
	"""Extract the top level prefix used for RDF. Although in most cases it is
	'rdf', we cannot be sure...
	@param html: the DOM Node for the HTML element
	@return: prefix name
	"""
	dict = {}
	for i in range(0,html.attributes.length) :
		attr = html.attributes.item(i)
		if attr.prefix == "xmlns" :
			# yep, there is a namespace setting
			key = attr.localName
			if key != "" :
				# exclude the top level xmlns setting...
				uri = attr.value
				if uri == ns_rdf.__str__() :
					return key

	# if it has not been set, the system will set it for 'rdf'...
	return 'rdf'

def dump(node) :
	"""
	This is just for debug purposes: it prints the essential content of the node in the tree starting at node.

	@param node: DOM node
	"""
	def _printNode(node) :
		"""
		Print the content of the DOM node's attributes (just a crude print, nothing fancy)
		@param node: DOM node
		"""
		debugStr = 'Node: %s, typeof="%s" property="%s" rel="%s" rev="%s" resource="%s" about="%s"' % (node.tagName,node.getAttribute("typeof"),node.getAttribute("property"),node.getAttribute("rel"),node.getAttribute("rev"),node.getAttribute("resource"),node.getAttribute("about"))
		print debugStr
		return False

	for i in range(0,node.attributes.length) :
		attr = node.attributes.item(i)
		if attr.prefix == "xmlns" :
			print "... %s:%s='%s'" % (attr.prefix,attr.localName,attr.value)

	traverse_tree(node,_printNode)
