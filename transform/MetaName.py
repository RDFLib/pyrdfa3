# -*- coding: utf-8 -*-
"""
Simple transfomer: C{meta} element is extended with a C{property} attribute, with a copy of the
C{name} attribute values.

@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}
@contact: Ivan Herman, ivan@w3.org
@version: $Id: MetaName.py,v 1.1 2010-01-18 13:42:38 ivan Exp $
$Date: 2010-01-18 13:42:38 $
"""

def meta_transform(html, options) :
	"""
	@param html: a DOM node for the top level html element
	@param options: invocation options
	@type options: L{Options<pyRdfa.Options>}
	"""
	for meta in html.getElementsByTagName("meta") :
		if meta.hasAttribute("name") and not meta.hasAttribute("property") :
			meta.setAttribute("property", meta.getAttribute("name"))

