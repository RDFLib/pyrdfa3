# -*- coding: utf-8 -*-
"""
Implementation of the Literal handling. Details of the algorithm are described on
U{RDFa Task Force's wiki page<http://www.w3.org/2006/07/SWD/wiki/RDFa/LiteralObject>}.

@summary: RDFa Literal generation
@requires: U{RDFLib package<http://rdflib.net>}
@organization: U{World Wide Web Consortium<http://www.w3.org>}
@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}
"""

"""
$Id: Literal.py,v 1.17 2011-05-31 12:41:36 ivan Exp $
$Date: 2011-05-31 12:41:36 $
"""

import re

import rdflib
from rdflib	import BNode
from rdflib	import Literal, URIRef, Namespace
if rdflib.__version__ >= "3.0.0" :
	from rdflib	import RDF as ns_rdf
else :
	from rdflib.RDF	import RDFNS as ns_rdf

from pyRdfa	import IncorrectBlankNodeUsage, err_no_blank_node 


XMLLiteral = ns_rdf["XMLLiteral"]

def __putBackEntities(str) :
	"""Put 'back' entities for the '&','<', and '>' characters, to produce kosher XML string.
	Used by XML Literal
	@param str: string to be converted
	@return: string with entities
	@rtype: string
	"""
	return str.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

#### The real meat...
def generate_literal(node, graph, subject, state) :
	"""Generate the literal, taking into account datatype, etc.
	Note: this method is called only if the C{@property} is indeed present, no need to check. 
	
	This method is an encoding of the algorithm documented
	U{task force's wiki page<http://www.w3.org/2006/07/SWD/wiki/RDFa/LiteralObject>}.
	
	The method returns a value whether the literal is a 'normal' literal (regardless of its datatype) 
	or an XML Literal. The return value is True or False, respectively. This value is used to control whether
	the parser should stop recursion. This also means that that if the literal is generated from @content, 
	the return value is False, regardless of the possible @datatype value.

	@param node: DOM element node
	@param graph: the (RDF) graph to add the properies to
	@param subject: the RDFLib URIRef serving as a subject for the generated triples
	@param state: the current state to be used for the CURIE-s
	@type state: L{State.ExecutionContext}
	@return: whether the literal is a 'normal' or an XML Literal (return value is True or False, respectively). Note that if the literal is generated from @content, the return value is False, regardless of the possible @datatype value.
	@rtype: Boolean
	"""
	def _get_literal(Pnode):
		"""
		Get (recursively) the full text from a DOM Node.

		@param Pnode: DOM Node
		@return: string
		"""
		rc = ""
		for node in Pnode.childNodes:
			if node.nodeType == node.TEXT_NODE:
				rc = rc + node.data
			elif node.nodeType == node.ELEMENT_NODE :
				rc = rc + _get_literal(node)

		# The decision of the group in February 2008 is not to normalize the result by default.
		# This is reflected in the default value of the option		
		
		if state.options.space_preserve :
			return rc
		else :
			return re.sub(r'(\r| |\n|\t)+'," ",rc).strip()
	# end getLiteral

	def _get_XML_literal(Pnode) :
		"""
		Get (recursively) the XML Literal content of a DOM Node. (Most of the processing is done
		via a C{node.toxml} call of the xml minidom implementation.)

		@param Pnode: DOM Node
		@return: string
		"""
					
		rc = ""		
		for node in Pnode.childNodes:
			if node.nodeType == node.TEXT_NODE:
				rc = rc + __putBackEntities(node.data)
			elif node.nodeType == node.ELEMENT_NODE :
				# Decorate the element with namespaces and lang values
				#for prefix in prefixes :
				#	if prefix in state.term_or_curie.xmlns and not node.hasAttribute("xmlns:%s" % prefix) :
				#		node.setAttribute("xmlns:%s" % prefix,"%s" % state.term_or_curie.xmlns[prefix])
				for prefix in state.term_or_curie.xmlns :
					if not node.hasAttribute("xmlns:%s" % prefix) :
						node.setAttribute("xmlns:%s" % prefix,"%s" % state.term_or_curie.xmlns[prefix])
				# Set the default namespace, if not done (and is available)
				if not node.getAttribute("xmlns") and state.defaultNS != None :
					node.setAttribute("xmlns",state.defaultNS)
				# Get the lang, if necessary
				if not node.getAttribute("xml:lang") and state.lang != None :
					node.setAttribute("xml:lang",state.lang)
				rc = rc + node.toxml()
		return rc
		# If XML Literals must be canonicalized for space, then this is the return line:
		#return re.sub(r'(\r| |\n|\t)+'," ",rc).strip()
	# end getXMLLiteral
	
	# Get the Property URI-s
	props = state.getURI("property")

	# Get, if exists, the value of @datatype
	datatype = ''
	dtset    = False
	if node.hasAttribute("datatype") :
		dtset = True
		dt = node.getAttribute("datatype")
		if dt != "" :
			datatype = state.getURI("datatype")

	if state.lang != None :
		lang = state.lang
	else :
		lang = ''
		
	# The simple case: separate @content attribute
	if node.hasAttribute("content") :
		val = node.getAttribute("content")
		# Handling the automatic uri conversion case
		if dtset == False :
			object = Literal(val, lang=lang)
		else :
			if datatype == None or datatype == '' :
				object = Literal(val, lang=lang)
			else :
				object = Literal(val, datatype=datatype)
		# The value of datatype has been set, and the keyword paramaters take care of the rest
	else :
		# see if there *is* a datatype (even if it is empty!)
		if dtset :
			# yep. The Literal content is the pure text part of the current element:
			# We have to check whether the specified datatype is, in fact, an
			# explicit XML Literal
			if datatype == XMLLiteral :
				object = Literal(_get_XML_literal(node),datatype=XMLLiteral)
				retval = False
			elif datatype == None or datatype == '' :
				object = Literal(_get_literal(node), lang=lang)
			else :
				object = Literal(_get_literal(node), datatype=datatype)
		else :
			if state.rdfa_version >= "1.1" :
				val = _get_literal(node)
				object = Literal(val, lang=lang)
			else :				
				# no controlling @datatype. We have to see if there is markup in the contained
				# element
				if True in [ n.nodeType == node.ELEMENT_NODE for n in node.childNodes ] :
					# yep, and XML Literal should be generated
					object = Literal(_get_XML_literal(node), datatype=XMLLiteral)
				else :
					val = _get_literal(node)
					# At this point, there might be entities in the string that are returned as real characters by the dom
					# implementation. That should be turned back
					object = Literal(_get_literal(node), lang=lang)

	# The object may be empty, for example in an ill-defined <meta> element...
	for prop in props :
		if not isinstance(prop,BNode) :
			graph.add((subject,prop,object))
		else :
			state.options.add_warning(no_blank_node % "property", warning_type=IncorrectBlankNodeUsage, node=node.nodeName)

	# return

"""
$Log: Literal.py,v $
Revision 1.17  2011-05-31 12:41:36  ivan
*** empty log message ***

Revision 1.16  2011/04/20 11:02:21  ivan
*** empty log message ***

Revision 1.15  2011/04/05 06:37:22  ivan
*** empty log message ***

Revision 1.14  2011/03/11 14:12:12  ivan
*** empty log message ***

Revision 1.13  2011/03/11 12:25:05  ivan
empty literal is allowed if the children are empty

Revision 1.12  2011/03/08 10:49:49  ivan
*** empty log message ***

Revision 1.11  2011/01/14 12:41:56  ivan
(1) only those namespaces are stored that are defined via xmlns (2) the optimization to store only used namespaces has been taken out, it would not work with CURIE type attribute values



"""