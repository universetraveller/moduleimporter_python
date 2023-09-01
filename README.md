# moduleimporter_python
Module importer with its own namespace and reflection feature for python

## Introduction
This importer works like Java URLClassLoader that you can import modules have same name or different versions without conflict. When you do not want to import a module to global namespace sys.modules, it also works.    

Every importer of this library will create its own namespace when initializing, and all modules imported by this importer will be injected into importer's namespace, rather than sys.modules.   

The package also provide wrapper for python modules, methods, classes and attributes to implement reflection.  

Two high level importers are provided, including PathModuleImporter as default and NsModuleImporter as optional if you have another implementation of namespace importer (refer to [nsimport](https://github.com/universetraveller/nsimport_python)) installed .  

* PathModuleImporter uses this package's util module which re-implement importlib with namespace specific so that it has its own namespace when instance is created.  

* NsModuleImporter uses [importlib](https://github.com/python/cpython/tree/3.8/Lib/importlib) as implementation but creates new namespace and bind it to `_bootstrap and` `_bootstrap_external`. It has its own namespace after `_bootstrap` is inintialized.  

## APIs
Available module can be checked in `__init__.py`, and the main functions to load modules can be checked in `_PathModuleImporter` of `Importer.py` and `util.py`. The functions are short enough to read.  

Functions and classes of reflection can be checked in  `_wrapper.py`.  

Generally, you can use `moduleimporter.PathModuleImporter(path)` to initialize a importer. Path is a list where importer to find modules, and it works like sys.path. Path will be initialized as path + sys.path to allow to import other package.  

`importer.load_module(name_of_module)` returns a wrapped module that supports reflection.  

Access importer's attribute with `importer.modules`, `importer.path` and `importer.meta_path` etc.  

Access wrapped module with `importer.unwrap(to_unwrap_object)` or `wrapped.module`.  

## Example
```
>>> import sys
>>> import moduleimporter as MI
>>> importer = MI.PathModuleImporter(['./'])
>>> importer
<moduleimporter.Importer.PathModuleImporter object at 0x7f976241de50>
>>> importer.load_module('codeop')
<moduleimporter._wrapper.PyModule object at 0x7f976222fb50>
>>> 'codeop' in sys.modules
False
>>> 'codeop' in importer.modules
True
>>> random_module = importer.load_module('random')
>>> random_module
<moduleimporter._wrapper.PyModule object at 0x7f976222fb50>
>>> rand_int = random_module.get_method('randint')
>>> rand_int
<moduleimporter._wrapper.PyMethod object at 0x7f97620fb550>
>>> rand_int.invoke(1, 10)
10
>>> rand_int.invoke(1, 10)
4
>>> random_module.get_attr('NV_MAGICCONST')
<moduleimporter._wrapper.PyAttr object at 0x7f9762107640>
>>> random_module.get_class('Random')
<moduleimporter._wrapper.PyClass object at 0x7f97620847c0>
>>> rand_int.get_parameter_names()
['a', 'b']
```

## Notice
Every importer has its own namespace, and all modules loaded by now loading module will be injected to importer's namespace rather than global sys.modules.  

Only test on python3.8, and you can run scripts in [tests](./tests) to check if the library works.  

Core implementation to load module to namespace is in [util](./moduleimporter/util.py). Importer initialization uses `functools` to bind a namespace to import function.  
