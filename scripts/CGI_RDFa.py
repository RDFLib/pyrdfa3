#!/usr/local/bin/python3
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
$Id: RDFa.py,v 1.27 2018/05/23 08:57:19 carcone Exp $
"""

__version__ = "4.0.0"
import cgi
import cgitb
import sys, os
#import StringIO
#cgi.print_environ()

if sys.platform == "darwin" :
	# this is my local machine
	sys.path.insert(0,'/Users/ivan/Library/Python')
	sys.path.insert(0,'/Users/ivan/Library/Python/RDFa')
	os.environ['PyRdfaCacheDir'] = '/Users/ivan/.pyrdfa-cache'
	cgitb.enable()

else :
	# This will have to be updated for the Python3 installation!!!
	# webencodings pip3 should also be done!!!
	sys.path.insert(0,"/usr/lib/python2.7/dist-packages")
	sys.path.insert(0,'/home/ivan/lib/python')
	os.environ['PyRdfaCacheDir'] = '/usr/local/apache/cgi/cgi-bin-other/RDFa/data-local'
	cgitb.enable(display=0, logdir="/home/nobody/tracebacks/")

from pyRdfa import processURI, RDFaError

# Register the RDFa JSON-LD serializer; for some reasons installing via pip did not work
from rdflib.plugin import register, Serializer
register('json', Serializer, 'rdflib_jsonld.serializer', 'JsonLDSerializer')

def err_message(msg) :
	from cleanhtml import clean_print
	print('Content-type: text/html; charset=utf-8')
	print('Status: 400 Invalid Input')
	print()
	print("<html>")
	print("<head>")
	print("<title>Error in RDFa processing</title>")
	print("</head><body>")
	print("<h1>Error in distilling RDFa</h1>")
	print("<p>")
	clean_print("pyRdfa cannot process this URI: %s", uri)
	print("</p>")
	if len(msg) != 0 :
		print("<p>")
		clean_print(msg)
		print("</p>")
	print("</body>")
	print("</html>")
	sys.exit(1)


def brett_test(uri) :

	if not sys.platform == "darwin" :
		from checkremote import check_url_safety, UnsupportedResourceError
		from urllib2 import HTTPError, URLError
		try:
			check_url_safety(uri)
		except HTTPError as e:
			err_message('HTTP Error with the error code: %s and the error message: "%s"' (e.code, e.reason))
		except URLError as e:
			err_message('URL Error with the error message: "%s"' % e.reason)
		except UnsupportedResourceError as e:
			msg = e.args[0] + ": " + e.args[1]
			err_message('Unsupported Resource Error with the error message "%s"' % msg)
		except Exception as e:
			l = len(e.args)
			msg = "" if l == 0 else (e.args[0] if l == 1 else e.args)
			err_message('Exception raised: "%s"' % msg)

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
		print('Content-type: text/html; charset=utf-8')
		print('Status: 400 Invalid Input')
		print()
		print("<html>")
		print("<head>")
		print("<title>Error in RDFa processing</title>")
		print("</head><body>")
		print("<h1>Error in distilling RDFa</h1>")
		print("<p>No URI has been specified</p>")
		print("</body>")
		print("</html>")
		sys.exit(1)

	try :
		uri = form.getfirst("uri")
	except :
		print('Content-type: text/html; charset=utf-8')
		print('Status: 400 Invalid Input')
		print()
		print("<html>")
		print("<head>")
		print("<title>Error in RDFa processing</title>")
		print("</head><body>")
		print("<h1>Error in distilling RDFa</h1>")
		print("<p>No URI has been specified</p>")
		print("</body>")
		print("</html>")
		sys.exit(1)

if "validate" in form  :
	from rdfavalidator import validateURI
	if not (uri == 'text:' or uri == 'uploaded:') :
		brett_test(uri)
	print('Content-Type: text/html; charset=utf-8')
	print()
	print(validateURI(uri, form))
else :
	try :
		# Thanks to Sergio and Diego for the idea and code for the referer branch
		if uri == "referer" :
			uri    = os.getenv('HTTP_REFERER')
			if uri is None:
				newuri = "http://www.w3.org/2012/pyRdfa/no_referer.html"
			else:
				brett_test(uri)
				newuri = "http://www.w3.org/2012/pyRdfa/extract?uri=" + uri
			print("Status: 307 Moved Temporarily")
			print("Location: " + newuri)
			print()
		else :
			# last point of check: use Brett's script to check the validity of the URI
			if not (uri == 'text:' or uri == 'uploaded:') :
				brett_test(uri)

			if "format" in form.keys() :
				format = form.getfirst("format")
			else :
				format = "turtle"
			retval = processURI(uri, format, form)
			print(retval)
	except Exception as e :
		l = len(e.args)
		msg = "" if l == 0 else (e.args[0] if l == 1 else e.args)
		err_message('Exception raised: "%s"' % msg)
