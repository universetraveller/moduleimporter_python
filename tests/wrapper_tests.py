import moduleimporter as mi
import unittest

class PyObjectsTest(unittest.TestCase):
    def test_get_py_module(self):
        inst = mi.PathModuleImporter(['./dir0'])
        m = inst.load_module('wrapper_types')
        self.assertIsInstance(m, mi.PyObjects.PyModule)
        self.assertIsInstance(m.module, type(unittest))
        self.assertIsInstance(m.get_module(), type(unittest))

    def test_py_module_get_name(self):
        inst = mi.PathModuleImporter(['./'])
        m = inst.load_module('dir0.wrapper_types')
        self.assertEqual('dir0', m.get_package())
        self.assertEqual('dir0.wrapper_types', m.get_name())
        self.assertEqual('wrapper_types', m.get_simple_name())

    def test_py_module_get_members(self):
        inst = mi.PathModuleImporter(['./dir0'])
        m = inst.load_module('wrapper_types')

        self.assertIsInstance(m.get_importer(), mi.PathModuleImporter)
        self.assertEqual(inst, m.get_importer())

        self.assertEqual(1, len(m.get_classes()))
        self.assertEqual(m.get_classes()[0].get_class(), m.get_class('clz').get_class())
        self.assertIsInstance(m.get_class('clz'), mi.PyObjects.PyClass)

        self.assertEqual('sqlite3', m.get_submodules()[0].get_name())
        self.assertEqual(m.get_submodule('sqlite3').module, m.get_submodules()[0].module)
        self.assertIsInstance(m.get_submodule('sqlite3'), mi.PyObjects.PyModule)
        
        self.assertEqual(1, m.get_attr('int_1').get_instance())
        self.assertEqual('1', m.get_attr('str_1').get_instance())

        self.assertEqual('func1', m.get_method('func1').method.__name__)
        self.assertEqual(5, m.get_method('func5').get_parameter_count())

    def test_py_class_get_members(self):
        inst = mi.PathModuleImporter(['./dir0'])
        m = inst.load_module('wrapper_types')
        clz = m.get_class('clz')
        clz_inst = clz.new_instance(1)
        self.assertEqual(1, clz_inst.i)
        self.assertEqual(2, clz.get_constructor().get_parameter_count())
        self.assertTrue(clz.is_instance(clz_inst))
        self.assertEqual(2, clz_inst.func1(2))
        self.assertEqual(2, clz.get_method('func1').invoke(clz_inst, 2))
    
    def test_py_method_get_members(self):
        inst = mi.PathModuleImporter(['./dir0'])
        m = inst.load_module('wrapper_types')
        f = m.get_method('func5')
        self.assertEqual(['a', 'b', 'c', 'd', 'e'], f.get_parameter_names())
        self.assertEqual(100, f.invoke(100, 1, 10, 999, 1000))
        self.assertEqual([int, int, str, list, dict], f.get_parameter_types())

    def test_py_attr_get_members(self):
        inst = mi.PathModuleImporter(['./dir0'])
        m = inst.load_module('wrapper_types')
        a = m.get_attr('int_1')
        self.assertEqual('int', a.get_type())
        self.assertEqual('wrapper_types.int_1', a.get_name())
        self.assertEqual('int_1', a.get_simple_name())
        self.assertEqual(m, a.get_source())

if __name__ == '__main__':
    unittest.main()
