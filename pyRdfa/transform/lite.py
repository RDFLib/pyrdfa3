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

non_lite_attributes = ["resource","inlist","datatype","rev", "rel"]

def lite_prune(top, options) :
	"""
	@param top: a DOM node for the top level element
	@param options: invocation options
	@type options: L{Options<pyRdfa.Options>}
	"""
	def generate_warning(node, attr) :
		options.add_warning("Attribute %s is not used in RDFa Lite, ignored (element <%s>)" % (attr,node.tagName))

	def remove_attrs(node) :
		# first the @content; this has a special treatment
		if node.tagName != "meta" and node.hasAttribute("content") :
			generate_warning(node, "content")
			node.removeAttribute("content")
		else :
			for attr in non_lite_attributes :
				if node.hasAttribute(attr) :
					generate_warning(node, attr)
					node.removeAttribute(attr)
					
	
	remove_attrs(top)
	for n in top.childNodes :
		if n.nodeType == top.ELEMENT_NODE :
			lite_prune(n, options)

	