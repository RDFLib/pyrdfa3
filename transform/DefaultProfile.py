# -*- coding: utf-8 -*-
"""
Simple transfomer: Add a default @profile value, depending on the media type of the source. The
mapping is defined in L{pyRdfa.host.default_profiles}.

@summary: Add a top "about" to <head> and <body>
@requires: U{RDFLib package<http://rdflib.net>}
@organization: U{World Wide Web Consortium<http://www.w3.org>}
@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}
@contact: Ivan Herman, ivan@w3.org
"""

"""
$Id: DefaultProfile.py,v 1.5 2011-03-08 10:50:15 ivan Exp $
$Date: 2011-03-08 10:50:15 $
"""

def add_default_profile(node, options) :
	"""
	@param node: a DOM node for the top level element
	@param options: invocation options
	@type options: L{Options<pyRdfa.Options>}
	"""	
	from pyRdfa.host import default_profiles
	if options and options.host_language in default_profiles :
		list_of_profiles = default_profiles[options.host_language]
		if len(list_of_profiles) > 0 : 
			proftxt = ""
			for pr in list_of_profiles :
				proftxt += pr + " "
			# Modify the dom
			if node.hasAttribute("profile") :
				dprofs = node.getAttribute("profile").strip()
				node.setAttribute("profile",proftxt + dprofs)
			else :
				node.setAttribute("profile",proftxt.strip())
