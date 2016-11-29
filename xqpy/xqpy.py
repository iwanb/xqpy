from _xqpy import ffi, lib
import base64
from decimal import Decimal as _Decimal

try:
    unicode
except NameError:
    unicode = str

class Implementation:
    def create_context(self):
        """Create a static context to use for expressions"""
        _context = ffi.new('XQC_StaticContext**')
        _handle_error(self._impl.create_context(self._impl, _context))
        c = StaticContext(self, _context[0])
        c.set_error_handler()
        return c
    
    def prepare(self, expression, context=None):
        """Prepare an XQuery expression"""
        _expr = ffi.new('XQC_Expression**')
        _expr_str = expression.encode('utf8')
        if context is None:
            context = self.create_context()
            _context = context._context
        else:
            _context = context._context
        _handle_error(self._impl.prepare(self._impl, _expr_str, _context, _expr))
        e = Expression(self, _expr[0], context)
        # context should be deleted before expression
        context.refs.append(e)
        return e
    def prepare_file(self, expression_file, context=None):
        """Same as prepare but from a file"""
        _expr = ffi.new('XQC_Expression**')
        if context is None:
            context = self.create_context()
            _context = context._context
        else:
            _context = context._context
        _handle_error(self._impl.prepare_file(self._impl, expression_file, _context, _expr))
        e = Expression(self, _expr[0], context)
        # context should be deleted before expression
        context.refs.append(e)
        return e
        
    def parse_document(self, document):
        _seq = ffi.new('XQC_Sequence**')
        _handle_error(self._impl.parse_document(self._impl, document.encode('utf8'), _seq))
        return Sequence(self, _seq[0])
    def parse_document_file(self, document_file):
        _seq = ffi.new('XQC_Sequence**')
        _handle_error(self._impl.parse_document_file(self._impl, document_file, _seq))
        return Sequence(self, _seq[0])
    
    def create_empty_sequence(self):
        _seq = ffi.new('XQC_Sequence**')
        _handle_error(self._impl.create_empty_sequence(self._impl, _seq))
        return Sequence(self, _seq[0])
    def create_singleton_sequence(self, value):
        """Create a sequence with a single value
        
        You can force the type by wrapping your value in a type class"""
        t = type(value)
        if t in _type_to_id:
            type_ = t
            value = unicode(value)
        elif t in _int_type_to_type:
            type_ = _int_type_to_type[t]
            value = unicode(type_(value))
        else:
            raise ValueError('Unsupported type '+repr(t))
        tid = _type_to_id[type_]
        _seq = ffi.new('XQC_Sequence**')
        _handle_error(self._impl.create_singleton_sequence(self._impl, tid, value.encode('utf8'), _seq))
        return Sequence(self, _seq[0])
    def create_string_sequence(self, values):
        cvalues = []
        for v in values:
            cvalues.append(ffi.new('char[]', unicode(v).encode('utf8')))
        _seq = ffi.new('XQC_Sequence**')
        _handle_error(self._impl.create_string_sequence(self._impl, cvalues, len(cvalues), _seq))
        return Sequence(self, _seq[0])
    # Looks like there is loss of precision and zorba interprets the doubles weirdly
    # Ignoring this for now
    #def create_double_sequence(self, values):
    #    cvalues = []
    #    for v in values:
    #        cvalues.append(float(v))
    #    _seq = ffi.new('XQC_Sequence**')
    #    _handle_error(self._impl.create_double_sequence(self._impl, cvalues, len(cvalues), _seq))
    #    return Sequence(self, _seq[0])

if hasattr(lib, 'createMyXQillaXQCImplementation'):
    class XQillaImplementation(Implementation):
        def __init__(self):
            self._impl = lib.createMyXQillaXQCImplementation()
        def __del__(self):
            self._impl.free(self._impl)
  
if hasattr(lib, 'zorba_implementation'):
    class ZorbaImplementation(Implementation):
        def __init__(self):
            self._store = lib.create_store()
            if self._store == ffi.NULL:
                raise RuntimeError('Could not create Zorba store')
            _impl = ffi.new('XQC_Implementation **')
            _handle_error(lib.zorba_implementation(_impl, self._store))
            self._impl = _impl[0]
        def __del__(self):
            self._impl.free(self._impl)
            lib.shutdown_store(self._store)

class StaticContext:
    """
    Static context for preparing expressions
    """
    def __init__(self, impl, _context, refs=[]):
        self.impl = impl
        self._context = _context
        self.refs = refs
    
    def set_error_handler(self, handler=None):
        if handler is None:
            handler = _error_handler
        _handle_error(
            self._context.set_error_handler(self._context, 
                                            _error_handler))
    
    def create_child_context(self):
        context = ffi.new('XQC_StaticContext**')
        _handle_error(
            self._context.create_child_context(self._context, context))
        return StaticContext(self.impl, context[0], refs=[self])
    
    def declare_ns(self, prefix, uri):
        _handle_error(
            self._context.declare_ns(self._context, 
                                    prefix.encode('utf8'),
                                    uri.encode('utf8')))
    def get_ns_by_prefix(self, prefix):
        uri = ffi.new('char**', ffi.NULL)
        _handle_error(
            self._context.get_ns_by_prefix(self._context, 
                                    prefix.encode('utf8'),
                                    uri))
        if uri[0] == ffi.NULL:
            raise XQueryStaticError
        return ffi.string(uri[0]).decode('utf8')
    def set_default_element_and_type_ns(self, uri):
        _handle_error(
            self._context.set_default_element_and_type_ns(self._context, 
                                    uri.encode('utf8')))
    def get_default_element_and_type_ns(self):
        uri = ffi.new('char**')
        _handle_error(
            self._context.get_default_element_and_type_ns(self._context, 
                                    uri))
        return ffi.string(uri[0]).decode('utf8')
    def set_default_function_ns(self, uri):
        _handle_error(
            self._context.set_default_function_ns(self._context, 
                                    uri.encode('utf8')))
    def get_default_function_ns(self):
        uri = ffi.new('char**')
        _handle_error(
            self._context.set_default_element_and_type_ns(self._context, 
                                    uri))
        if uri[0] == ffi.NULL:
            return None
        return ffi.string(uri[0]).decode('utf8')
    
    def set_xpath_compatib_mode(self, mode):
        _handle_error(
            self._context.set_xpath_compatib_mode(self._context, 
                                    int(mode)))
    def get_xpath_compatib_mode(self):
        mode = ffi.new('XQC_XPath1Mode*')
        _handle_error(
            self._context.get_xpath_compatib_mode(self._context, 
                                    mode))
        return int(mode[0])
    def set_construction_mode(self, mode):
        _handle_error(
            self._context.set_construction_mode(self._context, 
                                    int(mode)))
    def get_construction_mode(self):
        mode = ffi.new('XQC_ConstructionMode*')
        _handle_error(
            self._context.get_construction_mode(self._context, 
                                    mode))
        return int(mode[0])
    def set_ordering_mode(self, mode):
        _handle_error(
            self._context.set_ordering_mode(self._context, 
                                    int(mode)))
    def get_ordering_mode(self):
        mode = ffi.new('XQC_OrderingMode*')
        _handle_error(
            self._context.get_ordering_mode(self._context, 
                                    mode))
        return int(mode[0])
    def set_default_order_empty_sequences(self, mode):
        _handle_error(
            self._context.set_default_order_empty_sequences(self._context, 
                                    int(mode)))
    def get_default_order_empty_sequences(self):
        mode = ffi.new('XQC_OrderEmptyMode*')
        _handle_error(
            self._context.get_default_order_empty_sequences(self._context, 
                                    mode))
        return int(mode[0])
    def set_boundary_space_policy(self, mode):
        _handle_error(
            self._context.set_boundary_space_policy(self._context, 
                                    int(mode)))
    def get_boundary_space_policy(self):
        mode = ffi.new('XQC_BoundarySpaceMode*')
        _handle_error(
            self._context.get_boundary_space_policy(self._context, 
                                    mode))
        return int(mode[0])
    def set_copy_ns_mode(self, preserve, inherit):
        _handle_error(
            self._context.set_copy_ns_mode(self._context, 
                                    int(preserve), int(inherit)))
    def get_copy_ns_mode(self):
        preserve = ffi.new('XQC_PreserveMode*')
        inherit = ffi.new('XQC_InheritMode*')
        _handle_error(
            self._context.get_copy_ns_mode(self._context, 
                                    preserve, inherit))
        return (int(preserve[0]), int(inherit[0]))
    
    def set_base_uri(self, base_uri):
        bue = base_uri.encode('utf8')
        _handle_error(
            self._context.set_base_uri(self._context, bue))
    def get_base_uri(self):
        s = ffi.new('char**')
        self._context.get_base_uri(self._context, s)
        return ffi.string(s[0]).decode('utf8')
    
    def __del__(self):
        self._context.free(self._context)

# Enums
class XPathMode:
    xpath2_0 = lib.XQC_XPATH2_0
    xpath1_0 = lib.XQC_XPATH1_0
class ConstructionMode:
    preserve = lib.XQC_PRESERVE_CONS
    strip = lib.XQC_STRIP_CONS
class BoundarySpaceMode:
    preserve = lib.XQC_PRESERVE_SPACE
    strip = lib.XQC_STRIP_SPACE
class PreserveMode:
    preserve = lib.XQC_PRESERVE_NS
    no_preserve = lib.XQC_NO_PRESERVE_NS
class InheritMode:
    inherit = lib.XQC_INHERIT_NS
    no_inherit = lib.XQC_NO_INHERIT_NS
class OrderEmptyMode:
    empty_greatest = lib.XQC_EMPTY_GREATEST
    empty_least = lib.XQC_EMPTY_LEAST
class OrderingMode:
    ordered = lib.XQC_ORDERED
    unordered = lib.XQC_UNORDERED

class DynamicContext:
    def __init__(self, expr, _context, refs=[]):
        self.expr = expr
        self._context = _context
        self._context_item = None
        self.refs = refs
    
    def set_error_handler(self, handler=None):
        if handler is None:
            handler = _error_handler
        _handle_error(
            self._context.set_error_handler(self._context, 
                                            _error_handler))
    
    def set_variable(self, name, value, uri=''):
        """
        Set a variable from a sequence
        Note that after this call the sequence is bound 
        to the lifetime of the dynamic context
        """
        _handle_error(self._context.set_variable(
                                        self._context, 
                                        uri.encode('utf8'), 
                                        name.encode('utf8'), 
                                        value._seq))
        value._owned = False
    def get_variable(self, name, uri=''):
        _seq = ffi.new('XQC_Sequence**')
        _handle_error(self._context.get_variable(
                                        self._context, 
                                        uri.encode('utf8'), 
                                        name.encode('utf8'), 
                                        _seq))
        # Should seq be freed? no idea
        s = Sequence(self.expr.impl, _seq[0])
        self.refs.append(s)
        return s
    def set_context_item(self, value):
        if value.type() is Empty:
            value.movenext()
        _handle_error(self._context.set_context_item(
                                        self._context, 
                                        value._seq))
        self._context_item = value
    def get_context_item(self):
        _seq = ffi.new('XQC_Sequence**')
        _handle_error(self._context.get_context_item(
                                        self._context,  
                                        _seq))
        s = Sequence(self.expr.impl, _seq[0])
        self.refs.append(s)
        return s
    
    def set_implicit_timezone(self, timezone):
        _handle_error(self._context.set_implicit_timezone(
                                        self._context, 
                                        timezone))
    def get_implicit_timezone(self):
        t = ffi.new('int*')
        _handle_error(self._context.get_implicit_timezone(
                                        self._context,  
                                        t))
        return int(t[0])
    def __del__(self):
        self._context.free(self._context)

class Expression:
    """
    A prepared XQuery expression which can be executed
    """
    def __init__(self, impl, _expr, context=None):
        self.impl = impl
        self._expr = _expr
        self.context = context
    def execute(self, context=None):
        _seq = ffi.new('XQC_Sequence**')
        if context is None:
            context = self.create_context()
        _context = context._context
        _handle_error(self._expr.execute(self._expr, _context, _seq))
        s = Sequence(self.impl, _seq[0], refs=[self])
        # Sequence needs to be deleted after context
        context.refs.append(s)
        return s
    def create_context(self):
        _context = ffi.new('XQC_DynamicContext**')
        _handle_error(self._expr.create_context(self._expr, _context))
        c = DynamicContext(self, _context[0])
        c.set_error_handler()
        return c
    def __del__(self):
        self._expr.free(self._expr)

class Sequence:
    def __init__(self, impl, _seq, refs=[], _owned=True):
        self.impl = impl
        self._refs = refs
        self._seq = _seq
        self._owned = _owned
    def __iter__(self):
        return self
    def type(self):
        t = ffi.new('XQC_ItemType*')
        self._seq.item_type(self._seq, t)
        return _id_to_type[int(t[0])]
    def string_value(self):
        s = ffi.new('char**')
        _handle_error(self._seq.string_value(self._seq, s))
        return ffi.string(s[0]).decode('utf8')
    def double_value(self):
        d = ffi.new('double*')
        _handle_error(self._seq.double_value(self._seq, d))
        return float(d[0])
    def node_name(self):
        uri = ffi.new('char**')
        s = ffi.new('char**')
        _handle_error(self._seq.node_name(self._seq, uri, s))
        return (ffi.string(uri[0]).decode('utf8'), ffi.string(s[0]).decode('utf8'))
    def movenext(self):
        _handle_error(self._seq.next(self._seq))
        return self
    def __next__(self):
        self.movenext()
        t = self.type()
        return t.from_item(self)
    def next(self):
        return self.__next__()
    def values(self):
        for v in self:
            yield v.val()
    def __del__(self):
        if self._owned:
            self._seq.free(self._seq)

# Errors and error handling
class XQueryStaticError(Exception):
    pass
class XQueryDynamicError(Exception):
    pass
class XQueryTypeError(Exception):
    pass
class XQuerySerializationError(Exception):
    pass
class ParseError(Exception):
    pass
class NotNodeError(Exception):
    pass
class UnrecognizedEncodingError(Exception):
    pass
class NoItemError(Exception):
    pass
class NoPrefix(Exception):
    pass

_last_exception = None

@ffi.def_extern()
def error_handle_callback(handler, err, error_uri, error_localname, description, error_object):
    """Handle XQuery errors and create a corresponding Python exception"""
    error_uri_str = ffi.string(error_uri).decode('utf8')
    error_localname_str = ffi.string(error_localname).decode('utf8')
    description_str = ffi.string(description).decode('utf8')
    info = "\n".join((error_uri_str, error_localname_str, description_str))
    if err == lib.XQC_STATIC_ERROR:
        exc = XQueryStaticError
    elif err == lib.XQC_TYPE_ERROR:
        exc = XQueryTypeError
    elif err == lib.XQC_DYNAMIC_ERROR:
        exc = XQueryDynamicError
    elif err == lib.XQC_SERIALIZATION_ERROR:
        exc = XQuerySerializationError
    else:
        exc = Exception
    # TODO should make this thread safe
    global _last_exception
    _last_exception = exc(info)

_error_handler = ffi.new('XQC_ErrorHandler *')
_error_handler.user_data = ffi.NULL
_error_handler.error = lib.error_handle_callback

def _handle_error(err):
    """Check the return value of calls and raise an exception
    if there was an error"""
    global _last_exception
    if _last_exception is not None:
        _last_exception_ = _last_exception
        _last_exception = None
        raise _last_exception_
    if err == lib.XQC_END_OF_SEQUENCE:
        raise StopIteration
    elif err == lib.XQC_NOT_IMPLEMENTED:
        raise NotImplementedError
    elif err == lib.XQC_NO_CURRENT_ITEM:
        raise NoItemError
    elif err == lib.XQC_PARSE_ERROR:
        raise ParseError
    elif err == lib.XQC_INVALID_ARGUMENT:
        raise ValueError
    elif err == lib.XQC_NOT_NODE:
        raise NotNodeError
    elif err == lib.XQC_UNRECOGNIZED_ENCODING:
        raise UnrecognizedEncodingError
    elif err == lib.XQC_STATIC_ERROR:
        raise XQueryStaticError
    elif err == lib.XQC_TYPE_ERROR:
        raise XQueryTypeError
    elif err == lib.XQC_DYNAMIC_ERROR:
        raise XQueryDynamicError
    elif err == lib.XQC_SERIALIZATION_ERROR:
        raise XQuerySerializationError
    elif err != lib.XQC_NO_ERROR:
        # TODO proper error checking
        raise RuntimeError

# Types
class BaseType(object):
    """
    Base class for types that can be used as argument
    or returned from Sequence
    """
    def __init__(self, value):
        """Transform, if need be, the given Python value to the XQuery representation"""
        self.value = unicode(value)
    def __unicode__(self):
        return self.__str__()
    def __str__(self):
        return unicode(self.value)
    def __eq__(self, other):
        return (self.val() == other.val())
    @classmethod
    def from_item(cls, sequence):
        """Create the type from a sequence item"""
        return cls(sequence.string_value())
    def val(self):
        """Get the usable Python representation"""
        return self.value
class Empty(BaseType):
    def __init__(self, value=None):
        if value is None or len(value) == 0:
            value = ''
        super(Empty, self).__init__(value)
    def val(self):
        return self.value
class Document(BaseType):
    def __init__(self, node_name, value, uri=""):
        self.node_name = node_name
        self.value = value
        self.uri = ""
    @classmethod
    def from_item(cls, sequence):
        (uri, node) = sequence.node_name()
        return cls(node, sequence.string_value(), uri=uri)
    def __str__(self):
        # Better way to do this?
        return '<'+self.uri+self.node_name+'>' + self.value + '</'+self.node_name+'>'
    def val(self):
        return (self.node_name, self.value)
class Element(Document):
    pass
class Attribute(BaseType):
    pass
class Text(BaseType):
    pass
class ProcessingInstruction(BaseType):
    pass
class Comment(BaseType):
    pass
class Namespace(BaseType):
    pass
class AnySimple(BaseType):
    pass
class AnyUri(BaseType):
    pass
class Base64Binary(BaseType):
    pass
class Boolean(BaseType):
    def __init__(self, value):
        if type(value) is bool:
            if value:
                value = 'true'
            else:
                value = 'false'
        super(Boolean, self).__init__(value)
    def __bool__(self):
        return self.value == 'true'
    def val(self):
        return self.__bool__()
class Date(BaseType):
    pass
class DateTime(BaseType):
    pass
class DayTime(BaseType):
    pass
class Decimal(BaseType):
    def __int__(self):
        return int(self.value)
    def val(self):
        try:
            return self.__int__()
        except ValueError:
            return Decimal_(self.value)
class Double(BaseType):
    def __init__(self, value):
        self.value = float(value)
    def __float__(self):
        return self.value
    @classmethod
    def from_item(cls, sequence):
        return cls(sequence.double_value())
    def val(self):
        return self.value
class Duration(BaseType):
    pass
class Float(Double):
    pass
class GDay(BaseType):
    pass
class GMonth(BaseType):
    pass
class GMonthDay(BaseType):
    pass
class GYear(BaseType):
    pass
class GYearMonth(BaseType):
    pass
class HexBinary(BaseType):
    pass
class Notation(BaseType):
    pass
class Qname(BaseType):
    pass
class String(BaseType):
    pass
class Time(BaseType):
    pass
class UntypedAtomic(BaseType):
    pass
class YearMonth(BaseType):
    pass
_id_to_type = {
lib.XQC_EMPTY_TYPE                  : Empty,
lib.XQC_DOCUMENT_TYPE               : Document,
lib.XQC_ELEMENT_TYPE                : Element,
lib.XQC_ATTRIBUTE_TYPE              : Attribute,
lib.XQC_TEXT_TYPE                   : Text,
lib.XQC_PROCESSING_INSTRUCTION_TYPE : ProcessingInstruction,
lib.XQC_COMMENT_TYPE                : Comment,
lib.XQC_NAMESPACE_TYPE              : Namespace,
lib.XQC_ANY_SIMPLE_TYPE             : AnySimple,
lib.XQC_ANY_URI_TYPE                : AnyUri,
lib.XQC_BASE_64_BINARY_TYPE         : Base64Binary,
lib.XQC_BOOLEAN_TYPE                : Boolean,
lib.XQC_DATE_TYPE                   : Date,
lib.XQC_DATE_TIME_TYPE              : DateTime,
lib.XQC_DAY_TIME_DURATION_TYPE      : DayTime,
lib.XQC_DECIMAL_TYPE                : Decimal,
lib.XQC_DOUBLE_TYPE                 : Double,
lib.XQC_DURATION_TYPE               : Duration,
lib.XQC_FLOAT_TYPE                  : Float,
lib.XQC_G_DAY_TYPE                  : GDay,
lib.XQC_G_MONTH_TYPE                : GMonth,
lib.XQC_G_MONTH_DAY_TYPE            : GMonthDay,
lib.XQC_G_YEAR_TYPE                 : GYear,
lib.XQC_G_YEAR_MONTH_TYPE           : GYearMonth,
lib.XQC_HEX_BINARY_TYPE             : HexBinary,
lib.XQC_NOTATION_TYPE               : Notation,
lib.XQC_QNAME_TYPE                  : Qname,
lib.XQC_STRING_TYPE                 : String,
lib.XQC_TIME_TYPE                   : Time,
lib.XQC_UNTYPED_ATOMIC_TYPE         : UntypedAtomic,
lib.XQC_YEAR_MONTH_DURATION_TYPE    : YearMonth
}

_type_to_id = {v: k for k, v in _id_to_type.items()}

_int_type_to_type = {
    int: Decimal,
    bool: Boolean,
    str: String,
    unicode: String,
    float: Double
}

if __name__ == "__main__":
    # TODO command
    pass
