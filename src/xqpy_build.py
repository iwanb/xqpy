import os 
from cffi import FFI
ffibuilder = FFI()

# TODO allow to choose between xqilla and zorba
ffibuilder.set_source("_xqpy",
    r""" 
        #include "xqc.h"
        #include <xqilla/xqilla-xqc.h>
        
        XQC_Implementation * createXQCImplementation(void) {
            return createXQillaXQCImplementation(XQC_VERSION_NUMBER);
        }
    """,
    libraries=['xqilla'])   # or a list of libraries to link with
    # (more arguments like setup.py's Extension class:
    # include_dirs=[..], extra_objects=[..], and so on)

dir_path = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(dir_path, 'xqcbody.h')) as f:
    ffibuilder.cdef(f.read())

ffibuilder.cdef("""
XQC_Implementation * createXQCImplementation(void);
extern "Python" void error_handle_callback(XQC_ErrorHandler *, XQC_Error, const char *,
        const char *, const char *description, XQC_Sequence *error_object);

""")

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
