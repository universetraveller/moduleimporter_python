import inspect
class PyAttr:
    def __init__(self, name=None, instance=None, source=None):
        if instance is None:
            raise ValueError('instance could not be None')
        self._inst = instance
        self._name = instance.__name__ if name is None else name
        self._from = inspect.getmodule(instance) if source is None else source

    def get_instance(self):
        return self._inst

    def get_name(self):
        return f'{self._from.get_name()}.{self._name}'

    def get_simple_name(self):
        return self._name

    def get_type(self):
        return type(self._inst).__name__

    def get_source(self):
        return self._from

_checkers = (inspect.isclass, inspect.ismodule, inspect.ismethod, inspect.isfunction, inspect.isbuiltin)
def skip_attr(attr, _checkers=_checkers):
    for _checker in _checkers:
        if _checker(attr):
            return True
    return False

def ismodule(obj):
    return inspect.ismodule(obj)

class PyMethod(PyAttr):
    def __init__(self, name=None, instance=None, source=None):
        super().__init__(name, instance, source)
        self._signature = None

    @property
    def method(self):
        return self._inst

    @property
    def signature(self):
        if self._signature is None:
            self._signature = inspect.signature(self._inst)
        return self._signature

    def get_method(self):
        return self._inst

    def __call__(self, *args, **kwargs):
        return self._inst(*args, **kwargs)

    def invoke(self, *args, **kwargs):
        return self._inst(*args, **kwargs)

    def get_parameters(self):
        return list(self.signature.parameters.values())

    def get_parameter_names(self):
        return list(self.signature.parameters.keys())

    def get_parameter_types(self):
        return list(map(lambda x:x.annotation, list(self.signature.parameters.values())))
    
    def get_parameter_count(self):
        return len(list(self.signature.parameters))

class BaseModule:
    def __init__(self, instance):
        self._module = instance
        self._cache = {}

    def _cache_it(self, name, inst, _type, _attr='_inst'):
        o = self._cache.get(name, None)
        if o is None or getattr(o, _attr) != inst:
            self._cache[name] = _type(name, inst, self)
        return self._cache.get(name)
        
    def get_attrs(self, _all=False):
        _attrs = []
        for attr in inspect.getmembers(self._module):
            if not _all:
                if skip_attr(attr):
                    continue
            _attrs.append(self._cache_it(attr[0], attr[1], PyAttr))
        return _attrs
    
    def get_attr(self, name, _all=False):
        try:
            _attr = getattr(self._module, name)
        except KeyError:
            raise ValueError(f'Attribute {name} does not exist')
        else:
            if not _all and skip_attr(_attr):
                raise ValueError(f'Not permitted to get this attribute because _all is False')
            return self._cache_it(name, _attr, PyAttr)

    def get_method(self, name):
        try:
            _met = getattr(self._module, name)
        except KeyError:
            raise ValueError(f'Method {name} does not exist')
        else:
            if inspect.ismethod(_met) or inspect.isfunction(_met):
                return self._cache_it(name, _met, PyMethod)
            else:
                raise ValueError(f'Method {name} does not exist')

    def get_methods(self):
        _methods = []
        for _met in inspect.getmembers(self._module, inspect.isfunction):
            _methods.append(self._cache_it(_met[0], _met[1], PyMethod))
        return _methods

class PyClass(PyAttr, BaseModule):
    def __init__(self, name=None, inst=None, source=None):
        PyAttr.__init__(self, name, inst, source)
        BaseModule.__init__(self, inst)

    @property
    def cls(self):
        return self._inst

    def get_class(self):
        return self._inst
    
    def is_instance(self, obj):
        return isinstance(obj, self._inst)

    def get_constructor(self):
        return self._cache_it('__init__', getattr(self._inst, '__init__'), PyMethod)

    def get_init(self):
        return self._cache_it('__init__', getattr(self._inst, '__init__'), PyMethod)

    def new_instance(self, *args, **kwargs):
        new_inst = object.__new__(self._inst)
        self.get_init().invoke(new_inst, *args, **kwargs)
        return new_inst

    def get_parent_classes(self):
        return self._inst.__bases__

_MODULE_WRAPPER = lambda name, inst, p : PyModule(inst, p)
class PyModule(BaseModule):
    def __init__(self, instance, importer=None):
        super().__init__(instance)
        if not inspect.ismodule(self._module):
            raise ValueError(f'Expected module type as argument, but got {type(self._module)}')
        self._importer = importer

    @property
    def module(self):
        return self._module

    def get_module(self):
        return self._module

    def get_name(self):
        return self._module.__name__

    def get_simple_name(self):
        return self._module.__name__.rpartition('.')[2]

    def get_package(self):
        return self._module.__name__.rpartition('.')[0]

    def get_importer(self):
        return self._importer

    def get_classes(self):
        _classes = []
        for _cls in inspect.getmembers(self._module, inspect.isclass):
            _classes.append(self._cache_it(_cls[0], _cls[1], PyClass))
        return _classes

    def get_class(self, name):
        try:
            _cls = getattr(self._module, name)
        except KeyError:
            raise ValueError(f'Class {name} does not exist')
        else:
            if inspect.isclass(_cls):
                return self._cache_it(name, _cls, PyClass)
            else:
                raise ValueError(f'Class {name} does not exist')

    def get_submodules(self):
        _ms = []
        for _m in inspect.getmembers(self._module, inspect.ismodule):
            _ms.append(self._cache_it('', _m[1], _MODULE_WRAPPER, '_module'))
        return _ms

    def get_submodule(self, name):
        try:
            _m = getattr(self._module, name)
        except KeyError:
            raise ValueError(f'Module {name} does not exists')
        else:
            if inspect.ismodule(_m):
                return self._cache_it('', _m, _MODULE_WRAPPER, '_module')
            else:
                raise ValueError(f'Module {name} does not exists')
