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
 from pyRdfa import pyRdfa
 print pyRdfa().rdf_from_source('filename')

Other output formats (eg, turtle) are also possible. Eg, to produce Turtle output, one could use:
 from pyRdfa import pyRdfa
 print pyRdfa().rdf_from_source('filename', outputFormat='turtle')

It is also possible to embed an RDFa processing. Eg, using:
 from pyRdfa import pyRdfa
 print pyRdfa().graph_from_source('filename')

This will return an RDFLib.Graph object instead of a serialization thereof. See the the description of the
L{pyRdfa class<pyRdfa.pyRdfa>} for further details.

There is a L{separate entry for CGI calls<processURI>}.

Return formats
--------------

By default, the output format for the graph is RDF/XML. At present, the following formats are also available:

 - "xml": RDF/XML.
 - "turtle": Turtle format.
 - "nt": N triples

Options
=======

The package also implements some optional features that are not fully part of the RDFa syntax. At the moment these are:

 - extra warnings and information (eg, possibly erronous CURIE-s) are added to the output graph
 - possibility that plain literals are normalized in terms of white spaces. Default: false. (The RDFa specification requires keeping the white spaces and leave applications to normalize them, if needed)
 - extra, built-in transformers are executed on the DOM tree prior to RDFa processing (see below)

Options are collected in an instance of the L{Options} class and passed to the processing functions as an extra argument. Eg,
if extra warnings are required, the code may be::
 from pyRdfa import processFile, Options
 options = Options(warnings=True)
 print pyRdfa(options=options).rdf_from_source('filename')

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

The user of the package may refer to those and pass it on to the L{processFile} call via an L{Options} instance. The caller of the package may also add his/her transformer modules. Here is a possible usage with the 'openid' transformer
added to the call::
 from pyRdfa import processFile, Options
 from pyRdfa.transform.OpenID import OpenID_transform
 options = Options(transformers=[OpenID_transform])
 print pyRdfa(options=options).rdf_from_source('filename')

In the case of a call via a CGI script, these built-in transformers can be used via extra flags, see L{processURI} for further details.

Note that the current option instance is passed to all transformers as extra parameters. Extensions of the package
may make use of that to control the transformers, if necessary.

Host Languages
==============

RDFa 1.1. Core is defined for generic XML; there are specific documents to describe how the generic specification is valid
for XHTML and HTML5.

pyRdfa makes an automatic switch among these based on the content type of the source. If the content type is 'text/html', the
content is supposed to be HTML5; if it is 'application/xml+xhtml', then it is considered to be XHTML; finally, if it is
'application/xml' or 'application/xxx+xml' (where 'xxx' stands for anything except 'xhtml'), then it is considered
to be general XML.

Beyond the differences described in the RDFa documents, the effect of this choice have the following effect on the
behaviour of pyRdfa:

 - In the case of HTML5, pyRdfa uses an U{HTML5 parser<http://code.google.com/p/html5lib/>}; otherwise the simple XML parser, part of the core Python environment, is used.
 - In the case of generic XML the distiller also considers a more "traditional" way of adding RDF metadata to a file, namely by directly including RDF/XML into the XML file with a proper namespace. The distiller extracts that RDF graph and merges it with the output of the regular RDFa processing.

The content type can be set by the caller when initializing the L{pyRdfa class<pyRdfa.pyRdfa>}. However, the distiller attempts
to find the content type by

 - looking at the content type header as returned by an HTTP call; if unsuccessful or the invocation is done locally then
 - looking at the suffix of the URI or file name (.html and .xhtml are considered to be HTML5 and XHTML, respectively; otherwise XML is considered)

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
$Id: __init__.py,v 1.24 2010-10-26 14:32:10 ivan Exp $ $Date: 2010-10-26 14:32:10 $

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
import os, httpheader

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

import xml.dom.minidom
import urlparse

ns_rdfa		= Namespace("http://www.w3.org/ns/rdfa#")
ns_xsd		= Namespace(u'http://www.w3.org/2001/XMLSchema#')
ns_distill	= Namespace("http://www.w3.org/2007/08/pyRdfa/vocab#")

debug = True

#########################################################################################################

# Exception/error handling. Essentially, all the different exceptions are re-packaged into
# separate exception class, to allow for an easier management on the user level

class RDFaError(Exception) :
	"""Just a wrapper around the local exceptions. It does not add any new functionality to the
	Exception class."""
	def __init__(self, msg) :
		self.msg = msg
		Exception.__init__(self)

class FailedProfile(RDFaError) :
	"""Raised when @profile references cannot be properly dereferenced. It does not add any new functionality to the
	Exception class."""
	def __init__(self, msg, context, http_code = None) :
		self.msg 		= msg
		self.context	= context
		self.http_code 	= http_code
		RDFaError.__init__(self, msg)

class FailedSource(RDFaError) :
	"""Raised when the original source cannot be accessed. It does not add any new functionality to the
	Exception class."""
	def __init__(self, msg, http_code = None) :
		self.msg		= msg
		self.http_code 	= http_code
		RDFaError.__init__(self, msg)
		
class HTTPError(RDFaError) :
	"""Raised when HTTP problems are detected. It does not add any new functionality to the
	Exception class."""
	def __init__(self, http_msg, http_code) :
		self.msg		= http_msg
		self.http_code	= http_code
		RDFaError.__init__(self,http_msg)

class ProcessingError(RDFaError) :
	"""Error found during processing. It does not add any new functionality to the
	Exception class."""
	pass

class pyRdfaError(Exception) :
	"""Used as a wrapper around local exceptions. This is outside the error conditions described by the
	RDFa specification"""
	pass

# Error and Warning classes
RDFA_Error					= ns_distill["Error"]
RDFA_Warning				= ns_distill["Warning"]
RDFA_Info					= ns_distill["Information"]
NonConformantMarkup			= ns_distill["NonConformantMarkup"]
ProfileReferenceError		= ns_distill["ProfileReferenceError"]
UnresolvablePrefix			= ns_distill["InvalidCurie"]
UnresolvableTerm			= ns_distill["InvalidTerm"]

FileReferenceError			= ns_distill["FileReferenceError"]
IncorrectProfileDefinition 	= ns_distill["IncorrectProfileDefinition"]
IncorrectPrefixDefinition 	= ns_distill["IncorrectPrefixDefinition"]

#############################################################################################

from pyRdfa.State						import ExecutionContext
from pyRdfa.Parse						import parse_one_node
from pyRdfa.Options						import Options
from pyRdfa.transform.HeadAbout			import head_about_transform
from pyRdfa.transform.DefaultProfile	import add_default_profile
from pyRdfa.Utils						import URIOpener, MediaTypes, HostLanguage

#: Variable used to characterize cache directories for RDFa profiles
CACHED_PROFILES_ID = 'cached_profiles'

#: current "official" version of RDFa that this package implements
rdfa_current_version	= "1.1"

#: List of built-in transformers that are to be run regardless, because they are part of the RDFa spec
builtInTransformers = [
	head_about_transform,
	add_default_profile
]
	
#########################################################################################################
class pyRdfa :
	"""Main processing class for the distiller"""
	
	def __init__(self, options = None, base = "", media_type = "") :
		"""
		@keyword options: Options for the distiller
		@type options: L{Options}
		@keyword base: URI for the default "base" value (usually the URI of the file to be processed)
		@keyword media_type: explicit setting of media type (a.k.a. media type) of the the RDFa source
		"""
		self.base    	  = base

		# predefined content type
		self.media_type = media_type

		if options == None :
			self.options = Options()
		else :
			self.options = options
			self.options.set_host_language(self.media_type)
		
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
		try :
			if isinstance(name, basestring) :
				# check if this is a URI, ie, if there is a valid 'scheme' part
				# otherwise it is considered to be a simple file
				if urlparse.urlparse(name)[0] != "" :
					url_request 	  = URIOpener(name)
					self.base 		  = url_request.location
					if self.media_type == "" :
						if url_request.content_type in [ MediaTypes.xhtml, MediaTypes.html, MediaTypes.xml ] :
							self.media_type = url_request.content_type
						else :
							self.media_type = MediaTypes.xml
						self.options.set_host_language(self.media_type)
					return url_request.data
				else :
					self.base = name
					if self.media_type == "" :
						if name.endswith(".xhtml") :
							self.media_type = MediaTypes.xhtml
						elif name.endswith(".html") :
							self.media_type = MediaTypes.html
						else :
							self.media_type = MediaTypes.xml
						self.options.set_host_language(self.media_type)
					return file(name)
			else :
				return name
		except :
			(type, value, traceback) = sys.exc_info()
			raise FailedSource(value)
		
	def _register_XML_serializer(self) :
		"""The default XML Serializer of RDFLib 2.X is buggy, mainly when handling lists. An L{own version<serializers.PrettyXMLSerializer>} is
		registered in RDFlib and used in the rest of the package. This is not used for RDFLib 3.X.
		"""
		if not self.xml_serializer_registered :
			from rdflib.plugin import register
			from rdflib.syntax import serializer, serializers
			register(self.xml_serializer_name, serializers.Serializer, "pyRdfa.serializers.PrettyXMLSerializer", "PrettyXMLSerializer")
			self.xml_serializer_registered = True

	def _register_Turtle_serializer(self) :
		"""The default Turtle Serializers of RDFLib 2.X is buggy and not very nice as far as the output is concerned.
		An L{own version<serializers.TurtleSerializer>} is registered in RDFLib and used in the rest of the package.
		This is not used for RDFLib 3.X.
		"""
		if not self.turtle_serializer_registered :
			from rdflib.plugin import register
			from rdflib.syntax import serializer, serializers
			register(self.turtle_serializer_name, serializers.Serializer, "pyRdfa.serializers.TurtleSerializer", "TurtleSerializer")
			self.turtle_serialzier_registered = True

	def _register_serializers(self, outputFormat) :
		"""If necessary, register the serializer for a specific name. Frontend to
		L{_register_XML_serializer} and L{_register_Turtle_serializer}.
		@param outputFormat: serialization format. Can be one of "turtle", "n3", "xml", "pretty-xml", "nt". "xml" and "pretty-xml", as well as "turtle" and "n3" are synonyms. Used for RDFLib 2.X.
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
		def copyGraph(tog,fromg) :
			for t in fromg :
				tog.add(t)
			for k,ns in fromg.namespaces() :
				tog.bind(k,ns)

		if graph == None :
			# Create the RDF Graph, that will contain the return triples...
			graph   = Graph()
			
		# this will collect the content, the 'default graph', as called in the RDFa spec
		default_graph = Graph()
	
		# get the DOM tree
		topElement = dom.documentElement
	
		# Perform the built-in and external transformations on the HTML tree. This is,
		# in simulated form, the hGRDDL approach of Ben Adida
		for trans in self.options.transformers + builtInTransformers :
			trans(topElement, self.options)
	
		# Create the initial state. This takes care of things
		# like base, top level namespace settings, etc.
		try :
			state = ExecutionContext(topElement, default_graph, base=self.base, options=self.options)
			# The top level subject starts with the current document; this
			# is used by the recursion
			subject = URIRef(state.base)
			parse_one_node(topElement, default_graph, subject, state, [])
		except FailedProfile, f :
			# This may occur if the top level @profile cannot be dereferenced, which stops the processing as a whole!
			bnode = self.options.add_error(f.msg, ProfileReferenceError, f.context)
			if f.http_code :
				self.options.processor_graph.add_http_context(bnode, f.http_code)
			# This may occur if the top level @profile cannot be dereferenced, which stops the processing as a whole!
	
		# What should be returned depends on the way the options have been set up
		if self.options.output_default_graph :
			copyGraph(graph, default_graph)
			if self.options.output_processor_graph :
				copyGraph(graph, self.options.processor_graph.graph)
		elif self.options.output_processor_graph :
			copyGraph(graph, self.options.processor_graph.graph)

		self.options.reset_processor_graph()

		return graph
	
	def graph_from_source(self, name, graph = None, rdfOutput = False) :
		"""
		Extract an RDF graph from an RDFa source. The source is parsed, the RDF extracted, and the RDFa Graph is
		returned. This is a fron-end to the L{pyRdfa.graph_from_DOM} method.
				
		@param name: a URI, a file name, or a file-like object
		@param graph: rdflib Graph instance. If None, a new one is created.
		@param rdfOutput: whether exception should be turned into RDF and returned as part of the processor graph
		@return: an RDF Graph
		@return: an RDF Graph
		@rtype: rdflib Graph instance
		"""
		def copyErrors(tog, options) :
			if tog == None :
				tog = Graph()
			if options.output_processor_graph :
				for t in options.processor_graph.graph :
					tog.add(t)
				for k,ns in options.processor_graph.graph.namespaces() :
					tog.bind(k,ns)
			options.reset_processor_graph()
			return tog
		
		try :
			# First, open the source...
			input = self._get_input(name)
			msg = ""
			
			parser = None
			if self.options.host_language == HostLanguage.html_rdfa :
				import warnings
				warnings.filterwarnings("ignore", category=DeprecationWarning)
				import html5lib
				parser = html5lib.HTMLParser(tree=html5lib.treebuilders.getTreeBuilder("dom"))
				parse = parser.parse
			else :
				# in other cases an XML parser has to be used
				parse = xml.dom.minidom.parse			
			dom = parse(input)
	
			return self.graph_from_DOM(dom, graph)
		except FailedSource, f :
			if not rdfOutput : raise f
			self.options.add_error(f.msg, FileReferenceError, name)
			return copyErrors(graph, self.options)
		except Exception :
			if not rdfOutput : raise
			(type, value, traceback) = sys.exc_info()
			return copyErrors(graph, self.options)
	
	def rdf_from_sources(self, names, outputFormat = "pretty-xml", rdfOutput = False) :
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
		if rdflib.__version__ >= "3.0.0" :
			# there is no need to use the private serializers, the previous bugs are supposed to have been
			# handled. Only the merge of the output format names are necessary...
			if outputFormat == "xml"  : outputFormat = "pretty-xml"
			elif outputFormat == "n3" : outputFormat = "turtle"
		else :
			# use the extra serializers, needed for older versions of rdflib...
			outputFormat = self._register_serializers(outputFormat)
		
		graph = Graph()
		graph.bind("xsd", Namespace(u'http://www.w3.org/2001/XMLSchema#'))
		# the value of rdfOutput determines the reaction on exceptions...
		for name in names :
			self.graph_from_source(name, graph, rdfOutput)
		return graph.serialize(format=outputFormat)

	def rdf_from_source(self, name, outputFormat = "pretty-xml", rdfOutput = False) :
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

	The call accepts extra form options (eg, HTTP GET options) as follows:
	
	 - C{graph=[default|processor|default,processor|processor,default]} specifying which graphs are returned. Default: default.
	 - C{space-preserve=[true|false]} means that plain literals are normalized in terms of white spaces. Default: false.
	 - C{extras=[true|false]} means that extra, built-in transformers are executed on the DOM tree prior to RDFa processing. Default: false. Alternatively, a finer granurality can be used with the following options:
	  - C{extras-meta=[true|false]}: the @name attribute for metas are converted into @property for further processing
	  - C{extras-cc=[true|false]}: containers and collections are generated. See L{transform.ContainersCollections} for further details.
	 - C{host_language=[xhtml,html,xml]} : the host language. Used when files are uploaded or text is added verbatim, otherwise the HTTP return header shoudl be used

	@param uri: URI to access. Note that the "text:" and "uploaded:" values are treated separately; the former is for textual intput (in which case a StringIO is used to get the data) and the latter is for uploaded file, where the form gives access to the file directly.
	@param outputFormat: serialization formats, as understood by RDFLib. Note that though "turtle" is
	a possible parameter value, some versions of the RDFLib turtle generation does funny (though legal) things with
	namespaces, defining unusual and unwanted prefixes...
	@param form: extra call options (from the CGI call) to set up the local options
	@type form: cgi FieldStorage instance
	@return: serialized graph
	@rtype: string
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
	# Host language: HTML, XHTML, or XML
	# Note that these options should be used for the upload and inline version only in case of a form
	# for real uris the returned content type should be used
	if "host_language" in form.keys() :
		if form.getfirst("host_language").lower() == "xhtml" :
			media_type = MediaTypes.xhtml
		elif form.getfirst("host_language").lower() == "html" :
			media_type = MediaTypes.html
		else :
			media_type = MediaTypes.xml
	else :
		media_type = ""
		
	transformers = []
	if "extras" in form.keys() and form.getfirst("extras").lower() == "true" :
		from pyRdfa.transform.MetaName              	import meta_transform
		from pyRdfa.transform.OpenID                	import OpenID_transform
		from pyRdfa.transform.DublinCore            	import DC_transform
		from pyRdfa.transform.ContainersCollections		import containers_collections
		transformers = [containers_collections, OpenID_transform, DC_transform, meta_transform]
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
		if "extra-cc" in form.keys() and form.getfirst("extra-cc").lower() == "true" :
			from pyRdfa.transform.ContainersCollections import containers_collections
			transformers.append(containers_collections)
		# This is here only for backward compatibility
		if "extra-li" in form.keys() and form.getfirst("extra-li").lower() == "true" :
			from pyRdfa.transform.ContainersCollections import containers_collections
			transformers.append(containers_collections)

	output_default_graph 	= True
	output_processor_graph 	= False
	if "graph" in form.keys() :
		a = form.getfirst("graph").lower()
		if a == "processor" :
			output_default_graph 	= False
			output_processor_graph 	= True
		elif a == "processor,default" or a == "default,processor" :
			output_processor_graph 	= True
		elif a == "default" :				
			output_default_graph 	= True
			output_processor_graph 	= False			

	if "space-preserve" in form.keys() and form.getfirst("space-preserve").lower() == "false" :
		space_preserve = False
	else :
		space_preserve = True

	options = Options(output_default_graph = output_default_graph,
					  output_processor_graph = output_processor_graph,
					  space_preserve=space_preserve,
					  transformers=transformers)
	processor = pyRdfa(options = options, base = base, media_type = media_type)
	
	
	# Decide the output format; the issue is what should happen in case of a top level error like an inaccessibility of
	# the html source: should a graph be returned or an HTML page with an error message?

	# decide whether HTML or RDF should be sent. 
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
	rdfOutput = ("forceRDFOutput" in form.keys()) or not htmlOutput
	
	try :
		return processor.rdf_from_source(input, outputFormat, rdfOutput = rdfOutput)
	except :
		# This branch should occur only if an exception is really raised, ie, if it is not turned
		# into a graph value.
		(type,value,traceback) = sys.exc_info()

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
		print "<h1>Distiller request details</h1>"
		print "<dl>"
		if uri == "text:" and "text" in form and form["text"].value != None and len(form["text"].value.strip()) != 0 :
			print "<dt>Text input:</dt><dd>%s</dd>" % cgi.escape(form["text"].value).replace('\n','<br/>')
		elif uri == "uploaded:" :
			print "<dt>Uploaded file</dt>"
		else :
			print "<dt>URI received:</dt><dd><code>'%s'</code></dd>" % cgi.escape(uri)
		if "host_language" in form.keys() :
			print "<dt>Media Type:</dt><dd>%s</dd>" % media_type
		if "graph" in form.keys() :
			print "<dt>Requested graphs:</dt><dd>%s</dd>" % form.getfirst("graph").lower()
		else :
			print "<dt>Requested graphs:</dt><dd>default</dd>"
		print "<dt>Output serialization format:</dt><dd> %s</dd>" % outputFormat
		if "space-preserve" in form : print "<dt>Space preserve:</dt><dd> %s</dd>" % form["space-preserve"].value
		print "</dl>"
		print "</body>"
		print "</html>"

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

###################################################################################################
"""
$Log: __init__.py,v $
Revision 1.24  2010-10-26 14:32:10  ivan
*** empty log message ***

Revision 1.23  2010/08/25 11:22:19  ivan
Adaptation to the new collection/container approach

Revision 1.22  2010/07/26 13:27:52  ivan
testing the log entry part

"""
