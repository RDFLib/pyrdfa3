# -*- coding: utf-8 -*-
"""
RDFa parser, also referred to as a "RDFa Distiller". It is
deployed, via a CGI front-end, on the U{W3C RDFa Distiller page<http://www.w3.org/2007/08/pyRdfa/>}.

For details on RDFa, the reader should consult the U{RDFa syntax document<http://www.w3.org/TR/rdfa-syntax>}. This package
can be downloaded U{as a compressed tar file<http://dev.w3.org/2004/PythonLib-IH/dist/pyRdfa.tar.gz>}. The
distribution also includes the CGI front-end and a separate utility script to be run locally.


(Simple) Usage
==============

From a Python file, expecting an RDF/XML pretty printed output::
 from pyRdfa import processFile
 print processFile('filename.html')

Other output formats (eg, turtle) are also possible. There is a L{separate entry for CGI calls<processURI>} as well
as for L{processing an XML DOM Tree directly<parseRDFa>} (instead of a file).

Return formats
--------------

By default, the output format for the graph is RDF/XML. At present, the following formats are also available:

 - "xml": RDF/XML.
 - "turtle": Turtle format.
 - "nt": N triples

Options
=======

The package also implements some optional features that are not fully part of the RDFa syntax. At the moment these are:

 - extra warnings and information (eg, missing C{@profile, @version} attribute or DTD, possibly erronous CURIE-s) are added to the output graph
 - possibility that plain literals are normalized in terms of white spaces. Default: false. (The RDFa specification requires keeping the white spaces and leave applications to normalize them, if needed)
 - extra, built-in transformers are executed on the DOM tree prior to RDFa processing (see below)

Options are collected in an instance of the L{Options} class and passed to the processing functions as an extra argument. Eg,
if extra warnings are required, the code may be::
 from pyRdfa import processFile, Options
 options = Options(warnings=True)
 print processFile('filename.html',options=options)

Transformers
============

The package uses the concept of 'transformers': the parsed DOM tree is possibly
transformed before performing the real RDFa processing. This transformer structure makes it possible to
add additional 'services' without distoring the core code of RDFa processing. (Ben Adida referred to these as "hGRDDL"...)

Some transformations are included in the package and can be used at invocation. These are:

 - 'ol' and 'ul' elements are possibly transformed to generate collections or containers. See L{transform.ContainersCollections} for further details.
 - The 'name' attribute of the 'meta' element is copied into a 'property' attribute of the same element
 - Interpreting the 'openid' references in the header. See L{transform.OpenID} for further details.
 - Implementing the Dublin Core dialect to include DC statements from the header.  See L{transform.DublinCore} for further details.
 - Use the C{@prefix} attribute as a possible replacement for the C{xmlns} formalism. See L{transform.Prefix} for further details.
 - Use the C{@var-xx} pattern instead of the official attribute names; this may be the way to get around HTML5’s extension issues. See  L{transform.Prefix} for further details.

The user of the package may refer to those and pass it on to the L{processFile} call via an L{Options} instance. The caller of the
package may also add his/her transformer modules. Here is a possible usage with the 'openid' transformer
added to the call::
 from pyRdfa import processFile, Options
 from pyRdfa.transform.OpenID import OpenID_transform
 options = Options(transformers=[OpenID_transform])
 print processFile('filename.html',options=options)

In the case of a call via a CGI script, these built-in transformers can be used via extra flags, see L{processURI} for further details.

Note that the current option instance is passed to all transformers as extra parameters. Extensions of the package
may make use of that to control the transformers, if necessary.

HTML5
=====

The U{RDFa syntax<http://www.w3.org/TR/rdfa-syntax>} is defined in terms of XHTML. However, in future,
U{HTML5<http://www.w3.org/TR/html5/>} may also be considered as a carrier language for RDFa. Therefore, the distiller can be started up in two different modes:
 - in a "strict" XML mode the input is parsed by an XML parser (Python's xml minidom), and an exception is raised if the parser experiences problems
 - in a "lax" mode, meaning that if the XML parser has problems, then there is a fallback on an U{HTML5 parser<http://code.google.com/p/html5lib/>} to parse the input. This also covers HTML4 "tag soup" files.

The CGI script's setup uses "lax" as a default; a separate flag can be used to force the system to use strict mode  (see L{processURI}).

SVG 1.2 (and XML host languages in general)
===========================================

The U{SVG 1.2 Tiny<http://www.w3.org/TR/SVGMobile12/>} specification has also adopted RDFa as a means to add metadata to SVG content.
This means that RDFa attributes can also be used to express metadata. There are, however, two subtle differences when using RDFa with XHTML
or with SVG, namely:

 - SVG also has a more "traditional" way of adding RDF metadata to a file, namely by directly including RDF/XML into SVG (as a child of a C{metadata} element. According to the specification of SVG, the graphs extracted from an SVG file and originating from such embedded contents and the graph extracted via RDFa attributes should be merged to yield the output RDF graph.
 - whereas XHTML1.1 does I{not} use the C{xml:base} functionality, SVG (and generic XML applications) does.

By default, the distiller runs in XHTML 'mode', ie, these two extra features are not implemented.
However, if an L{Options} instance is created with xhtml=False, distiller considers that the underlying host language is pure XML,
and these two additional features are also implemented. An example would be::
 from pyRdfa import processFile, Options
 options = Options(xhtml=False)
 print processFile('filename.svg',options=options)

The CGI interface can also be used to set this option (see L{processURI}). Note that the 'lax' parsing is (obviously) disallowed in this case.


@summary: RDFa parser (distiller)
@requires: Python version 2.5 or up
@requires: U{RDFLib<http://rdflib.net>}
@requires: U{html5lib<http://code.google.com/p/html5lib/>} for the HTML5 parsing; note possible dependecies on Python's version on the project's web site
@requires: U{httpheader<http://deron.meranda.us/python/httpheader/>}. To make distribution easier this module (single file) is added to the distributed tarball.
@organization: U{World Wide Web Consortium<http://www.w3.org>}
@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}

@var builtInTransformers: list of built-in transformers that are unconditionally executed.
"""

"""
$Id: __init__.py,v 1.11 2010-02-19 12:34:49 ivan Exp $ $Date: 2010-02-19 12:34:49 $

Thanks to Peter Mika who was probably my most prolific tester and bug reporter...

Thanks to Sergio Fernandez to amend the list of non-escaped characters for URI-s (ie, hunted down the necessary steps
as a reaction to his practical problem)

Thanks to Wojciech Polak, who suggested (and provided some example code) to add the feature of
using external file-like objects as input, too (the main usage being to use stdin).

Thanks to Elias Torrez, who provided with the idea and patches to interface to the HTML5 parser.

"""

__version__ = "3.0"
__author__  = 'Ivan Herman'
__contact__ = 'Ivan Herman, ivan@w3.org'
__license__ = u'W3C® SOFTWARE NOTICE AND LICENSE, http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231'

import sys, StringIO
from rdflib.Graph		import Graph
from rdflib.URIRef		import URIRef
from rdflib.BNode		import BNode
from rdflib.Namespace	import Namespace
from rdflib.RDF			import RDFNS  as ns_rdf
from rdflib.RDFS		import RDFSNS as ns_rdfs

from pyRdfa.State				import ExecutionContext
from pyRdfa.Parse				import parse_one_node
from pyRdfa.Options				import Options, DIST_NS, _add_to_comment_graph, ERROR, GENERIC_XML, XHTML_RDFA, HTML5_RDFA
from pyRdfa.transform.HeadAbout	import head_about_transform

import xml.dom.minidom
import urlparse, urllib


debug = True

#: current "official" version of RDFa that this package implements
rdfa_current_version	= 1.1

#: List of built-in transformers that are to be run regardless, because they are part of the RDFa spec
builtInTransformers = [
	head_about_transform
]

# Exception handling. Essentially, all the different exceptions are re-packaged into
# separate exception class, to allow for an easier management on the user level
class RDFaError(Exception) :
	"""Just a wrapper around the local exceptions. It does not add any new functionality to the
	Exception class."""
	pass

#########################################################################################################
# Handling URIs
class _MyURLopener(urllib.FancyURLopener) :
	"""This class raises an exception if an authentication is required to access a specific URI; for the time being,
	I have not found a proper way of handling that case for a CGI script... For all other features (eg, redirection), it
	relies on the superclass, ie, the official Python distribution class.

	Also, the class sets an accept header to the outgoing request, namely text/html and application/xhtml+xml
	"""
	def __init__(self) :
		urllib.FancyURLopener.__init__(self)
		self.addheader('Accept','text/html, application/xhtml+xml')

	def prompt_user_passwd(self, host, realm) :
		"""This is the method to be provided for the superclass in case authentication is required. At the moment, it
		simply raises an RDFError exception.
		@raise RDFaError: for authentication requests.
		"""
		raise RDFaError,'unfortunately, the distiller cannot handle URI authentication'
	
#########################################################################################################
class pyRdfa :
	"""Main processing class for the distiller"""
	#: For some doctype and element name combinations an automatic switch to an input mode is done
	_switch = {
		("http://www.w3.org/1999/xhtml","html") : XHTML_RDFA,
		("http://www.w3.org/2000/svg","svg")    : GENERIC_XML
	}
	
	def __init__(self, options = None, base = "") :
		"""
		@keyword options: Options for the distiller
		@type options: L{Options}
		@keyword base: URI for the default "base" value (usually the URI of the file to be processed)
		"""
		if options == None :
			self.options = Options()
		else :
			self.options = options
		self.base    = base
		self.xml_serializer_registered		= False
		self.turtle_serializer_registered	= False
		self.xml_serializer_name			= "my-rdfxml"
		self.turtle_serializer_name			= "my-turtle"
		
	
	def _get_input(self, name) :
		"""
		Trying to guess whether "name" is a URI, a string; it then tries to open these as such accordingly,
		returning a file-like object. If name is a plain string then it returns the input argument (that should
		be, supposidly, a file-like object already)
		@param name: identifier of the input source
		@type name: string or a file-like object
		@return: a file like object if opening "name" is possible and successful, "name" otherwise
		"""
		if isinstance(name, basestring) :
			# check if this is a URI, ie, if there is a valid 'scheme' part
			# otherwise it is considered to be a simple file
			if urlparse.urlparse(name)[0] != "" :
				retval = _MyURLopener().open(name)
			else :
				retval = file(name)
			self.base = name
			return retval
		else :
			return name
		
		
	def _register_XML_serializer(self) :
		"""The default XML Serializer of RDFlib is buggy, mainly when handling lists. An L{own version<serializers.PrettyXMLSerializer>} is
		registered in RDFlib and used in the rest of the package.
		"""
		if not self.xml_serializer_registered :
			from rdflib.plugin import register
			from rdflib.syntax import serializer, serializers
			register(self.xml_serializer_name, serializers.Serializer, "pyRdfa.serializers.PrettyXMLSerializer", "PrettyXMLSerializer")
			self.xml_serializer_registered = True

	def _register_Turtle_serializer(self) :
		"""The default Turtle Serializers of RDFlib is buggy and not very nice as far as the output is concerned.
		An L{own version<serializers.TurtleSerializer>} is registered in RDFLib and used in the rest of the package.
		"""
		if not self.turtle_serializer_registered :
			from rdflib.plugin import register
			from rdflib.syntax import serializer, serializers
			register(self.turtle_serializer_name, serializers.Serializer, "pyRdfa.serializers.TurtleSerializer", "TurtleSerializer")
			self.turtle_serialzier_registered = True

	def _register_serializers(self, outputFormat) :
		"""If necessary, register the serializer for a specific name. Frontend to L{_register_XML_serializer} and L{_register_Turtle_serializer}.
		@param outputFormat: serialization format. Can be one of "turtle", "n3", "xml", "pretty-xml", "nt". "xml" and "pretty-xml", as well as "turtle" and "n3" are synonyms.
		@return: the final output format name
		"""
		# Exchanging the pretty xml and turtle serializers against the version stored with this package
		if outputFormat in ["pretty-xml", "xml"] :
			self._register_XML_serializer()
			return self.xml_serializer_name
		elif outputFormat in ["turtle", "n3"] :
			self._register_Turtle_serializer()
			return self.turtle_serializer_name
		else :
			return outputFormat

	def create_exception_graph(self, exception_msg, graph=None, http=True) :
		"""
		This method takes an exception and turns its message into a serialized RDF Graph. This is used when
		the distiller is used as a CGI script or with files and is asked to return an RDF content in case of exceptions.
	
		@param exception_msg: message of an exception
		@type exception_msg: string
		@param format: the format of the return, should be n3/turtle or xml
		@keyword graph: an RDF Graph (if None, than a new one is created)
		@type graph: rdflib Graph instance
		@keyword http: whether an extra http information should be added or not
		@type http: Boolean
		"""
		from rdflib.Literal	import Literal
	
		if graph == None :
			graph = Graph()

		graph.bind("dist",DIST_NS)
		
		if not exception_msg :
			_add_to_comment_graph(graph, Literal("%s" % exception_msg), ERROR, URIRef(self.base))
	
		# Add a 400 error message information
		if http:
			ns_http=Namespace("http://www.w3.org/2006/http#")
			graph.bind("http",ns_http)
			response = BNode()
			graph.add((response,ns_rdf["type"],ns_http["Response"]))
			graph.add((response,ns_http["statusCodeNumber"],Literal("400")))
			graph.add((response,ns_http["statusCode"],URIRef("http://www.w3.org/2008/http-statusCodes#statusCode400")))
			
		return graph
	
	####################################################################################################################
	# Externally used methods
	#
	def graph_from_DOM(self, dom, graph = None) :
		"""
		Extract the RDF Graph from a DOM tree.
		@param dom: a DOM Node element, the top level entry node for the whole tree (to make it clear, a dom.documentElement is used to initiate processing)
		@keyword graph: an RDF Graph (if None, than a new one is created)
		@type graph: rdflib Graph instance. If None, a new one is created.
		@return: an RDF Graph
		@rtype: rdflib Graph instance
		"""
		if graph == None :
			# Create the RDF Graph
			graph   = Graph()
	
		# get the DOM tree
		topElement = dom.documentElement
	
		# Perform the built-in and external transformations on the HTML tree. This is,
		# in simulated form, the hGRDDL approach of Ben Adida
		for trans in self.options.transformers + builtInTransformers :
			trans(topElement, self.options)
	
		# Create the initial state. This takes care of things
		# like base, top level namespace settings, etc.
		state = ExecutionContext(topElement, graph, base=self.base, options=self.options)
	
		# The top level subject starts with the current document; this
		# is used by the recursion
		subject = URIRef(state.base)
	
		parse_one_node(topElement, graph, subject, state, [])
		
		# possibly add the comment graph content
		if self.options.comment_graph.graph != None :
			# Add the content of the comment graph to the output
			bound = False
			for t in self.options.comment_graph.graph :
				if not bound :
					graph.bind("dist", DIST_NS)
					bound = True
				graph.add(t)
				
		return graph
	
	def graph_from_source(self, name, graph = None) :
		"""
		Extract an RDF graph from an RDFa source. The source is parsed, the RDF extracted, and the RDFa Graph is
		returned. This is a fron-end to the L{pyRdfa.graph_from_DOM} method.
		
		At the moment the choice between an HTML5 parsing and an pure XML parsing is not really clear. I expect that
		to be cleaner in RDF1.1. The clean approach may be, at least for URI-s, to look at the return media type...
		
		@param name: a URI, a file name, or a file-like object
		@type graph: rdflib Graph instance. If None, a new one is created.
		@return: an RDF Graph
		@return: an RDF Graph
		@rtype: rdflib Graph instance
		"""
		# First, open the source...
		input = self._get_input(name)
		msg = ""
		
		# Check if the host language is HTML5 or not
		parser = None
		if self.options.host_language == HTML5_RDFA :
			import html5lib
			parser = html5lib.HTMLParser(tree=html5lib.treebuilders.getTreeBuilder("dom"))
			parse = parser.parse
		else :
			# in other cases an XML parser has to be used
			parse = xml.dom.minidom.parse
			
		dom = parse(input)
		
		# Try to second-guess the input type for the non HTML5 case.
		# This is _not_ really kosher, but the minidom is not really namespace aware...
		# In practice the goal is to have the system recognize svg content automatically
		# I expect this to possibly disappear in case of RDFa 1.1
		if 	self.options.host_language != HTML5_RDFA :
			top = dom.documentElement
			if top.hasAttribute("xmlns") :
				key = (top.getAttribute("xmlns"), top.nodeName)
				if key in self._switch :
					self.options.host_language = self._switch[key]

		return self.graph_from_DOM(dom, graph)	
	
	def rdf_from_sources(self, names, outputFormat = "xml", rdfOutput = False) :
		"""
		Extract and RDF graph from a list of RDFa sources and serialize them in one graph. The sources are parsed, the RDF
		extracted, and serialization is done in the specified format.
		@param names: list of sources, each can be a URI, a file name, or a file-like object
		@keyword outputFormat: serialization format. Can be one of "turtle", "n3", "xml", "pretty-xml", "nt". "xml" and "pretty-xml", as well as "turtle" and "n3" are synonyms.
		@keyword rdfOutput: controls what happens in case an exception is raised. If the value is False, the caller is responsible handling it; otherwise a graph is returned with an error message
		@type rdfOutput: boolean
		@return: a serialized RDF Graph
		@rtype: string
		"""
		outputFormat = self._register_serializers(outputFormat)
		
		graph = Graph()
		# the value of rdfOutput determines the reaction on exceptions...
		if rdfOutput :
			for name in names :
				try :
					self.graph_from_source(name, graph)
				except :
					(type, value, traceback) = sys.exc_info()
					self.create_exception_graph(value, graph= graph, http=False)
		else :
			# let the caller deal with the exceptions
			for name in names :
				self.graph_from_source(name, graph)
		return graph.serialize(format=outputFormat)

	def rdf_from_source(self, name, outputFormat = "xml", rdfOutput = False) :
		"""
		Extract and RDF graph from an RDFa source and serialize it in one graph. The source is parsed, the RDF
		extracted, and serialization is done in the specified format.
		@param name: a URI, a file name, or a file-like object
		@keyword outputFormat: serialization format. Can be one of "turtle", "n3", "xml", "pretty-xml", "nt". "xml" and "pretty-xml", as well as "turtle" and "n3" are synonyms.
		@keyword rdfOutput: controls what happens in case an exception is raised. If the value is False, the caller is responsible handling it; otherwise a graph is returned with an error message
		@type rdfOutput: boolean
		@return: a serialized RDF Graph
		@rtype: string
		"""
		return self.rdf_from_sources([name], outputFormat, rdfOutput)

################################################# CGI Entry point
def processURI(uri, outputFormat, form={}) :
	"""The standard processing of an RDFa uri options in a form, ie, as an entry point from a CGI call.

	The call accepts extra form options (ie, HTTP GET options) as follows:
	
	 - C{warnings=[true|false]} means that extra warnings (eg, missing C{@profile} attribute, possibly erronous CURIE-s) are added to the output graph. Default: False
	 - C{space-preserve=[true|false]} means that plain literals are normalized in terms of white spaces. Default: false.
	 - C{extras=[true|false]} means that extra, built-in transformers are executed on the DOM tree prior to RDFa processing. Default: false. Alternatively, a finer granurality can be used with the following options:
	  - C{extras-meta=[true|false]}: the 'name' attribute of the 'meta' element is copied into a 'property' attribute of the same element
	  - C{extras-dc=[true|false]}: implement the Dublin Core dialect to include DC statements from the header. See L{transform.DublinCore} for further details.
	  - C{extras-openid=[true|false]}: interpret the 'openid' references in the header. See L{transform.OpenID} for further details.
	  - C{extras-li=[true|false]}: 'ol' and 'ul' elements are possibly transformed to generate collections or containers. See L{transform.ContainersCollections} for further details.
	  - C{extras-prefix=[true|false]}: the @prefix attribute can be used as a replacement for the xmlns handling. See L{transform.Prefix} for details.
	  - C{extras-var=[true|false]}: the @var-XXX pattern can also be used for the RDFa attribute (eg, C{@var-resource}). See L{transform.Prefix} for details.
	 - C{parser=[strict|lax]}: use the "strict" mode, ie, only strict XML input is accepted, or try with the HTML5 parser, too. Default is C{lax}.
	 - C{host=[xhtml|xml]}: the underlying host language is XHTML or XML (e.g., SVG1.2). In the xml case the C{xml:base} attribute as well as the built-in C{metadata} is properly interpreted. Default is C{xhtml}. Note that the C{svg} value can also be used as an alias to C{xml}.
	 - C{rdfa11=[true|false]}: implement those features that the RDFa group has already accepted as part of the next release of RDFa but is not yet final

	@param uri: URI to access. Note that the "text:" and "uploaded:" values are treated separately; the former is for textual intput (in which case a StringIO is used to get the data) and the latter is for uploaded file, where the form gives access to the file directly.
	@param outputFormat: serialization formats, as understood by RDFLib. Note that though "turtle" is
	a possible parameter value, the RDFLib turtle generation does funny (though legal) things with
	namespaces, defining unusual and unwanted prefixes...
	@param form: extra call options (from the CGI call) to set up the local options
	@type form: cgi FieldStorage instance
	@return: serialized graph
	@rtype: string
	@raise RDFaError: if the accept header of the call requires HTML, then all possible exceptions are re-raised as RDFaError
	"""
	if uri == "uploaded:" :
		input	= form["uploaded"].file
		base	= ""
	elif uri == "text:" :
		input	= StringIO.StringIO(form.getfirst("text"))
		base	= ""
	else :
		input	= uri
		base	= uri

	# working through the possible options
	# Host language: generic XML or strictly XHTML
	xhtml = True
	if "host" in form.keys() and form.getfirst("host").lower() == "xhtml" :
		xhtml = True
	if "host" in form.keys() and (form.getfirst("host").lower() == "xml" or form.getfirst("host").lower() == "svg"):
		xhtml = False

	# Lax parsing for XHTML is allowed
	lax = True
	if "parser" in form.keys() and form.getfirst("parser").lower() == "strict" :
		# the request is to stick to XHTML
		lax = False
	if "parser" in form.keys() and form.getfirst("parser").lower() == "lax" :
		# the request is to be lax
		lax = True
		
	transformers = []
	if "extras" in form.keys() and form.getfirst("extras").lower() == "true" :
		from pyRdfa.transform.MetaName              	import meta_transform
		from pyRdfa.transform.OpenID                	import OpenID_transform
		from pyRdfa.transform.DublinCore            	import DC_transform
		from pyRdfa.transform.ContainersCollections		import decorate_li_s
		from pyRdfa.transform.Prefix				 	import set_prefixes, handle_vars
		transformers = [decorate_li_s, OpenID_transform, DC_transform, meta_transform, handle_vars, set_prefixes]
	else :
		if "extra-meta" in form.keys() and form.getfirst("extra-meta").lower() == "true" :
			from pyRdfa.transform.MetaName import meta_transform
			transformers.append(MetaName)
		if "extra-openid" in form.keys() and form.getfirst("extra-openid").lower() == "true" :
			from pyRdfa.transform.OpenID import OpenID_transform
			transformers.append(OpenID_transform)
		if "extra-dc" in form.keys() and form.getfirst("extra-dc").lower() == "true" :
			from pyRdfa.transform.DublinCore import DC_transform
			transformers.append(DC_transform)
		if "extra-li" in form.keys() and form.getfirst("extra-li").lower() == "true" :
			from pyRdfa.transform.ContainersCollections import decorate_li_s
			transformers.append(decorate_li_s)
		if "extra-prefix" in form.keys() and form.getfirst("extra-prefix").lower() == "true" :
			from pyRdfa.transform.Prefix import set_prefixes
			transformers.append(set_prefixes)
		if "extra-vars" in form.keys() and form.getfirst("extra-vars").lower() == "true" :
			from pyRdfa.transform.Prefix import handle_vars
			transformers.append(handle_vars)

	if "warnings" in form.keys() and form.getfirst("warnings").lower() == "true" :
		warnings = True
	else :
		warnings = False

	if "space-preserve" in form.keys() and form.getfirst("space-preserve").lower() == "false" :
		space_preserve = False
	else :
		space_preserve = True

	options = Options(warnings=warnings, space_preserve=space_preserve, transformers=transformers, xhtml = xhtml, lax = lax)
	processor = pyRdfa(options, base)
	
	try:
		return processor.rdf_from_source(input, outputFormat)
	except :
		(type,value,traceback) = sys.exc_info()

		# decide whether HTML or RDF should be sent. 
		import os, httpheader
		htmlOutput = False
		if 'HTTP_ACCEPT' in os.environ :
			acc = os.environ['HTTP_ACCEPT']
			possibilities = ['text/html','application/rdf+xml','text/turtle; charset=utf-8']

			# this nice module does content negotiation and returns the preferred format
			sg = httpheader.acceptable_content_type(acc, possibilities)
			htmlOutput = (sg != None and sg[0] == httpheader.content_type('text/html'))
			os.environ['rdfaerror'] = 'true'

		# This is really for testing purposes only, it is an unpublished flag to force RDF output no
		# matter what
		forceRDFOutput = "forceRDFOutput" in form.keys()

		if (not forceRDFOutput) and htmlOutput :
			import traceback, cgi
			print 'Content-type: text/html; charset=utf-8'
			print
			print "<html>"
			print "<head>"
			print "<title>Error in RDFa processing</title>"
			print "</head><body>"
			print "<h1>Error in distilling RDFa</h1>"
			print "<pre>"
			traceback.print_exc(file=sys.stdout)
			print "</pre>"
			print "<pre>%s</pre>" % value
			print "<h1>Information received</h1>"
			print "<dl>"
			if "text" in form and form["text"].value != None and len(form["text"].value.strip()) != 0 :
				print "<dt>Text input:</dt><dd>%s</dd>" % cgi.escape(form["text"].value).replace('\n','<br/>')
			else :
				print "<dt>URI received:</dt><dd><code>'%s'</code></dd>" % cgi.escape(uri)
			print "<dt>Format:</dt><dd> %s</dd>" % outputFormat
			if "warnings" in form : print "<dt>Warnings:</dt><dd> %s</dd>" % form["warnings"].value
			if "space-preserve" in form : print "<dt>Space preserve:</dt><dd> %s</dd>" % form["space-preserve"].value
			if "parser" in form : print "<dt>Parser strict or lax:</dt><dd> %s</dd>" % form["parser"].value
			if "host" in form : print "<dt>Host language:</dt><dd> %s</dd>" % form["host"].value
			print "</dl>"
			print "</body>"
			print "</html>"
		else :
			return processor.create_exception_graph(value).serialize(format=outputFormat)


################################################# Deprecated entry points, kept for backward compatibility... 
def processFile(input, outputFormat="xml", options = None, base="", rdfOutput = False) :
	"""The standard processing of an RDFa file.
	This is a front end to the L{Processing function<_process>}, once the input file like object is identified.

	@param input: input file name, URI, or file-like object. 
	@keyword outputFormat: serialization format. Can be one of "turtle", "n3", "xml", "pretty-xml", "nt". "xml" and "pretty-xml", as well as "turtle" and "n3" are synonyms.
	@keyword options: Options for the distiller (in case of C{None}, the default options are used)
	@type options: L{Options}
	@keyword base: the base URI to be used in the RDFa generation. In case 'input' is a file and this value is empty, the
	file name will be used.
	@keyword rdfOutput: whether, in case of an exception down the line, the exception should be raised or to be turned into and RDF graph
	@return: serialized graph
	@rtype: string
	@raise RDFaError: the file opening has problems, this is re-raised as an RDFa Error (unless rdfOutput is True).
	@deprecated: use the pyRdfa class with rdf_from_source method directly
	"""
	import warnings
	warnings.warn("Use the pyRdfa class with rdf_from_source method directly", DeprecationWarning)
	return pyRdfa(options, base).rdf_from_source(input, outputFormat, rdfOutput)

def parseRDFa(dom, base, graph = None, options=None) :
	"""The standard processing of an RDFa DOM into a Graph. This method is aimed at the inclusion of
	the library in other RDF applications using RDFLib.

	@param dom: DOM node for the document element (as returned from an XML parser)
	@param base: URI for the default "base" value (usually the URI of the file to be processed)
	@keyword graph: a graph. If the value is None, the graph is created.
	@type graph: RDFLib Graph
	@keyword options: Options for the distiller (in case of C{None}, the default options are used)
	@type options: L{Options}
	@return: the graph
	@rtype: RDFLib Graph
	@deprecated: use the pyRdfa class with rdf_from_source method directly
	"""
	import warnings
	warnings.warn("Use the pyRdfa class with graph_from_DOM method directly", DeprecationWarning)
	return pyRdfa(options, base).graph_from_DOM(graph)


