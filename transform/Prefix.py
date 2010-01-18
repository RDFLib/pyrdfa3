# -*- coding: utf-8 -*-
"""
This module, in fact, implements the features that might be added to RDFa to accomodate with HTML5. This is, of course, I{highly
speculative at the moment}, and the overall direction and behaviour of the HTML5 folks is not really predictable. But there seems
to be two sticking points in the discussion (beyond the fact that the HTML5 proponents have some philosophical problem with RDF
altogether):

 - Usage of the 'xmlns' formalism to set the CURIE prefixes
 - Usage of the core RDFa attributes which are not sanctioned by HTML5. The extension mechanism preferred by this group is to use the 'var-XXX' model. 

This module provides two separate transformers to handle this issue. In both cases the transformer modifies the DOM tree to 
match to the official RDFa specification.

Use @prefix instead of @xmlns
=============================

Possibility to use the C{@prefix} attribute instead of C{@xmlns:} to set the prefixes for Curies. 

At the moment, although RDFa does I{not} use XML namespaces for CURIE-s, it does use the C{@xmlns:} attributes (borrowed from XML namespaces)
to set the prefixes for CURIE-s. This may not be the best options on long term, in view of the disagreements in HTML circles
on the usage of namespaces (or anything that reminds of namespaces). This transformer implements an alternative. For each element
in the DOM tree, the C{@prefix} attribute is considered. The value of the attribute should be::
 <... prefix="pref1=uri1 pref2=uri2" ...>
The behaviour is I{exactly} the same as if::
 <... xmlns:pref1="uri1" xmlns:pref2="uri2" ...>	 
was used, including inheritance rules of prefixes. C{@prefix} has a higher priority; ie, in case of::
 <... prefix="pref=uri1" xmlns:pref="uri2" ...>
the setting with C{uri2} will be ignored.

Whitespaces around the '=' sign will be filtered, ie, @prefix="A = B" is the same as @prefix="A=B". A @prefix="DEFAULTNS=A" will set the
default namespace, ie, it will be identical to @xmlns=A.

Use the @var-xxx pattern
========================

This pattern is the preferred format for extensions by the HTML5 at the moment. What this means is that RDFa processing should use, say, C{@var-about}
instead of C{@about}. The transformer finds all those attributes and replaces them with the original, RDFa ones.


@summary: Transfomers to handle C{@prefix} as an alternative to C{@xmlns:} type namespace setting, as well as using the C{@var-xxx} extension pattern for attributes
@requires: U{RDFLib package<http://rdflib.net>}
@organization: U{World Wide Web Consortium<http://www.w3.org>}
@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}
"""

"""
$Id: Prefix.py,v 1.1 2010-01-18 13:42:38 ivan Exp $
$Date: 2010-01-18 13:42:38 $
"""

import re
from pyRdfa.transform.utils import traverse_tree, dump

__RDFaAttributes = ["href", "resource", "about", "property", "rel", "rev", "typeof", "src", "datatype", "content", "prefix"]

DEFAULTNS="DEFAULTNS"

def set_prefixes(html, options) :
	def _handle_prefix(node) :
		pr = None
		if node.hasAttribute("prefix") :
			pr = node.getAttribute("prefix")
#		elif node.hasAttribute("var-prefix") :
#			pr = node.getAttribute("var-prefix")
			
		if pr != None :
			# '=' may be surrounded by whitespace characters.
			st = re.sub("\s*=\s*","=",pr.strip())
			
			# the split produces the individual prefix setting stuff stuffs
			for n in st.split() :
				# separate the prefix from the URI
				ns = n.strip().split('=')
				if len(ns) >= 3 :
					# this is the case when either the left hand or the right hand side of a 
					# '=' is empty and there are several declarations in @prefix
					print "Ambiguous prefix declaration: %s" % ns
					options.comment_graph.add_warning("Error in @prefix, ambiguous prefix declaration: %s" % ns)
					continue
				elif len(ns) > 1 :
					# sorting out the cases when the left or the right hand side of '=' is empty and
					# this is the only declaration in @prefix (cumulated cases are handled by the case for len(ns)>=3
					if ns[1] == "" :
						options.comment_graph.add_warning("Error in @prefix, missing URI in prefix declaration: %s" % ns[0])
						continue
					if ns[0] == "" :
						options.comment_graph.add_warning("Error in @prefix, missing prefix for prefix declaration: %s" % ns[1])
						continue	
					(prefix,value) = (ns[0],ns[1])
					if prefix == DEFAULTNS :
						xmlns = "xmlns"
					else :
						xmlns = "xmlns:%s" % prefix
						
					# @prefix has a lower priority, ie, xmlns takes precedence
					if not node.hasAttribute(xmlns) :
						node.setAttributeNS("", xmlns,value)

				else :
					# stand alone term without any '=' in @prefix
					options.comment_graph.add_warning("Error in @prefix, uninterpretable prefix declaration: %s" % ns[0])
					continue
		return False
	traverse_tree(html, _handle_prefix)
		
def handle_vars(html, options) :
	def _handle_vars(node) :
		# I am not sure why the one below did not work:
		# for attr in node.attributes :
		for attr in node._attrs.keys() :
			spl = attr.split('-',1)
			if len(spl) > 1 and spl[0] == 'var' and spl[1] in __RDFaAttributes :
				# Yep, we have one; that should take the upper hand, so simply add this attribute, possibly overwriting the other
				node.setAttribute(spl[1],node.getAttribute(attr))
		return False
	traverse_tree(html, _handle_vars)


