
# -*- coding: utf-8 -*-
"""
Built-in version of the default profile contents. The code may use this directly instead of caching the
vocabulary.

@summary: Management of vocabularies, terms, and their mapping to URI-s.
@requires: U{RDFLib package<http://rdflib.net>}
@organization: U{World Wide Web Consortium<http://www.w3.org>}
@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}

@var default_profiles: prefix for the XHTML vocabulary URI (set to 'xhv')
"""

"""
$Id: DefaultProfiles.py,v 1.1 2011-04-20 11:02:21 ivan Exp $
$Date: 2011-04-20 11:02:21 $
"""

class Wrapper :
	pass
	
default_profiles = {
	"http://www.w3.org/profile/rdfa-1.1" : Wrapper(),
	"http://www.w3.org/profile/html-rdfa-1.1" : Wrapper(),
}

default_profiles["http://www.w3.org/profile/rdfa-1.1"].ns = {
	'owl'	: 'http://www.w3.org/2002/07/owl#',
	'dbp-owl'	: 'http://dbpedia.org/ontology/',
	'gr'	: 'http://purl.org/goodrelations/v1#',
	'cc'	: 'http://creativecommons.org/ns#',
	'grddl'	: 'http://www.w3.org/2003/g/data-view#',
	'rif'	: 'http://www.w3.org/2007/rif#',
	'dbp'	: 'http://dbpedia.org/property/',
	'sioc'	: 'http://rdfs.org/sioc/ns#',
	'dbr'	: 'http://dbpedia.org/resource/',
	'skos'	: 'http://www.w3.org/2004/02/skos/core#',
	'xml'	: 'http://www.w3.org/XML/1998/namespace',
	'rdfs'	: 'http://www.w3.org/2000/01/rdf-schema#',
	'rdfa'	: 'http://www.w3.org/ns/rdfa#',
	'dcterms'	: 'http://purl.org/dc/terms/',
	'foaf'	: 'http://xmlns.com/foaf/0.1/',
	'bibo'	: 'http://purl.org/ontology/bibo/',
	'void'	: 'http://rdfs.org/ns/void#',
	'v'	: 'http://rdf.data-vocabulary.org/#',
	'doap'	: 'http://usefulinc.com/ns/doap#',
	'dc'	: 'http://purl.org/dc/elements/1.1/',
	'geo'	: 'http://www.w3.org/2003/01/geo/wgs84_pos#',
	'vcard'	: 'http://www.w3.org/2006/vcard/ns#',
	'rss'	: 'http://purl.org/rss/1.0/',
	'xmlns'	: 'http://www.w3.org/2000/xmlns/',
	'wdrs'	: 'http://www.w3.org/2007/05/powder-s#',
	'og'	: 'http://ogp.me/ns#',
	'wdr'	: 'http://www.w3.org/2007/05/powder#',
	'rdf'	: 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
	'xhv'	: 'http://www.w3.org/1999/xhtml/vocab#',
	'xsd'	: 'http://www.w3.org/2001/XMLSchema#',
	'cal'	: 'http://www.w3.org/2002/12/cal/ical#',
	'skosxl'	: 'http://www.w3.org/2008/05/skos-xl#',
	'sd'	: 'http://www.w3.org/ns/sparql-service-description#',
}

default_profiles["http://www.w3.org/profile/rdfa-1.1"].terms = {
	'describedby'	: 'http://www.w3.org/2007/05/powder-s#describedby',
}

default_profiles["http://www.w3.org/profile/rdfa-1.1"].vocabulary = ""

default_profiles["http://www.w3.org/profile/html-rdfa-1.1"].ns = {
}

default_profiles["http://www.w3.org/profile/html-rdfa-1.1"].terms = {
	'p3pv1'	: 'http://www.w3.org/1999/xhtml/vocab#p3pv1',
	'help'	: 'http://www.w3.org/1999/xhtml/vocab#help',
	'meta'	: 'http://www.w3.org/1999/xhtml/vocab#meta',
	'contents'	: 'http://www.w3.org/1999/xhtml/vocab#contents',
	'index'	: 'http://www.w3.org/1999/xhtml/vocab#index',
	'copyright'	: 'http://www.w3.org/1999/xhtml/vocab#copyright',
	'bookmark'	: 'http://www.w3.org/1999/xhtml/vocab#bookmark',
	'top'	: 'http://www.w3.org/1999/xhtml/vocab#top',
	'alternate'	: 'http://www.w3.org/1999/xhtml/vocab#alternate',
	'next'	: 'http://www.w3.org/1999/xhtml/vocab#next',
	'start'	: 'http://www.w3.org/1999/xhtml/vocab#start',
	'stylesheet'	: 'http://www.w3.org/1999/xhtml/vocab#stylesheet',
	'role'	: 'http://www.w3.org/1999/xhtml/vocab#role',
	'subsection'	: 'http://www.w3.org/1999/xhtml/vocab#subsection',
	'prev'	: 'http://www.w3.org/1999/xhtml/vocab#prev',
	'transformation'	: 'http://www.w3.org/2003/g/data-view#transformation',
	'appendix'	: 'http://www.w3.org/1999/xhtml/vocab#appendix',
	'itsRules'	: 'http://www.w3.org/1999/xhtml/vocab#itsRules',
	'icon'	: 'http://www.w3.org/1999/xhtml/vocab#icon',
	'chapter'	: 'http://www.w3.org/1999/xhtml/vocab#chapter',
	'last'	: 'http://www.w3.org/1999/xhtml/vocab#last',
	'license'	: 'http://www.w3.org/1999/xhtml/vocab#license',
	'glossary'	: 'http://www.w3.org/1999/xhtml/vocab#glossary',
	'up'	: 'http://www.w3.org/1999/xhtml/vocab#up',
	'cite'	: 'http://www.w3.org/1999/xhtml/vocab#cite',
	'section'	: 'http://www.w3.org/1999/xhtml/vocab#section',
	'first'	: 'http://www.w3.org/1999/xhtml/vocab#first',
}

default_profiles["http://www.w3.org/profile/html-rdfa-1.1"].vocabulary = ""

