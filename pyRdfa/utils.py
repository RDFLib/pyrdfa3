# -*- coding: utf-8 -*-
"""
Various utilities for pyRdfa.

Most of the utilities are straightforward.

@summary: RDFa core parser processing step
@requires: U{RDFLib package<http://rdflib.net>}
@requires: U{httpheader<http://deron.meranda.us/python/httpheader/>}. To make distribution easier this module (single file) is added to the distributed tarball.
@organization: U{World Wide Web Consortium<http://www.w3.org>}
@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}


"""

"""
$Id: utils.py,v 1.3 2011/11/14 14:02:48 ivan Exp $
$Date: 2011/11/14 14:02:48 $
"""
import os, os.path, sys, imp, datetime
import urllib, urlparse, urllib2
import httpheader

import rdflib
if rdflib.__version__ >= "3.0.0" :
	from rdflib	import RDF as ns_rdf
else :
	from rdflib.RDF	import RDFNS  as ns_rdf

from pyRdfa.host import HostLanguage, preferred_suffixes
from types import *

#########################################################################################################
# Handling URIs
class URIOpener :
	"""A wrapper around the urllib2 method to open a resource. Beyond accessing the data itself, the class
	sets a number of instance variable that might be relevant for processing.
	The class also adds an accept header to the outgoing request, namely
	text/html and application/xhtml+xml (unless set explicitly by the caller).
	
	The content type is either set by the HTTP return. If not set by the server, some common
	suffixes are used (see L{preferred_suffixes}) to set the content type (this is really of importance
	for file:/// URI-s). If none of these works, the content type is empty.
		
	Interpretation of the content type for the return is done by Deron Meranda's <http://deron.meranda.us/>
	httpheader module.
	
	@ivar data: the real data, ie, a file-like object
	@ivar headers: the return headers as sent back by the server
	@ivar content_type: the content type of the resource or the empty string, if the content type cannot be determined
	@ivar location: the real location of the data (ie, after possible redirection and content negotiation)
	@ivar last_modified_date: sets the last modified date if set in the header, None otherwise
	@ivar expiration_date: sets the expiration date if set in the header, I{current UTC plus one day} otherwise (this is used for caching purposes, hence this artificial setting)
	"""
	CONTENT_LOCATION	= 'Content-Location'
	CONTENT_TYPE		= 'Content-Type'
	LAST_MODIFIED		= 'Last-Modified'
	EXPIRES				= 'Expires'
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
				ct = httpheader.content_type(self.headers[URIOpener.CONTENT_TYPE])
				self.content_type = ct.media_type
				if 'charset' in ct.parmdict :
					self.charset = ct.parmdict['charset']
				else :
					self.charset = None
				# print
			else :
				# check if the suffix can be used for the content type; this may be important
				# for file:// type URI or if the server is not properly set up to return the right
				# mime type
				self.charset = None
				self.content_type = ""
				for suffix in preferred_suffixes.keys() :
					if name.endswith(suffix) :
						self.content_type = preferred_suffixes[suffix]
						break
			
			if URIOpener.CONTENT_LOCATION in self.headers :
				self.location = urlparse.urljoin(self.data.geturl(),self.headers[URIOpener.CONTENT_LOCATION])
			else :
				self.location = name
			
			self.expiration_date = datetime.datetime.utcnow() + datetime.timedelta(days=1)
			if URIOpener.EXPIRES in self.headers :
				try :
					# Thanks to Deron Meranda for the HTTP date conversion method...
					self.expiration_date = httpheader.parse_http_datetime(self.headers[URIOpener.EXPIRES])
				except :
					# The Expires date format was wrong, sorry, forget it...
					pass

			self.last_modified_date = None
			if URIOpener.LAST_MODIFIED in self.headers :
				try :
					# Thanks to Deron Meranda for the HTTP date conversion method...
					self.last_modified_date = httpheader.parse_http_datetime(self.headers[URIOpener.LAST_MODIFIED])
				except :
					# The last modified date format was wrong, sorry, forget it...
					pass
				
		except urllib2.HTTPError, e :
			from pyRdfa import HTTPError
			raise HTTPError('%s' % e, e.code)
		except Exception, e :
			from pyRdfa import RDFaError
			raise RDFaError('%s' % e)

#########################################################################################################

# 'safe' characters for the URI quoting, ie, characters that can safely stay as they are. Other 
# special characters are converted to their %.. equivalents for namespace prefixes
_unquotedChars = ':/\?=#~'
_warnChars     = [' ','\n','\r','\t']

def quote_URI(uri, options = None) :
	"""
	'quote' a URI, ie, exchange special characters for their '%..' equivalents. Some of the characters
	may stay as they are (listed in L{_unquotedChars}. If one of the characters listed in L{_warnChars} 
	is also in the uri, an extra warning is also generated.
	@param uri: URI
	@param options: 
	@type options: L{Options<pyRdfa.Options>}
	"""
	from pyRdfa import err_unusual_char_in_URI
	suri = uri.strip()
	for c in _warnChars :
		if suri.find(c) != -1 :
			if options != None :
				options.add_warning(err_unusual_char_in_URI % suri)
			break
	return urllib.quote(suri, _unquotedChars)
	
#########################################################################################################
	
def create_file_name(uri) :
	"""
	Create a suitable file name from an (absolute) URI. Used, eg, for the generation of a file name for a cached vocabulary file.
	"""
	suri = uri.strip()
	final_uri = urllib.quote(suri,_unquotedChars)
	# Remove some potentially dangereous characters
	return final_uri.replace(' ','_').replace('%','_').replace('-','_').replace('+','_').replace('/','_').replace('?','_').replace(':','_').replace('=','_').replace('#','_')

#########################################################################################################
def has_one_of_attributes(node,*args) :
	"""
	Check whether one of the listed attributes is present on a (DOM) node.
	@param node: DOM element node
	@param args: possible attribute names
	@return: True or False
	@rtype: Boolean
	"""
	if len(args) == 0 :
		return None
	if isinstance(args[0], (tuple, list)) :
		rargs = args[0]
	else :
		rargs = args
	
	return True in [ node.hasAttribute(attr) for attr in rargs ]

#########################################################################################################
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
			
#########################################################################################################

def dump(node) :
	"""
	This is just for debug purposes: it prints the essential content of the node in the tree starting at node.

	@param node: DOM node
	"""
	print node.toprettyxml(indent="", newl="")
	
	
	
##################
# Testing
if __name__ == '__main__':
	u = URIOpener("http://www.ivan-herman.net/foaf.html")
	print u.charset
	
