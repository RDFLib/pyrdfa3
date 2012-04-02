# -*- coding: utf-8 -*-
"""
Transformers
============

The package uses the concept of 'transformers': the parsed DOM tree is possibly
transformed I{before} performing the real RDFa processing. This transformer structure makes it possible to
add additional 'services' without distoring the core code of RDFa processing.

Some transformations are included in the package and can be used at invocation. These are:

 - The 'name' attribute of the 'meta' element is copied into a 'property' attribute of the same element
 - Interpreting the 'openid' references in the header. See L{transform.OpenID} for further details.
 - Implementing the Dublin Core dialect to include DC statements from the header.  See L{transform.DublinCore} for further details.

The user of the package may refer to those and pass it on to the L{processFile} call via an L{Options} instance. The caller of the package may also add his/her transformer modules. Here is a possible usage with the 'openid' transformer
added to the call::
 from pyRdfa import processFile, Options
 from pyRdfa.transform.OpenID import OpenID_transform
 options = Options(transformers=[OpenID_transform])
 print pyRdfa(options=options).rdf_from_source('filename')

In the case of a call via a CGI script, some of these built-in transformers can be used via extra flags, see L{processURI} for further details.

The current option instance is passed to all transformers as extra parameters. Extensions of the package
may make use of that to control the transformers, if necessary.
"""

