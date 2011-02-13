# -*- coding: utf-8 -*-
"""
Host language sub-package for the pyRdfa package. It contains variables and possible modules necessary to manage various RDFa
host languages.

This module may have to be modified if a new host language is added to the system. In many cases the rdfa_core as a host language is enough, because there is no need for a special processing. However, some host languages may require a default profile, or their value may control some transformations, in which case additional data have to be added to this module. This module header contains all tables and arrays to be adapted, and the module content may contain specific transformation methods.


@summary: RDFa Transformer package
@requires: U{RDFLib package<http://rdflib.net>}
@organization: U{World Wide Web Consortium<http://www.w3.org>}
@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}

@var content_to_host_language: a dictionary mapping a media type to a host language
@var preferred_suffixes: mapping from preferred suffixes for media types; used if the file is local, ie, there is not HTTP return value for the media type. It corresponds to the preferred suffix in the media type registration
@var default_profiles: mapping from host languages to default profiles
@var accept_xml_base: list of host languages that accept the xml:base attribute for base setting
@var accept_xml_lang: list of host languages that accept the xml:lang attribute for language setting. Note that XHTML and HTML have some special rules, and those are hard coded...
@var accept_embedded_rdf: list of host languages that might also include RDF data using an embedded RDF/XML (e.g., SVG). That RDF data is merged with the output
@var host_dom_transforms: dictionary mapping a host language to an array of methods that are invoked at the beginning of the parsing process for a specific node. That function can do a last minute change on that DOM node, eg, adding or modifying an attribute. The method's signature is (node, state), where node is the DOM node, and state is the L{Execution context<pyRdfa.State.ExecutionContext>}.

"""

"""
$Id: __init__.py,v 1.2 2011-02-13 16:35:40 ivan Exp $
$Date: 2011-02-13 16:35:40 $
"""
__version__ = "3.0"

from pyRdfa.host.Atom import atom_add_entry_type

class HostLanguage :
	"""An enumeration style class: recognized host language types for RDFa. Some processing details may depend on these host languages."""
	rdfa_core 	= "RDFa Core"
	xhtml		= "XHTML+RDFa"
	html		= "HTML5+RDFa"
	atom		= "Atom+RDFa"
	svg			= "SVG+RDFa"
	smil		= "SMIL+RDFa"
	
class MediaTypes :
	"""An enumeration style class: some common media types (better have them at one place to avoid misstyping...)"""
	rdfxml 	= 'application/rdf+xml'
	turtle 	= 'text/turtle'
	html	= 'text/html'
	xhtml	= 'application/xhtml+xml'
	svg		= 'application/svg+xml'
	smil	= 'application/smil+xml'
	atom	= 'application/atom+xml'
	xml		= 'application/xml'
	xmlt	= 'text/xml'
	nt		= 'text/plain'
	
# mapping from (some) content types to RDFa host languages. This may control the exact processing or at least the default profile (see below)...
content_to_host_language = {
	MediaTypes.html		: HostLanguage.html,
	MediaTypes.xhtml	: HostLanguage.xhtml,
	MediaTypes.xml		: HostLanguage.rdfa_core,
	MediaTypes.xmlt		: HostLanguage.rdfa_core,
	MediaTypes.smil		: HostLanguage.smil,
	MediaTypes.svg		: HostLanguage.svg,
	MediaTypes.atom		: HostLanguage.atom,
}

# mapping preferred suffixes to media types...
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
	".nt"		: MediaTypes.nt,
	".atom"		: MediaTypes.atom
}
	
# default profiles for some of the host languages
# URI-s to be updated!!!!
rdfa_default_profile = "http://www.w3.org/2007/08/pyRdfa/profiles/sw-prefixes.ttl"

default_profiles = {
	HostLanguage.xhtml	: "http://www.w3.org/1999/xhtml/vocab",
	HostLanguage.html 	: "http://www.w3.org/1999/xhtml/vocab",
	#HostLanguage.atom	: "http://www.w3.org/2010/rdfa/atom_profile"
}

accept_xml_base		= [ HostLanguage.rdfa_core, HostLanguage.atom, HostLanguage.svg, HostLanguage.smil ]
accept_xml_lang		= [ HostLanguage.rdfa_core, HostLanguage.atom, HostLanguage.svg, HostLanguage.smil ]
accept_embedded_rdf	= [ HostLanguage.svg ]

host_dom_transforms = {
	HostLanguage.atom : [atom_add_entry_type]
}
