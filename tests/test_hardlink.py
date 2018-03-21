from ntfsutils.hardlink import create, samefile
from tests.common import TestDir


class TestHardlink(TestDir):
    def test(self):
        link = 'hardlink'
        contents = 'bar'

        create(self.FOO, link)
        self.assertTrue(samefile(self.FOO, link))

        with open(link, 'r') as fd:
            self.assertEqual(fd.read(), self.FOO_CONTENTS)

        with open(self.FOO, 'w') as fd:
            fd.write(contents)

        with open(link, 'r') as fd:
            self.assertEqual(fd.read(), contents)
