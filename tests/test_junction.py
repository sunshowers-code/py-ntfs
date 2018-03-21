import os
from ntfsutils.junction import create, readlink, unlink
from tests.common import TestDir


class TestJunction(TestDir):
    def test(self):
        link = 'junction'
        contents = 'bar'
        link_file = os.path.join(link, os.path.relpath(self.DIR_FILE, self.DIR))

        create(self.DIR, link)
        self.assertEqual(os.path.abspath(self.DIR), readlink(link))

        with open(link_file, 'r') as fd:
            self.assertEqual(fd.read(), self.DIR_FILE_CONTENTS)

        with open(self.DIR_FILE, 'w') as fd:
            fd.write(contents)

        with open(link_file, 'r') as fd:
            self.assertEqual(fd.read(), contents)

        unlink(link)
        self.assertFalse(os.path.exists(link))
