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
$Id: __init__.py,v 1.7 2010-01-29 12:32:56 ivan Exp $ $Date: 2010-01-29 12:32:56 $

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

from pyRdfa.State		import ExecutionContext
from pyRdfa.Parse		import parse_one_node
from pyRdfa.Options		import Options, DIST_NS, _add_to_comment_graph, ERROR, GENERIC_XML, XHTML_RDFA, HTML5_RDFA


import xml.dom.minidom

from pyRdfa.transform.utils			import dump
from pyRdfa.transform.HeadAbout		import head_about_transform

# For some doctype and element name combinations an automatic switch to an input mode is done
__switch = {
	("http://www.w3.org/1999/xhtml","html") : XHTML_RDFA,
	("http://www.w3.org/2000/svg","svg")    : GENERIC_XML
}

debug = True

#: current "official" version of RDFa that this package implements
rdfa_current_version	= 1.1

# Exception handling. Essentially, all the different exceptions are re-packaged into
# separate exception class, to allow for an easier management on the user level
class RDFaError(Exception) :
	"""Just a wrapper around the local exceptions. It does not add any new functionality to the
	Exception class."""
	pass

#########################################################################################################
# Handling URIs

import urllib
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

def _open_URI(uri) :
	"""
	Open a URI via urllib. It relies on the capabilities of the FancyURLopener class of the official Python distribution,
	eg, redirection features. However, it does not handle authentication. If that is required, an exception is raised.
	@param uri: The URI to be opened
	@return: file-like object, as returned by the standard urllib module of Python
	@raise RDFaError: this encapsulates the possible exceptions raised by the urllib package, as well as authentication requests.
	"""
	try :
		# the simple version was: return urllib.urlopen(uri) but that was really too simple; eg, redirections were not followed...
		# the Proxy auth URL is Dominique's version that should handle authentication. Somehow it does not work...:-(
		# import http_auth
		# urlopener = http_auth.ProxyAuthURLopener()
		return _MyURLopener().open(uri)
	except :
		# XML Parsing error in the input
		(type,value,traceback) = sys.exc_info()
		msg = "Problems in accessing the information on uri '%s': %s" % (uri,value)
		raise RDFaError, msg

#########################################################################################################
def create_exception_graph(exception_msg, uri, format, http=True) :
	"""
	This function takes an exception and turns its message into a serialized RDF Graph. This is used when
	the distiller is used as a CGI script and is asked to return an RDF content whatever happens.

	@param exception_msg: message of an exception
	@type exception_msg: string
	@param uri: the top URI used to invoke the distiller
	@param format: the format of the return, should be n3/turtle or xml
	@keyword http: whether an extra http information should be added or not
	@type http: Boolean
	"""
	from rdflib.Literal	import Literal

	graph = Graph()
	graph.bind("dist",DIST_NS)
	_add_to_comment_graph(graph, Literal(exception_msg), ERROR, URIRef(uri))

	# Add a 400 error message information
	if http:
		ns_http=Namespace("http://www.w3.org/2006/http#")
		graph.bind("http",ns_http)
		response = BNode()
		graph.add((response,ns_rdf["type"],ns_http["Response"]))
		graph.add((response,ns_http["statusCodeNumber"],Literal("400")))
		graph.add((response,ns_http["statusCode"],URIRef("http://www.w3.org/2008/http-statusCodes#statusCode400")))

	if format == "n3" or format == "turtle" :
		retval = graph.serialize(format="n3")
	else :
		retval = graph.serialize(format="pretty-xml")
	return retval


#########################################################################################################
# List of built-in transformers that are to be run regardless, because
# they are part of the RDFa spec
builtInTransformers = [
	head_about_transform
]

def _process_DOM(dom, base, outputFormat, options, local=False) :
	"""Core processing. The transformers ("pre-processing") is done
	on the DOM tree, the state is initialized, and the "real" RDFa parsing is done. Finally,
	the result (which is an RDFLib Graph) is serialized using RDFLib's serializers.

	The real work is done in the L{parser function<Parse.parse_one_node>}.

	@param dom: XML DOM Tree node (for the top level)
	@param base: URI for the default "base" value (usually the URI of the file to be processed)
	@param outputFormat: serialization format
	@param options: Options for the distiller
	@type options: L{Options}
	@keyword local: whether the call is for a local usage or via CGI (influences the way
	exceptions are handled)
	@return: serialized graph
	@rtype: string
	@raise RDFaError: when called via CGI, this encapsulates the possible exceptions raised by the RDFLib serializer or the processing itself
	"""
	def __register_XML_serializer(formatstring) :
		"""The default XML Serializer of RDFlib is buggy, mainly when handling lists. An L{own version<serializers.PrettyXMLSerializer>} is
		registered in RDFlib and used in the rest of the package.
		@param formatstring: the string to identify this serializer with.
		"""
		from rdflib.plugin import register
		from rdflib.syntax import serializer, serializers
		register(formatstring, serializers.Serializer, "pyRdfa.serializers.PrettyXMLSerializer", "PrettyXMLSerializer")

	def __register_Turtle_serializer(formatstring) :
		"""The default Turtle Serializers of RDFlib is buggy and not very nice as far as the output is concerned.
		An L{own version<serializers.TurtleSerializer>} is registered in RDFLib and used in the rest of the package.
		@param formatstring: the string to identify this serializer with.
		"""
		from rdflib.plugin import register
		from rdflib.syntax import serializer, serializers
		register(formatstring, serializers.Serializer, "pyRdfa.serializers.TurtleSerializer", "TurtleSerializer")

	# Exchaning the pretty xml serializer agaist the version stored with this package
	if outputFormat == "pretty-xml"  :
		outputFormat = "my-xml"
		__register_XML_serializer(outputFormat)
	elif outputFormat == "turtle" or outputFormat == "n3" :
		outputFormat = "my-turtle"
		__register_Turtle_serializer(outputFormat)

	# Create the RDF Graph
	graph   = Graph()

	# get the DOM tree
	html 	= dom.documentElement

	# Perform the built-in and external transformations on the HTML tree. This is,
	# in simulated form, the hGRDDL approach of Ben Adida
	for trans in options.transformers + builtInTransformers :
		trans(html,options)

	# collect the initial state. This takes care of things
	# like base, top level namespace settings, etc.
	# Ensure the proper initialization
	state = ExecutionContext(html, graph, base=base, options=options)

	# The top level subject starts with the current document; this
	# is used by the recursion
	subject = URIRef(state.base)

	parse_one_node(html, graph, subject, state,[])
	if options.comment_graph.graph != None :
		# Add the content of the comment graph to the output
		graph.bind("dist",DIST_NS)
		for t in options.comment_graph.graph : graph.add(t)
	retval = graph.serialize(format=outputFormat)
	return retval

def _process(input, base, outputFormat, options, local=False) :
	"""Core processing. The XML input is parsed, the transformers ("pre-processing") is done
	on the DOM tree, the state is initialized, and the "real" RDFa parsing is done. Finally,
	the result (which is an RDFLib Graph) is serialized using RDFLib's serializers.

	This is just a simle front end to the L{DOM Processing function<_process_DOM>}, parsing the input.

	@param input: file like object for the XHTML input
	@param base: URI for the default "base" value (usually the URI of the file to be processed)
	@param outputFormat: serialization format
	@param options: Options for the distiller
	@type options: L{Options}
	@keyword local: whether the call is for a local usage or via CGI (influences the way
	exceptions are handled)
	@return: serialized graph
	@rtype: string
	@raise RDFaError: this encapsulates the possible parsing errors
	"""
	msg = ""
	parse = xml.dom.minidom.parse
	try :
		dom = parse(input)
		# Try to second-guess the input type
		# This is _not_ really kosher, but the minidom is not really namespace aware...
		# In practice the goal is to have the system recognize svg content automatically
		# First see if there is a default namespace defined for the document:
		top = dom.documentElement
		if top.hasAttribute("xmlns") :
			key = (top.getAttribute("xmlns"),top.nodeName)
			if key in __switch :
				options.host_language = __switch[key]
	except :
		# XML Parsing error in the input
		(type,value,traceback) = sys.exc_info()
		if options.host_language == GENERIC_XML or options.lax == False :
			msg = 'Parsing error in input file: "%s"' % value
			raise RDFaError, msg
		else :
			# XML Parsing error in the input
			msg = 'XHTML Parsing error in input file: %s. Falling back on the HTML5 parser' % value

			if options != None and options.warnings : options.comment_graph.add_warning(msg)

			# note that if a urllib is used, the input has to be closed and reopened...
			if not local :
				input.close()
				input = _open_URI(base)

			# Now try to see if and HTML5 parser is an alternative...
			try :
				import html5lib
			except :
				# no alternative to the XHTML error, because HTML5 parser not available...
				msg2 = 'XHTML Parsing error in input file: %s. Though parsing is lax, HTML5 parser not available' % value
				raise RDFaError, msg2

			from html5lib import treebuilders
			parser = html5lib.HTMLParser(tree=treebuilders.getTreeBuilder("dom"))
			parse = parser.parse
			try :
				dom = parse(input)
				# The host language has changed
				options.host_language = HTML5_RDFA
			except :
				# Well, even the HTML5 parser could not do anything with this...
				(type,value,traceback) = sys.exc_info()
				msg2 = 'Parsing error in input file as HTML5: "%s"' % value
				msg3 = msg + '/n' + msg2
				raise RDFaError, msg3

	return _process_DOM(dom, base, outputFormat, options, local)

###########################################################################################################
# External entry points to the module

def processURI(uri, outputFormat, form={}) :
	"""The standard processing of an RDFa uri (ie, as an entry point from a CGI call).
	This is a front end to the L{Processing function<_process>}, once the input file like object is identified and the options are processed.

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

	@param uri: URI to access. Note that the "text:" value is treated separately; the value of the form["text"] is considered as a textual input, to be handled by the rest of the software via StringIO
	@param outputFormat: serialization formats, as understood by RDFLib. Note that though "turtle" is
	a possible parameter value, the RDFLib turtle generation does funny (though legal) things with
	namespaces, defining unusual and unwanted prefixes...
	@param form: extra call options (from the CGI call) to set up the local options
	@type form: cgi FieldStorage instance
	@return: serialized graph
	@rtype: string
	@raise RDFaError: if the accept header of the call requires HTML, then all possible exceptions are re-raised as RDFaError
	"""
	try :
		if uri == "text:" :
			input = StringIO.StringIO(form["text"].value)
		else :
			input = _open_URI(uri)

		# working through the possible options
		# Host language: generic XML or strictly XHTML
		xhtml = True
		if "host" in form.keys() and form["host"].value.lower() == "xhtml" :
			xhtml = True
		if "host" in form.keys() and (form["host"].value.lower() == "xml" or form["host"].value.lower() == "svg"):
			xhtml = False

		# Lax parsing for XHTML is allowed
		lax = True
		if "parser" in form.keys() and form["parser"].value.lower() == "strict" :
			# the request is to stick to XHTML
			lax = False
		if "parser" in form.keys() and form["parser"].value.lower() == "lax" :
			# the request is to be lax
			lax = True

		transformers = []
		if "extras" in form.keys() and form["extras"].value.lower() == "true" :
			from pyRdfa.transform.MetaName              	import meta_transform
			from pyRdfa.transform.OpenID                	import OpenID_transform
			from pyRdfa.transform.DublinCore            	import DC_transform
			from pyRdfa.transform.ContainersCollections		import decorate_li_s
			from pyRdfa.transform.Prefix				 	import set_prefixes, handle_vars
			transformers = [decorate_li_s, OpenID_transform, DC_transform, meta_transform, handle_vars, set_prefixes]
		else :
			if "extra-meta" in form.keys() and form["extra-meta"].value.lower() == "true" :
				from pyRdfa.transform.MetaName import meta_transform
				transformers.append(MetaName)
			if "extra-openid" in form.keys() and form["extra-openid"].value.lower() == "true" :
				from pyRdfa.transform.OpenID import OpenID_transform
				transformers.append(OpenID_transform)
			if "extra-dc" in form.keys() and form["extra-dc"].value.lower() == "true" :
				from pyRdfa.transform.DublinCore import DC_transform
				transformers.append(DC_transform)
			if "extra-li" in form.keys() and form["extra-li"].value.lower() == "true" :
				from pyRdfa.transform.ContainersCollections import decorate_li_s
				transformers.append(decorate_li_s)
			if "extra-prefix" in form.keys() and form["extra-prefix"].value.lower() == "true" :
				from pyRdfa.transform.Prefix import set_prefixes
				transformers.append(set_prefixes)
			if "extra-vars" in form.keys() and form["extra-vars"].value.lower() == "true" :
				from pyRdfa.transform.Prefix import handle_vars
				transformers.append(handle_vars)

		if "warnings" in form.keys() and form["warnings"].value.lower() == "true" :
			warnings = True
		else :
			warnings = False

		if "space-preserve" in form.keys() and form["space-preserve"].value.lower() == "false" :
			space_preserve = False
		else :
			space_preserve = True

		options = Options(warnings=warnings,
						  space_preserve=space_preserve,
						  transformers=transformers,
						  xhtml = xhtml,
						  lax = lax)
		
		return _process(input, uri, outputFormat, options)
	except :
		(type,value,traceback) = sys.exc_info()

		# decide whether HTML or RDF should be sent. The former means re-raising the exception (and the latter is taken
		# care of by the CGI interface)
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
			import traceback
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
			print "<dt>Format:</dt><dd> %s</dd>" % format
			if "warnings" in form : print "<dt>Warnings:</dt><dd> %s</dd>" % form["warnings"].value
			if "space-preserve" in form : print "<dt>Space preserve:</dt><dd> %s</dd>" % form["space-preserve"].value
			if "parser" in form : print "<dt>Parser strict or lax:</dt><dd> %s</dd>" % form["parser"].value
			if "host" in form : print "<dt>Host language:</dt><dd> %s</dd>" % form["host"].value
			print "</dl>"
			print "</body>"
			print "</html>"
		else :
			return create_exception_graph("%s" % value, uri, outputFormat)

def processFile(input, outputFormat="xml", options = None, base="", rdfOutput = False) :
	"""The standard processing of an RDFa file.
	This is a front end to the L{Processing function<_process>}, once the input file like object is identified.

	@param input: input file name or file-like object. If the type of the input is a string (unicode or otherwise), that
	is considered to be the name of a file, and is opened
	@keyword outputFormat: serialization format, as understood by RDFLib. Note that though "turtle" is
	a possible parameter value, the RDFLib turtle generation does funny (though legal) things with
	namespaces, defining unusual and unwanted prefixes...
	@keyword options: Options for the distiller (in case of C{None}, the default options are used)
	@type options: L{Options}
	@keyword base: the base URI to be used in the RDFa generation. In case 'input' is a file and this value is empty, the
	file name will be used.
	@keyword rdfOutput: whether, in case of an exception down the line, the exception should be raised or to be turned into and RDF graph
	@return: serialized graph
	@rtype: string
	@raise RDFaError: the file opening has problems, this is re-raised as an RDFa Error (unless rdfOutput is True).
	"""
	try :
		if options == None :
			options = Options()
		inputStream = None
		if isinstance(input,basestring) :
			# a file should be opened for the input
			try :
				inputStream = file(input)
				if base == "" : base = input
			except :
				# Problems opening the file
				(type,value,traceback) = sys.exc_info()
				msg = 'Problems in opening the file: "%s"\n (problematic file name: %s)' % (value,input)
				raise RDFaError, msg
		else :
			# This is already a file-like object
			inputStream = input
		return _process(inputStream, base, outputFormat, options, local=True)
	except :
		(type,value,traceback) = sys.exc_info()

		if rdfOutput :
			if base == "" : base = input
			return create_exception_graph("%s" % value, base, outputFormat, http=False)
		else :
			# re-raise the exception and let the caller deal with it...
			raise RDFaError("%s" % value)

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
	"""
	if graph == None :
		graph = Graph()
	if options == None :
		options = Options()

	html = dom.documentElement

	# Perform the built-in and external transformations on the HTML tree. This is,
	# in simulated form, the hGRDDL approach of Ben Adida
	for trans in options.transformers + builtInTransformers :
		trans(html,options)

	# collect the initial state. This takes care of things
	# like base, top level namespace settings, etc.
	# Ensure the proper initialization
	state = ExecutionContext(html, graph, base=base, options=options)

	# The top level subject starts with the current document; this
	# is used by the recursion
	subject = URIRef(state.base)

	# parse the whole thing recursively and fill the graph
	parse_one_node(html, graph, subject, state, [])
	if options.comment_graph.graph != None :
		# Add the content of the comment graph to the output
		graph.bind("dist",DIST_NS)
		for t in options.comment_graph.graph : graph.add(t)

	# That is it...
	return graph

