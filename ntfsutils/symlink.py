# Copyright (c) 2012, the Mozilla Foundation. All rights reserved.
# Use of this source code is governed by the Simplified BSD License which can
# be found in the LICENSE file.

# Library to deal with symbolic links

__all__ = ["create", "readlink", "issymlink", "hasprivilege"]

import os
from . import fs
from . import junction
from .fs import CreateSymbolicLink, GetLastError

import ctypes
from ctypes import WinError, wintypes, byref
from ctypes.wintypes import HANDLE, DWORD

ERROR_PRIVILEGE_NOT_HELD = 1314
ERROR_NOT_A_REPARSE_POINT = 4390

# http://svn.python.org/projects/python/branches/py3k-futures-on-windows/Lib/test/symlink_support.py
GetCurrentProcess = ctypes.windll.kernel32.GetCurrentProcess
GetCurrentProcess.restype = wintypes.HANDLE
OpenProcessToken = ctypes.windll.advapi32.OpenProcessToken
OpenProcessToken.argtypes = (wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE))
OpenProcessToken.restype = wintypes.BOOL

class LUID(ctypes.Structure):
    _fields_ = [
            ('low_part', wintypes.DWORD),
            ('high_part', wintypes.LONG),
            ]

LookupPrivilegeValue = ctypes.windll.advapi32.LookupPrivilegeValueW
LookupPrivilegeValue.argtypes = (
    wintypes.LPWSTR, # system name
    wintypes.LPWSTR, # name
    ctypes.POINTER(LUID),
)
LookupPrivilegeValue.restype = wintypes.BOOL

class TOKEN_INFORMATION_CLASS:
    TokenUser = 1
    TokenGroups = 2
    TokenPrivileges = 3
    # ... see http://msdn.microsoft.com/en-us/library/aa379626%28VS.85%29.aspx

SE_PRIVILEGE_ENABLED_BY_DEFAULT = (0x00000001)
SE_PRIVILEGE_ENABLED            = (0x00000002)
SE_PRIVILEGE_REMOVED            = (0x00000004)
SE_PRIVILEGE_USED_FOR_ACCESS    = (0x80000000)

class LUID_AND_ATTRIBUTES(ctypes.Structure):
    _fields_ = [
            ('LUID', LUID),
            ('attributes', wintypes.DWORD),
            ]

    def is_enabled(self):
        return bool(self.attributes & SE_PRIVILEGE_ENABLED)

    def enable(self):
        self.attributes |= SE_PRIVILEGE_ENABLED

LookupPrivilegeName = ctypes.windll.advapi32.LookupPrivilegeNameW
LookupPrivilegeName.argtypes = (
        wintypes.LPWSTR, # lpSystemName
        ctypes.POINTER(LUID), # lpLuid
        wintypes.LPWSTR, # lpName
        ctypes.POINTER(wintypes.DWORD), #cchName
        )
LookupPrivilegeName.restype = wintypes.BOOL

class TOKEN_PRIVILEGES(ctypes.Structure):
    _fields_ = [
            ('count', wintypes.DWORD),
            ('privileges', LUID_AND_ATTRIBUTES*0),
            ]

    def get_array(self):
        array_type = LUID_AND_ATTRIBUTES*self.count
        privileges = ctypes.cast(self.privileges,
                                 ctypes.POINTER(array_type)).contents
        return privileges

PTOKEN_PRIVILEGES = ctypes.POINTER(TOKEN_PRIVILEGES)

GetTokenInformation = ctypes.windll.advapi32.GetTokenInformation
GetTokenInformation.argtypes = [
        wintypes.HANDLE, # TokenHandle
        ctypes.c_uint, # TOKEN_INFORMATION_CLASS value
        ctypes.c_void_p, # TokenInformation
        wintypes.DWORD, # TokenInformationLength
        ctypes.POINTER(wintypes.DWORD), # ReturnLength
        ]
GetTokenInformation.restype = wintypes.BOOL

# http://msdn.microsoft.com/en-us/library/aa375202%28VS.85%29.aspx
AdjustTokenPrivileges = ctypes.windll.advapi32.AdjustTokenPrivileges
AdjustTokenPrivileges.restype = wintypes.BOOL
AdjustTokenPrivileges.argtypes = [
        wintypes.HANDLE,                # TokenHandle
        wintypes.BOOL,                  # DisableAllPrivileges
        PTOKEN_PRIVILEGES,              # NewState (optional)
        wintypes.DWORD,                 # BufferLength of PreviousState
        PTOKEN_PRIVILEGES,              # PreviousState (out, optional)
        ctypes.POINTER(wintypes.DWORD), # ReturnLength
        ]

def get_process_token():
    "Get the current process token"
    token = wintypes.HANDLE()
    TOKEN_ALL_ACCESS = 0xf01ff
    res = OpenProcessToken(GetCurrentProcess(), TOKEN_ALL_ACCESS, token)
    if not res > 0:
        raise RuntimeError("Couldn't get process token")
    return token

def get_symlink_luid():
    "Get the LUID for the SeCreateSymbolicLinkPrivilege"
    symlink_luid = LUID()
    res = LookupPrivilegeValue(None, "SeCreateSymbolicLinkPrivilege",
                               symlink_luid)
    if not res > 0:
        raise RuntimeError("Couldn't lookup privilege value")
    return symlink_luid

def get_privilege_information():
    "Get all privileges associated with the current process."
    # first call with zero length to determine what size buffer we need

    return_length = wintypes.DWORD()
    params = [
            get_process_token(),
            TOKEN_INFORMATION_CLASS.TokenPrivileges,
            None,
            0,
            return_length,
            ]

    res = GetTokenInformation(*params)

    # assume we now have the necessary length in return_length

    buffer = ctypes.create_string_buffer(return_length.value)
    params[2] = buffer
    params[3] = return_length.value

    res = GetTokenInformation(*params)
    assert res > 0, "Error in second GetTokenInformation (%d)" % res

    privileges = ctypes.cast(buffer, ctypes.POINTER(TOKEN_PRIVILEGES)).contents
    return privileges

def hasprivilege():
    """
    Try to assign the symlink privilege to the current process token.
    Return True if the assignment is successful.
    """
    # create a space in memory for a TOKEN_PRIVILEGES structure
    #  with one element
    size = ctypes.sizeof(TOKEN_PRIVILEGES)
    size += ctypes.sizeof(LUID_AND_ATTRIBUTES)
    buffer = ctypes.create_string_buffer(size)
    tp = ctypes.cast(buffer, ctypes.POINTER(TOKEN_PRIVILEGES)).contents
    tp.count = 1
    tp.get_array()[0].enable()
    tp.get_array()[0].LUID = get_symlink_luid()
    token = get_process_token()
    res = AdjustTokenPrivileges(token, False, tp, 0, None, None)
    if res == 0:
        raise Exception("Error in AdjustTokenPrivileges")

    ERROR_NOT_ALL_ASSIGNED = 1300
    return ctypes.windll.kernel32.GetLastError() != ERROR_NOT_ALL_ASSIGNED

def create(source, link_name):
    """
    from python 2.7 /Lib/test/symlink_support.py
    """
    if not hasprivilege():
        raise WinError(ERROR_PRIVILEGE_NOT_HELD)
        
    is_directory = os.path.isdir(source)
    res = CreateSymbolicLink(link_name, source, is_directory)
    if res == 0:
        raise WinError()

def win32_get_reparse_tag(hlink):
    (junctioninfo, infolen) = junction.new_junction_reparse_buffer()
    dummy = DWORD(0)
    res = fs.DeviceIoControl(
        hlink,
        junction.FSCTL_GET_REPARSE_POINT,
        None,
        0,
        byref(junctioninfo),
        infolen,
        byref(dummy),
        None)
    
    if res == 0:
        return (False, None)

    return (True, junctioninfo.ReparseTag)
        
def issymlink(path):
    # from python 3.5 Modules/posixmodule.c, win32_xstat_impl
    reparse_tag = -1
    
    hFile = fs.CreateFile(
        path,
        fs.FILE_READ_ATTRIBUTES, # desired access
        0, # share mode
        None, # security attributes
        fs.OPEN_EXISTING,
        # FILE_FLAG_BACKUP_SEMANTICS is required to open a directory
        # FILE_FLAG_OPEN_REPARSE_POINT does not follow the symlink.
        # Because of this, calls like GetFinalPathNameByHandle will return
        # the symlink path again and not the actual final path. 
        fs.FILE_ATTRIBUTE_NORMAL | fs.FILE_FLAG_BACKUP_SEMANTICS| fs.FILE_FLAG_OPEN_REPARSE_POINT,
        None)
        
    if hFile == fs.INVALID_HANDLE_VALUE:
        return False
    else:
        info = fs.BY_HANDLE_FILE_INFORMATION()
        if not fs.GetFileInformationByHandle(hFile, byref(info)):
            fs.CloseHandle(hFile)
            return False
        
        if info.dwFileAttributes & fs.FILE_ATTRIBUTE_REPARSE_POINT:
            success, reparse_tag = win32_get_reparse_tag(hFile)
            if not success:
                return False
                
        if not fs.CloseHandle(hFile):
            return False

        return (reparse_tag == junction.IO_REPARSE_TAG_SYMLINK)

def readlink(path):
    try:
        not_symlink_exc = Exception("%s does not exist or is not a symbolic link" % path)
        reparseinfo = junction.readreparseinfo(path)
        if reparseinfo.ReparseTag != junction.IO_REPARSE_TAG_SYMLINK:
            raise not_symlink_exc
    except OSError as e:
        raise not_symlink_exc

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
