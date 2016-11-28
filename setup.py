#!/usr/bin/env python
"""Python bindings for the XQC Xquery API.

See https://sourceforge.net/projects/xqc/
Supports XQilla as implementation.
"""
doclines = __doc__.split("\n")

classifiers = """\
Development Status :: 5 - Production/Stable
Intended Audience :: Developers
License :: OSI Approved :: Apache Software License
Operating System :: POSIX
Operating System :: Microsoft :: Windows
Operating System :: Unix
Programming Language :: Python
Programming Language :: Python :: 2
Programming Language :: Python :: 3
Topic :: Text Processing :: Markup :: XML
Topic :: Software Development :: Libraries :: Python Modules
"""
try:
    from setuptools import setup
    pass
except:
    from distutils.core import setup
    pass

try:
    import os
    for key in setting.keys():
        if key in os.environ:
            setting[key] = [s.strip() for s in os.environ[key].split(",") if s]
            pass
        pass
    pass
except:
    pass

setup(
    name="xqpy",
    version="1.0",
    author="Iwan Briquemont",
    author_email="tracnar@gmail.com",
    url="https://github.com/iwanb/xqpy",
    packages=['xqpy'],
    keywords=["xml", "xquery", "xqilla"],
    license="http://www.apache.org/licenses/LICENSE-2.0",
    description=doclines[0],
    long_description="\n".join(doclines[2:]),
    classifiers=[l for l in classifiers.split("\n") if l],
    setup_requires=["cffi>=1.0.0"],
    cffi_modules=["src/xqpy_build.py:ffibuilder"],
    install_requires=["cffi>=1.0.0"],
    test_suite="test",
)
