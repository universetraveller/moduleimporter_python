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

def skip_attr(attr, _checkers=[inspect.isclass, inspect.ismodule, inspect.ismethod, inspect.isfunction, inspect.isbuiltin]):
    for _checker in _checkers:
        if _checker(attr):
            return True
    return False

def ismodule(obj):
    return inspect.ismodule(obj)

class PyMethod(PyAttr):
    def __init__(self, name=None, instance=None, source=None):
        super().__init__(name, instance, source)

    @property
    def method(self):
        return self._inst

    def get_method(self):
        return self._inst

    def __call__(self, *args, **kwargs):
        return self._inst(*args, **kwargs)

    def invoke(self, *args, **kwargs):
        return self._inst(*args, **kwargs)

    def get_parameters(self):
        return list(inspect.signature(self._inst).parameters.values())

    def get_parameter_names(self):
        return list(inspect.signature(self._inst).parameters.keys())

    def get_parameter_types(self):
        return list(map(lambda x:x.annotation, list(inspect.signature(self._inst).parameters.values())))
    
    def get_parameter_count(self):
        return len(list(inspect.signature(self._inst).parameters))

class BaseModule:
    def __init__(self, instance):
        self._module = instance

    def get_attrs(self, _all=False):
        _attrs = []
        for attr in inspect.getmembers(self._module):
            if not _all:
                if skip_attr(attr):
                    continue
            _attrs.append(PyAttr(attr[0], attr[1], self))
        return _attrs
    
    def get_attr(self, name, _all=False):
        try:
            _attr = getattr(self._module, name)
        except KeyError:
            raise ValueError(f'Attribute {name} does not exist')
        else:
            if not _all and skip_attr(_attr):
                raise ValueError(f'_all is not True, not allow to get this attribute')
            return PyAttr(name, _attr, self)

    def get_method(self, name):
        try:
            _met = getattr(self._module, name)
        except KeyError:
            raise ValueError(f'Method {name} does not exist')
        else:
            if inspect.ismethod(_met) or inspect.isfunction(_met):
                return PyMethod(name, _met, self)
            else:
                raise ValueError(f'Method {name} does not exist')

    def get_methods(self):
        _methods = []
        for _met in inspect.getmembers(self._module, inspect.isfunction):
            _methods.append(PyMethod(_met[0], _met[1], self))
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
        return PyMethod('__init__', getattr(self._inst, '__init__'), self)

    def get_init(self):
        return PyMethod('__init__', getattr(self._inst, '__init__'), self)

    def new_instance(self, *args, **kwargs):
        new_inst = object.__new__(self._inst)
        self.get_init().invoke(new_inst, *args, **kwargs)
        return new_inst

    def get_parent_classes(self):
        return self._inst.__bases__

class PyModule(BaseModule):
    def __init__(self, instance, importer=None):
        super().__init__(instance)
        if not inspect.ismodule(self._module):
            raise ValueError(f'Need module type as argument, but got {type(self._module)}')
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
            _classes.append(PyClass(_cls[0], _cls[1], self))
        return _classes

    def get_class(self, name):
        try:
            _cls = getattr(self._module, name)
        except KeyError:
            raise ValueError(f'Class {name} does not exist')
        else:
            if inspect.isclass(_cls):
                return PyClass(name, _cls, self)
            else:
                raise ValueError(f'Class {name} does not exist')

    def get_submodules(self):
        _ms = []
        for _m in inspect.getmembers(self._module, inspect.ismodule):
            _ms.append(PyModule(_m[1], self))
        return _ms

    def get_submodule(self, name):
        try:
            _m = getattr(self._module, name)
        except KeyError:
            raise ValueError(f'Module {name} does not exists')
        else:
            if inspect.ismodule(_m):
                return PyModule(_m, self)
            else:
                raise ValueError(f'Module {name} does not exists')
