# Copyright (c) 2012, the Mozilla Foundation. All rights reserved.
# Use of this source code is governed by the Simplified BSD License which can
# be found in the LICENSE file.

# Library to deal with hardlinks

__all__ = ["create", "samefile"]

import fs
import ctypes
from ctypes import WinError
from ctypes.wintypes import BOOL
CreateHardLink = ctypes.windll.kernel32.CreateHardLinkW
CreateHardLink.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_void_p]
CreateHardLink.restype = BOOL

def create(source, link_name):
    """
    Creates a hardlink at link_name referring to the same file as source.
    """
    res = CreateHardLink(link_name, source, None)
    if rv == 0:
        raise WinError("Couldn't create hardlink from %s to %s" %
            (source, link_name))

def samefile(path1, path2):
    """
    Returns True if path1 and path2 refer to the same file.
    """
    # Check if both are on the same volume and have the same file ID
    info1 = fs.getfileinfo(path1)
    info2 = fs.getfileinfo(path2)
    return (info1.dwVolumeSerialNumber == info2.dwVolumeSerialNumber and
            info1.nFileIndexHigh == info2.nFileIndexHigh and
            info1.nFileIndexLow == info2.nFileIndexLow)
