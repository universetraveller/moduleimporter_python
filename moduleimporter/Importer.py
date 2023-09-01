from . import util
import importlib.util
from . import _wrapper
import functools

SYS_DIR_SEP = '/'

class BaseImporter:
    def __init__(self, _path=[], _globals=None):
        self.path = _path
        self.modules = {}
        if _globals is None:
            self.init_path(_globals)
            self.init_globals(_globals)
        else:
            self.init_from_globals(_globals)

    def init_from_globals(self, _globals):
        if not isinstance(_globals, dict):
            _globals = vars(_globals)
        for name in _globals:
            setattr(self, name, _globals[name])

    def init_globals(self, _globals):
        # works like globals()
        util.reset_sys()
        self.modules = util.lib_setup()
        self.modules['__virtual_top__']=self
        self.modules['builtins'] = util.copy_builtins(self)
        self.meta_path = util.default_meta_path
        self.import_functions = [util.default_import_functions[0]]
        self.builtins = util.create_builtins(self)
        self.import_module = functools.partial(util._util_import, self)
        self.set_module_attrs = functools.partial(util.set_module_attrs, self)
        self.modules['sys'] = util.copy_sys(self)

    def init_path(self, _globals):
        self.path.extend(util.base_path())

    def load_from_spec(self, spec):
        module = importlib.util.module_from_spec(spec)
        self.modules[module.__name__] = module
        module = self.set_module_attrs(module)
        try:
            spec.loader.exec_module(module)
        except:
            spec.loader.exec_module(module)
        return module

    def spec_from_path(self, path):
        last_sep = path.rfind(SYS_DIR_SEP)
        last_level = path if last_sep == -1 else path[last_sep + 1:]
        module_name = last_level[:last_level.find('.')] if '.' in last_level else last_level
        spec = importlib.util.spec_from_file_location(module_name, path)
        if not spec:
            msg = f'Could not load {module_name} from {path}'
            raise ModuleNotFoundError(msg, name=module_name)
        return spec

    def load_from_path(self, path):
        return self.load_from_spec(self.spec_from_path(path))

    def set_import_functions(self, _obj=None):
        if _obj is None:
            _obj = util.default_import_functions
        self.import_functions = _obj

    def set_meta_path(self, _obj):
        if _obj is None:
            _obj = util.default_meta_path
        self.meta_path = _obj

class _PathModuleImporter(BaseImporter):
    def __init__(self, _dirs, _globals=None):
        # _dirs:list - paths to find modules
        self.base_dirs = _dirs
        super().__init__(_dirs, _globals)

    def convert(self, obj):
        if isinstance(obj, _wrapper.PyModule):
            return obj
        return self._convert(obj)

    def _convert(self, obj):
        return _wrapper.PyModule(obj, self)

    def unwrap(self, obj):
        if isinstance(obj, _wrapper.PyModule):
            obj = self._unwrap(obj)
        return obj

    def _unwrap(self, obj):
        if not hasattr(obj, 'module'):
            raise AttributeError('No module to unwrap')
        return obj.module

    def load_module(self, module_name):
        # name:str - module name 
        return self.find_module(module_name)
    
    def find_module(self, module_name):
        if module_name in self.modules:
            return self.modules.get(module_name)
        return self.import_module(module_name)

    def find_loaded_module(self, module_name):
        if module_name in self.modules:
            return self.modules.get(module_name)
        raise ValueError(f'{module_name} is not loaded')

    def remove_module(self, name):
        return self.modules.pop(name, None)

    def reload_module(self, name, obj=None):
        if name in self.modules:
            self.remove_module(name)
            if obj is None:
                return self.import_module(name)
            return self.load_given_module(name, obj).module
        else:
            msg = f'{name} not in modules'
            raise ValueError(msg)

    def load_given_module(self, name, obj):
        if name in self.modules:
            raise ValueError(f'{name} has been used')
        obj = self.unwrap(obj)
        if _wrapper.ismodule(obj):
            self.modules[name] = obj
            return obj
        else:
            msg = f'{obj} is not module'
            raise ValueError(msg)

    def define_module(self, name, s, dont_inherit=True, optimize=-1):
        code = compile(s, name, 'exec', dont_inherit=dont_inherit, optimize=optimize)
        module = util.create_module(name)
        exec(code, module.__dict__)
        return self.set_module_attrs(module)

    def add_path(self, p):
        self.base_dirs.append(p)
        self.path.insert(0, p)

class PathModuleImporter(_PathModuleImporter):
    def __init__(self, _dirs, _globals=None, _cast=None):
        super().__init__(_dirs, _globals)
        _methods = ['find_module', 'find_loaded_module', 'reload_module', 'load_given_module', 'define_module']
        self.cast_methods(_cast, _methods)

    def cast_methods(self, _cast, _methods):
        self._cast = self._convert if _cast is None else _cast
        # define _cast_method here for embedding _cast in the method body otherwise it will run slightly slower
        def _cast_method(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return self._cast(func(*args, **kwargs))
            return wrapper
        # replace original methods with wrapped ones that returns specific types
        # types of return values are turned into return type of _cast
        for _method_name in _methods:
            _method = getattr(self, _method_name)
            if not callable(_method) and not isinstance(_method, type):
                raise ValueError(f'{_method_name} should be callable or class type')
            setattr(self, _method_name, _cast_method(_method))

    def cast_now(self, _method):
        if isinstance(_method, str):
            _method = [_method]
        self.cast_methods(self._cast, _method)

    def cast_of_now(self):
        return self._cast

    def cast_name_of_now(self):
        return self.cast_of_now().__name__

try:
    import nsimport
    class NsModuleImporter(PathModuleImporter):
        def __init__(self, _dirs, _cast=None):
            self.importer = nsimport.get_NsImporter(_dirs)
            self.sys = self.importer.sys
            _exposed_attrs = {
                    'modules': self.sys.modules,
                    'path': self.sys.path,
                    'meta_path': self.sys.meta_path,
                    'import_module': self.importer.import_module
                    }
            super().__init__(_dirs, _exposed_attrs, _cast)

except:
    class NsModuleImporter(PathModuleImporter):
        def __init__(self, _dir, _cast=None):
            raise NotImplementedError('Module nsimport needed')
