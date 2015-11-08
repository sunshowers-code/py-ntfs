import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest

from ntfsutils import junction

BASE_PATH = os.path.dirname(os.path.abspath(__file__))

class junction_Test(unittest.TestCase):
    def setUp(self):
        self.source = os.path.join(BASE_PATH, "data")
        self.link_name = os.path.join(BASE_PATH, "data-junction")
        
    def tearDown(self):
        try:
            os.removedirs(self.link_name)
        except OSError:
            pass
        
    def test_create_for_directory(self):
        junction.create(self.source, self.link_name)
        self.assertTrue(os.path.exists(self.link_name))
        
    def test_isjunction_success(self):
        junction.create(self.source, self.link_name)
        self.assertEqual(junction.isjunction(self.link_name), True)
    
    def test_isjunction_fail(self):
        self.assertEqual(junction.isjunction(self.source), False)

    def test_readlink(self):
        junction.create(self.source, self.link_name)
        self.assertEqual(junction.readlink(self.link_name), self.source)

if __name__ == "__main__":
    unittest.main()
