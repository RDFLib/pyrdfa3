#!/usr/bin/python2.5
# -*- coding: utf-8 -*-
# Maintainer: Ivan Herman <ivan@w3.org>

"""
Possible CGI entry point for the RDFa 1.1 package.

This version is adapted to the particualarities of the W3C setup as well as my own machine for Python paths


@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}
@contact: Ivan Herman, ivan@w3.org
"""

"""
$Id: RDFa.py,v 1.9 2012/03/12 11:06:47 ivan Exp $
"""

__version__ = "3.0"
import cgi
import cgitb; cgitb.enable()
import sys, os
import StringIO
#cgi.print_environ()

if sys.platform == "darwin" :
	# this is my local machine
	sys.path.insert(0,"/Users/ivan/W3C/dev/2004/PythonLib-IH")
	sys.path.insert(0,"/Users/ivan/Library/Python")
	sys.path.insert(0,"/Users/ivan/W3C/dev/2004/PythonLib-IH/rdfa-1.1")
	os.environ['PyRdfaCacheDir'] = '/Users/ivan/.pyrdfa-cache'
else :
	# this is the server on W3C
	sys.path.insert(0,"/usr/local/lib/python2.4/site-packages/PythonLib-IH")
	sys.path.insert(0,"/usr/local/lib/python2.4/site-packages/PythonLib-IH/rdfa-1.1")
	os.environ['PyRdfaCacheDir'] = '/usr/local/apache/cgi/cgi-bin-other/RDFa/data-local'

from pyRdfa import processURI, RDFaError

#
# to make this thing exist...
uri  = ""
form = cgi.FieldStorage()
# First see if an upload is present in the form
if "uploaded" in form and form["uploaded"].file :
	uri = "uploaded:"
elif "text" in form and form["text"].value != None and len(form["text"].value.strip()) != 0 :
	uri  = "text:"
else :
	if not "uri" in form :
		print 'Content-type: text/html; charset=utf-8'
		print 'Status: 400 Invalid Input'
		print
		print "<html>"
		print "<head>"
		print "<title>Error in RDFa processing</title>"
		print "</head><body>"
		print "<h1>Error in distilling RDFa</h1>"
		print "No URI has been specified"
		print "</body>"
		print "</html>"
		sys.exit(1)

	try :
		#uri = form["uri"].value
		uri = form.getfirst("uri")
	except :
		print 'Content-type: text/html; charset=utf-8'
		print 'Status: 400 Invalid Input'
		print
		print "<html>"
		print "<head>"
		print "<title>Error in RDFa processing</title>"
		print "</head><body>"
		print "<h1>Error in distilling RDFa</h1>"
		print "No URI has been specified"
		print "</body>"
		print "</html>"
		sys.exit(1)

if "validate" in form  :
	from rdfavalidator import validateURI
	print 'Content-Type: text/html; charset=utf-8'
	print
	print validateURI(uri, form)
else :
	# Thanks to Sergio and Diego for the idea and code for the referer branch
	if uri == "referer" :
		uri    = os.getenv('HTTP_REFERER')
		newuri = "http://www.w3.org/2012/pyRdfa/extract?uri=" + uri
		print "Status: 302 Moved"
		print "Location: " + newuri
		print
	else :
		if "format" in form.keys() :
			format = form.getfirst("format")
		else :
			format = "turtle"
		retval = processURI(uri, format, form)
		print retval
