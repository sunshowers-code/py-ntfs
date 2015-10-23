import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest

from ntfsutils import symboliclink
from ntfsutils import junction

BASE_PATH = os.path.dirname(os.path.abspath(__file__))

class create_for_dir_Test(unittest.TestCase):
    def setUp(self):
        self.source = os.path.join(BASE_PATH, 'data')
        self.link_name =  os.path.join(BASE_PATH, 'tmp-data')
        
    def tearDown(self):
        try:
            os.removedirs(self.link_name)
        except OSError:
            pass
    
    def test_run(self):
        try:
            symboliclink.create(self.source, self.link_name)        
            self.assertEqual(True, os.path.isdir(self.link_name))
        except symboliclink.SymLinkPermissionError as e:
            print(e.message)
        except:
            self.fail()
            
class create_for_file_Test(unittest.TestCase):
    def setUp(self):
        self.source = os.path.join(BASE_PATH, 'data', 'dummy.txt')
        self.invalid_source = os.path.join(BASE_PATH, 'not-exist')
        self.link_name =  os.path.join(BASE_PATH, 'data', 'tmp-data.txt')
    
    def tearDown(self):
        try:
            os.remove(self.link_name)
        except OSError:
            pass
        
    def test_source_not_exist(self):
        with self.assertRaises(Exception) as cm:
            symboliclink.create(self.invalid_source, self.link_name)
            
    def assertEqualFile(self, filepath_a, filepath_b):
        with open(filepath_a, "rb") as f:
            content_a = f.read()
        with open(filepath_b, "rb") as f:
            content_b = f.read()
        self.assertEqual(content_a, content_b)
            
    def test_create(self):
        try:
            symboliclink.create(self.source, self.link_name)
            self.assertEqualFile(self.source, self.link_name)
        except symboliclink.SymLinkPermissionError as e:
            print(e.message)
        except:
            self.fail()

class issymboliclink_Test(unittest.TestCase):
    def setUp(self):
        self.source_file = os.path.join(BASE_PATH, 'data', 'dummy.txt')
        self.source_dir = os.path.join(BASE_PATH, 'data')

        self.link_name_file =  os.path.join(BASE_PATH, 'data', 'tmp-data.txt')
        self.link_name_dir =  os.path.join(BASE_PATH, 'tmp-data')

    def tearDown(self):
        try:
            os.removedirs(self.link_name_dir)
        except OSError:
            pass
        try:
            os.remove(self.link_name_file)
        except OSError:
            pass

    def test_for_dir(self):
        try:
            symboliclink.create(self.source_dir, self.link_name_dir)
        except symboliclink.SymLinkPermissionError as e:
            return
        except:
            self.fail()    
        self.assertTrue(symboliclink.issymboliclink(self.link_name_dir))

    def test_for_file(self):
        try:
            symboliclink.create(self.source_file, self.link_name_file)
        except symboliclink.SymLinkPermissionError as e:
            return
        except:
            self.fail()    
        self.assertTrue(symboliclink.issymboliclink(self.link_name_file))

    def test_for_not_link_file(self):  
        self.assertFalse(symboliclink.issymboliclink(self.source_file))
    
    def test_for_not_link_dir(self):
        self.assertFalse(symboliclink.issymboliclink(self.source_dir))

    def test_for_not_exist(self):
        self.assertFalse(symboliclink.issymboliclink("invalid-path"))

class readlink_for_file_Test(unittest.TestCase):
    def setUp(self):
        self.source = os.path.join(BASE_PATH, 'data', 'dummy.txt')
        self.link_name =  os.path.join(BASE_PATH, 'data', 'tmp-data.txt')

    def tearDown(self):
        try:
            os.remove(self.link_name)
        except OSError:
            pass

    def test_absolute_path(self):
        try:
            symboliclink.create(self.source, self.link_name)
            actual = symboliclink.readlink(self.link_name)
            self.assertEqual(actual, self.source)
        except symboliclink.SymLinkPermissionError as e:
            print(e.message)
        except:
            self.fail()

    def test_relative_path(self):
        source = "dummy.txt"
        try:
            symboliclink.create(source, self.link_name, True)
            actual = symboliclink.readlink(self.link_name)
            self.assertEqual(actual, source)
        except symboliclink.SymLinkPermissionError as e:
            print(e.message)
        except:
            self.fail()

class readlink_for_dir_Test(unittest.TestCase):
    def setUp(self):
        self.source = os.path.join(BASE_PATH, 'data')
        self.link_name =  os.path.join(BASE_PATH, 'tmp-data')

    def tearDown(self):
        try:
            os.removedirs(self.link_name)
        except OSError:
            pass
        try:
            os.remove(self.link_name)
        except OSError:
            pass

    def test_absolute_path(self):
        try:
            symboliclink.create(self.source, self.link_name)
            actual = symboliclink.readlink(self.link_name)
            self.assertEqual(actual, self.source)
        except symboliclink.SymLinkPermissionError as e:
            print(e.message)
        except:
            self.fail()

    def test_relative_path(self):
        source = "tmp-data"
        try:
            symboliclink.create(source, self.link_name, True)
            actual = symboliclink.readlink(self.link_name)
            self.assertEqual(actual, source)
        except symboliclink.SymLinkPermissionError as e:
            print(e.message)
        except:
            self.fail()

class readlink_for_not_symlink_Test(unittest.TestCase):
    def setUp(self):
        self.filename = os.path.join(BASE_PATH, 'data', 'dummy.txt')

    def test_raise_exc(self):
        with self.assertRaises(Exception) as cm:
            symboliclink.readlink(self.filename)

if __name__ == "__main__":
    unittest.main()
