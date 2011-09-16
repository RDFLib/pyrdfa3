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
$Id: parse.py,v 1.3 2011-09-16 12:26:02 ivan Exp $
$Date: 2011-09-16 12:26:02 $

Added a reaction on the RDFaStopParsing exception: if raised while setting up the local execution context, parsing
is stopped (on the whole subtree)
"""

import sys

from pyRdfa.state   		import ExecutionContext
from pyRdfa.literal 		import generate_literal
from pyRdfa.embeddedRDF	 	import handle_embeddedRDF
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

from pyRdfa import IncorrectBlankNodeUsage, err_no_blank_node
from pyRdfa.utils import has_one_of_attributes

#######################################################################
def parse_one_node(node, graph, parent_object, incoming_state, parent_incomplete_triples) :
	"""The (recursive) step of handling a single node. See the
	U{RDFa syntax document<http://www.w3.org/TR/rdfa-syntax>} for further details.

	@param node: the DOM node to handle
	@param graph: the RDF graph
	@type graph: RDFLib's Graph object instance
	@param parent_object: the parent's object, as an RDFLib URIRef
	@param incoming_state: the inherited state (namespaces, lang, etc)
	@type incoming_state: L{state.ExecutionContext}
	@param parent_incomplete_triples: list of hanging triples (the missing resource set to None) to be handled (or not)
	by the current node.
	@return: whether the caller has to complete it's parent's incomplete triples
	@rtype: Boolean
	"""

	# Update the state. This means, for example, the possible local settings of
	# namespaces and lang
	state = None
	state = ExecutionContext(node, graph, inherited_state=incoming_state)

	#---------------------------------------------------------------------------------
	# Handle the special case for embedded RDF, eg, in SVG1.2. 
	# This may add some triples to the target graph that does not originate from RDFa parsing
	# If the function return TRUE, that means that an rdf:RDF has been found. No
	# RDFa parsing should be done on that subtree, so we simply return...
	if state.options.host_language in accept_embedded_rdf and node.nodeType == node.ELEMENT_NODE and handle_embeddedRDF(node, graph, state) : 
		return	

	#---------------------------------------------------------------------------------
	# calling the host language specific massaging of the DOM
	if state.options.host_language in host_dom_transforms and node.nodeType == node.ELEMENT_NODE :
		for func in host_dom_transforms[state.options.host_language] : func(node, state)

	#---------------------------------------------------------------------------------
	# First, let us check whether there is anything to do at all. Ie,
	# whether there is any relevant RDFa specific attribute on the element
	#
	if not has_one_of_attributes(node, "href", "resource", "about", "property", "rel", "rev", "typeof", "src", "vocab", "prefix") :
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
	new_collection  = False

	if has_one_of_attributes(node, "rel", "rev")  :
		# in this case there is the notion of 'left' and 'right' of @rel/@rev
		# in establishing the new Subject and the objectResource

		# set first the subject
		if node.hasAttribute("about") :
			current_subject = state.getURI("about")
		elif state.rdfa_version < "1.1" and node.hasAttribute("src") :
			current_subject = state.getURI("src")
		elif node.hasAttribute("typeof") :
			current_subject = BNode()
			
		# get_URI may return None in case of an illegal CURIE, so
		# we have to be careful here, not use only an 'else'
		if current_subject == None :
			current_subject = parent_object
		else :
			state.reset_list_mapping()
			new_collection  = True

		# set the object resource
		if node.hasAttribute("resource") :
			current_object = state.getURI("resource")
		elif node.hasAttribute("href") :
			current_object = state.getURI("href")
		elif state.rdfa_version >= "1.1" and node.hasAttribute("src") :
			current_object = state.getURI("src")
		state.setting_subject = (current_object != None)
	else :
		# in this case all the various 'resource' setting attributes
		# behave identically, though they also have their own priority
		if node.hasAttribute("about") :
			current_subject = state.getURI("about")
		elif  state.rdfa_version < "1.1" and node.hasAttribute("src") :
			current_subject = state.getURI("src")
		elif node.hasAttribute("resource") :
			current_subject = state.getURI("resource")
		elif node.hasAttribute("href") :
			current_subject = state.getURI("href")
		elif  state.rdfa_version >= "1.1" and node.hasAttribute("src") :
			current_subject = state.getURI("src")
		elif node.hasAttribute("typeof") :
			current_subject = BNode()

		# get_URI_ref may return None in case of an illegal CURIE, so
		# we have to be careful here, not use only an 'else'
		state.setting_subject = (current_object != None)
		if current_subject == None :
			current_subject = parent_object
		else :
			state.reset_list_mapping()
			new_collection  = True

		# in this case no non-literal triples will be generated, so the
		# only role of the current_object Resource is to be transferred to
		# the children node
		current_object = current_subject
		
	# Last step, related to the subject setting by somebody else higher up and list management
	if new_collection == False and incoming_state.setting_subject == True :
			state.reset_list_mapping()
			new_collection  = True

	# ---------------------------------------------------------------------
	## The possible typeof indicates a number of type statements on the new Subject
	for defined_type in state.getURI("typeof") :
		graph.add((current_subject, ns_rdf["type"], defined_type))

	# ---------------------------------------------------------------------
	# In case of @rel/@rev, either triples or incomplete triples are generated
	# the (possible) incomplete triples are collected, to be forwarded to the children
	incomplete_triples  = []
	for prop in state.getURI("rel") :
		if not isinstance(prop,BNode) :
			if state.rdfa_version >= "1.1" and node.hasAttribute("inlist") :
				if current_object != None :
					state.add_to_list_mapping(prop, current_object)
				else :
					incomplete_triples.append((None, prop, None))
			else :
				theTriple = (current_subject, prop, current_object)
				if current_object != None :
					graph.add(theTriple)
				else :
					incomplete_triples.append(theTriple)
		else :
			state.options.add_warning(err_no_blank_node % "rel", warning_type=IncorrectBlankNodeUsage, node=node.nodeName)

	for prop in state.getURI("rev") :
		if not isinstance(prop,BNode) :
			theTriple = (current_object,prop,current_subject)
			if current_object != None :
				graph.add(theTriple)
			else :
				incomplete_triples.append(theTriple)
		else :
			state.options.add_warning(err_no_blank_node % "rev", warning_type=IncorrectBlankNodeUsage, node=node.nodeName)

	# ----------------------------------------------------------------------
	# Generation of the literal values. The newSubject is the subject
	# A particularity of property is that it stops the parsing down the DOM tree if an XML Literal is generated,
	# because everything down there is part of the generated literal. 
	if node.hasAttribute("property") :
		# Generate the literal. It has been put it into a separate module to make it more managable
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
		if s == None and o == None :
			# This is an encoded version of a hanging rel for a collection:
			incoming_state.add_to_list_mapping( p, current_subject )
		else :
			if s == None : s = current_subject
			if o == None : o = current_subject
			graph.add((s,p,o))

	# Generate the lists, if any...	
	if state.rdfa_version >= "1.1" and new_collection and len(state.list_mapping) != 0 :
		for prop in state.list_mapping :
			heads = [ (BNode(), r) for r in state.list_mapping[prop] ]
			if len(heads) == 0 :
				# should not happen, though
				continue
			for (b,r) in heads :
				graph.add( (b, ns_rdf["first"], r) )
			for i in range(0, len(heads)-1) :
				graph.add( (heads[i][0], ns_rdf["rest"], heads[i+1][0]) )
				
			graph.add( (heads[-1][0], ns_rdf["rest"], ns_rdf["nil"]) )
			graph.add( (current_subject, prop, heads[0][0]) )

	# -------------------------------------------------------------------
	# This should be it...
	# -------------------------------------------------------------------
	return


