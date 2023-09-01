import importlib
from importlib.machinery import PathFinder
from importlib import _bootstrap_external
from importlib._bootstrap_external import _NamespacePath
import importlib._bootstrap
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
            #return self._globals.paths
            return '__virtual_top__', 'path'
        # Not a top-level module. parent-module.__path__ contains the
        #  parent path.
        #return getattr(self._globals.modules[parent], '__path__')
        return parent, '__path__'

    def _get_parent_path(self):
        #return self._find_parent_path_names()
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
    @classmethod
    def find_spec(cls, _globals, fullname, path=None, target=None):
        return super().find_spec(fullname, path, target)

class FrozenImporter(importlib._bootstrap.FrozenImporter):
    @classmethod
    def find_spec(cls, _globals, fullname, path=None, target=None):
        return super().find_spec(fullname, path, target)
