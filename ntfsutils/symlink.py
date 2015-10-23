# Copyright (c) 2012, the Mozilla Foundation. All rights reserved.
# Use of this source code is governed by the Simplified BSD License which can
# be found in the LICENSE file.

# Library to deal with symbolic links

__all__ = ["create", "readlink", "issymlink"]

import os
from . import fs
from . import junction
from .fs import CreateSymbolicLink, GetLastError

import ctypes
from ctypes import WinError

ERROR_PRIVILEGE_NOT_HELD = 1314
ERROR_NOT_A_REPARSE_POINT = 4390

def create(source, link_name, ignore_validate = False):
    """
    Create a symbolic link at link_name pointing to source.
    Need administrator permission to create a symbolic link.

    http://stackoverflow.com/questions/6260149/os-symlink-support-in-windows
    """
    if not os.path.exists(source) and not ignore_validate:
        raise Exception("%s: source is not exists." % source)
    if os.path.exists(link_name):
        raise Exception("%s: symbolic link name already exists" % link_name)

    flags = 1 if os.path.isdir(source) else 0
    res = CreateSymbolicLink(link_name, source, flags)
    if res == 0:
        raise WinError()

def issymlink(path):
    try:
        reparseinfo = junction.readreparseinfo(path)
    except OSError as e:
        error_code = fs.GetLastError()
        if error_code == ERROR_NOT_A_REPARSE_POINT:
            return False
        # default
        return False

    if reparseinfo.ReparseTag != junction.IO_REPARSE_TAG_SYMLINK:
        return False

    attrs = fs.GetFileAttributes(path)
    return bool(attrs & fs.FILE_ATTRIBUTE_REPARSE_POINT)
    
def readlink(path):
    if not issymlink(path):
        raise Exception("%s does not exist or is not a symbolic link" % path)

    reparseinfo = junction.readreparseinfo(path)
    name_buffer = reparseinfo.readable_SubstituteNameBuffer
    
    magic = name_buffer[0:2]
    if magic == '\x01\x00':
        # relative path
        # example : \x01\x00dummy.txtdummy.txt
        total_len = len(name_buffer)
        return name_buffer[2:(total_len-2)//2 + 2]

    elif magic == '\x00\x00':
        # absolute path
        # example : \x00\x00c:\devel\ntfs\tests\data\dummy.txt\??\c:\devel\ntfs\tests\data\dummy.txt
        total_len = len(name_buffer)
        return name_buffer[2:(total_len-6)//2 + 2]

    else:
        raise Exception("unknown name buffer format : %r" % name_buffer)
