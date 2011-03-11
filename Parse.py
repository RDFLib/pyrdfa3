# -*- coding: utf-8 -*-
"""
The core parsing function of RDFa. Some details are
put into other modules to make it clearer to update/modify (eg, generation of literals, or managing the current state).

@summary: RDFa core parser processing step
@requires: U{RDFLib package<http://rdflib.net>}
@organization: U{World Wide Web Consortium<http://www.w3.org>}
@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}
"""

"""
$Id: Parse.py,v 1.13 2011-03-11 14:12:12 ivan Exp $
$Date: 2011-03-11 14:12:12 $

Added a reaction on the RDFaStopParsing exception: if raised while setting up the local execution context, parsing
is stopped (on the whole subtree)
"""

import sys

from pyRdfa.State   		import ExecutionContext
from pyRdfa.Literal 		import generate_literal
from pyRdfa.EmbeddedRDF	 	import handle_embeddedRDF
from pyRdfa.host			import HostLanguage, host_dom_transforms, accept_embedded_rdf

import rdflib
from rdflib	import URIRef
from rdflib	import Literal
from rdflib	import BNode
from rdflib	import Namespace
if rdflib.__version__ >= "3.0.0" :
	from rdflib	import Graph
	from rdflib	import RDF  as ns_rdf
	from rdflib	import RDFS as ns_rdfs
else :
	from rdflib.Graph	import Graph
	from rdflib.RDFS	import RDFSNS as ns_rdfs
	from rdflib.RDF		import RDFNS  as ns_rdf

from pyRdfa import IncorrectBlankNodeUsage, FailedProfile, ProfileReferenceError

#######################################################################
# Function to check whether one of a series of attributes
# is part of the DOM Node
def _has_one_of_attributes(node,*args) :
	"""
	Check whether one of the listed attributes is present on a (DOM) node.
	@param node: DOM element node
	@param args: possible attribute names
	@return: True or False
	@rtype: Boolean
	"""
	return True in [ node.hasAttribute(attr) for attr in args ]

#######################################################################
def parse_one_node(node, graph, parent_object, incoming_state, parent_incomplete_triples) :
	"""The (recursive) step of handling a single node. See the
	U{RDFa syntax document<http://www.w3.org/TR/rdfa-syntax>} for further details.

	@param node: the DOM node to handle
	@param graph: the RDF graph
	@type graph: RDFLib's Graph object instance
	@param parent_object: the parent's object, as an RDFLib URIRef
	@param incoming_state: the inherited state (namespaces, lang, etc)
	@type incoming_state: L{State.ExecutionContext}
	@param parent_incomplete_triples: list of hanging triples (the missing resource set to None) to be handled (or not)
	by the current node.
	@return: whether the caller has to complete it's parent's incomplete triples
	@rtype: Boolean
	"""

	# Update the state. This means, for example, the possible local settings of
	# namespaces and lang
	state = None
	try :
		state = ExecutionContext(node, graph, inherited_state=incoming_state)
	except FailedProfile, f :
		bnode = incoming_state.options.add_error(f.msg, ProfileReferenceError, f.context)
		if f.http_code :
			incoming_state.options.processor_graph.add_http_context(bnode, f.http_code)
		return

	#---------------------------------------------------------------------------------
	# Handle the special case for embedded RDF, eg, in SVG1.2. 
	# This may add some triples to the target graph that does not originate from RDFa parsing
	# If the function return TRUE, that means that an rdf:RDF has been found. No
	# RDFa parsing should be done on that subtree, so we simply return...
	if state.options.host_language in accept_embedded_rdf and node.nodeType == node.ELEMENT_NODE and handle_embeddedRDF(node, graph, state) : 
		return	

	#---------------------------------------------------------------------------------
	# calling the host specific massaging of the DOM
	if state.options.host_language in host_dom_transforms and node.nodeType == node.ELEMENT_NODE :
		for func in host_dom_transforms[state.options.host_language] : func(node, state)

	#---------------------------------------------------------------------------------
	# First, let us check whether there is anything to do at all. Ie,
	# whether there is any relevant RDFa specific attribute on the element
	#
	if not _has_one_of_attributes(node, "href", "resource", "about", "property", "rel", "rev", "typeof", "src", "vocab", "profile", "prefix") :
		# nop, there is nothing to do here, just go down the tree and return...
		for n in node.childNodes :
			if n.nodeType == node.ELEMENT_NODE : parse_one_node(n, graph, parent_object, state, parent_incomplete_triples)
		return

	#-----------------------------------------------------------------
	# The goal is to establish the subject and object for local processing
	# The behaviour is slightly different depending on the presense or not
	# of the @rel/@rev attributes
	current_subject = None
	current_object  = None

	if _has_one_of_attributes(node, "rel", "rev")  :
		# in this case there is the notion of 'left' and 'right' of @rel/@rev
		# in establishing the new Subject and the objectResource

		# set first the subject
		if node.hasAttribute("about") :
			current_subject = state.getURI("about")
		elif node.hasAttribute("src") :
			current_subject = state.getURI("src")
		elif node.hasAttribute("typeof") :
			current_subject = BNode()
			
		# get_URI may return None in case of an illegal CURIE, so
		# we have to be careful here, not use only an 'else'
		if current_subject == None :
			current_subject = parent_object

		# set the object resource
		if node.hasAttribute("resource") :
			current_object = state.getURI("resource")
		elif node.hasAttribute("href") :
			current_object = state.getURI("href")
	else :
		# in this case all the various 'resource' setting attributes
		# behave identically, though they also have their own priority
		if node.hasAttribute("about") :
			current_subject = state.getURI("about")
		elif node.hasAttribute("src") :
			current_subject = state.getURI("src")
		elif node.hasAttribute("resource") :
			current_subject = state.getURI("resource")
		elif node.hasAttribute("href") :
			current_subject = state.getURI("href")
		elif node.hasAttribute("typeof") :
			current_subject = BNode()

		# get_URI_ref may return None in case of an illegal CURIE, so
		# we have to be careful here, not use only an 'else'
		if current_subject == None :
			current_subject = parent_object

		# in this case no non-literal triples will be generated, so the
		# only role of the current_objectResource is to be transferred to
		# the children node
		current_object = current_subject

	# ---------------------------------------------------------------------
	## The possible typeof indicates a number of type statements on the newSubject
	for defined_type in state.getURI("typeof") :
		graph.add((current_subject, ns_rdf["type"], defined_type))

	# ---------------------------------------------------------------------
	# In case of @rel/@rev, either triples or incomplete triples are generated
	# the (possible) incomplete triples are collected, to be forwarded to the children
	incomplete_triples  = []
	for prop in state.getURI("rel") :
		if not isinstance(prop,BNode) :
			theTriple = (current_subject,prop,current_object)
			if current_object != None :
				graph.add(theTriple)
			else :
				incomplete_triples.append(theTriple)
		else :
			state.options.add_warning("Blank node in rel position is not allowed: [element '%s']" % node.nodeName, IncorrectBlankNodeUsage)

	for prop in state.getURI("rev") :
		if not isinstance(prop,BNode) :
			theTriple = (current_object,prop,current_subject)
			if current_object != None :
				graph.add(theTriple)
			else :
				incomplete_triples.append(theTriple)
		else :
			state.options.add_warning("Blank node in rev position is not allowed: [element '%s']" % node.nodeName, IncorrectBlankNodeUsage)




	# ----------------------------------------------------------------------
	# Generation of the literal values. The newSubject is the subject
	# A particularity of property is that it stops the parsing down the DOM tree if an XML Literal is generated,
	# because everything down there is part of the generated literal. 
	if node.hasAttribute("property") :
		# Generate the literal. It has been put it into a separate module to make it more managable
		# the overall return value should be set to true if any valid triple has been generated
		generate_literal(node, graph, current_subject, state)

	# ----------------------------------------------------------------------
	# Setting the current object to a bnode is setting up a possible resource
	# for the incomplete triples downwards
	if current_object == None :
		object_to_children = BNode()
	else :
		object_to_children = current_object

	#-----------------------------------------------------------------------
	# Here is the recursion step for all the children
	for n in node.childNodes :
		if n.nodeType == node.ELEMENT_NODE : 
			parse_one_node(n, graph, object_to_children, state, incomplete_triples)

	# ---------------------------------------------------------------------
	# At this point, the parent's incomplete triples may be completed
	for (s,p,o) in parent_incomplete_triples :
		if s == None : s = current_subject
		if o == None : o = current_subject
		graph.add((s,p,o))

	# -------------------------------------------------------------------
	# This should be it...
	# -------------------------------------------------------------------
	return


