# -*- coding: utf-8 -*-
"""
Various Utilities

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
import urllib
from rdflib.RDF import RDFNS  as ns_rdf
import urlparse, urllib2
import httpheader


# Some common media types, better have them at one place to avoid misstyping...
RDFXML_MT 	= 'application/rdf+xml'
TURTLE_MT 	= 'text/turtle'
HTML_MT		= 'text/html'
XHTML_MT	= 'application/xhtml+xml'
SVG_MT		= 'application/svg+xml'
XML_MT		= 'application/xml'
NT_MT		= 'text/plain'

#: mapping suffixes to media types...
preferred_suffixes = {
	"rdf"	: RDFXML_MT,
	"ttl"	: TURTLE_MT,
	"n3"	: TURTLE_MT,
	"owl"	: RDFXML_MT,
	"html"	: HTML_MT,
	"xhtml"	: XHTML_MT,
	"svg"	: SVG_MT,
	"xml"	: XML_MT,
	"nt"	: NT_MT
}

#########################################################################################################
# Handling URIs
class URIOpener :
	"""A wrapper around the urllib2 method to open a resource. Beyond accessing the data itself, the class
	sets a number of instance variable that might be relevant for processing.
	The class also adds an accept header to the outgoing request, namely text/html and application/xhtml+xml (unless set explicitly by the caller).
	
	@ivar data : the real data, ie, a file-like object
	@ivar headers : the return headers as sent back by the server
	@ivar content_type : the 'CONTENT_TYPE' header or, if not set by the server, the empty string
	@ivar location : the real location of the data (ie, after possible redirection and content negotiation)
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
		except Exception, msg :
			from pyRdfa import RDFaError
			raise RDFaError,' %s' % msg


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
				options.comment_graph.add_warning('Unusual character in uri:%s; possible error?' % suri)
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
