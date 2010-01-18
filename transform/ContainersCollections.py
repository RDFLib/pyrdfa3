# -*- coding: utf-8 -*-
"""
Transfomer: handles the RDF collections and containers. This means that structures of the form::

  <ul typeof="rdf:Seq">
    <li>....</li>
    ....
  </ul>

are turned into intermediate DOM nodes that yield, via the RDFa processing, RDF containers, whereas structures of the form::

  <ul typeof="rdf:List">
    <li>....</li>
    ....
  </ul>

are turned into intermediate DOM nodes that yield, via the RDFa processing, RDF collections.

The details are as follows:

The Container case
==================

In its simplest form the transformation adds C{@property} attributes to the C{<li>} elements with the values of C{rdf:_1},
C{rdf:_2},... Ie, the transformed DOM tree is equivalent to::

 <ul typeof="rdf:Seq">
    <li property="rdf:1">....</li>
    <li property="rdf:2">....</li>
    ....
  </ul>

which will yield the right RDF collection triples. This simple case occurs if the C{li} element does not include any
of the RDFa attributes C{href}, C{resource}, C{typeof}, C{rel}, C{rev}, or C{property}. Otherwise, the C{li} will be
I{surrounded} by a new element with a C{rel} attribute of value C{rdf:_1}, C{rdf:_2},... Ie, the following XHTML code::

  <ul typeof="rdf:Seq">
    <li typeof="a:b">....</li>
    <li about="#b">...</li>
    ....
  </ul>

will be transformed into::

  <ul typeof="rdf:Seq">
    <div rel="rdf:_1"><li typeof="a:b">....</li></div>
    <div rel="rdf:_2"><li about="#b">...</li></div>
    ....
  </ul>

Although this is meaningless (and invalid!) in terms of XHTML, this modified DOM tree is used by the RDFa parser only and
will generate the right RDF triplets.

The Collection case
===================

The simple case is again when the individual C{<li>} elements do not include and of RDFa attributes
C{href}, C{resource}, C{typeof}, C{rel}, C{rev}, or C{property}. The code::

  <ul typeof="rdf:List">
    <li>text 1</li>
    <li>text 2</li>
  </ul>

is transformed into::

  <ul about="_:a1" typeof="rdf:List">
    <li about="_:a1" property="rdf:first">text 1</li>
    <li about="_:a1" rel="rdf:rest" resource="[_:a2]"/>
    <li about="_:a2" property="rdf:first">text 2</li>
    <li about="_:a2" typeof="rdf:List" rel="rdf:rest" resource="[rdf:nil]"/>
  </ul>

(Where the C{_:a1}, C{_:a2}, etc are just for illustration; for I{each} C{<ul>/<li>} structure unique identifiers are used.) Just
as in the case of containers, the transformation is more complicated insofar as the original C{<li>} is I{surrounded} by
a new element. Ie::

  <ul typeof="rdf:List">
    <li typeof="a:b" property="q:r">text 1</li>
    <li about="#b">text 2</li>
    ....
  </ul>

is transformed into::

  <ul about="_:a1" typeof="rdf:List">
    <div about="_:a1" rel="rdf:first"><li typeof="a:b" property="q:r">text 1</li></div>
    <li about="_:a1" rel="rdf:rest" resource="[_:a2]"/>
    <div about="_:a2" rel="rdf:first"><li about="#b">text 2</li></div>
    <li about="_:a2" typeof="rdf:List" rel="rdf:rest" resource="[rdf:nil]"/>
  </ul>

In both cases, the RDFa processing rules generate the right set of triples for RDF collections.

@summary: Transfomer to handle RDF collections and containers
@requires: U{RDFLib package<http://rdflib.net>}
@organization: U{World Wide Web Consortium<http://www.w3.org>}
@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}
"""

"""
$Id: ContainersCollections.py,v 1.1 2010-01-18 13:42:38 ivan Exp $
$Date: 2010-01-18 13:42:38 $
"""

import random
from pyRdfa.Parse           import _has_one_of_attributes
from pyRdfa.transform.utils import rdf_prefix, traverse_tree, dump

_NONE       = 0
_CONTAINER  = 1
_COLLECTION = 2


def decorate_li_s(html, options) :
	"""
	The main transformer entry point. See the module description for details.
	@param html: a DOM node for the top level html element
	@param options: invocation options
	@type options: L{Options<pyRdfa.Options>}
	"""
	_bids = []
	def _collect_BIDs(node) :
		"""Check and collect the possible bnode id-s in the file that might occur in CURIE-s. The
		function is called recursively on each node. The L{_bids} variable is filled with the initial values.
		@param node: a DOM element node
		"""
		def _suspect(val) :
			if len(val) > 1 :
				if val[0] == "_" and val[1] == ":" :
					if not val in _bids : _bids.append(val)
				elif val[0] == "[" and val[-1] == "]" :
					_suspect(val[1:-1])
		for a in ["about","resource","typeof"] :
			if node.hasAttribute(a) : _suspect(node.getAttribute(a))
		return False

	def _give_BID() :
		"""Generate a new value that can be used as a bnode id...
		@return: a string of the form _:XXXX where XXXX is unique (ie, not yet stored in the L{_bids} array).
		"""
		while True :
			i = random.randint(1,10000)
			val = "_:x%s" % i
			if not val in _bids :
				_bids.append(val)
				return val

	def _check_if_hit(node, rdfprefix) :
		"""
		Check if the node has one of the C{typeof} values that would trigger the transformation.
		@param node: DOM node (standing for a C{<ul>} or a C{<ol>})
		@param rdfprefix: prefix to be used for the RDF namespace
		@return: the value of _CONTAINER, _COLLECTION, or _NONE
		"""
		if node.hasAttribute("typeof") :
			types = node.getAttribute("typeof").split()
			for t in types :
				# check if it is a namespaces thing at all...
				if t.find(":") != -1 :
					key   = t.split(":",1)[0]
					lname = t.split(":",1)[1]
					if key == rdfprefix :
						if lname in ["Seq","Alt","Bag"] :
							return _CONTAINER
						elif lname in ["List"] :
							return _COLLECTION
		return _NONE

	def _decorate_container(node, rdfprefix) :
		"""Take care of containers (ie, Seq, Alt, and Bag).
		@param node: the node for the C{<ul>/<ol>}
		@param rdfprefix: the prefix of the RDF namespace
		"""
		index = 1
		originalNodes = [n for n in node.childNodes if n.nodeType == node.ELEMENT_NODE and n.tagName == "li" ]
		for n in originalNodes :
			pr = "%s:_%s"  % (rdfprefix,index)
			index += 1
			if not _has_one_of_attributes(n,"href","resource","typeof","about","rel","rev","property") :
				# the simple case...
				n.setAttribute("property",pr)
			else :
				# the original node should not be changed, but should be reparanted into a new
				# enclosure
				newEnclosure = node.ownerDocument.createElement("div")
				newEnclosure.setAttribute("rel",pr)
				node.replaceChild(newEnclosure,n)
				newEnclosure.appendChild(n)


	def _decorate_collection(node, rdfprefix) :
		"""Take care of collection (a.k.a. Lists).
		@param node: the node for the C{<ul>/<ol>}
		@param rdfprefix: the prefix of the RDF namespace
		"""
		List  = "%s:List"  % rdfprefix
		first = "%s:first" % rdfprefix
		rest  = "%s:rest"  % rdfprefix
		nil   = "[%s:nil]"   % rdfprefix
		rtype = "%s:type"  % rdfprefix
		# the list of 'li'-s is needed in advance (eg, for their numbers)
		originalNodes = [ n for n in node.childNodes if n.nodeType == node.ELEMENT_NODE and n.tagName == "li" ]
		# a bnode id should be generated for the top level node
		if node.hasAttribute("about") :
			currId = node.getAttribute("about")
		else :
			currId = "[%s]" % _give_BID()
			node.setAttribute("about",currId)

		index = 1
		for i in xrange(0,len(originalNodes)) :
			n = originalNodes[i]
			# first the current <li> must be massaged
			if not _has_one_of_attributes(n,"href","resource","typeof","about","rel","rev","property") :
				# the simple case, the node is changed in situ..
				n.setAttribute("about",currId)
				n.setAttribute("property",first)
			else :
				# an enclosure for that node should be created, and the original node
				# is just reparented
				newEnclosure = node.ownerDocument.createElement("div")
				newEnclosure.setAttribute("rel",first)
				newEnclosure.setAttribute("about",currId)
				node.replaceChild(newEnclosure,n)
				newEnclosure.appendChild(n)
			# An extra <li> is necessary to add some additional info...
			newLi = node.ownerDocument.createElement("li")
			newLi.setAttribute("about",currId)
			newLi.setAttribute("rel",rest)
			if i != 0 : newLi.setAttribute("typeof",List)
			if i == len(originalNodes) - 1 :
				# This is the last element
				newLi.setAttribute("resource",nil)
				node.appendChild(newLi)
			else :
				newId = "[%s]" % _give_BID()
				newLi.setAttribute("resource",newId)
				currId = newId
				node.insertBefore(newLi,originalNodes[i+1])

	uls = [ n for n in html.getElementsByTagName("ul") ]
	ols = [ n for n in html.getElementsByTagName("ol") ]
	if len(uls) == 0 and len(ols) == 0 : return

	#--------------------------------------------------------------------------------
	# We have to extract the prefix used for rdf. It may not be 'rdf'...
	rdfprefix = rdf_prefix(html)

	#--------------------------------------------------------------------------------
	# We have to collect the current bnode id-s from the file to avoid conflicts
	traverse_tree(html,_collect_BIDs)
	# We will need the random function to generate unique bid-s
	random.seed(None)

	#--------------------------------------------------------------------------------

	for node in uls+ols :
		# check if this is one of those guys...
		t = _check_if_hit(node, rdfprefix)
		if t == _CONTAINER :
			_decorate_container(node, rdfprefix)
		elif t == _COLLECTION :
			_decorate_collection(node, rdfprefix)

