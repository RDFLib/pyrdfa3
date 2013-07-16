
***
*** Warning (2013-07-16): the latest version of the html5lib package has a bug.
*** This bug manifests itself if the source HTML file contains non-ASCII Unicode characters
*** Until the bug is handled, users should use the older, 0.95 version. It can be downloaded
*** at https://code.google.com/p/html5lib/downloads/detail?name=html5lib-0.95.tar.gz
***

pyRdfa distiller/parser library. The distribution contains:

- ./pyRdfa: the Python library. You should copy the directory
  somewhere into your PYTHONPATH. Alternatively, you can also run the

    python setup.py install

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
 - RDFLib<http://rdflib.net>. Version 3.2.0 or higher is strongly recommended.
 - html5lib<https://github.com/html5lib/html5lib-python> 
 - simplejson<http://undefined.org/python/#simplejson>  (in the additional packages folder), needed if the JSON serialization is used and if the underlying python version is 2.5 or lower
 - isodate<http://hg.proclos.com/isodate> (in the additional packages folder) which, in some cases, is missing and RDFLib complains (?)
   
The package has been tested on Python version 2.5 and higher. Python 2.6 or higher is strongly recommended. The package has been adapted to Python 3, though not yet thoroughly tested, because the html5lib does not have yet a Python 3 version.

For the details on RDFa 1.1, see:

http://www.w3.org/TR/rdfa-core
http://www.w3.org/TR/rdfa-lite/
http://www.w3.org/TR/xhtml-rdfa/
http://www.w3.org/TR/rdfa-in-html/

possibly:

http://www.w3.org/TR/rdfa-primer/
