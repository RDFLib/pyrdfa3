# -*- coding: utf-8 -*-
"""
Simple transfomer: the C{@about=""} is added to the C{<head>} and C{<body>} elements (unless something is already there) for the HTML cases, and the root element for others.
Note that this transformer is always invoked by the parser because this behaviour is mandated by the RDFa syntax.

@summary: Add a top "about" to <head> and <body> or root element
@requires: U{RDFLib package<http://rdflib.net>}
@organization: U{World Wide Web Consortium<http://www.w3.org>}
@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}
@contact: Ivan Herman, ivan@w3.org
"""

"""
$Id: toplevelabout.py,v 1.3 2012-01-18 14:16:45 ivan Exp $
$Date: 2012-01-18 14:16:45 $
"""

def top_about(root, options, state) :
	"""
	@param root: a DOM node for the top level element
	@param options: invocation options
	@type options: L{Options<pyRdfa.options>}
	@param state: top level execution state
	@type state: L{State<pyRdfa.state>}
	"""
	def set_about(node) :
		if has_one_of_attributes(node, "rel", "rev") :
			if not has_one_of_attributes(top, "about", "src") :
				node.setAttribute("about","")
		else :
			if not has_one_of_attributes(node, "href", "resource", "about", "src") :
				node.setAttribute("about","")
	
	from pyRdfa.host import HostLanguage
	from pyRdfa.utils import has_one_of_attributes
	
	if not has_one_of_attributes(root, "about") :
		root.setAttribute("about","")
		
	if state.rdfa_version < "1.1" :
		if options.host_language in [ HostLanguage.xhtml, HostLanguage.html5, HostLanguage.xhtml5 ] :
			for top in root.getElementsByTagName("head") :
				if not has_one_of_attributes(top, "href", "resource", "about", "src") :
					set_about(top)
			for top in root.getElementsByTagName("body") :
				if not has_one_of_attributes(top, "href", "resource", "about", "src") :
					set_about(top)

