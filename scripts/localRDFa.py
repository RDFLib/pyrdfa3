#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Run the pyRdfa package locally, ie, on a local file

"""
# You may want to adapt this to your environment...
import sys, getopt, platform

sys.path.insert(0,"/Users/ivan/Library/Python")

from pyRdfa                        import pyRdfa
from pyRdfa.transform.metaname     import meta_transform
from pyRdfa.transform.OpenID       import OpenID_transform
from pyRdfa.transform.DublinCore   import DC_transform
from pyRdfa.transform.lite         import lite_prune
from pyRdfa.options                import Options

extraTransformers = [
	# containers_collections,
	#OpenID_transform,
	#DC_transform,
	# meta_transform
]

###########################################

usageText="""Usage: %s -[vjxtnpzsb:g:ryle] [filename[s]]
where:
  -x: output format RDF/XML
  -t: output format Turtle (default)
  -j: output format JSON-LD
  -n: output format N Triples
  -p: output format pretty RDF/XML
  -z: exceptions should be returned as graphs instead of exceptions raised
  -b: give the base URI; if a file name is given, this can be left empty and the file name is used
  -s: whitespace on plain literals are not preserved (default: preserved, per RDFa syntax document); this is a non-standard feture
  -l: run in RDFa 1.1 Lite mode (non-RDFa Lite generate warnings) (default: False)
  -r: report on the details of the vocabulary caching process
  -y: bypass the vocabulary cache checking, generate a new cache every time (good for debugging) (default:False)
  -v: perform vocabulary expansion (default: False)
  -g: value can be 'output', 'processor', 'output,processor' or 'processor,output'; controls which graphs are returned
  -e: embedded (in a <script> element) Turtle content or RDF/XML (in its own namespace) _not_ parsed and added to the output graph (default:True, i.e., parsed)

'Filename' can be a local file name or a URI. In case there is no filename, stdin is used.

The -g option may be unnecessary, the script tries to make a guess based on a default xmlns value for XHTML or SVG.
"""

def usage() :
	print usageText % sys.argv[0]

format                 = "turtle"
extras                 = []
value                  = ""
space_preserve         = True
base                   = ""
value                  = []
rdfOutput              = False
output_default_graph   = True
output_processor_graph = True
vocab_cache_report     = False
refresh_vocab_cache    = False
vocab_expansion        = False
vocab_cache            = True
embedded_rdf           = True

try :
	opts, value = getopt.getopt(sys.argv[1:],"vxetjnpzsb:g:ryl",['graph='])
	for o,a in opts:
		if o == "-t" :
			format = "turtle"
		elif o == "-n" :
			format = "nt"
		elif o == "-j" :
			format = "json-ld"
		elif o == "-p" or o == "-x":
			format = "pretty-xml"
		elif o == "-z" :
			rdfOutput = True
		elif o == "-b" :
			base = a
		elif o == "-e" :
			embedded_rdf = False
		elif o == "-s" :
			space_preserve = False
		elif o == "-l" :
			extras.append(lite_prune)
		elif o == "-r" :
			vocab_cache_report = True			
		elif o == "-v" :
			vocab_expansion = True
		elif o == "-y" :
			bypass_vocab_cache = True
		elif o in ("-g", "--graph") :
			if a == "processor" :
				output_default_graph 	= False
				output_processor_graph 	= True
			elif a == "processor,default" or a == "default,processor" :
				output_processor_graph 	= True
			elif a == "default" :				
				output_default_graph 	= True
				output_processor_graph 	= False			
		else :
			usage()
			sys.exit(1)
except :
	usage()
	sys.exit(1)

options = Options(output_default_graph = output_default_graph,
				  output_processor_graph = output_processor_graph,
				  space_preserve=space_preserve,
				  transformers = extras,
				  embedded_rdf = embedded_rdf,
				  vocab_expansion = vocab_expansion,
				  vocab_cache = vocab_cache,
				  vocab_cache_report = vocab_cache_report,
				  refresh_vocab_cache = refresh_vocab_cache,
				  experimental_features = True
)

processor = pyRdfa(options, base)
if len(value) >= 1 :
	print processor.rdf_from_sources(value, outputFormat = format, rdfOutput = rdfOutput)
else :
	print processor.rdf_from_source(sys.stdin, outputFormat = format, rdfOutput = rdfOutput)

