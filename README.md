Note: the development and maintenance of this package has been stalled for a long time. I have moved on from this project to radically different areas. I would be pleased if somebody decided to pick it up and develop it further if problems arise…

Historically, the core of this repository content was part to the core RDFLib package as a parser, i.e., it could be used without further ado. However, this setup created some problems and, in 2018, it was decided to remove it from the core distribution of RDFLib, starting with version 5.0.0. Users wishing to use this parser should import _both_ rdflib and pyrdfa3 before using the parser, ie, before invoking `graph.parse( ..., format='rdfa')`. The package can also be used as a standalone tool, in the documentation; this is maintained to secure that deployed applications would not break.

The package can be downloaded from [PyPI](https://pypi.org/project/pyRdfa3/) via `pip install pyRdfa3`.

2013-12-18

---

[![DOI](https://zenodo.org/badge/doi/10.5281/zenodo.14547.svg)](http://dx.doi.org/10.5281/zenodo.14547)

PyRDFA
======


What is it
----------

pyRdfa distiller/parser library. The distribution contains:

- ./pyRdfa: the Python library. You should copy the directory
  somewhere into your PYTHONPATH. Alternatively, you can also run the

    `python setup.py install`

  script in the directory.

- ./scripts/CGI_RDFa.py: can be used as a CGI script to invoke the library.
  It has to be adapted to the local server setup, namely in setting the right paths

- ./scripts/localRdfa.py: script that can be run locally on to transform
  a file into RDF (on the standard output). Run the script with "-h" to
  get the available flags.

- ./Doc-pyRdfa: (epydoc) documentation of the classes and functions

- ./Additional_Packages: some additional packages that are necessary for the library; added here for an easier distribution.
Each of those libraries must be installed separately. Exception is RDFLib that should be installed directly from the server

The package primarily depends on:
 - RDFLib: <http://rdflib.net>. Version 3.2.0 or higher is strongly recommended.
 - html5lib: <https://github.com/html5lib/html5lib-python> 
 - simplejson: <http://undefined.org/python/#simplejson>  (in the additional packages folder), needed if the JSON serialization is used and if the underlying python version is 2.5 or lower
 - isodate: <http://hg.proclos.com/isodate> (in the additional packages folder) which, in some cases, is missing and RDFLib complains (?)

At the moment, the JSON-LD serialization depends on an external JSON-LD serializer. The package comes with a simple one, but if Niklas Lindström's rdflib_jsonld package is available, then this will be used. The former is not really maintained; the latter is in github: https://github.com/RDFLib/rdflib-jsonld. Note that, eventually, this serializer will find its way to the core RDFLib distribution.
   
The package has been tested on Python version 2.5 and higher. Python 2.6 or higher is strongly recommended. The package has been adapted to Python 3, though not yet thoroughly tested, because the html5lib does not have yet a Python 3 version.

For the details on RDFa 1.1, see:

- <http://www.w3.org/TR/rdfa-core>
- <http://www.w3.org/TR/rdfa-lite/>
- <http://www.w3.org/TR/xhtml-rdfa/>
- <http://www.w3.org/TR/rdfa-in-html/>

possibly:

- <http://www.w3.org/TR/rdfa-primer/>
