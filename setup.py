#!/usr/bin/env python
import sys
import re

def setup_python3():
    # Taken from "distribute" setup.py
    from distutils.filelist import FileList
    from distutils import dir_util, file_util, util, log
    from os.path import join
  
    tmp_src = join("build", "src")
    log.set_verbosity(1)
    fl = FileList()
    for line in open("MANIFEST.in"):
        if not line.strip():
            continue
        fl.process_template_line(line)
    dir_util.create_tree(tmp_src, fl.files)
    outfiles_2to3 = []
    for f in fl.files:
        outf, copied = file_util.copy_file(f, join(tmp_src, f), update=1)
        if copied and outf.endswith(".py"):
            outfiles_2to3.append(outf)
  
    util.run_2to3(outfiles_2to3)
  
    # arrange setup to use the copy
    sys.path.insert(0, tmp_src)
  
    return tmp_src

kwargs = {}
if sys.version_info[0] >= 3:
    from setuptools import setup
    kwargs['use_2to3'] = True
    kwargs['install_requires'] = ['html5lib', 'rdflib>3.0.0']
    kwargs['src_root'] = setup_python3()
else:
    try:
        from setuptools import setup
        kwargs['test_suite'] = "nose.collector"
        kwargs['install_requires'] = ['html5lib', 'rdflib>3.0.0']
    except ImportError:
        from distutils.core import setup


# Find version. We have to do this because we can't import it in Python 3 until
# its been automatically converted in the setup process.
def find_version(filename):
    _version_re = re.compile(r'__version__ = "(.*)"')
    for line in open(filename):
        version_match = _version_re.match(line)
        if version_match:
            return version_match.group(1)

version = find_version('pyRdfa/__init__.py')

setup(
    name = 'pyRdfa',
    version = version,
    description = "",
    author = "",
    author_email = "",
    maintainer = "",
    maintainer_email = "",
    url = "",
    license = "LICENSE",
    platforms = ["any"],
    classifiers = ["Programming Language :: Python",
                   "Programming Language :: Python :: 2",
                   "Programming Language :: Python :: 3",
                   "Programming Language :: Python :: 2.4",
                   "Programming Language :: Python :: 2.5",
                   "Programming Language :: Python :: 2.6",
                   "Programming Language :: Python :: 2.7",
                   "Programming Language :: Python :: 3.2",
                   "License :: OSI Approved :: BSD License",
                   "Topic :: Software Development :: Libraries :: Python Modules",
                   "Operating System :: OS Independent",
                   "Natural Language :: English",
                   ],
    long_description = \
    """
    """,
    download_url = "%s.tar.gz" % version,
    packages = ['pyRdfa',
                'pyRdfa/extras',
                'pyRdfa/host',
                'pyRdfa/rdfs',
                'pyRdfa/serializers',
                'pyRdfa/transform',
                ],
    **kwargs
    )

