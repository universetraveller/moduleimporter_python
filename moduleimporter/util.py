import builtins
import sys
import _imp
import importlib.util
import importlib._bootstrap
import functools
from . import PathFinder
#import copy
__oimport__ = builtins.__import__
#__builtins = {}
#for name in builtins.__dict__:
#    __builtins[name]=builtins.__dict__[name]
__builtins = builtins.__dict__.copy()

def base_builtins():
    return __builtins.copy()

def create_builtins(_globals):
    base = base_builtins()
    base['__import__'] = functools.partial(_import_core, _globals)
    return base

def copy_builtins(_globals):
    _builtins = copy_module(builtins)
    _builtins.__dict__['__import__'] = functools.partial(_import_core, _globals)
    return _builtins 

def base_path():
    return sys.path[1:]

def original_import():
    return __oimport__

class _GLOBALS:
    def __init__(self, modules, path):
        self.modules = modules
        self.path = path
    def debug(self):
        print('{}\nself.modules: {}\nself.path: {}\n{}'.format('*'*10, self.modules, self.path, '*'*10))

default_meta_path = [PathFinder.NameSpacePathFinder, PathFinder.BuiltinImporter, PathFinder.FrozenImporter]
def get_default_meta_path(num=-1):
    ret = default_meta_path.copy()
    return ret if num < 0 else ret[:num]

def set_default_meta_path(obj=None):
    default_meta_path = default_meta_path if obj is None else obj
    return obj

def _find_spec_core(_globals, name, path, target=None):
    meta_path = _globals.meta_path
    if meta_path is None:
        raise ImportError("meta_path is None, Python is likely "
                      "shutting down")
    if not meta_path:
        _warnings.warn('meta_path is empty', ImportWarning)

    is_reload = name in _globals.modules
    for finder in meta_path:
        with importlib._bootstrap._ImportLockContext():
                try:
                    find_spec = finder.find_spec
                except AttributeError:
                    continue
                else:
                    spec = find_spec(_globals, name, path, target)
        if spec is not None:
            if not is_reload and name in _globals.modules:
                module = _globals.modules[name]
                try:
                    __spec__ = module.__spec__
                except AttributeError:
                    # We use the found spec since that is the one that
                    # we would have used if the parent module hadn't
                    # beaten us to the punch.
                    return spec
                else:
                    if __spec__ is None:
                        return spec
                    else:
                        return __spec__
            else:
                return spec
    return None

def _load_backward_compatible(_globals, spec):
    try:
        spec.loader.load_module(spec.name)
    except:
        if spec.name in _globals.modules:
            module = _globals.modules.pop(spec.name)
            _globals.modules[spec.name] = module
        raise
    module = _globals.modules.pop(spec.name)
    _globals.modules[spec.name] = module
    if getattr(module, '__loader__', None) is None:
        try:
            module.__loader__ = spec.loader
        except AttributeError:
            pass
    if getattr(module, '__package__', None) is None:
        try:
            # Since module.__path__ may not line up with
            # spec.submodule_search_paths, we can't necessarily rely
            # on spec.parent here.
            module.__package__ = module.__name__
            if not hasattr(module, '__path__'):
                module.__package__ = spec.name.rpartition('.')[0]
        except AttributeError:
            pass
    if getattr(module, '__spec__', None) is None:
        try:
            module.__spec__ = spec
        except AttributeError:
            pass
    return module

def _load_unlocked(_globals, spec):
    if spec.loader is not None:
        # Not a namespace package.
        if not hasattr(spec.loader, 'exec_module'):
            msg = (f"{importlib._bootstrap._object_name(spec.loader)}.exec_module() not found; "
                    "falling back to load_module()")
            _warnings.warn(msg, ImportWarning)
            return _load_backward_compatible(_globals, spec)
    module = importlib.util.module_from_spec(spec)
    spec._initializing = True
    try:
        #module.__dict__['__builtins__'] = _globals.modules['__virtual_top__'].builtins
        set_module_attrs(_globals, module)
        _globals.modules[spec.name] = module
        try:
            if spec.loader is None:
                if spec.submodule_search_locations is None:
                    raise ImportError('missing loader', name=spec.name)
            else:
                spec.loader.exec_module(module)
        except:
            try:
                del _globals.modules[spec.name]
            except KeyError:
                pass
            raise
        module = _globals.modules.get(spec.name)
        _globals.modules[spec.name] = module
        importlib._bootstrap._verbose_message('import {!r} # {!r}', spec.name, spec.loader)
    finally:
        spec._initializing = False
    return module

_ERR_MSG_PREFIX = 'No module named '
_ERR_MSG = _ERR_MSG_PREFIX + '{!r}'
# from importlib._bootstrap._find_and_load_unlocked
def _import_internal(_globals, name, __backup_import):
    # needs to bind modules and paths
    parent_spec = None
    parent = name.rpartition('.')[0]
    path=None
    if parent:
        if parent not in _globals.modules:
            module = __backup_import(_globals, parent)
            #_globals.modules[parent] = module
        if name in _globals.modules:
            return _globals.modules[name]
        parent_module = _globals.modules[parent]
        try:
            path = parent_module.__path__
        except AttributeError:
            msg = f'{_ERR_MSG_PREFIX}{name!r}; {parent!r} is not a package'
            raise ModuleNotFoundError(msg, name=name) from None
        parent_spec = parent_module.__spec__
        child = name.rpartition('.')[2]
    #_globals.path.append(path)
    spec = _find_spec_core(_globals, name, path)
    if spec is None:
        #_globals.debug()
        raise ModuleNotFoundError(f'{_ERR_MSG_PREFIX}{name!r}', name=name)
    else:
        if parent_spec:
            try:
                parent_spec._uninitialized_submodules.append(child)
            except AttributeError:
                parent_spec._uninitialized_submodules = [child]
        try:
            module = _load_unlocked(_globals, spec)
        finally:
            if parent_spec:
                parent_spec._uninitialized_submodules.pop()
    if parent:
        parent_module=_globals.modules[parent]
        try:
            setattr(parent_module, child, module)
        except AttributeError:
            msg = f"Cannot set an attribute on {parent!r} for child module {child!r}"
            raise Exception(msg)
    return module

# _find_load
# from importlib._bootstrap._find_and_load
_NEEDS_LOADING = object()
def _find_load(_globals, name, func_):
    # should bind modules
    module = _globals.modules.get(name, _NEEDS_LOADING)
    if (module is _NEEDS_LOADING or
        getattr(getattr(module, "__spec__", None), "_initializing", False)):
        with importlib._bootstrap._ModuleLockManager(name):
            module = _globals.modules.get(name, _NEEDS_LOADING)
            if module is _NEEDS_LOADING:
                return _import_internal(_globals, name, func_)
        importlib._bootstrap._lock_unlock_module(name)

    if module is None:
        message = ('import of {} halted; '
                   'None in _globals.modules'.format(name))
        raise ModuleNotFoundError(message, name=name)

    return module

# from importlib._bootstrap._gcd_import
# replace _gcd_import as _util_import
def _util_import(_globals, name, package=None, level=0):
    importlib._bootstrap._sanity_check(name, package, level)
    if level > 0:
        name = importlib._bootstrap._resolve_name(name, package, level)
    return _find_load(_globals, name, _util_import)

# from importlib._bootstrap._handle_fromlist
# add parameter, replace sys.modules with _globals.modules
def _handle_fromlist(_globals, module, fromlist, import_, *, recursive=False):
    for x in fromlist:
        if not isinstance(x, str):
            if recursive:
                where = module.__name__ + '.__all__'
            else:
                where = "``from list''"
            raise TypeError(f"Item in {where} must be str, "
                            f"not {type(x).__name__}")
        elif x == '*':
            if not recursive and hasattr(module, '__all__'):
                _handle_fromlist(_globals, module, module.__all__, import_,
                                 recursive=True)
        elif not hasattr(module, x):
            from_name = f'{module.__name__}.{x}'
            try:
                import_(_globals, from_name)
            except ModuleNotFoundError as exc:
                if (exc.name == from_name and
                    _globals.modules.get(from_name, _NEEDS_LOADING) is not None):
                    continue
                raise
    return module

def _import_to_loader(_globals, name, globals=None, locals=None, fromlist=(), level=0):
    if level==0:
        module=_util_import(_globals, name)
    else:
        globals_ = globals if globals is not None else {}
        package = importlib._bootstrap._calc___package__(globals_)
        module = _util_import(_globals, name, package, level)
    if not fromlist:
        if level == 0:
            return _util_import(_globals, name.partition('.')[0])
        elif not name:
            return module
        else:
            cut_off = len(name) - len(name.partition('.')[0])
            return _globals.modules[module.__name__[:len(module.__name__)-cut_off]]
    elif hasattr(module, '__path__'):
        return _handle_fromlist(_globals, module, fromlist, _util_import)
    else:
        return module

def _import_backup(_globals, name, globals=None, locals=None, fromlist=(), level=0):
    # delegate to original import
    imported = __oimport__(name, globals, locals, fromlist, level)
    _globals.modules[name] = imported
    return imported

default_import_functions = [_import_to_loader, _import_backup]
def get_default_import_functions(num=-1):
    ret = default_import_functions.copy()
    return ret if num < 0 else ret[:num]

def set_default_import_functions(_obj):
    default_import_functions = _obj
    return _obj

# core function to implement import
def _import_core(_globals, name, globals=None, locals=None, fromlist=(), level=0):
    # _globals: _GLOBALS, consists of modules and paths
    # modules: list, bind a list like sys.modules
    # paths: list, bind a list like sys.path
    try:
        _import_functions = _globals.import_functions
    except KeyError:
        _import_functions = default_import_functions
    last_exception = None
    for import_instance in _import_functions:
        try:
            return import_instance(_globals, name, globals, locals, fromlist, level)
        except Exception as E:
            last_exception = E
            continue
    else:
        raise last_exception

def _import_core_dev(_globals, name, globals=None, locals=None, fromlist=(), level=0):
    return __oimport__(name, globals, locals, fromlist, level)

def copy_module(_module, **keywords):
    module = type(sys)(_module.__name__, 'from copy_module')
    keyword_list = []
    for name in keywords:
        keyword_list.append(name)
        setattr(module, name, keywords[name])
    for attr in dir(_module):
        if attr in keyword_list:
            continue
        setattr(module, attr, getattr(_module, attr))
    return module

def copy_sys(_globals):
    _sys = copy_module(sys)
    _sys.modules = _globals.modules
    _sys.path = _globals.path
    _sys.meta_path = _globals.meta_path
    return _sys

def reset_sys():
    sys.modules = dict(sys.modules)

def set_module_attrs(_globals, module):
    module.__dict__['__builtins__'] = _globals.modules['__virtual_top__'].builtins
    module.__dict__['sys'] = _globals.modules['sys']
    return module

def lib_setup(sys_module=sys, _imp_module=_imp):
    _modules = {}
    importlib._bootstrap._setup(sys_module, _imp_module)
    for name, module in sys.modules.items():
        if isinstance(module, type(sys)):
            if name in sys.builtin_module_names or _imp.is_frozen(name):
                _modules[name] = module
    for name in ['_thread', '_warnings', '_weakref']:
        if not name in _modules:
            _modules[name] = sys.modules[name]
    return _modules

class ImportFunc:
    '''
    def __init__(self, _globals, _import=_import_core):
        self.sys_globals = _globals
        self.instance = _import
    '''
    def __new__(cls, _glb, _imp):
        self = super(ImportFunc, cls).__new__(cls)
        self.sys_globals = _glb
        self.instance = _imp
        return self

    def __call__(self, *args, **kwargs):
        return self.instance(self.sys_globals, *args, **kwargs)

def bind_method(_globals, _method=_import_core):
    # faster than ImportFunc
    return functools.partial(_method, _globals)

def cast_method(method, _cast):
    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        return _cast(method(*args, **kwargs))
    return wrapper

def cast(_method, _cast, *args, **kwargs):
    return _cast(_method(*args, **kwargs))

SYS_NEWLINE = '\n'
def write_error(s):
    sys.stderr.write(f'{s}{SYS_NEWLINE}')

def create_module(name):
    return type(sys)(name)
