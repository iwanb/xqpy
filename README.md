# Python bindings for the XQC XQuery API

See the [XQC website](https://sourceforge.net/projects/xqc/). 
The bindings are done with cffi.
For now there is only a [XQilla](http://xqilla.sourceforge.net) implementation, so it is a dependency.

Sample usage:

```python
import xqpy

xquery = xqpy.XQillaImplementation()
query = xquery.prepare('1 to 100')
sequence = query.execute()
# sequence is an iterator
for val in sequence.values():
    print(val)

# Looks like CPython does not call __del__ in order for module variables otherwise?!
del xquery
```

Only tried it on CPython on Linux (Python 2 and 3), but it should work on platforms where cffi works.
