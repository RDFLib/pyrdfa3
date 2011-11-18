# -*- coding: utf-8 -*-
"""
Simple transfomer for HTML5: add a @src for any @data, and add a @content for the @value attribute of the <data> element.

@summary: Add a top "about" to <head> and <body>
@requires: U{RDFLib package<http://rdflib.net>}
@organization: U{World Wide Web Consortium<http://www.w3.org>}
@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}
@contact: Ivan Herman, ivan@w3.org
"""

"""
$Id: html5.py,v 1.2 2011-11-18 08:42:48 ivan Exp $
$Date: 2011-11-18 08:42:48 $
"""

# The handling of datatime is a little bit more complex... better put this in a separate function for a better management
from datetime import datetime
import re
datetime_type 	= "http://www.w3.org/2001/XMLSchema#dateTime"
time_type 	 	= "http://www.w3.org/2001/XMLSchema#time"
date_type 	 	= "http://www.w3.org/2001/XMLSchema#date"
date_gYear		= "http://www.w3.org/2001/XMLSchema#gYear"
date_gYearMonth	= "http://www.w3.org/2001/XMLSchema#gYearMonth"
date_gMonthDay	= "http://www.w3.org/2001/XMLSchema#gMonthDay"
plain			= "plain"

_formats = {
	date_gMonthDay	: [ "%m-%d" ],
	date_gYearMonth	: [ "%Y-%m"],
	date_gYear     	: [ "%Y" ],
	date_type      	: [ "%Y-%m-%d" ],
	time_type      	: [ "%H:%M", "%H:%M:%S", "%H:%M:%S.%f" ],
	datetime_type  	: [ "%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%MZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ" ],
}

def _format_test(string) :
	for key in _formats :
		for format in _formats[key] :
			try :
				# try to check if the syntax is fine
				d = datetime.strptime(string, format)
				# bingo!
				return key
			except ValueError :
				pass
	
	# If we got here, we should check the time zone
	# there is a discrepancy betwen the python and the HTML5/XSD lexical string,
	# which means that this has to handled separately for the date and the timezone portion
	try :
		# The time-zone-less portion of the string
		str = string[0:-6]
		# The time-zone portion
		tz = string[-5:]
		print tz
		try :
			t = datetime.strptime(tz,"%H:%M")
		except ValueError :
			# Bummer, this is not a correct time
			return plain
		# The time-zone is fine, the datetime portion has to be checked
		for format in datetypes[datetime_type] :
			try :
				# try to check if it is fine
				d = datetime.strptime(str, format)
				# Bingo!
				return datetime_type
			except ValueError :
				pass
	except :
		pass
	return plain

def html5_extra_attributes(node, state) :
	"""
	@param node: the current node that could be modified
	@param state: current state
	@type state: L{Execution context<pyRdfa.state.ExecutionContext>}
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
				rc = rc + self._get_literal(node)
		return re.sub(r'(\r| |\n|\t)+',"",rc).strip()
	# end getLiteral
	
	if node.tagName == "data" and not node.hasAttribute("content") :
		# state.supress_lang = True
		if node.hasAttribute("value") :
			node.setAttribute("content", node.getAttribute("value"))
		else :
			node.setAttribute("content","")

	elif node.tagName == "time" and not node.hasAttribute("content"):
		# see if there is already a content element; if so, the author has made his/her own encoding
		# The value can come from the attribute or the content:
		if node.hasAttribute("datetime") :
			value = node.getAttribute("datetime")
		else :
			# The value comes from the content of the XML
			value = _get_literal(node)
		# If the user has already set the datatype, then let that one win
		if not node.hasAttribute("datatype") :			
			# Check the datatype:
			dt = _format_test(value)
			if dt != plain :
				node.setAttribute("datatype",dt)
		# Finally, set the value itself
		node.setAttribute("content",value)
			
	elif node.hasAttribute("data") and not node.hasAttribute("src") :
		node.setAttribute("src", node.getAttribute("data"))
