# Copyright (c) 2012, the Mozilla Foundation. All rights reserved.
# Use of this source code is governed by the Simplified BSD License which can
# be found in the LICENSE file.

# Library to deal with symbolic links

__all__ = ["create"]

import os
from . import fs
from .fs import CreateSymbolicLink, GetLastError

import ctypes
from ctypes import WinError

ERROR_PRIVILEGE_NOT_HELD = 1314

class SymLinkPermissionError(Exception):
    pass

def create(source, link_name):
    """
    Create a symbolic link at link_name pointing to source.
    Need administrator permission to create a symbolic link.

    http://stackoverflow.com/questions/6260149/os-symlink-support-in-windows
    """
    if not os.path.exists(source):
        raise Exception("%s: source is not exists." % source)
    if os.path.exists(link_name):
        raise Exception("%s: symbolic link name already exists" % link_name)

    flags = 1 if os.path.isdir(source) else 0
    res = CreateSymbolicLink(link_name, source, flags)
    if res == 0:
        error_code = GetLastError() 
        if error_code == ERROR_PRIVILEGE_NOT_HELD:
            raise SymLinkPermissionError("no permission, error code : %d" % error_code)
        else:
            raise WinError()
