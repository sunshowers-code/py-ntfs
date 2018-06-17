import os

from ntfsutils.fs import getfileinfo, getdirinfo
from tests.common import TestDir


class TestFs(TestDir):
    def test_getdirinfo(self):
        info = getdirinfo(self.DIR)
        self.assertNotEqual(info, None)

    def test_getfileinfo(self):
        with self.assertRaises(WindowsError) as cx:
            info = getfileinfo(self.DIR)

        # simulate someone holding an exclussive access
        locked = 'locked'
        fd = os.open(locked, os.O_WRONLY | os.O_CREAT | os.O_EXCL)

        # should not raise WinError
        info = getfileinfo(locked)

        os.close(fd)
