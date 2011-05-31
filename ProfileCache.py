# -*- coding: utf-8 -*-
"""
Managing Profile Caching.

@summary: RDFa parser (distiller)
@requires: U{RDFLib<http://rdflib.net>}
@organization: U{World Wide Web Consortium<http://www.w3.org>}
@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}
"""
import os, sys, datetime, re

import rdflib
from rdflib	import URIRef
from rdflib	import Literal
from rdflib	import BNode
from rdflib	import Namespace
if rdflib.__version__ >= "3.0.0" :
	from rdflib	import RDF  as ns_rdf
	from rdflib	import RDFS as ns_rdfs
	from rdflib	import Graph
else :
	from rdflib.RDFS	import RDFSNS as ns_rdfs
	from rdflib.RDF		import RDFNS  as ns_rdf
	from rdflib.Graph 	import Graph

import urllib, urlparse, urllib2
import httpheader

from pyRdfa			import HTTPError, RDFaError
from pyRdfa.host 	import MediaTypes, HostLanguage
from pyRdfa.Utils	import create_file_name, URIOpener, quote_URI
from pyRdfa.Options	import Options
from pyRdfa			import ns_rdfa
from pyRdfa			import IncorrectProfileDefinition, IncorrectPrefixDefinition
from pyRdfa			import ProfileCachingError, ProfileCachingInfo
from pyRdfa 		import FailedProfile

from pyRdfa import err_no_blank_node
from pyRdfa import err_outdated_cache
from pyRdfa import err_unreachable_profile
from pyRdfa import err_unparsable_Turtle_profile
from pyRdfa import err_unparsable_xml_profile
from pyRdfa import err_unparsable_ntriples_profile
from pyRdfa import err_unparsable_rdfa_profile
from pyRdfa import err_unrecognised_profile_type
from pyRdfa import err_more_vocab_URI_in_profile
from pyRdfa import err_non_literal_in_profile
from pyRdfa import err_non_ncname_in_profile
from pyRdfa import err_double_def_in_profile
from pyRdfa import err_same_subj_1_in_profile
from pyRdfa import err_same_subj_2_in_profile
from pyRdfa import err_no_URI_defined_in_profile
from pyRdfa import err_more_URI_defined_in_profile

#import Options

# Regular expression object for a general XML application media type
xml_application_media_type = re.compile("application/[a-zA-Z0-9]+\+xml")

from pyRdfa.Utils import URIOpener

#===========================================================================================
import cPickle as pickle
# Protocol to be used for pickle files. 0 is good for debug, it stores the data in ASCII; 1 is better for deployment,
# it stores data in binary format. Care should be taken for consistency; when changing from 0 to 1 or back, all
# cached data should be removed/regenerated, otherwise mess may occur...
_Pickle_Protocol = 1

# If I could rely on python 2.5 or 2.6 (or higher) I could use the with...as... idiom for what is below, it
# is indeed nicer. But I cannot...
def _load(fname) :
	"""
	Load a cached file and return the resulting object
	@param fname: file name
	"""
	try :
		f = open(fname)
		return pickle.load(f)
	finally :
		f.close()
	
def _dump(obj, fname) :
	"""
	Dump an object into cached file
	@param obj: Python object to store
	@param fname: file name
	"""
	try :
		f = open(fname, "w")
		pickle.dump(obj, f, _Pickle_Protocol)
		f.flush()
	finally :
		f.close()

#===========================================================================================
class CachedProfileIndex :
	"""
	Class to manage the cache index. Takes care of finding the profile directory, and manages the index
	to the individual profile data.
	
	The profile directory is set to a platform specific area, unless an environment variable
	sets it explicitly. The environment variable is "PyRdfaCacheDir"
	
	Every time the index is changed, the index is put back (via pickle) to the directory.
	
	@ivar app_data_dir: directory for the profile cache directory
	@ivar index_fname: the full path of the index file on the disc
	@ivar indeces: the in-memory version of the index (a directory mapping URI-s to tuples)
	@ivar options: the error handler (option) object to send warnings to
	@type options: L{Options.Options}
	@ivar report: whether details on the caching should be reported
	@type report: Boolean
	@cvar profiles: File name used for the index in the cache directory
	@cvar preference_path: Cache directories for the three major platforms (ie, mac, windows, unix)
	@type preference_path: directory, keyed by "mac", "win", and "unix"
	@cvar architectures: Various 'architectures' as returned by the python call, and their mapping on one of the major platforms. If an architecture is missing, it is considered to be "unix"
	@type architectures: directory, mapping architectures to "mac", "win", or "unix"
	"""
	# File Name used for the index in the cache directory
	profiles = "cache_index"
	# Cache directories for the three major platforms...
	preference_path = {
		"mac"	: "Library/Application Support/pyRdfa-cache",
		"win"	: "pyRdfa-cache",
		"unix"	: ".pyRdfa-cache"
	}
	# various architectures as returned by the python call, and their mapping on platorm. If an architecture is not here, it is considered as unix
	architectures = {
		"darwin"	: "mac",
		"nt" 		: "win",
		"win32"		: "win",
		"cygwin"	: "win"
	}
	def __init__(self, options = None, report = False) :
		"""
		@param options: the error handler (option) object to send warnings to
		@type options: L{Options.Options}
		@param report: whether details on the caching should be reported
		@type report: Boolean
		"""
		self.options = options
		self.report  = (options != None) and report
		
		# This is where the cache files should be
		self.app_data_dir	= self._give_preference_path()
		self.index_fname	= os.path.join(self.app_data_dir, self.profiles)
		self.indeces 		= {}
		
		# Check whether that directory exists.
		if not os.path.isdir(self.app_data_dir) :
			try :
				os.mkdir(self.app_data_dir)
			except Exception, e:
				(type,value,traceback) = sys.exc_info()
				if self.report: options.add_info("Could not create the profile cache area %s" % value, ProfileCachingInfo)
				return
		else :
			# check whether it is at least readable
			if not os.access(self.app_data_dir, os.R_OK) :
				if self.report: options.add_info("Profile cache directory is not readable", ProfileCachingInfo)
				return
			if not os.access(self.app_data_dir, os.W_OK) :
				if self.report: options.add_info("Profile cache directory is not writeable, but readable", ProfileCachingInfo)
				return

		if os.path.exists(self.index_fname) :
			if os.access(self.index_fname, os.R_OK) :
				self.indeces = _load(self.index_fname)
			else :
				if self.report: options.add_info("Profile cache index not readable", ProfileCachingInfo)				
		else :
			# This is the very initial phase, creation
			# of a a new index
			if os.access(self.app_data_dir, os.W_OK) :
				# This is then put into a pickle file to put the stake on the ground...
				try :
					_dump(self.indeces, self.index_fname)
				except Exception, e:
					if self.report: options.add_info("Could not create the profile index %s" % e.msg, ProfileCachingInfo)
			else :
				if self.report: options.add_info("Profile cache directory is not writeable", ProfileCachingInfo)				
				self.cache_writeable	= False	
				
				
	def add_ref(self, uri, profile_reference) :
		"""
		Add a new entry to the index, possibly removing the previous one.
		
		@param uri: the URI that serves as a key in the index directory
		@param profile_reference: tuple consisting of file name, modification date, and expiration date
		"""
		# Store the index right away
		self.indeces[uri] = profile_reference		
		try :
			_dump(self.indeces, self.index_fname)
		except Exception, e:
			(type,value,traceback) = sys.exc_info()
			if self.report: self.options.add_info("Could not store the profile index %s" % value, ProfileCachingInfo)
			
	def get_ref(self, uri) :
		"""
		Get an index entry, if available, None otherwise.
		The return value is a tuple: file name, modification date, and expiration date
		
		@param uri: the URI that serves as a key in the index directory		
		"""
		if uri in self.indeces :
			return tuple(self.indeces[uri])
		else :
			return None

	def _give_preference_path(self) :
		"""
		Find the profile cache directory.
		"""
		from pyRdfa	import CACHE_DIR_VAR
		if CACHE_DIR_VAR in os.environ :
			return os.environ[CACHE_DIR_VAR]
		else :
			# find the preference path on the architecture
			platform = sys.platform
			if platform in self.architectures :
				system = self.architectures[platform]
			else :
				system = "unix"
	
			if system == "win" :
				# there is a user variable that is set for that purpose
				app_data = os.path.expandvars("%APPDATA%")
				return os.path.join(app_data,self.preference_path[system])
			else :
				return os.path.join(os.path.expanduser('~'),self.preference_path[system])

#===========================================================================================
class CachedProfile(CachedProfileIndex) :
	"""
	Cache for a specific profile. The content of the cache are three fold: a dictionary of term mappings,
	a dictionary of prefix mappings, and a default vocabulary. These are also the data that are stored
	on the disc (in pickled form)
	
	@ivar terms: collection of all term mappings
	@type terms: dictionary
	@ivar ns: namespace mapping
	@type ns: dictionary
	@ivar vocabulary: default vocabulary
	@type vocabulary: string
	@ivar URI: profile URI
	@ivar filename: file name (not the complete path) of the cached version
	@ivar creation_date: creation date of the cache
	@type creation_date: datetime
	@ivar expiration_date: expiration date of the cache
	@type expiration_date: datetime
	@cvar runtime_cache : a run time cache for already 'seen' profiles. Apart from (marginally) speeding up processing, this also prevents recursion
	@type runtime_cache : dictionary
	"""
	local_cache = {}
	def __init__(self, URI, options = None, report = False) :
		"""
		@param URI: real URI for the profile
		@param options: the error handler (option) object to send warnings to
		@type options: L{Options.Options}
		@param report: whether details on the caching should be reported
		@type report: Boolean
		"""
		# First see if this particular profile has been handled before. If yes, it is extracted and everything
		# else can be forgotten. 
		self.uri													= URI
		(self.filename, self.creation_date, self.expiration_date)	= ("",None,None)
		(self.terms, self.ns, self.vocabulary)						= ({},{},"")

		if URI in CachedProfile.local_cache :
			(self.terms, self.ns, self.vocabulary) = CachedProfile.local_cache[URI]
			if (options != None) and report: options.add_info("Reading local cache for %s" % URI, ProfileCachingInfo)
			return

		try :
			CachedProfileIndex.__init__(self, options, report)
			profile_reference 	= self.get_ref(URI)
			self.caching 		= True
		except Exception, e :
			# what this means is that the caching becomes impossible ProfileCachingError
			(type,value,traceback) = sys.exc_info()
			if self.report: options.add_info("Could not access the profile cache area %s" % value, ProfileCachingError, URI)
			profile_reference	= None
			self.caching		= False

		# Get the stake in the ground in the local cache to avoid recursion on the same profile file
		CachedProfile.local_cache[URI] = ({},{},"")
		
		if profile_reference == None :
			# This has never been cached before
			if self.report: options.add_info("No cache exists, has to generate a new one for %s" % URI, ProfileCachingInfo)
			
			self._get_profile_data(newCache=True)
			# Store all the cache data unless caching proves to be impossible
			if self.caching :
				self.filename = create_file_name(self.uri)
				self._store_caches()
		else :
			(self.filename, self.creation_date, self.expiration_date) = profile_reference
			if self.report: options.add_info("Got a cache for %s, expiring on %s" % (URI,self.expiration_date), ProfileCachingInfo)
			# Check if the expiration date is still away
			if datetime.datetime.utcnow() <= self.expiration_date :
				# We are fine, we can just extract the data from the cache and we're done
				if self.report: options.add_info("Just extracting the data from the cache for %s" % URI, ProfileCachingInfo)
				fname = os.path.join(self.app_data_dir, self.filename)
				try :
					(self.terms, self.ns, self.vocabulary) = tuple(_load(fname))
				except Exception, e :
					# what this means is that the caching becomes impossible ProfileCachingError
					(type,value,traceback) = sys.exc_info()
					sys.excepthook(type,value,traceback)
					if self.report: options.add_info("Could not access the profile cache %s (%s)" % (value,fname), ProfileCachingError, URI)
			else :
				if self.report: options.add_info("Refreshing the cache for %s (ie, getting the graph)" % URI, ProfileCachingInfo)
				# we have to refresh the graph
				if self._get_profile_data(newCache=False) == None :
					# bugger; the cache could not be refreshed, using the current one, and setting the cache artificially
					# to be valid for the coming hour, hoping that the access issues will be resolved by then...
					fname = os.path.join(self.app_data_dir, self.filename)
					try :
						(self.terms, self.ns, self.vocabulary) = tuple(_load(fname))
						self.expiration_date = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
					except Exception, e :
						# what this means is that the caching becomes impossible ProfileCachingError
						(type,value,traceback) = sys.exc_info()
						sys.excepthook(type,value,traceback)
						if self.report: options.add_info("Could not access the profile cache %s (%s)" % (value,fname), ProfileCachingError, URI)
				self.creation_date = datetime.datetime.utcnow()
				self._store_caches()

		# Store the local cache to avoid indirection
		CachedProfile.local_cache[URI] = (self.terms, self.ns, self.vocabulary)

	def _get_profile_data(self,newCache=True) :
		"""Just a macro-like method: get the graph from the profile file with a URI, and then extract the
		profile data (ie, add values to self.terms, self.ns, and self.vocabulary). The real work is done in the
		L{_get_graph} and L{_extract_profile_info} methods.
		"""
		g = self._get_graph(newCache)
		if g != None :
			self._extract_profile_info(g)
		else :
			return None
		
	def _get_graph(self,newCache) :
		"""
		Parse the vocabulary file, and return an RDFLib Graph. The URI's content type is checked and either one of
		RDFLib's parsers is invoked (for the Turtle, RDF/XML, and N Triple cases) or a separate RDFa processing is invoked
		on the RDFa content.
				
		The Accept header of the HTTP request gives a preference to Turtle, followed by HTML (RDFa), and then RDF/XML in case content negotiation is used.
		
		@return: An RDFLib Graph instance; None if the dereferencing or the parsing was unsuccessful
		@raise FailedProfile: if the profile document could not be dereferenced or is not a known media type. Note that this is caught higher up in the parser and that terminates processing on the whole subtree.
		"""
		def return_to_cache(msg) :
			if newCache :
				raise FailedProfile(err_unreachable_profile % self.uri, self.uri)
			else :
				self.options.add_warning(err_outdated_cache % self.uri)
		
		content = None
		try :
			content = URIOpener(self.uri,
							    {'Accept' : 'text/html;q=0.8, application/xhtml+xml;q=0.8, text/turtle;q=1.0, application/rdf+xml;q=0.7'})

		except HTTPError, e :
			return_to_cache(e.msg)
			return None
		except RDFaError, e :
			return_to_cache(e.msg)
			return None
		except Exception, e :
			(type,value,traceback) = sys.exc_info()
			return_to_cache(value)
			return None
		
		# Store the expiration date of the newly accessed data
		self.expiration_date = content.expiration_date
				
		if content.content_type == MediaTypes.turtle :
			try :
				retval = Graph()
				retval.parse(content.data, format="n3")
				return retval
			except :
				(type,value,traceback) = sys.exc_info()
				raise FailedProfile(err_unparsable_Turtle_profile % (self.uri,value), self.uri)
		elif content.content_type == MediaTypes.rdfxml :
			try :
				retval = Graph()
				retval.parse(content.data)
				return retval
			except :
				(type,value,traceback) = sys.exc_info()
				raise FailedProfile(err_unparsable_Turtle_profile % (self.uri,value), self.uri)
		elif content.content_type == MediaTypes.nt :
			try :
				retval = Graph()
				retval.parse(content.data, format="nt")
				return retval
			except :
				(type,value,traceback) = sys.exc_info()
				raise FailedProfile(err_unparsable_ntriples_profile % (self.uri,value), self.uri)
		elif content.content_type in [MediaTypes.xhtml, MediaTypes.html, MediaTypes.xml] or xml_application_media_type.match(content.content_type) != None :
			try :
				from pyRdfa import pyRdfa
				from pyRdfa.Options	import Options
				options = Options()
				return pyRdfa(options).graph_from_source(content.data)
			except :
				(type,value,traceback) = sys.exc_info()
				print type
				print value
				raise FailedProfile(err_unparsable_rdfa_profile % (self.uri,value), self.uri)
		else :
			raise FailedProfile(err_unrecognised_profile_type % (self.uri, content.content_type), self.uri)

	def _extract_profile_info(self, graph) :
		"""
		Extract the profile information from a graph.
		@param graph: the graph to extract the triplets from		
		"""
		if graph == None :
			return		
		# Find the vocabulary first
		voc_defs = [ uri for uri in graph.objects(None,ns_rdfa["vocabulary"]) ]				
		# if the array is bigger than 1, this means several vocabulary definitions have been added
		# which is not acceptable...
		if len(voc_defs) == 1 :
			self.vocabulary = str(voc_defs[0])
		elif len(voc_defs) > 1 :
			self.state.options.add_warning(err_more_vocab_URI_in_profile, IncorrectProfileDefinition, self.uri)
			
		self._find_terms(graph,"term")
		self._find_terms(graph,"prefix")
				
	def _find_terms(self, graph, term_or_prefix) :
		"""
		Extract the term/prefix definitions from the graph and fill in the necessary dictionaries. A load
		of possible warnings are checked and handled.
		@param graph: the graph to extract the triplets from
		@param term_or_prefix: the string "term" or "prefix"
		"""
		from pyRdfa.TermOrCurie import ncname
		opposite_term_or_prefix = ((term_or_prefix == "term") and "prefix") or "term"
			
		# Note the usage of frozenset: it removes duplicates
		for term in frozenset([ term for term in graph.objects(None, ns_rdfa[term_or_prefix]) ]) :
			e_tuple = (term_or_prefix, term)
			
			# check if the term is really a literal and and and NCNAME
			# that is an error
			if not isinstance(term, Literal) :
				self.options.add_warning(err_non_literal_in_profile % e_tuple, IncorrectProfileDefinition, self.uri)
				continue
			# check of the term is really a valid literal, ie, an NCNAME
			if ncname.match(term) == None :
				self.options.add_warning(err_non_ncname_in_profile % e_tuple, IncorrectProfileDefinition, self.uri)
				continue
			
			# find all the subjects for a specific term. If there are more than one, that is an error
			subjs = [ subj for subj in graph.subjects(ns_rdfa[term_or_prefix],term) ]
			if len(subjs) != 1 :
				self.options.add_warning(err_double_def_in_profile % e_tuple, IncorrectProfileDefinition, self.uri)
				continue
			
			# we got THE subject!
			subj = subjs[0]
			
			# check if the same subj has been used for several term definitions
			if len([ oterm for oterm in graph.objects(subj,ns_rdfa[term_or_prefix]) ]) != 1 :
				self.options.add_warning(err_same_subj_1_in_profile % e_tuple, IncorrectProfileDefinition, self.uri)
				continue
			# check if the same subj has been used for prefix definion, too; if so, that is an error
			if len([pr for pr in graph.objects(subj,ns_rdfa[opposite_term_or_prefix])]) != 0 :
				# if we get here, the same subject has been reused, which is not allowed
				self.options.add_warning(err_same_subj_2_in_profile % (term_or_prefix, opposite_term_or_prefix, term, pr), IncorrectProfileDefinition, self.uri)
				continue
				
			# The subject is also kosher, we can get the uris
			uris = [ uri for uri in graph.objects(subj,ns_rdfa["uri"]) ]
			if len(uris) == 0 :
				self.options.add_warning(err_no_URI_defined_in_profile % e_tuple, IncorrectProfileDefinition, self.uri)
			elif len(uris) > 1 :
				self.options.add_warning(err_more_URI_defined_in_profile % e_tuple, IncorrectProfileDefinition, self.uri)
			else :
				if term_or_prefix == "term" :
					self.terms[unicode(term)] = unicode(uris[0])
				else :
					self.ns[unicode(term).lower()] = quote_URI(uris[0], self.options)
		
	def _store_caches(self) :
		"""Called if the creation date, etc, have been refreshed or new, and
		all content must be put into a cache file
		"""
		# Store the cached version of the profile
		fname = os.path.join(self.app_data_dir, self.filename)
		try :
			_dump((self.terms, self.ns, self.vocabulary), fname)
		except Exception, e :
			(type,value,traceback) = sys.exc_info()
			if self.report : self.options.add_info("Could not write cache file %s (%s)", (fname,value), ProfileCachingInfo)
		# Update the index
		self.add_ref(self.uri,(self.filename, self.creation_date, self.expiration_date))
		
		
##############################################################################################################################################

def offline_cache_generation(args) :
	"""Generate a cache for the profile in args.
	
	@param args: array of profile URIs.
	"""
	class LocalOption :
		def __init__(self) :
			pass
		def pr(self, wae, txt, warning_type, context) :
			print "===="
			if warning_type != None : print warning_type
			print wae + ": " + txt
			if context != None: print context
			print "===="
			
		def add_warning(self, txt, warning_type=None, context=None) :
			"""Add a warning to the processor graph.
			@param txt: the warning text. 
			@keyword warning_type: Warning Class
			@type warning_type: URIRef
			@keyword context: possible context to be added to the processor graph
			@type context: URIRef or String
			"""
			self.pr("Warning",txt,warning_type,context)
	
		def add_info(self, txt, info_type=None, context=None) :
			"""Add an informational comment to the processor graph.
			@param txt: the information text. 
			@keyword info_type: Info Class
			@type info_type: URIRef
			@keyword context: possible context to be added to the processor graph
			@type context: URIRef or String
			"""
			self.pr("Info",txt,info_type,context)
	
		def add_error(self, txt, err_type=None, context=None) :
			"""Add an error  to the processor graph.
			@param txt: the information text. 
			@keyword err_type: Error Class
			@type err_type: URIRef
			@keyword context: possible context to be added to the processor graph
			@type context: URIRef or String
			"""
			self.pr("Error",txt,err_type,context)
			
	for uri in args :
		# This should write the cache
		print ">>>>> Writing Cache <<<<<"
		writ = CachedProfile(uri,options = LocalOption(),report = True)
		# Now read it back and print the content for tracing
		print ">>>>> Reading Cache <<<<<"
		rd = CachedProfile(uri,options = LocalOption(),report = True)
		print "URI: " + uri
		print "default vocab: " + rd.vocabulary
		print "terms: ",
		print rd.terms
		print "prefixes: ",
		print rd.ns

	