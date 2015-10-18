# Copyright (c) 2012, the Mozilla Foundation. All rights reserved.
# Use of this source code is governed by the Simplified BSD License which can
# be found in the LICENSE file.

# Python module to create, delete and get the target of junctions on
# Windows.

__all__ = ["create", "readlink", "unlink", "isjunction"]

import os
from . import fs
from .fs import CreateFile, GetFileAttributes, DeviceIoControl, CloseHandle

import ctypes
from ctypes import WinError, sizeof, byref
from ctypes.wintypes import DWORD

IO_REPARSE_TAG_MOUNT_POINT = 0xA0000003
IO_REPARSE_TAG_SYMLINK = 0xA000000C

FSCTL_SET_REPARSE_POINT    = 0x000900A4
FSCTL_GET_REPARSE_POINT    = 0x000900A8
FSCTL_DELETE_REPARSE_POINT = 0x000900AC

def new_junction_reparse_buffer(path=None):    
    """
    Given a path, return a pair containing a new REPARSE_DATA_BUFFER and the
    length of the buffer (not necessarily the same as sizeof due to packing
    issues).
    If no path is provided, the maximum length is assumed.
    """

    if path is None:
        # The maximum reparse point data buffer length is 16384 bytes. We are a
        # bit conservative here and set a length of 16000 bytes (8000
        # characters) + a few more for the header.
        substnamebufferchars = 8000
    else:
        # 1 more character for the null terminator. Python 2.x calculates
        # len(surrogate pair) = 2, so multiplying this by 2 is the right thing
        # to do.
        substnamebufferchars = len(path) + 1

    # It is amazing how ugly MSDN's version of REPARSE_DATA_BUFFER is:
    # <http://msdn.microsoft.com/en-us/library/windows/hardware/ff552012>. It
    # is a variable-length struct with two strings in the wchar[] buffer at
    # the end. Both are supposed to be null-terminated, and the individual
    # lengths do not include that of the null character, but the total
    # ReparseDataLength does.
    #
    # In our case, only the SubstituteName part of the mount point/junction-
    # specific part is relevant. So we set PrintNameLength to 0, but we still
    # need to allow for one null character, so PrintNameBuffer has length 1.
    class REPARSE_DATA_BUFFER(ctypes.Structure):
        _fields_ = [("ReparseTag", ctypes.c_ulong),
                    ("ReparseDataLength", ctypes.c_ushort),
                    ("Reserved", ctypes.c_ushort),
                    ("SubstituteNameOffset", ctypes.c_ushort),
                    ("SubstituteNameLength", ctypes.c_ushort),
                    ("PrintNameOffset", ctypes.c_ushort),
                    ("PrintNameLength", ctypes.c_ushort),
                    ("SubstituteNameBuffer", ctypes.c_ushort * substnamebufferchars),
                    ("PrintNameBuffer", ctypes.c_wchar * 1)]
                    
        def buffer_to_string(self, buf):
            readable_name_buffer = [chr(x) for x in buf]
            readable_name = "".join(readable_name_buffer)
            return readable_name.rstrip("\0")
        
        @property
        def readable_PrintNameBuffer(self):
            return self.buffer_to_string(self.PrintNameBuffer)
        
        @property    
        def readable_SubstituteNameBuffer(self):
            return self.buffer_to_string(self.SubstituteNameBuffer)

    numpathbytes = (substnamebufferchars - 1) * sizeof(ctypes.c_ushort)
    # We can't really use sizeof on the struct because of packing issues.
    # Instead, calculate the size manually
    buffersize = (numpathbytes + (sizeof(ctypes.c_ushort) * 2) + 
        (sizeof(ctypes.c_ushort) * 4))
    if path is None:
        buffer = REPARSE_DATA_BUFFER()
        buffer.ReparseTag = IO_REPARSE_TAG_MOUNT_POINT
    else:
        tmp = REPARSE_DATA_BUFFER()
        for i, x in enumerate(path):
            tmp.SubstituteNameBuffer[i] = ord(x);
            
        buffer = REPARSE_DATA_BUFFER(
            IO_REPARSE_TAG_MOUNT_POINT,
            buffersize,
            0,
            # print name offset, length
            0, numpathbytes,
            # substitute name offset, length
            numpathbytes + 2, 0,
            # print name
            tmp.SubstituteNameBuffer,
            # substitute name
            "")

    return (buffer, buffersize + REPARSE_DATA_BUFFER.SubstituteNameOffset.offset)

def unparsed_convert(path):
    path = os.path.abspath(path)
    # Remove the trailing slash for root drives
    if path[-2:] == ":\\":
        path = path[:-1]
    # This magic prefix disables parsing. Note that we do not want to use
    # \\?\, since that doesn't tolerate a different case.
    return "\\??\\" + path

def unparsed_unconvert(path):
    if path[0:4] == "\\??\\":
        path = path[4:]
    return path

def isjunction(path):
    if not os.path.exists(path) or not fs.junctions_supported(path):
        return False

    attrs = GetFileAttributes(path)
    return bool((attrs & fs.FILE_ATTRIBUTE_DIRECTORY) and
                (attrs & fs.FILE_ATTRIBUTE_REPARSE_POINT))

def create(source, link_name):
    """
    Create a junction at link_name pointing to source.
    """
    success = False
    if not os.path.isdir(source):
        raise Exception("%s is not a directory" % source)
    if os.path.exists(link_name):
        raise Exception("%s: junction link name already exists" % link_name)

    link_name = os.path.abspath(link_name)
    os.mkdir(link_name)

    # Get a handle to the directory
    hlink = CreateFile(link_name, fs.GENERIC_WRITE,
        fs.FILE_SHARE_READ | fs.FILE_SHARE_WRITE, None, fs.OPEN_EXISTING,
        fs.FILE_FLAG_OPEN_REPARSE_POINT | fs.FILE_FLAG_BACKUP_SEMANTICS,
        None)
    try:
        if hlink == fs.INVALID_HANDLE_VALUE:
            raise WinError()

        srcvolpath = unparsed_convert(source)
        (junctioninfo, infolen) = new_junction_reparse_buffer(srcvolpath)

        dummy = DWORD(0)
        res = DeviceIoControl(
            hlink,
            FSCTL_SET_REPARSE_POINT,
            byref(junctioninfo),
            infolen,
            None,
            0,
            byref(dummy),
            None)

        if res == 0:
            raise WinError()
        success = True
    finally:
        if hlink != fs.INVALID_HANDLE_VALUE:
            CloseHandle(hlink)
        if not success:
            os.rmdir(link_name)

def readlink(path):
    # Make sure the path exists and is actually a junction
    if not isjunction(path):
        raise Exception("%s does not exist or is not a junction" % path)

    reparseinfo = readreparseinfo(path)
    name_buffer = reparseinfo.readable_SubstituteNameBuffer
    return unparsed_unconvert(name_buffer)

def readreparseinfo(path):
    hlink = CreateFile(path, fs.GENERIC_READ, fs.FILE_SHARE_READ, None,
        fs.OPEN_EXISTING,
        fs.FILE_FLAG_OPEN_REPARSE_POINT | fs.FILE_FLAG_BACKUP_SEMANTICS,
        None)
    if hlink == fs.INVALID_HANDLE_VALUE:
        raise WinError()
    
    try:
        (junctioninfo, infolen) = new_junction_reparse_buffer()
        dummy = DWORD(0)
        res = DeviceIoControl(
            hlink,
            FSCTL_GET_REPARSE_POINT,
            None,
            0,
            byref(junctioninfo),
            infolen,
            byref(dummy),
            None)
        
        if res == 0:
            raise WinError()

        return junctioninfo
    finally:
        CloseHandle(hlink)

def unlink(path):
    # Make sure the path exists and is actually a junction
    if not isjunction(path):
        raise Exception("%s does not exist or is not a junction" % path)
    # Just get rid of the directory
    os.rmdir(path)

def showreparseinfo(reparseinfo):            
    keys = [
        "ReparseTag",
        "ReparseDataLength",
        "Reserved",
        "SubstituteNameOffset",
        "SubstituteNameLength",
        "PrintNameOffset",
        "PrintNameLength",
    ]
    for key in keys:
        val = getattr(reparseinfo, key)
        print("%s\t:%s" % (key, str(val)))

    extra_keys = ["readable_PrintNameBuffer", "readable_SubstituteNameBuffer"]
    for key in extra_keys:
        val = getattr(reparseinfo, key)
        print("%s\t:%s" % (key, str(val)))
