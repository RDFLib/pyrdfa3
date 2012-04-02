# -*- coding: utf-8 -*-
"""
URI data

@summary: RDFa Literal generation
@requires: U{RDFLib package<http://rdflib.net>}
@organization: U{World Wide Web Consortium<http://www.w3.org>}
@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}
"""

"""
$Id: uri.py,v 1.1 2010-10-05 10:34:22 ivan Exp $
$Date: 2010-10-05 10:34:22 $
"""

url_regexp = "^(([^:/?#]+):)?(//([^/?#]*))?([^?#]*)(\?([^#]*))?(#(.*))?"

registered_schemes = [
	"aaa",
	"aaas",
	"acap",
	"cap",
	"cid",
	"crid",
	"data",
	"dav",
	"dict",
	"dns",
	"fax",
	"file",
	"ftp",
	"geo",
	"go",
	"gopher",
	"h323",
	"http",
	"https",
	"iax",
	"icap",
	"im",
	"imap",
	"info",
	"ipp",
	"iris",
	"iris.beep",
	"iris.xpc",
	"iris.xpcs",
	"iris.lwz",
	"ldap",
	"mailto",
	"mid",
	"modem",
	"msrp",
	"msrps",
	"mtqp",
	"mupdate",
	"news",
	"nfs",
	"nntp",
	"opaquelocktoken",
	"pop",
	"pres",
	"rtsp",
	"service",
	"shttp",
	"sieve",
	"sip",
	"sips",
	"sms",
	"snmp",
	"soap.beep",
	"soap.beeps",
	"telnet",
	"tftp",
	"tv",
	"urn",
	"vemmi",
	"xmlrpc.beep",
	"xmlrpc.beeps",
	"xmpp",
	"z39.50r",
	"z39.50s",
	"afs",
	"dtn",
	"dvb",
	"icon",
	"mailserver",
	"pack",
	"rsync",
	"tn3270",
	"ws",
	"wss",
	"prospero",
	"snews",
	"videotex",
	"wais"
]
