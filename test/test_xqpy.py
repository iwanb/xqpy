from unittest import TestCase, TestSuite
import xqpy

import math
import tempfile

try:
    unicode
except NameError:
    unicode = str


class TestImplementation(TestCase):
    def test_example(self):
        q = self.impl.prepare('./parent/child/text()')
        c = q.create_context()
        d = self.impl.parse_document('<parent><child>1</child><child>2</child></parent>')
        c.set_context_item(d)
        s = q.execute(context=c)
        self.assertEqual(list(s.values()), ['1', '2'])
    def test_file(self):
        with tempfile.TemporaryFile() as f:
            f.write('1 to 10'.encode('utf8'))
            f.flush()
            f.seek(0)
            q = self.impl.prepare_file(f)
            s = q.execute()
            self.assertEqual(list(s.values()), list(range(1, 11)))
    def test_document_file(self):
        with tempfile.TemporaryFile() as f:
            f.write('<a>value</a>'.encode('utf8'))
            f.flush()
            f.seek(0)
            s = self.impl.parse_document_file(f)
            # Crash on node_name, XQilla bug?
            #self.assertEqual(tuple(s.values()), ('value',))
    def test_document(self):
        s = self.impl.parse_document('<a>value</a>')
        # Crash on node_name, XQilla bug?
        #self.assertEqual(tuple(s.values()), ('value',))
    def test_expression(self):
        q = self.impl.prepare('''
        declare variable $test external;
        $test
        ''')
        c = q.create_context()
        c.set_variable('test', self.impl.create_singleton_sequence(5))
        # Bug?
        #print('set var')
        #self.assertEqual(tuple(c.get_variable('test').values()), (5,))
        #print('get var')
        s = q.execute(context=c)
        self.assertEqual(tuple(s.values()), (5, ))

class TestStaticContext(TestCase):
    def setUp(self):
        self.context = self.impl.create_context()
        
    def test_base_uri(self):
        self.assertEqual('', self.context.get_base_uri())
        self.context.set_base_uri('myuri:')
        self.assertEqual('myuri:', self.context.get_base_uri())
    def test_child(self):
        self.context.set_base_uri('myuri:')
        child = self.context.create_child_context()
        self.assertEqual('myuri:', child.get_base_uri())
        child.set_base_uri('myuri2:')
        self.assertNotEqual('myuri2:', self.context.get_base_uri())
    def test_ns(self):
        self.context.declare_ns('pref:', 'http://test.com/')
        self.assertEqual(None, self.context.get_ns_by_prefix('unknown:'))
        self.assertEqual('http://test.com/', self.context.get_ns_by_prefix('pref:'))
        self.assertEqual('', self.context.get_default_element_and_type_ns())
        self.context.set_default_element_and_type_ns('http://other.com/')
        self.assertEqual('http://other.com/', self.context.get_default_element_and_type_ns())
    def test_modes(self):
        tests = (
            ('xpath_compatib_mode', (xqpy.XPathMode.xpath1_0, xqpy.XPathMode.xpath2_0)),
            ('construction_mode', (xqpy.ConstructionMode.preserve, xqpy.ConstructionMode.strip)),
            ('ordering_mode', (xqpy.OrderingMode.ordered, xqpy.OrderingMode.unordered)),
            ('default_order_empty_sequences', (xqpy.OrderEmptyMode.empty_greatest, xqpy.OrderEmptyMode.empty_least)),
            ('boundary_space_policy', (xqpy.BoundarySpaceMode.preserve, xqpy.BoundarySpaceMode.strip)),
            ('copy_ns_mode', 
                ((xqpy.PreserveMode.preserve, xqpy.InheritMode.no_inherit), 
                (xqpy.PreserveMode.no_preserve, xqpy.InheritMode.inherit))),
            )
        for (fname, vals) in tests:
            for val in vals:
                if type(val) is not tuple:
                    val = (val,)
                getattr(self.context, 'set_'+fname)(*val)
                res = getattr(self.context, 'get_'+fname)()
                if type(res) is not tuple:
                    res = (res, )
                self.assertEqual(val, res)
class TestSequence(TestCase):
    def test_empty(self):
        s = self.impl.create_empty_sequence()
        self.assertEqual(list(s), list())
    def test_string(self):
        tests = (
            ("ab", "cd"),
            ("1", "dzadzq", "DZQdzq"),
            ("",),
        )
        for vals in tests:
            s = self.impl.create_string_sequence(vals)
            self.assertEqual(tuple(s.values()), vals)
            s = self.impl.create_string_sequence(vals)
            self.assertEqual(tuple(s), tuple((xqpy.String(v) for v in vals)))
    def test_double(self):
        tests = (
            (1, 1.2),
            ("10.4", -54.1, float('Inf')),
            ("3189432.3",),
        )
        for vals in tests:
            # Apparently they are transformed to strings internally
            s = self.impl.create_string_sequence(vals)
            self.assertEqual(tuple(s.values()), tuple((unicode(v) for v in vals)))
            s = self.impl.create_string_sequence(vals)
            self.assertEqual(tuple(s), tuple((xqpy.String(v) for v in vals)))
    def test_singleton(self):
        tests = (
            (3, xqpy.Decimal(3)),
            (3.1, xqpy.Double(3.1)),
            ("test", xqpy.String("test")),
            (True, xqpy.Boolean(True)),
            (False, xqpy.Boolean(False)),
        )
        for (pyval, xval) in tests:
            s = self.impl.create_singleton_sequence(pyval)
            self.assertEqual(list(s.values()), [pyval])
            s = self.impl.create_singleton_sequence(xval)
            self.assertEqual(list(s.values()), [pyval])
            s = self.impl.create_singleton_sequence(pyval)
            self.assertEqual(list(s), [xval])
            s = self.impl.create_singleton_sequence(pyval)
            s.__next__()
            self.assertEqual(s.string_value(), unicode(xval))
            self.assertEqual(s.type(), type(xval))
            if type(xval) is xqpy.Double or type(xval) is xqpy.Float:
                self.assertEqual(s.double_value(), pyval)
            else:
                self.assertTrue(math.isnan(s.double_value()) or s.double_value() == float(pyval))
            with self.assertRaises(StopIteration):
                s.__next__()
def implementations():
    imps = []
    if hasattr(xqpy, 'XQillaImplementation'):
        imps.append(('XQilla', xqpy.XQillaImplementation))
    if hasattr(xqpy, 'ZorbaImplementation'):
        imps.append(('Zorba', xqpy.ZorbaImplementation))
    return imps

test_cases = (TestStaticContext, TestImplementation, TestSequence)

def load_tests(loader, tests, pattern):
    suite = TestSuite()
    for (name, impl) in implementations():
        for test_class in test_cases:
            new_class = type(name + test_class.__name__, (test_class,), {})
            tests = loader.loadTestsFromTestCase(new_class)
            for test in tests:
                test.impl = impl()
                suite.addTest(test)
    return suite

if __name__ == '__main__':
    unittest.main()
