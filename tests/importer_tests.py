import moduleimporter as mi
import unittest

class NsImporterTest(unittest.TestCase):
    def test_nsimporter_base(self):
        inst = mi.NsModuleImporter(['./dir0'])
        m = inst.find_module('wrapper_types')
        self.assertIsInstance(m, mi.PyObjects.PyModule)
        self.assertIsInstance(inst.unwrap(m), type(unittest))
        self.assertEqual('wrapper_types', m.get_name())
        m1 = inst.find_loaded_module('wrapper_types')
        self.assertEqual(id(m.module), id(m1.module))
        self.assertIn('wrapper_types', inst.modules)

class PathImporterTest(unittest.TestCase):
    def test_load_module(self):
        inst = mi.PathModuleImporter(['./dir0'])
        with self.assertRaises(ValueError):
            self.assertIsNone(inst.find_loaded_module('wrapper_types'))
        m = inst.load_module('wrapper_types')
        m1 = inst.find_module('wrapper_types')
        self.assertIsNotNone(inst.find_loaded_module('wrapper_types'))
        self.assertEqual(id(m.module), id(m1.module))
        self.assertIn('wrapper_types', inst.modules)
        m2 = inst.find_module('sqlite3')
        self.assertIsInstance(m2, mi.PyObjects.PyModule)

    def test_convert_unwrap(self):
        inst = mi.PathModuleImporter(['./dir0'])
        m = inst.load_module('wrapper_types')
        self.assertIsInstance(m, mi.PyObjects.PyModule)
        m1 = inst.unwrap(m)
        self.assertIsInstance(m1, type(unittest))
        self.assertIsInstance(inst.unwrap(m1), type(unittest))
        self.assertIsInstance(inst.convert(m1), mi.PyObjects.PyModule)
        self.assertIsInstance(inst.convert(m), mi.PyObjects.PyModule)

    def test_init_globals(self):
        inst = mi.PathModuleImporter(['./dir0'])
        self.assertIn('__virtual_top__', inst.modules)
        self.assertEqual('./dir0', inst.path[0])

    def test_remove_module(self):
        inst = mi.PathModuleImporter(['./dir0'])
        inst.load_module('sqlite3')
        inst.load_module('ftplib')
        inst.load_module('re')
        inst.load_module('wrapper_types')
        self.assertIn('sqlite3', inst.modules)
        self.assertIn('ftplib', inst.modules)
        self.assertIn('re', inst.modules)
        self.assertIn('wrapper_types', inst.modules)
        inst.remove_module('ftplib')
        self.assertIn('sqlite3', inst.modules)
        self.assertNotIn('ftplib', inst.modules)
        self.assertIn('re', inst.modules)
        self.assertIn('wrapper_types', inst.modules)
        inst.remove_module('re')
        self.assertIn('sqlite3', inst.modules)
        self.assertNotIn('ftplib', inst.modules)
        self.assertNotIn('re', inst.modules)
        self.assertIn('wrapper_types', inst.modules)
        inst.remove_module('wrapper_types')
        self.assertNotIn('wrapper_types', inst.modules)

    def test_reload_module(self):
        inst = mi.PathModuleImporter(['./dir0'])
        m = inst.load_module('re')
        m1 = inst.load_module('sqlite3')
        self.assertEqual('re', inst.reload_module('sqlite3', m).get_name())
        self.assertEqual('re', inst.modules['sqlite3'].__name__)
        self.assertEqual('sqlite3', inst.reload_module('sqlite3').get_name())
        self.assertEqual('sqlite3', inst.modules['sqlite3'].__name__)
        self.assertEqual(m1.module, inst.reload_module('re', m1).module)

    def test_load_given_module(self):
        inst = mi.PathModuleImporter(['./dir0'])
        m = inst.load_module('wrapper_types')
        m1 = inst.load_module('sqlite3')
        self.assertEqual(m.module, inst.load_given_module('re', m).module)
        self.assertEqual(m.module, inst.modules['re'])
        inst.load_given_module('new_re', m1)
        self.assertEqual(m1.module, inst.modules['new_re'])

    def test_define_module(self):
        inst = mi.PathModuleImporter(['./dir0'])
        m = inst.define_module('test_m', 'a=100')
        self.assertIsInstance(m, mi.PyObjects.PyModule)
        self.assertEqual(100, m.get_attr('a').get_instance())
        self.assertEqual('test_m', m.get_name())

    def test_add_path(self):
        inst = mi.PathModuleImporter(['./dir0'])
        path = './test_path'
        o_path = inst.path[0]
        inst.add_path(path)
        self.assertEqual(path, inst.path[0])
        self.assertEqual(o_path, inst.path[1])








if  __name__  == '__main__':
    unittest.main()
