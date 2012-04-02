# -*- coding: utf-8 -*-
"""
Simple transfomer: C{meta} element is extended with a C{property} attribute, with a copy of the
C{name} attribute values.

@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}
@contact: Ivan Herman, ivan@w3.org
@version: $Id: metaname.py,v 1.1 2011/08/12 10:10:33 ivan Exp $
$Date: 2011/08/12 10:10:33 $
"""

def meta_transform(html, options) :
	"""
	@param html: a DOM node for the top level html element
	@param options: invocation options
	@type options: L{Options<pyRdfa.Options>}
	"""
	from pyRdfa.host import HostLanguage
	if not( options.host_language in [ HostLanguage.xhtml, HostLanguage.html ] ) :
		return

	for meta in html.getElementsByTagName("meta") :
		if meta.hasAttribute("name") and not meta.hasAttribute("property") :
			meta.setAttribute("property", meta.getAttribute("name"))

