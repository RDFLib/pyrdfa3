from setuptools import setup

install_requires=[
    "rdflib",
    "html5lib",
]

setup(name="pyRdfa3",
      description="pyRdfa Libray",
      version="3.5.1",
      author="Ivan Herman",
      author_email="ivan@w3.org",
      maintainer="Ivan Herman",
      maintainer_email="ivan@w3.org",
      install_requires=install_requires,
      packages=['pyRdfa',
				'pyRdfa.transform',
				'pyRdfa.extras',
				'pyRdfa.rdfs',
				'pyRdfa.host',
				'pyRdfaExtras',
				'pyRdfaExtras.extras',
				'pyRdfaExtras.serializers'
				],
    entry_points={
        'rdf.plugins.parser': [
            'rdfa = pyRdfa.rdflibparsers:RDFaParser',
            'rdfa1.0 = pyRdfa.rdflibparsers:RDFa10Parser',
            'rdfa1.1 = pyRdfa.rdflibparsers:RDFaParser',
            'application/svg+xml = pyRdfa.rdflibparsers:RDFaParser',
            'application/xhtml+xml = pyRdfa.rdflibparsers:RDFaParser',
            'hturtle = pyRdfa.rdflibparsers:HTurtleParser'
            'html = pyRdfa.rdflibparsers:StructuredDataParser'
            'html/text = pyRdfa.rdflibparsers:StructuredDataParser'

        ],
    }

)
