# -*- coding: utf-8 -*-
"""
Handling of collections and containers as a preprocessor to the full RDFa processing. See the
U{text on the RDFa WG’s pages<http://www.w3.org/2010/02/rdfa/wiki/ContainersAndCollections>} for the details.

@summary: Transfomer to handle RDF collections and containers
@requires: U{RDFLib package<http://rdflib.net>}
@organization: U{World Wide Web Consortium<http://www.w3.org>}
@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}
"""

"""
$Id: containerscollections.py,v 1.1 2011-08-12 10:10:33 ivan Exp $
$Date: 2011-08-12 10:10:33 $
"""

import uuid
from pyRdfa.utils import traverse_tree, dump

import rdflib
from rdflib	import Namespace
if rdflib.__version__ >= "3.0.0" :
	from rdflib	import RDF  as ns_rdf
	from rdflib	import RDFS as ns_rdfs
else :
	from rdflib.RDFS	import RDFSNS as ns_rdfs
	from rdflib.RDF		import RDFNS  as ns_rdf

_trigger_Seq = "::Seq"
_trigger_Bag = "::Bag"
_trigger_Alt = "::Alt"
_trigger_Lst = "::List"
_trigger_mb  = "::member"

class BIDs :
	"""Class to handle the collection and the generation of unique blank node identifiers.
	
	@ivar bids: set of Blank node id-s
	@ivar bidnum: the integer used to create a new id
	@ivar latestbid: the latest id that has been generated
	
	"""
	def __init__(self, html) :
		"""
		@param html: the top level DOM node
		"""
		self.bidnum    = 10
		self.bids      = set()
		self.latestbid = ""
		def collect(node) :
			"""Check and collect the possible bnode id-s in the file that might occur in CURIE-s. The
			function is called recursively on each node. The L{bids} variable is filled with the initial values.
			@param node: a DOM element node
			"""
			def suspect(val) :
				if len(val) > 1 :
					if val[0] == "_" and val[1] == ":" :
						self.bids.add(val)
					elif val[0] == "[" and val[-1] == "]" :
						suspect(val[1:-1])
			for value in ["about","resource","typeof"] :
				if node.hasAttribute(value) :
					for b in node.getAttribute(value).strip().split() :
						suspect(b)
			return False
		# fill the bnode collection:
		traverse_tree(html, collect)
		
	def new_id(self) :
		"""Generate a new value that can be used as a bnode id...
		@return: a string of the form _:XXXX where XXXX is unique (ie, not yet stored in the L{bids} set).
		"""
		while True :
			# Eventually that should succeed...
			val = "_:xyz%d" % self.bidnum
			self.bidnum += 1
			if not val in self.bids :
				self.bids.add(val)
				self.latestbid = val
				return val
			
	def get_latestid(self) :
		"""
		@return: the latest blank node id
		"""
		return self.latestbid
	
#################################################

class CollectionsContainers :
	"""
	Handling of collections and containers as a preprocessor to the full RDFa processing. See the module description for the details.

	@cvar blanks: collections of blank node id-s
	@type blanks: L{BIDs}
	"""
	def __init__(self, html) :
		"""
		@param html: top level DOM Node
		"""
		self.blanks = BIDs(html)
		
	def is_trigger(self, node) :
		"""
		Check if the node is a "trigger", ie, the head of a collection or a container
		@return: boolean
		"""
		if node.hasAttribute("resource") :
			target = node.getAttribute("resource")
			return _trigger_Seq == target or _trigger_Alt == target or _trigger_Bag == target or _trigger_Lst == target 
		else :
			return False

	def look_for_triggers(self, node) :
		"""
		Recursively check the DOM tree for a "trigger" and initiate the transformation of the DOM tree at that point.
		@param node: DOM Element Node
		"""
		def addNewType(parent, ctype) :
			subject = self.blanks.new_id()
			parent.setAttribute("resource", subject)
			if not ctype == "" :
				type_node = parent.ownerDocument.createElement("container")
				parent.appendChild(type_node)
				type_node.setAttribute("about", subject)
				type_node.setAttribute("typeof", ctype)
				
		# Take care of a rare case: the node has a datatype property set to XMLLiteral. In this case nothing should be done!
		if node.hasAttribute("datatype") :
			val = node.getAttribute("datatype")
			if val == str(ns_rdf["XMLLiteral"]) or val == "rdf:XMLLiteral" :
				return
				
		if node.hasAttribute("resource") :
			target = node.getAttribute("resource")
			if target == _trigger_Seq :
				addNewType(node, str(ns_rdf["Seq"]))
				self.handle_container(node)
			elif target == _trigger_Alt :
				addNewType(node, str(ns_rdf["Alt"]))
				self.handle_container(node)
			elif target == _trigger_Bag :
				addNewType(node, str(ns_rdf["Bag"]))
				self.handle_container(node)
			elif target == _trigger_Lst :
				# Note that there no type information is added here!
				addNewType(node, "")
				self.handle_collection(node)				
			
		# handled the possible triggers, go for the children
		for n in node.childNodes :
			if n.nodeType == node.ELEMENT_NODE :
				self.look_for_triggers(n)
				
	def handle_container(self, node) :
		"""
		Handle a container with the head at the incoming node
		@param node: DOM Element node triggering a container transformation
		"""
		def update_li(n) :
			if self.is_trigger(n) :
				return
			elif n.hasAttribute("property") and n.getAttribute("property") == _trigger_mb :
				# Grrrr... there is a backward incompatibility with RDFLib...
				# It checks the closed namespaces, which is fine, but
				# the only way to generate an rdf:_i attribute is to pass
				# an integer; otherwise it raises an exception.
				attr = (rdflib.__version__ >= "3.0.0" and str(ns_rdf[self.li])) or str(ns_rdf["_%d" % self.li])
				n.setAttribute("property", attr)
				self.li += 1
				return
			elif n.hasAttribute("rel") and n.getAttribute("rel") == _trigger_mb :
				# See comment above...
				attr = (rdflib.__version__ >= "3.0.0" and str(ns_rdf[self.li])) or str(ns_rdf["_%d" % self.li])
				n.setAttribute("rel", attr)
				self.li += 1
				return
			for nc in n.childNodes :
				if nc.nodeType == node.ELEMENT_NODE :
					update_li(nc)

		self.li = 1
		for n in node.childNodes :
			if n.nodeType == node.ELEMENT_NODE :
				update_li(n)
					
	def handle_collection(self, node) :
		"""
		Handle a collection with the head at the incoming node
		@param node: DOM Element node triggering a container transformation
		"""
		def add_about(node) :
			if not self.current_subject == "" :
				node.setAttribute("about", self.current_subject)
			self.subj_lst.append(self.current_subject)
			self.current_subject = self.blanks.new_id()
			
		def update_mb(n) :
			if self.is_trigger(n) : return
			if n.hasAttribute("property") and n.getAttribute("property") == _trigger_mb :
				n.setAttribute("property", str(ns_rdf["first"]))
				add_about(n)
				return
			elif n.hasAttribute("rel") and n.getAttribute("rel") == _trigger_mb :
				n.setAttribute("rel", str(ns_rdf["first"]))
				add_about(n)
				return
			for nc in n.childNodes :
				if nc.nodeType == node.ELEMENT_NODE :
					update_mb(nc)

		self.current_subject = self.blanks.get_latestid()
		self.subj_lst        = []
		for n in node.childNodes :
			if n.nodeType == node.ELEMENT_NODE :
				update_mb(n)
				
		# Link the list elements together and ground it
		for i in xrange(0,len(self.subj_lst)) :
			link_elements = node.ownerDocument.createElement("list_links")
			node.appendChild(link_elements)
			if not self.subj_lst[i] == "" :
				link_elements.setAttribute("about", self.subj_lst[i])
			link_elements.setAttribute("rel",str(ns_rdf["rest"]))
			try :
				link_elements.setAttribute("resource",self.subj_lst[i+1])
			except IndexError :
				link_elements.setAttribute("resource",str(ns_rdf["nil"]))

def containers_collections(html, option) :
	"""
	The main transformer entry point. See the module description for details.
	@param html: a DOM node for the top level html element
	@param option: invocation options (not used in this module)
	@type option: L{Options<pyRdfa.Options>}
	"""
	handler = CollectionsContainers(html)
	handler.look_for_triggers(html)
	#dump(html)
	
############
"""
$Log: containerscollections.py,v $
Revision 1.1  2011-08-12 10:10:33  ivan
*** empty log message ***

Revision 1.8  2011/03/08 10:50:14  ivan
*** empty log message ***

Revision 1.7  2010/11/19 13:52:52  ivan
*** empty log message ***

Revision 1.6  2010/11/02 14:56:46  ivan
*** empty log message ***

Revision 1.5  2010/08/27 13:45:44  ivan
Added cvs log placeholder

"""