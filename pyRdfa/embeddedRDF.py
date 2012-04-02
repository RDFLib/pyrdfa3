# -*- coding: utf-8 -*-
"""
Extracting possible embedded RDF/XML content from the file and parse it separately into the Graph. This is used, for example
by U{SVG 1.2 Tiny<http://www.w3.org/TR/SVGMobile12/>}.

@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}
@contact: Ivan Herman, ivan@w3.org
@version: $Id: embeddedRDF.py,v 1.4 2011/11/15 10:03:13 ivan Exp $
$Date: 2011/11/15 10:03:13 $
"""

from StringIO	 import StringIO
from pyRdfa.host import HostLanguage
import re, sys

def handle_embeddedRDF(node, graph, state) :
	"""
	Handles embedded RDF. There are two possibilities:
	
	 - the file is one of the XML dialects that allow for an embedded RDF/XML portion. See the host description for those (a typical example is SVG). This is a standard feature, always enabled.
	 - the file is HTML and there is a turtle portion in the <script> element with type text/turtle. This is a non-standard options that has to be enabled globally via an option...
	
	
	@param node: a DOM node for the top level xml element
	@param graph: target rdf graph
	@type graph: RDFLib's Graph object instance
	@param state: the inherited state (namespaces, lang, etc)
	@type state: L{state.ExecutionContext}
	@return: whether an RDF/XML content has been detected or not. If TRUE, the RDFa processing should not occur on the node and its descendents. 
	@rtype: Boolean
	"""
	def _get_prefixes_in_turtle() :
		retval = ""
		for key in state.term_or_curie.ns :
			retval += "@prefix %s: <%s> .\n" % (key, state.term_or_curie.ns[key])
		retval += '\n'
		return retval
	
	def _get_literal(Pnode):
		"""
		Get the full text
		@param Pnode: DOM Node
		@return: string
		"""
		rc = ""
		for node in Pnode.childNodes:
			if node.nodeType in [node.TEXT_NODE, node.CDATA_SECTION_NODE] :
				rc = rc + node.data
		# Sigh... the HTML5 parser does not recognize the CDATA escapes, ie, it just passes on the <![CDATA[ and ]]> strings:-(
		return rc.replace("<![CDATA[","").replace("]]>","")

	# Embedded turtle, per the latest Turtle draft
	if state.options.host_language in [HostLanguage.html, HostLanguage.xhtml, HostLanguage.svg] :
		if state.options.hturtle == True and node.nodeName.lower() == "script" :
			if node.hasAttribute("type") and node.getAttribute("type") == "text/turtle" :
				prefixes = _get_prefixes_in_turtle()
				content  = _get_literal(node)
				rdf = StringIO(prefixes + content)
				try :
					graph.parse(rdf, format="n3", publicID = state.base)
				except :
					(type,value,traceback) = sys.exc_info()
					state.options.add_error("Embedded Turtle content could not be parsed (problems with %s?); ignored" % value)
			return True
		else :
			return False
	else :
		# This is the embedded RDF/XML case in XML based languages
		if node.localName == "RDF" and node.namespaceURI == "http://www.w3.org/1999/02/22-rdf-syntax-ns#" :
			node.setAttribute("xml:base",state.base)
			rdf = StringIO(node.toxml())
			try :
				graph.parse(rdf)
			except :
				(type,value,traceback) = sys.exc_info()
				state.options.add_error("Embedded RDF/XML content could not parsed (problems with %s?); ignored" % value)
			return True
		else :
			return False
	return False

