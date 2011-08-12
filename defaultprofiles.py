# -*- coding: utf-8 -*-
"""
Built-in version of the default profile contents. 

@summary: Management of vocabularies, terms, and their mapping to URI-s.
@requires: U{RDFLib package<http://rdflib.net>}
@organization: U{World Wide Web Consortium<http://www.w3.org>}
@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}

@var default_profiles: prefix for the XHTML vocabulary URI (set to 'xhv')
"""

"""
$Id: defaultprofiles.py,v 1.1 2011-08-12 10:01:54 ivan Exp $
$Date: 2011-08-12 10:01:54 $
"""

class Wrapper :
	pass
	
default_profiles = {
	"http://www.w3.org/profile/rdfa-1.1" : Wrapper(),
	"http://www.w3.org/profile/html-rdfa-1.1" : Wrapper(),
}

default_profiles["http://www.w3.org/profile/rdfa-1.1"].ns = {
	'owl'		: 'http://www.w3.org/2002/07/owl#',
	'gr'		: 'http://purl.org/goodrelations/v1#',
	'ctag'		: 'http://commontag.org/ns#',
	'cc'		: 'http://creativecommons.org/ns#',
	'grddl'		: 'http://www.w3.org/2003/g/data-view#',
	'rif'		: 'http://www.w3.org/2007/rif#',
	'sioc'		: 'http://rdfs.org/sioc/ns#',
	'skos'		: 'http://www.w3.org/2004/02/skos/core#',
	'xml'		: 'http://www.w3.org/XML/1998/namespace',
	'rdfs'		: 'http://www.w3.org/2000/01/rdf-schema#',
	'rev'		: 'http://purl.org/stuff/rev#',
	'rdfa'		: 'http://www.w3.org/ns/rdfa#',
	'dc'		: 'http://purl.org/dc/terms/',
	'foaf'		: 'http://xmlns.com/foaf/0.1/',
	'void'		: 'http://rdfs.org/ns/void#',
	'ical'		: 'http://www.w3.org/2002/12/cal/icaltzd#',
	'vcard'		: 'http://www.w3.org/2006/vcard/ns#',
	'xmlns'		: 'http://www.w3.org/2000/xmlns/',
	'wdrs'		: 'http://www.w3.org/2007/05/powder-s#',
	'og'		: 'http://ogp.me/ns#',
	'wdr'		: 'http://www.w3.org/2007/05/powder#',
	'rdf'		: 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
	'xhv'		: 'http://www.w3.org/1999/xhtml/vocab#',
	'xsd'		: 'http://www.w3.org/2001/XMLSchema#',
	'v'			: 'http://rdf.data-vocabulary.org/#',
	'skosxl'	: 'http://www.w3.org/2008/05/skos-xl#',
}

default_profiles["http://www.w3.org/profile/rdfa-1.1"].terms = {
	'describedby'	: 'http://www.w3.org/2007/05/powder-s#describedby',
}

default_profiles["http://www.w3.org/profile/rdfa-1.1"].vocabulary = ""

default_profiles["http://www.w3.org/profile/html-rdfa-1.1"].ns = {
}

default_profiles["http://www.w3.org/profile/html-rdfa-1.1"].terms = {
	'p3pv1'				: 'http://www.w3.org/1999/xhtml/vocab#p3pv1',
	'help'				: 'http://www.w3.org/1999/xhtml/vocab#help',
	'meta'				: 'http://www.w3.org/1999/xhtml/vocab#meta',
	'contents'			: 'http://www.w3.org/1999/xhtml/vocab#contents',
	'index'				: 'http://www.w3.org/1999/xhtml/vocab#index',
	'copyright'			: 'http://www.w3.org/1999/xhtml/vocab#copyright',
	'bookmark'			: 'http://www.w3.org/1999/xhtml/vocab#bookmark',
	'section'			: 'http://www.w3.org/1999/xhtml/vocab#section',
	'alternate'			: 'http://www.w3.org/1999/xhtml/vocab#alternate',
	'next'				: 'http://www.w3.org/1999/xhtml/vocab#next',
	'start'				: 'http://www.w3.org/1999/xhtml/vocab#start',
	'stylesheet'		: 'http://www.w3.org/1999/xhtml/vocab#stylesheet',
	'role'				: 'http://www.w3.org/1999/xhtml/vocab#role',
	'subsection'		: 'http://www.w3.org/1999/xhtml/vocab#subsection',
	'prev'				: 'http://www.w3.org/1999/xhtml/vocab#prev',
	'cite'				: 'http://www.w3.org/1999/xhtml/vocab#cite',
	'appendix'			: 'http://www.w3.org/1999/xhtml/vocab#appendix',
	'itsRules'			: 'http://www.w3.org/1999/xhtml/vocab#itsRules',
	'icon'				: 'http://www.w3.org/1999/xhtml/vocab#icon',
	'chapter'			: 'http://www.w3.org/1999/xhtml/vocab#chapter',
	'last'				: 'http://www.w3.org/1999/xhtml/vocab#last',
	'license'			: 'http://www.w3.org/1999/xhtml/vocab#license',
	'glossary'			: 'http://www.w3.org/1999/xhtml/vocab#glossary',
	'up'				: 'http://www.w3.org/1999/xhtml/vocab#up',
	'transformation'	: 'http://www.w3.org/2003/g/data-view#transformation',
	'top'				: 'http://www.w3.org/1999/xhtml/vocab#top',
	'first'				: 'http://www.w3.org/1999/xhtml/vocab#first',
}

default_profiles["http://www.w3.org/profile/html-rdfa-1.1"].vocabulary = ""

