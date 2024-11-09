import importlib
from importlib.machinery import PathFinder
from importlib._bootstrap_external import _NamespacePath
import importlib._bootstrap
import threading
import sys
import _imp

class NameSpacePath(_NamespacePath):
    _epoch = 0
    def __init__(self, _globals, name, path, path_finder):
        self._globals = _globals
        self._name = name
        self._path = path
        self._last_parent_path = tuple(self._get_parent_path())
        self._last_epoch = self._epoch
        self._path_finder = path_finder

    def _find_parent_path_names(self):
        """Returns a tuple of (parent-module-name, parent-path-attr-name)"""
        parent, dot, me = self._name.rpartition('.')
        if dot == '':
            # This is a top-level module. sys.path contains the parent path.
            return '__virtual_top__', 'path'
        # Not a top-level module. parent-module.__path__ contains the
        #  parent path.
        return parent, '__path__'

    def _get_parent_path(self):
        parent_module_name, path_attr_name = self._find_parent_path_names()
        return getattr(self._globals.modules[parent_module_name], path_attr_name)

class NameSpacePathFinder(PathFinder):

    @classmethod
    def find_spec(cls, _globals, fullname, path=None, target=None):
        if path is None:
            path = _globals.path
        spec = cls._get_spec(fullname, path, target)
        if spec is None:
            return None
        elif spec.loader is None:
            namespace_path = spec.submodule_search_locations
            if namespace_path:
                # We found at least one namespace path.  Return a spec which
                # can create the namespace package.
                spec.origin = None
                spec.submodule_search_locations = NameSpacePath(_globals, fullname, namespace_path, cls._get_spec)
                return spec
            else:
                # why goes there?
                return None
        else:
            return spec

class BuiltinImporter(importlib._bootstrap.BuiltinImporter):
    # built-in modules are deemed as singleton there
    _modules = {}
    # to clean the pollution
    _lock = threading.RLock()
    
    @classmethod
    def find_spec(cls, _globals, fullname, path=None, target=None):
        return super().find_spec(fullname, path, target)

    @staticmethod
    def create_module(spec):
        # skip _imp.create_builtin
        return None

    @staticmethod
    def exec_module(module):
        # actually load the built-in modules there
        spec = module.__spec__
        if spec.name not in BuiltinImporter._modules:
            if spec.name not in sys.builtin_module_names:
                raise ImportError(f'{spec.name!r} is not a built-in module',
                                name=spec.name)
            BuiltinImporter._lock.acquire()
            _frozen = sys.modules.copy()
            # This method invokes low-level C implementation which
            # injects the related modules into global sys.modules
            # see _imp_create_builtin in import.c
            # If sys.modules is redirected, this function
            # will raise exception because _imp uses the
            # very original sys.modules and injects related
            # modules into it
            real = _imp.create_builtin(spec)
            _imp.exec_builtin(real)
            BuiltinImporter._modules[spec.name] = real
            # workaround to keep sys.modules clean
            for name in sys.modules.copy():
                if name not in _frozen:
                    sys.modules.pop(name, None)
                    continue
                _frozen_module = _frozen[name]
                if sys.modules[name] != _frozen_module:
                    sys.modules[name] = _frozen_module
            BuiltinImporter._lock.release()
        real = BuiltinImporter._modules[spec.name]
        namespace = module.__dict__['sys'].modules
        namespace[spec.name] = real

class FrozenImporter(importlib._bootstrap.FrozenImporter):
    @classmethod
    def find_spec(cls, _globals, fullname, path=None, target=None):
        return super().find_spec(fullname, path, target)
