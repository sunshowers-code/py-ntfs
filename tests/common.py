import os
import tempfile

from unittest import TestCase


class TestDir(TestCase):
    FOO = 'foo'
    FOO_CONTENTS = FOO
    DIR = 'dir'
    DIR_FILE = os.path.join(DIR, 'file')
    DIR_FILE_CONTENTS = DIR_FILE

    def setUp(self):
        self._root_dir = tempfile.mkdtemp()
        self.pushd(self._root_dir)
        self.create(self.FOO, self.FOO_CONTENTS)
        self.create(self.DIR_FILE, self.DIR_FILE_CONTENTS)

    def tearDown(self):
        self.popd()

    def pushd(self, d):
        self._saved_dir = os.path.realpath(os.curdir)
        os.chdir(d)

    def popd(self):
        if not self._saved_dir:
            return

        os.chdir(self._saved_dir)
        self._saved_dir = None

    def create(self, path, contents):
        dname = os.path.dirname(path)
        if len(dname) > 0 and not os.path.isdir(dname):
            os.makedirs(dname)

        with open(path, 'w+') as fd:
            fd.write(contents)
