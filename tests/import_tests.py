import moduleimporter as mi
import unittest

class ImporterTest(unittest.TestCase):

    def test_init_importer(self):
        inst = mi.NsModuleImporter([])
        inst.load_module('sys')
        self.assertIsInstance(inst, mi.NsModuleImporter)
        
        inst1 = mi.PathModuleImporter([])
        inst1.load_module('os')
        self.assertIsInstance(inst, mi.PathModuleImporter)

    def test_import_core(self):
        import sys
        sys.modules.pop('for_test_module', None)
        inst = mi.PathModuleImporter(['./'])
        mi.util._import_core(inst, 'for_test_module')
        self.assertNotIn('for_test_module', sys.modules)
        self.assertIn('for_test_module', inst.modules)

    def test_load_single_module(self):
        import sys
        sys.modules.pop('for_test_module', None)
        inst = mi.PathModuleImporter(['./'])
        m = inst.load_module('for_test_module')
        self.assertNotIn('for_test_module', sys.modules)
        self.assertIn('for_test_module', inst.modules)
        self.assertEqual(1, m.get_method('return1').invoke())
    
    def test_load_multi_modules(self):
        import sys
        sys.modules.pop('for_test_module', None)

        inst = mi.PathModuleImporter(['./'])
        inst1 = mi.PathModuleImporter(['./'])
        m = inst.load_module('for_test_module')
        m1 = inst1.load_module('for_test_module1')

        self.assertNotIn('for_test_module', sys.modules)
        self.assertNotIn('for_test_module', inst1.modules)
        self.assertIn('for_test_module', inst.modules)

        self.assertNotIn('for_test_module1', sys.modules)
        self.assertNotIn('for_test_module1', inst.modules)
        self.assertIn('for_test_module1', inst1.modules)

        self.assertEqual(1, m.get_method('return1').invoke())
        self.assertEqual(2, m1.get_method('return_same').invoke(2))

    def test_cross_before_and_after_import_0(self):
        import sys
        sys.modules.pop('difflib', None)
        sys.modules.pop('datetime', None)
        sys.modules.pop('_datetime', None)

        inst = mi.PathModuleImporter(['./'])
        inst1 = mi.PathModuleImporter(['./'])
        m1 = inst1.load_module('difflib')
        m = inst.load_module('datetime')

        self.assertNotIn('difflib', sys.modules)
        self.assertNotIn('_datetime', sys.modules)
        self.assertNotIn('datetime', sys.modules)

        self.assertNotIn('datetime', inst1.modules)
        self.assertNotIn('_datetime', inst1.modules)
        self.assertIn('difflib', inst1.modules)

        self.assertNotIn('difflib', inst.modules)
        self.assertIn('datetime', inst.modules)
        self.assertIn('_datetime', inst.modules)

    def test_cross_before_and_after_import_1(self):
        import sys
        sys.modules.pop('difflib', None)
        sys.modules.pop('datetime', None)
        sys.modules.pop('_datetime', None)
        
        inst = mi.PathModuleImporter(['./'])
        m = inst.load_module('datetime')
        inst1 = mi.PathModuleImporter(['./'])
        m1 = inst1.load_module('difflib')

        self.assertNotIn('difflib', sys.modules)
        self.assertNotIn('_datetime', sys.modules)
        self.assertNotIn('datetime', sys.modules)

        self.assertNotIn('datetime', inst1.modules)
        self.assertNotIn('_datetime', inst1.modules)
        self.assertIn('difflib', inst1.modules)

        self.assertNotIn('difflib', inst.modules)
        self.assertIn('datetime', inst.modules)
        self.assertIn('_datetime', inst.modules)

    def test_import_sub_packages(self):
        import sys
        inst = mi.PathModuleImporter(['./dir0'])
        inst1 = mi.PathModuleImporter(['./'])
        m = inst.load_module('for_test_module_dir0')
        with self.assertRaises(ModuleNotFoundError):
            m1 = inst1.load_module('for_test_module_dir0')
        m1 = inst1.load_module('dir0.for_test_module_dir0_1')

        self.assertNotIn('for_test_module_dir0', sys.modules)
        self.assertNotIn('for_test_module_dir0_1', sys.modules)
        self.assertIn('for_test_module_dir0', inst.modules)
        self.assertIn('dir0.for_test_module_dir0_1', inst1.modules)

        self.assertEqual(1, m.get_attr('defined_in_sub_import').get_instance())
        self.assertEqual(1, m1.get_attr('defined_in_sub_import').get_instance())
        self.assertEqual(2, m.get_method('return_same').invoke(2))

    def test_recursive_import(self):
        import sys
        sys.modules.pop('ftplib', None)
        sys.modules.pop('pdb', None)
        inst = mi.PathModuleImporter(['./'])
        m = inst.find_module('ftplib')
        m = inst.find_module('pdb')
        self.assertNotIn('ftplib', sys.modules)
        self.assertIn('ftplib', inst.modules)
        self.assertNotIn('pdb', sys.modules)
        self.assertIn('pdb', inst.modules)

    def test_import_same_name_builtin_module(self):
        import sys
        sys.modules.pop('_sre', None)
        inst = mi.PathModuleImporter(['./'])
        self.assertNotIn('_sre', inst.modules)
        m = inst.find_module('_sre')
        import _sre
        sys.modules['_sre'] = __import__('_sre')
        self.assertNotEqual(id(sys.modules['_sre']), id(m))
        self.assertEqual('my _sre', m.get_method('return_same')('my _sre'))
        self.assertIsNone(getattr(sys.modules['_sre'], 'return_same', None))

    def test_import_same_name_common_module(self):
        import sys
        sys.modules.pop('cgitb', None)
        inst = mi.PathModuleImporter(['./dir0'])
        self.assertNotIn('cgitb', inst.modules)
        m = inst.find_module('cgitb')
        import cgitb
        self.assertNotEqual(id(sys.modules['cgitb']), id(m))
        self.assertEqual('my cgitb', m.get_method('return_same').method('my cgitb'))
        self.assertIsNone(getattr(sys.modules['cgitb'], 'return_same', None))

    def test_issue_pre_loaded_modules(self):
        # import enum before importing socket, and socket uses enum.IntEnum that uses global sys as namespace's sys
        import enum
        import sys
        sys.modules.pop('socket', None)
        inst = mi.PathModuleImporter(['./dir0'])
        m = inst.load_module('socket')
        self.assertIsInstance(m, mi.PyObjects.PyModule)

    def test_issue_pre_loaded_modules_solved_no_leakage(self):
        import enum
        import sys
        sys.modules.pop('socket', None)
        inst = mi.PathModuleImporter(['./dir0'])
        m = inst.load_module('socket')
        self.assertIsInstance(m, mi.PyObjects.PyModule)
        self.assertEqual(id(enum), id(sys.modules['enum']))
        self.assertNotEqual(id(enum), id(inst.modules['enum']))

if __name__ == '__main__':
    unittest.main()
