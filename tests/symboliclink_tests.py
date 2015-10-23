import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest

from ntfsutils import symboliclink

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

if __name__ == "__main__":
    unittest.main()
