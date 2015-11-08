import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest

from ntfsutils import symlink
from ntfsutils import junction

BASE_PATH = os.path.dirname(os.path.abspath(__file__))

class SymLinkTest(unittest.TestCase):
    def setUp(self):
        self.source_dir = os.path.join(BASE_PATH, 'data')
        self.link_name_dir =  os.path.join(BASE_PATH, 'tmp-data')

        self.source_file = os.path.join(BASE_PATH, 'data', 'dummy.txt')
        self.link_name_file =  os.path.join(BASE_PATH, 'data', 'tmp-data.txt')

        self.not_exist_dir = os.path.join(BASE_PATH, 'not-exist')
        self.not_exist_file = os.path.join(BASE_PATH, 'not-exist.txt')

        self.invalid_path = "dummy:\\dummy"

    def tearDown(self):
        for elem in [self.link_name_dir, self.link_name_file]:
            try:
                os.removedirs(elem)
            except OSError:
                pass
            try:
                os.remove(elem)
            except OSError:
                pass

    def assertSymlinkPrivilegeNotHeldException(self, e):
        self.assertEqual(e.__class__, OSError)
        if e.winerror != symlink.ERROR_PRIVILEGE_NOT_HELD:
            self.fail()

    def assertEqualFile(self, filepath_a, filepath_b):
        with open(filepath_a, "rb") as f:
            content_a = f.read()
        with open(filepath_b, "rb") as f:
            content_b = f.read()
        self.assertEqual(content_a, content_b)

    def assertBrokenLink(self, filepath):
        self.assertEqual(os.path.exists(filepath), False)
        self.assertEqual(os.path.lexists(filepath), True)

    def createSymlink(self, source, link_name):
        try:
            symlink.create(source, link_name)    
        except OSError as e:
            self.assertSymlinkPrivilegeNotHeldException(e)
            self.skipTest("symlink privilege not held")
        except Exception as e:
            self.fail()

class hasprivilege_Test(SymLinkTest):
    def test_run(self):
        retval = symlink.hasprivilege()
        self.assertIn(retval, (True, False))
    
class create_Test(SymLinkTest):    
    def test_for_dir(self):
        self.createSymlink(self.source_dir, self.link_name_dir)        
        self.assertEqual(True, os.path.isdir(self.link_name_dir))

    def test_for_file(self):
        self.createSymlink(self.source_file, self.link_name_file)
        self.assertEqualFile(self.source_file, self.link_name_file)

    def test_for_not_exist_path(self):
        self.createSymlink(self.not_exist_file, self.link_name_file)
        self.assertBrokenLink(self.link_name_file)

    def test_for_invalid_path(self):
        self.createSymlink(self.invalid_path, self.link_name_file)
        self.assertBrokenLink(self.link_name_file)

class issymlink_Test(SymLinkTest):
    def test_for_dir_symlink(self):
        self.createSymlink(self.source_dir, self.link_name_dir)
        self.assertTrue(symlink.issymlink(self.link_name_dir))

    def test_for_file_symlink(self):
        self.createSymlink(self.source_file, self.link_name_file)
        self.assertTrue(symlink.issymlink(self.link_name_file))

    def test_for_real_file(self):  
        self.assertFalse(symlink.issymlink(self.source_file))

    def test_for_real_dir(self):
        self.assertFalse(symlink.issymlink(self.source_dir))

    def test_for_not_exist_path(self):
        self.assertFalse(symlink.issymlink(self.invalid_path))
    
    def test_for_junction(self):
        junction.create(self.source_dir, self.link_name_dir)
        self.assertFalse(symlink.issymlink(self.link_name_dir))

class readlink_Test(SymLinkTest):
    def test_absolute_path_for_file_symlink(self):
        self.createSymlink(self.source_file, self.link_name_file)        
        actual = symlink.readlink(self.link_name_file)
        self.assertEqual(actual, self.source_file)

    def test_relative_path_for_file_symlink(self):
        source = "dummy.txt"
        self.createSymlink(source, self.link_name_file)        
        actual = symlink.readlink(self.link_name_file)
        self.assertEqual(actual, source)

    def test_absolute_path_for_dir_symlink(self):
        self.createSymlink(self.source_dir, self.link_name_dir)
        actual = symlink.readlink(self.link_name_dir)
        self.assertEqual(actual, self.source_dir)

    def test_relative_path_for_dir_symlink(self):
        source = "dummy-dir"
        self.createSymlink(source, self.link_name_dir)
        actual = symlink.readlink(self.link_name_dir)
        self.assertEqual(actual, source)

    def test_for_real_file(self):
        with self.assertRaises(Exception) as cm:
            symlink.readlink(self.source_file)

    def test_for_real_dir(self):
        with self.assertRaises(Exception) as cm:
            symlink.readlink(self.source_dir)

    def test_for_not_exist_path(self):
        with self.assertRaises(Exception) as cm:
            symlink.readlink(self.not_exist_file)

    def test_for_invalid_path(self):
        with self.assertRaises(Exception) as cm:
            symlink.readlink(self.invalid_path)

if __name__ == "__main__":
    unittest.main()
