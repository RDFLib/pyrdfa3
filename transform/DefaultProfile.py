# -*- coding: utf-8 -*-
"""
Simple transfomer: Add a default @profile value, depending on the media type of the source.

@summary: Add a top "about" to <head> and <body>
@requires: U{RDFLib package<http://rdflib.net>}
@organization: U{World Wide Web Consortium<http://www.w3.org>}
@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}
@contact: Ivan Herman, ivan@w3.org
"""

"""
$Id: DefaultProfile.py,v 1.2 2010-10-26 14:32:33 ivan Exp $
$Date: 2010-10-26 14:32:33 $
"""

def add_default_profile(top, options) :
	"""
	@param top: a DOM node for the top level element
	@param options: invocation options
	@type options: L{Options<pyRdfa.Options>}
	"""
	from pyRdfa.Utils import default_profiles
	if options and (options.host_language in default_profiles) :
		# otherwise this is meaningless...
		prof = default_profiles[options.host_language]
		if not top.hasAttribute("profile") :
			top.setAttribute("profile",prof)
		else :
			dprofs = top.getAttribute("profile").strip()
			# maybe it is already there, so avoid adding it twice:
			if not (len(dprofs.split()) == 1 and dprofs == prof) :
				top.setAttribute("profile",prof + " " + dprofs)
