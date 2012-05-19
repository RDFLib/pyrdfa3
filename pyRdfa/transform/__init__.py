# -*- coding: utf-8 -*-
"""
Transformer sub-package for the pyRdfa package. It contains modules with transformer functions; each may be
invoked by pyRdfa to transform the dom tree before the "real" RDfa processing.

@summary: RDFa Transformer package
@requires: U{RDFLib package<http://rdflib.net>}
@organization: U{World Wide Web Consortium<http://www.w3.org>}
@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}
"""

"""
$Id: __init__.py,v 1.5 2012/05/19 14:48:17 ivan Exp $
$Date: 2012/05/19 14:48:17 $
"""
__version__ = "3.0"

# Here are the transfomer functions that are to be performed for all RDFa files, no matter what

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
		# The situation is a bit complicated: if a @resource is present without anything else, then it sets
		# the subject, ie, should be accepted...
		if has_one_of_attributes(root, "resource", "href", "src") :
			if has_one_of_attributes(root, "rel", "rev") :
				root.setAttribute("about","")
		else :
			root.setAttribute("about","")
		
	if options.host_language in [ HostLanguage.xhtml, HostLanguage.html5, HostLanguage.xhtml5 ] :
		if state.rdfa_version >= "1.1" :
			pass
		else :
			for top in root.getElementsByTagName("head") :
				if not has_one_of_attributes(top, "href", "resource", "about", "src") :
					set_about(top)
			for top in root.getElementsByTagName("body") :
				if not has_one_of_attributes(top, "href", "resource", "about", "src") :
					set_about(top)


def empty_safe_curie(node, options, state) :
	"""
	Remove the attributes whose value is an empty safe curie.
	
	@param node: a DOM node for the top level element
	@param options: invocation options
	@type options: L{Options<pyRdfa.options>}
	@param state: top level execution state
	@type state: L{State<pyRdfa.state>}
	"""
	def prune_safe_curie(node,name) :
		if node.hasAttribute(name) :
			av = node.getAttribute(name)
			if av == '[]' :
				node.removeAttribute(name)
				msg = "Attribute @%s uses an empty safe CURIE; the attribute is ignored" % name
				options.add_warning(msg, node=node)
				
	prune_safe_curie(node, "about")
	prune_safe_curie(node, "resource")
	for n in node.childNodes :
		if n.nodeType == node.ELEMENT_NODE :
			empty_safe_curie(n, options, state)



