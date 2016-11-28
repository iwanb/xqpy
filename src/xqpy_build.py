import os
import shutil
from cffi import FFI

libraries = []
# Check XQilla and zorba availability
ffibuilder = FFI()
ffibuilder.set_source("xqillatest",
    r"""
        #include <xqilla/xqilla-xqc.h>
    """,
    libraries=['xqilla'])
try:
    ffibuilder.compile(tmpdir="trash")
    libraries.append('xqilla')
except Exception as e:
    print(e)
    pass

ffibuilder = FFI()
ffibuilder.set_source("zorbatest",
    r"""
        #include <zorba/zorbac.h>
        #include <zorba/store_manager_c.h>
    """,
    libraries=['zorba_simplestore'])
try:
    ffibuilder.compile(tmpdir="trash")
    libraries.append('zorba_simplestore')
except Exception as e:
    print(e)
    pass

shutil.rmtree('trash')

# Build module
ffibuilder = FFI()

dir_path = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(dir_path, 'xqcbody.h')) as f:
    ffibuilder.cdef(f.read())

source = r"""
#include "xqc.h"
"""
if 'xqilla' in libraries:
    source += r"""
        #include <xqilla/xqilla-xqc.h>
        
        XQC_Implementation * createMyXQillaXQCImplementation(void) {
            return createXQillaXQCImplementation(XQC_VERSION_NUMBER);
        }
    """
    ffibuilder.cdef("""
        XQC_Implementation * createMyXQillaXQCImplementation(void);
    """)

if 'zorba_simplestore' in libraries:
    source += r"""
        #include <zorba/zorbac.h>
        #include <zorba/store_manager_c.h>
    """
    ffibuilder.cdef("""
        void* create_store();
        void shutdown_store(void*);
        
        XQC_Error zorba_implementation(XQC_Implementation **impl, void* store);
    """)

ffibuilder.cdef("""
extern "Python" void error_handle_callback(XQC_ErrorHandler *, XQC_Error, const char *,
        const char *, const char *description, XQC_Sequence *error_object);

""")

ffibuilder.set_source("_xqpy",
    source,
    libraries=libraries)

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
