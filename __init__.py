# -*- coding: utf-8 -*-
"""
RDFa 1.1 parser, also referred to as a “RDFa Distiller”. It is
deployed, via a CGI front-end, on the U{W3C RDFa Distiller page<http://www.w3.org/2007/08/pyRdfa/>}.

For details on RDFa, the reader should consult the U{RDFa Core 1.1<http://www.w3.org/TR/rdfa-core/>}
and the U{XHTML+RDFa1.1<http://www.w3.org/TR/2010/xhtml-rdfa>} documents.

This package can also be downloaded U{as a compressed tar file<http://dev.w3.org/2004/PythonLib-IH/dist/pyRdfa.tar.gz>}. The
distribution also includes the CGI front-end and a separate utility script to be run locally.

(Simple) Usage
==============
From a Python file, expecting an RDF/XML pretty printed output::
 from pyRdfa import pyRdfa
 print pyRdfa().rdf_from_source('filename')

Other output formats (eg, turtle) are also possible. Eg, to produce Turtle output, one could use::
 from pyRdfa import pyRdfa
 print pyRdfa().rdf_from_source('filename', outputFormat='turtle')

It is also possible to embed an RDFa processing. Eg, using::
 from pyRdfa import pyRdfa
 print pyRdfa().graph_from_source('filename') 

From a Python file, expecting an RDF/XML pretty printed output::
 from pyRdfa import pyRdfa
 print pyRdfa().rdf_from_source('filename')

Other output formats (eg, turtle) are also possible. Eg, to produce Turtle output, one could use::
 from pyRdfa import pyRdfa
 print pyRdfa().rdf_from_source('filename', outputFormat='turtle')

It is also possible to embed an RDFa processing. Eg, using::
 from pyRdfa import pyRdfa
 print pyRdfa().graph_from_source('filename')

will return an RDFLib.Graph object instead of a serialization thereof. See the the description of the
L{pyRdfa class<pyRdfa.pyRdfa>} for further possible entry points details.

There is also, as part of this module, a L{separate entry for CGI calls<processURI>}.

Return formats
--------------

By default, the output format for the graph is RDF/XML. At present, the following formats are also available:

 - "xml": RDF/XML.
 - "turtle": Turtle format.
 - "nt": N triples

Options
=======

The package also implements some optional features that are not part of the RDFa recommendations. At the moment these are:

 - extra warnings and information (eg, possibly erronous CURIE-s) are created as a “processor graph”. There user options to determine whether this graph should be added to the output or not, or even whether that should be the only option.
 - possibility for plain literals to be normalized in terms of white spaces. Default: false. (The RDFa specification requires keeping the white spaces and leave applications to normalize them, if needed)
 - extra, built-in transformers are executed on the DOM tree prior to RDFa processing (see below)

Options are collected in an instance of the L{Options} class and passed to the processing functions as an extra argument. Eg,
if extra warnings are required, the code may be::
 from pyRdfa import processFile, Options
 options = Options(output_processor_graph=True)
 print pyRdfa(options=options).rdf_from_source('filename')
 
See the description of the L{Options} class for the details.

Transformers
============

The package uses the concept of 'transformers': the parsed DOM tree is possibly
transformed I{before} performing the real RDFa processing. This transformer structure makes it possible to
add additional 'services' without distoring the core code of RDFa processing.

Some transformations are included in the package and can be used at invocation. These are:

 - Special syntax to generate collections or containers. See the description of L{transform.containerscollections} for further details.
 - The 'name' attribute of the 'meta' element is copied into a 'property' attribute of the same element
 - Interpreting the 'openid' references in the header. See L{transform.OpenID} for further details.
 - Implementing the Dublin Core dialect to include DC statements from the header.  See L{transform.DublinCore} for further details.

The user of the package may refer to those and pass it on to the L{processFile} call via an L{Options} instance. The caller of the package may also add his/her transformer modules. Here is a possible usage with the 'openid' transformer
added to the call::
 from pyRdfa import processFile, Options
 from pyRdfa.transform.OpenID import OpenID_transform
 options = Options(transformers=[OpenID_transform])
 print pyRdfa(options=options).rdf_from_source('filename')

In the case of a call via a CGI script, some of these built-in transformers can be used via extra flags, see L{processURI} for further details.

The current option instance is passed to all transformers as extra parameters. Extensions of the package
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

The content type may be set by the caller when initializing the L{pyRdfa class<pyRdfa.pyRdfa>}. However, the distiller also attempts
to find the content type by

 - looking at the content type header as returned by an HTTP call; if unsuccessful or the invocation is done locally then
 - looking at the suffix of the URI or file name (.html and .xhtml are considered to be HTML5 and XHTML, respectively; otherwise XML is considered)
 
See the variables in the "utils" module if a new host language is added to the system. The current host language is available for transformers via the option argument, too, and can be used to control the effect of the transformer.

Profiles
========

RDFa 1.1 has the notion of profiles, and client are advised to cache the content of those profiles to avoid making HTTP requests all the time. This module implements caching.

Caching happens in a file system directory. The directory itself is determined by the platform the tool is used on, namely:
 - On Windows, it is the 'pyRdfa-cache' subdirectory of the "%APPDATA%" environment variable (referring to the usual place for application data)
 - On MacOS, it is the ~/Library/Application Support/pyRdfa-cache
 - Otherwise, it is the ~/.pyRdfa-cache
 
This automatic choise can be overridden by the 'CACHE_DIR_VAR' environment variable. 

Caching can be read-only, ie, the setup might generate the caches off-line instead of letting the tool writing its own cache. This can be achieved by making the cache directory read only. The L{ProfileCache.offline_cache_generation} method can be used as an entry point for a separate process that generates the cache file.

If the directories are neither readable nor writable, the profile files are retrieved via HTTP every time they are hit. This may slow down processing, it is advised to avoid such a setup for the package.

The cache includes a separate index file and a file for each profile. Cache control is based upon the 'EXPIRES' header of a profile file: when first seen, this data is stored in the index file and controls whether the cache has to be renewed or not. If the HTTP return header does not have this entry, the date is artificially set ot the current date plus one day.

The cache files themselves are dumped and loaded using Python’s cPickle package. They are binary files (care should be taken if they are managed by CVS: they must be declared as binary files for that purpose, too!).

Default profiles (i.e., http://www.w3.org/profile/rdfa-1.1 and http://www.w3.org/profile/html-rdfa-1.1) are treated just as any other profiles (there is a separate transformer that sets those for the host languages that define them). However, there is a possibility to speed those up by using the L{defaultprofiles} module containing a "pythonized" version of the profile content. The L{built_in_default_profiles} flag in the package "True" to enable this possibility or can be set to "False" to rely on caching. Which version to choose depends on the maintenance and update policy of this package when deployed; if deployment makes it easy to update the L{defaultprofiles.default_profiles}, then the built-in version is obviously faster. Note that the distribution includes a separate script called GenerateDefaultProfiles that can be used to generate the content of the L{defaultprofiles} by possibly going through a caching mechanism once. 


@summary: RDFa parser (distiller)
@requires: Python version 2.5 or up
@requires: U{RDFLib<http://rdflib.net>}; version 3.X is preferred, it has a more readable output serialization.
@requires: U{html5lib<http://code.google.com/p/html5lib/>} for the HTML5 parsing.
@requires: U{httpheader<http://deron.meranda.us/python/httpheader/>}; however, a small modification had to make on the original file, so for this reason and to make distribution easier this module (single file) is added to the distributed tarball.
@organization: U{World Wide Web Consortium<http://www.w3.org>}
@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}

@var builtInTransformers: List of built-in transformers that are to be run regardless, because they are part of the RDFa spec
@var CACHE_DIR_VAR: Environment variable used to characterize cache directories for RDFa profiles in case the default setting does not work or is not appropriate. See the L{caching mechanism description<ProfileCache>} for details
@var rdfa_current_version: Current "official" version of RDFa that this package implements by default. This can be changed at the invocation of the package
@var uri_schemes: List of registered (or widely used) URI schemes; used for warnings...
@var built_in_default_profiles: whether the built-in version of the default profile content should be used, or whether those should go through the same caching mechanism as all other profiles
"""

"""
$Id: __init__.py,v 1.42 2011-08-12 10:01:54 ivan Exp $ $Date: 2011-08-12 10:01:54 $

Thanks to Victor Andrée, who found some intricate bugs, and provided fixes, in the interplay between @prefix and @vocab...

Thanks to Peter Mika who was probably my most prolific tester and bug reporter...

Thanks to Sergio Fernandez to amend the list of non-escaped characters for URI-s (ie, hunted down the necessary steps
as a reaction to his practical problem).

Thanks to Wojciech Polak, who suggested (and provided some example code) to add the feature of
using external file-like objects as input, too (the main usage being to use stdin).

Thanks to Elias Torrez, who provided with the idea and patches to interface to the HTML5 parser.

"""

__version__ = "3.0.2"
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
	from rdflib	import RDF  as ns_rdf
	from rdflib	import RDFS as ns_rdfs
else :
	from rdflib.RDFS	import RDFSNS as ns_rdfs
	from rdflib.RDF		import RDFNS  as ns_rdf

from pyRdfa.graph import MyGraph as Graph

import xml.dom.minidom
import urlparse

# Namespace, in the RDFLib sense, for the rdfa vocabulary
ns_rdfa		= Namespace("http://www.w3.org/ns/rdfa#")

# Vocabulary terms for vocab reporting
RDFA_SOURCE = ns_rdfa["Source"]
RDFA_VOCAB  = ns_rdfa["hasVocab"]

# Namespace, in the RDFLib sense, for the XSD Datatypes
ns_xsd		= Namespace(u'http://www.w3.org/2001/XMLSchema#')

# Namespace, in the RDFLib sense, for the distiller vocabulary, used as part of the processor graph
ns_distill	= Namespace("http://www.w3.org/2007/08/pyRdfa/vocab#")

debug = False

#########################################################################################################

# Exception/error handling. Essentially, all the different exceptions are re-packaged into
# separate exception class, to allow for an easier management on the user level

class RDFaError(Exception) :
	"""Just a wrapper around the local exceptions. It does not add any new functionality to the
	Exception class."""
	def __init__(self, msg) :
		self.msg = msg
		Exception.__init__(self)

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

# Error and Warning RDFS classes
RDFA_Error					= ns_rdfa["Error"]
RDFA_Warning				= ns_rdfa["Warning"]
RDFA_Info					= ns_rdfa["Information"]
NonConformantMarkup			= ns_rdfa["DocumentError"]
UnresolvablePrefix			= ns_rdfa["UnresolvedCURIE"]
UnresolvableTerm			= ns_rdfa["UnresolvedTerm"]

FileReferenceError			= ns_distill["FileReferenceError"]
IncorrectPrefixDefinition 	= ns_distill["IncorrectPrefixDefinition"]
IncorrectBlankNodeUsage     = ns_distill["IncorrectBlankNodeUsage"]

# Error message texts
err_no_blank_node					= "Blank node in %s position is not allowed; ignored"

err_redefining_URI_as_prefix		= "'%s' a registered or a widely used URI scheme, but is defined as a prefix here; is this a mistake?"
err_xmlns_deprecated				= "The usage of 'xmlns' for prefix definition is deprecated; please use the 'prefix' attribute instead (definition for '%s')"
err_bnode_local_prefix				= "The '_' local CURIE prefix is reserved for blank nodes, and cannot be defined as a prefix"
err_col_local_prefix				= "The character ':' is not valid in a CURIE Prefix, and cannot be used in a prefix definition (definition for '%s')"
err_missing_URI_prefix				= "Missing URI in prefix declaration for '%s' (in '%s')"
err_invalid_prefix					= "Invalid prefix declaration '%s' (in '%s')"
err_no_default_prefix				= "Default prefix cannot be changed (in '%s')"
err_prefix_and_xmlns				= "@prefix setting for '%s' overrides the 'xmlns:%s' setting; may be a source of problem if same file is run through RDFa 1.0"
err_non_ncname_prefix				= "Non NCNAME '%s' in prefix definition (in '%s'); ignored"

err_lang							= "Both xml:lang and lang used on an element with different values; xml:lang prevails. (%s and %s)"
err_URI_scheme						= "Unusual URI scheme used in <%s>; may that be a mistake, e.g., by using an undefined CURIE prefix?"
err_illegal_safe_CURIE				= "Illegal safe CURIE: %s; ignored"
err_no_CURIE_in_safe_CURIE			= "Safe CURIE is used, but the value does not correspond to a defined CURIE: [%s]; ignored"
err_undefined_terms					= "'%s' is used as a term, but has not been defined as such; ignored"
err_non_legal_CURIE_ref				= "Relative URI is not allowed in this position (or not a legal CURIE reference) '%s'; ignored"
err_undefined_CURIE					= "Undefined CURIE: '%s'; ignored"

err_unusual_char_in_URI				= "Unusual character in uri: %s; possible error?"

#############################################################################################

from pyRdfa.state						import ExecutionContext
from pyRdfa.parse						import parse_one_node
from pyRdfa.options						import Options
from pyRdfa.transform.toplevelabout		import top_about
from pyRdfa.utils						import URIOpener
from pyRdfa.host 						import HostLanguage, MediaTypes, preferred_suffixes, content_to_host_language

# Environment variable used to characterize cache directories for RDFa profiles. See the L{caching mechanism description<ProfileCache>} for details
CACHE_DIR_VAR		= "PyRdfaCacheDir"

# current "official" version of RDFa that this package implements. This can be changed at the invocation of the package
rdfa_current_version	= "1.1"

# I removed schemes that would not appear as a prefix anyway, like iris.beep
registered_iana_schemes = [
	"aaa","aaas","acap","cap","cid","crid","data","dav","dict","dns","fax","ftp","geo","go",
	"gopher","h323","http","https","iax","icap","im","imap","info","ipp","iris","ldap",
	"mailto","mid","modem","msrp","msrps","mupdate","news","nfs","nntp","opaquelocktoken",
	"pop","pres","rstp","service","shttp","sieve","sip","snmp","soap","tag",
	"tel","telnet","thismessage","tn3270","tip","tv","urn","vemmi","xmpp",
]

historical_iana_schemes = [
	"mailserver", "prospero", "snews", "videotex", "wais",
]

provisional_iana_schemes = [
	"afs", "dtn", "dvb", "icon", "ipn", "jps", "oid", "pack", "rsync", "ws", "wss",
]

other_used_schemes = [
	"doi", "file", "git",  "hdl", "isbn", "javascript", "ldap", "lsid", "mms", "mstp", 
	"rtmp", "rtspu", "sftp", "sips", "sms", "snmp", "stp", "svn", 
]

uri_schemes = registered_iana_schemes + historical_iana_schemes + provisional_iana_schemes + other_used_schemes

# List of built-in transformers that are to be run regardless, because they are part of the RDFa spec
builtInTransformers = [
	top_about
]
	
#########################################################################################################
class pyRdfa :
	"""Main processing class for the distiller
	
	@ivar options: an instance of the L{Options} class
	@ivar media_type: the preferred default media type, possibly set at initialization
	@ivar base: the base value, possibly set at initialization
	"""
	def __init__(self, options = None, base = "", media_type = "", rdfa_version = None) :
		"""
		@keyword options: Options for the distiller
		@type options: L{Options}
		@keyword base: URI for the default "base" value (usually the URI of the file to be processed)
		@keyword media_type: explicit setting of the preferred media type (a.k.a. content type) of the the RDFa source
		@keyword rdfa_version: the RDFa version that should be used. If not set, the value of the global L{rdfa_current_version} variable is used
		"""
		self.base    = base
		self.charset = None

		# predefined content type
		self.media_type = media_type

		if options == None :
			self.options = Options()
		else :
			self.options = options

		if media_type != "" :
			self.options.set_host_language(self.media_type)
			
		if rdfa_version is not None :
			self.rdfa_version = rdfa_version
		else :
			self.rdfa_version = None
		
	def _get_input(self, name) :
		"""
		Trying to guess whether "name" is a URI or a string (for a file); it then tries to open this source accordingly,
		returning a file-like object. If name none of these, it returns the input argument (that should
		be, supposidly, a file-like object already)
		
		If the media type has not been set explicitly at initialization of this instance,
		the method also sets the media_type based on the HTTP GET response or the suffix of the file. See
		L{utils.preferred_suffixes} for the suffix to media type mapping. 
		
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
						if url_request.content_type in content_to_host_language :
							self.media_type = url_request.content_type
						else :
							self.media_type = MediaTypes.xml
						self.options.set_host_language(self.media_type)
					self.charset = url_request.charset
					return url_request.data
				else :
					self.base = name
					if self.media_type == "" :
						self.media_type = MediaTypes.xml
						# see if the default should be overwritten
						for suffix in preferred_suffixes :
							if name.endswith(suffix) :
								self.media_type = preferred_suffixes[suffix]
								self.charset = 'utf-8'
								break
						self.options.set_host_language(self.media_type)
					return file(name)
			else :
				return name
		except :
			(type, value, traceback) = sys.exc_info()
			raise FailedSource(value)
	
	####################################################################################################################
	# Externally used methods
	#
	def graph_from_DOM(self, dom, graph = None, pgraph = None) :
		"""
		Extract the RDF Graph from a DOM tree. This is where the real meat happens. All other methods get down to this
		one, eventually (eg, after opening a URI and parsing it into a DOM)
		@param dom: a DOM Node element, the top level entry node for the whole tree (to make it clear, a dom.documentElement is used to initiate processing)
		@keyword graph: an RDF Graph (if None, than a new one is created)
		@type graph: rdflib Graph instance. If None, a new one is created.
		@keyword pgraph: an RDF Graph to hold (possibly) the processor graph content. If None, and the error/warning triples are to be generated, they will be added to the returned graph. Otherwise they are stored in this graph.
		@type graph: rdflib Graph instance or None
		@return: an RDF Graph
		@rtype: rdflib Graph instance
		"""
		def copyGraph(tog, fromg) :
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
		
		# Perform the built-in and external transformations on the HTML tree. 
		for trans in self.options.transformers + builtInTransformers :
			trans(topElement, self.options)
		
		# Create the initial state. This takes care of things
		# like base, top level namespace settings, etc.
		state = ExecutionContext(topElement, default_graph, base=self.base, options=self.options, rdfa_version=self.rdfa_version)
		# The top level subject starts with the current document; this
		# is used by the recursion
		#subject = URIRef(state.base)
		# this function is the real workhorse
		parse_one_node(topElement, default_graph, None, state, [])
		
		# If the RDFS expansion has to be made, here is the place...
		if self.options.rdfa_sem :
			from pyRdfa.rdfs.process import process_rdfa_sem
			process_rdfa_sem(default_graph, self.options)
	
		# What should be returned depends on the way the options have been set up
		if self.options.output_default_graph :
			copyGraph(graph, default_graph)
			if self.options.output_processor_graph :
				if pgraph != None :
					copyGraph(pgraph, self.options.processor_graph.graph)
				else :					
					copyGraph(graph, self.options.processor_graph.graph)
		elif self.options.output_processor_graph :
			if pgraph != None :
				copyGraph(pgraph, self.options.processor_graph.graph)
			else :
				copyGraph(graph, self.options.processor_graph.graph)

		# this is necessary if several DOM trees are handled in a row...
		self.options.reset_processor_graph()

		return graph
	
	def graph_from_source(self, name, graph = None, rdfOutput = False, pgraph = None) :
		"""
		Extract an RDF graph from an RDFa source. The source is parsed, the RDF extracted, and the RDFa Graph is
		returned. This is a front-end to the L{pyRdfa.graph_from_DOM} method.
				
		@param name: a URI, a file name, or a file-like object
		@param graph: rdflib Graph instance. If None, a new one is created.
		@param pgraph: rdflib Graph instance for the processor graph. If None, and the error/warning triples are to be generated, they will be added to the returned graph. Otherwise they are stored in this graph.
		@param rdfOutput: whether exceptions should be turned into RDF and returned as part of the processor graph
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
			if self.options.host_language == HostLanguage.html :
				import warnings
				warnings.filterwarnings("ignore", category=DeprecationWarning)
				import html5lib
				parser = html5lib.HTMLParser(tree=html5lib.treebuilders.getTreeBuilder("dom"))
				if self.charset :
					# This means the HTTP header has provided a charset, or the
					# file is a local file when we suppose it to be a utf-8
					dom = parser.parse(input, encoding=self.charset)
				else :
					# No charset set. The HTMLLib parser tries to sniff into the
					# the file to find a meta header for the charset; if that
					# works, fine, otherwise it falls back on window-...
					dom = parser.parse(input)
					
			else :
				# in other cases an XML parser has to be used
				parse = xml.dom.minidom.parse
				dom = parse(input)
			#dom = parse(input,encoding='utf-8')
			return self.graph_from_DOM(dom, graph, pgraph)
		except FailedSource, f :
			if not rdfOutput : raise f
			self.options.add_error(f.msg, FileReferenceError, name)
			return copyErrors(graph, self.options)
		except Exception, e :
			(a,b,c) = sys.exc_info()
			sys.excepthook(a,b,c)
			#if not rdfOutput : raise e
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
	 - C{rfa-version} provides the RDFa version that should be used for distilling. The string should be of the form "1.0", "1.1", etc. Default is the highest version the current package implements.
	 - C{extras=[true|false]} means that extra, built-in transformers are executed on the DOM tree prior to RDFa processing. Default: false. Alternatively, a finer granurality can be used with the following options:
	  - C{extras-meta=[true|false]}: the @name attribute for metas are converted into @property for further processing
	  - C{extras-cc=[true|false]}: containers and collections are generated. See L{transform.containerscollections} for further details.
	 - C{host_language=[xhtml,html,xml]} : the host language. Used when files are uploaded or text is added verbatim, otherwise the HTTP return header should be used
	 - C{vocab-cache-report=[true|false]} : whether vocab caching details should be reported
	 - C{vocab-cache-bypass=[true|false]} : whether vocab caches have to be regenerated every time

	@param uri: URI to access. Note that the "text:" and "uploaded:" values are treated separately; the former is for textual intput (in which case a StringIO is used to get the data) and the latter is for uploaded file, where the form gives access to the file directly.
	@param outputFormat: serialization formats, as understood by RDFLib. 
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
		
	if "rdfa-version" in form.keys() :
		rdfa_version = form.getfirst("rdfa-version")
	else :
		rdfa_version = None
	
	# working through the possible options
	# Host language: HTML, XHTML, or XML
	# Note that these options should be used for the upload and inline version only in case of a form
	# for real uris the returned content type should be used
	if "host_language" in form.keys() :
		if form.getfirst("host_language").lower() == "xhtml" :
			media_type = MediaTypes.xhtml
		elif form.getfirst("host_language").lower() == "html" :
			media_type = MediaTypes.html
		elif form.getfirst("host_language").lower() == "svg" :
			media_type = MediaTypes.svg
		elif form.getfirst("host_language").lower() == "atom" :
			media_type = MediaTypes.atom
		else :
			media_type = MediaTypes.xml
	else :
		media_type = ""
		
	transformers = []
	if "extras" in form.keys() and form.getfirst("extras").lower() == "true" :
		from pyRdfa.transform.metaname              	import meta_transform
		from pyRdfa.transform.OpenID                	import OpenID_transform
		from pyRdfa.transform.DublinCore            	import DC_transform
		from pyRdfa.transform.containerscollections		import containers_collections
		transformers = [containers_collections, OpenID_transform, DC_transform, meta_transform]
	else :
		if "extra-meta" in form.keys() and form.getfirst("extra-meta").lower() == "true" :
			from pyRdfa.transform.metaname import meta_transform
			transformers.append(metaname)
		if "extra-openid" in form.keys() and form.getfirst("extra-openid").lower() == "true" :
			from pyRdfa.transform.OpenID import OpenID_transform
			transformers.append(OpenID_transform)
		if "extra-dc" in form.keys() and form.getfirst("extra-dc").lower() == "true" :
			from pyRdfa.transform.DublinCore import DC_transform
			transformers.append(DC_transform)
		if "extra-cc" in form.keys() and form.getfirst("extra-cc").lower() == "true" :
			from pyRdfa.transform.containerscollections import containers_collections
			transformers.append(containers_collections)
		# This is here only for backward compatibility
		if "extra-li" in form.keys() and form.getfirst("extra-li").lower() == "true" :
			from pyRdfa.transform.containerscollections import containers_collections
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

		
	space_preserve     = "space-preserve" in form.keys() and form.getfirst("space-preserve").lower() == "false"
	vocab_cache_report = "vocab-cache-report" in form.keys() and form.getfirst("vocab-cache-report").lower() == "true"
	bypass_vocab_cache = "vocab-cache-bypass" in form.keys() and form.getfirst("vocab-cache-bypass").lower() == "true"
	rdfa_sem           = "vocab-expansion" in form.keys() and form.getfirst("vocab-expansion").lower() == "true"
	vocab_cache        = "vocab-cache" in form.keys() and form.getfirst("vocab-cache").lower() == "true" 
	if vocab_cache_report : output_processor_graph = True

	options = Options(output_default_graph = output_default_graph,
					  output_processor_graph = output_processor_graph,
					  space_preserve=space_preserve,
					  transformers=transformers,
					  vocab_cache_report=vocab_cache_report,
					  bypass_vocab_cache=bypass_vocab_cache,
					  rdfa_sem=rdfa_sem,
					  vocab_cache=vocab_cache
					  )
	processor = pyRdfa(options = options, base = base, media_type = media_type, rdfa_version = rdfa_version)
	
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

