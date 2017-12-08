from setuptools import setup

install_requires=[
    "rdflib",
    "html5lib",
]

setup(name="pyRdfa",
      description="pyRdfa Libray",
      version="3.4.3",
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
				])

