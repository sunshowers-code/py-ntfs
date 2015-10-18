import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest

from ntfsutils import hardlink

BASE_PATH = os.path.dirname(os.path.abspath(__file__))

class hardlink_success_Test(unittest.TestCase):
    def setUp(self):
        self.source = os.path.join(BASE_PATH, "data", "data.txt")
        self.link_name = os.path.join(BASE_PATH, "data", "data-hardlink.txt")
        
    def tearDown(self):
        try:
            os.remove(self.link_name)
        except OSError:
            pass
    
    def test_run(self):
        hardlink.create(self.source, self.link_name)
        self.assertTrue(hardlink.samefile(self.source, self.link_name))
