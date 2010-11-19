# -*- coding: utf-8 -*-
"""
Simple transfomer for Atom: the C{@typeof=""} is added to the C{<entry>} element (unless something is already there).

@summary: Add a top "about" to <head> and <body>
@requires: U{RDFLib package<http://rdflib.net>}
@organization: U{World Wide Web Consortium<http://www.w3.org>}
@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}
@contact: Ivan Herman, ivan@w3.org
"""

"""
$Id: Atom.py,v 1.1 2010-11-19 13:52:32 ivan Exp $
$Date: 2010-11-19 13:52:32 $
"""

def add_entry_type(node, state) :
	"""
	@param node: the current node that could be modified
	@param state: current state
	@type options: L{Options<pyRdfa.Options>}
	@type state: L{Execution context<pyRdfa.State.ExecutionContext>}
	"""
	if node.tagName == "entry" and node.hasAttribute("typeof") == False :
		node.setAttribute("typeof","")
