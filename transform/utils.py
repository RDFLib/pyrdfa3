# -*- coding: utf-8 -*-
"""
Utilities to be used by the various transformers.

@requires: U{RDFLib package<http://rdflib.net>}
@organization: U{World Wide Web Consortium<http://www.w3.org>}
@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}
"""

"""
$Id: utils.py,v 1.1 2010-01-18 13:42:38 ivan Exp $
$Date: 2010-01-18 13:42:38 $
"""

from rdflib.RDF import RDFNS  as ns_rdf

def traverse_tree(node, func) :
	"""Traverse the whole element tree, and perform the function C{func} on all the elements.
	@param node: DOM element node
	@param func: function to be called on the node. Input parameter is a DOM Element Node. If the function returns a boolean True, the recursion is stopped.
	"""
	if func(node) :
		return

	for n in node.childNodes :
		if n.nodeType == node.ELEMENT_NODE :
			traverse_tree(n, func)

def rdf_prefix(html) :
	"""Extract the top level prefix used for RDF. Although in most cases it is
	'rdf', we cannot be sure...
	@param html: the DOM Node for the HTML element
	@return: prefix name
	"""
	dict = {}
	for i in range(0,html.attributes.length) :
		attr = html.attributes.item(i)
		if attr.prefix == "xmlns" :
			# yep, there is a namespace setting
			key = attr.localName
			if key != "" :
				# exclude the top level xmlns setting...
				uri = attr.value
				if uri == ns_rdf.__str__() :
					return key

	# if it has not been set, the system will set it for 'rdf'...
	return 'rdf'


def dump(node) :
	"""
	This is just for debug purposes: it prints the essential content of the node in the tree starting at node.

	@param node: DOM node
	"""
	def _printNode(node) :
		"""
		Print the content of the DOM node's attributes (just a crude print, nothing fancy)
		@param node: DOM node
		"""
		debugStr = 'Node: %s, typeof="%s" property="%s" rel="%s" rev="%s" resource="%s" about="%s"' % (node.tagName,node.getAttribute("typeof"),node.getAttribute("property"),node.getAttribute("rel"),node.getAttribute("rev"),node.getAttribute("resource"),node.getAttribute("about"))
		print debugStr
		return False

	for i in range(0,node.attributes.length) :
		attr = node.attributes.item(i)
		if attr.prefix == "xmlns" :
			print "... %s:%s='%s'" % (attr.prefix,attr.localName,attr.value)

	traverse_tree(node,_printNode)