# Copyright (c) 2012, the Mozilla Foundation. All rights reserved.
# Use of this source code is governed by the Simplified BSD License which can
# be found in the LICENSE file.

import ctypes
from ctypes import POINTER, WinError, sizeof, byref
from ctypes.wintypes import DWORD, HANDLE, BOOL

LPDWORD = POINTER(DWORD)

GENERIC_READ  = 0x80000000
GENERIC_WRITE = 0x40000000

FILE_SHARE_READ   = 0x00000001
FILE_SHARE_WRITE  = 0x00000002
FILE_SHARE_DELETE = 0x00000004

FILE_SUPPORTS_HARD_LINKS     = 0x00400000
FILE_SUPPORTS_REPARSE_POINTS = 0x00000080

FILE_ATTRIBUTE_DIRECTORY     = 0x00000010
FILE_ATTRIBUTE_REPARSE_POINT = 0x00000400

FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
FILE_FLAG_BACKUP_SEMANTICS   = 0x02000000

OPEN_EXISTING = 3

MAX_PATH = 260

INVALID_HANDLE_VALUE = -1

class FILETIME(ctypes.Structure):
    _fields_ = [("dwLowDateTime", DWORD),
                ("dwHighDateTime", DWORD)]

class BY_HANDLE_FILE_INFORMATION(ctypes.Structure):
    _fields_ = [("dwFileAttributes", DWORD),
                ("ftCreationTime", FILETIME),
                ("ftLastAccessTime", FILETIME),
                ("ftLastWriteTime", FILETIME),
                ("dwVolumeSerialNumber", DWORD),
                ("nFileSizeHigh", DWORD),
                ("nFileSizeLow", DWORD),
                ("nNumberOfLinks", DWORD),
                ("nFileIndexHigh", DWORD),
                ("nFileIndexLow", DWORD)]

# http://msdn.microsoft.com/en-us/library/windows/desktop/aa363858
CreateFile = ctypes.windll.kernel32.CreateFileW
CreateFile.argtypes = [ctypes.c_wchar_p, DWORD, DWORD, ctypes.c_void_p,
                       DWORD, DWORD, HANDLE]
CreateFile.restype = HANDLE

# http://msdn.microsoft.com/en-us/library/windows/desktop/aa364944
GetFileAttributes = ctypes.windll.kernel32.GetFileAttributesW
GetFileAttributes.argtypes = [ctypes.c_wchar_p]
GetFileAttributes.restype = DWORD

# http://msdn.microsoft.com/en-us/library/windows/desktop/aa364952
GetFileInformationByHandle = ctypes.windll.kernel32.GetFileInformationByHandle
GetFileInformationByHandle.argtypes = [HANDLE, POINTER(BY_HANDLE_FILE_INFORMATION)]
GetFileInformationByHandle.restype = BOOL

# http://msdn.microsoft.com/en-us/library/windows/desktop/aa364996
GetVolumePathName = ctypes.windll.kernel32.GetVolumePathNameW
GetVolumePathName.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, DWORD]
GetVolumePathName.restype = BOOL

# http://msdn.microsoft.com/en-us/library/windows/desktop/aa364993
GetVolumeInformation = ctypes.windll.kernel32.GetVolumeInformationW
GetVolumeInformation.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, DWORD,
                                 LPDWORD, LPDWORD, LPDWORD, ctypes.c_wchar_p,
                                 DWORD]
GetVolumeInformation.restype = BOOL

# http://msdn.microsoft.com/en-us/library/windows/desktop/aa363216
DeviceIoControl = ctypes.windll.kernel32.DeviceIoControl
DeviceIoControl.argtypes = [HANDLE, DWORD, ctypes.c_void_p, DWORD,
                            ctypes.c_void_p, DWORD, LPDWORD, ctypes.c_void_p]
DeviceIoControl.restype = BOOL

# http://msdn.microsoft.com/en-us/library/windows/desktop/ms724211
CloseHandle = ctypes.windll.kernel32.CloseHandle
CloseHandle.argtypes = [HANDLE]
CloseHandle.restype = BOOL

def getfileinfo(path):
    """
    Return information for the file at the given path. This is going to be a
    struct of type BY_HANDLE_FILE_INFORMATION.
    """
    hfile = CreateFile(path, GENERIC_READ, FILE_SHARE_READ, None, OPEN_EXISTING, 0, None)
    if hfile is None:
        raise WinError()
    info = BY_HANDLE_FILE_INFORMATION()
    rv = GetFileInformationByHandle(hfile, info)
    if rv == 0:
        raise WinError()
    return info

def getvolumeinfo(path):
    """
    Return information for the volume containing the given path. This is going
    to be a pair containing (file system, file system flags).
    """

    # Add 1 for a trailing backslash if necessary, and 1 for the terminating
    # null character.
    volpath = ctypes.create_unicode_buffer(len(path) + 2)
    rv = GetVolumePathName(path, volpath, len(volpath))
    if rv == 0:
        raise WinError()

    fsnamebuf = ctypes.create_unicode_buffer(MAX_PATH + 1)
    fsflags = DWORD(0)
    rv = GetVolumeInformation(volpath, None, 0, None, None, byref(fsflags),
                              fsnamebuf, len(fsnamebuf))
    if rv == 0:
        raise WinError()

    return (fsnamebuf.value, fsflags.value)

def hardlinks_supported(path):
    (fsname, fsflags) = getvolumeinfo(path)
    # FILE_SUPPORTS_HARD_LINKS isn't supported until Windows 7, so also check
    # whether the file system is NTFS
    return bool((fsflags & FILE_SUPPORTS_HARD_LINKS) or (fsname == "NTFS"))

def junctions_supported(path):
    (fsname, fsflags) = getvolumeinfo(path)
    return bool(fsflags & FILE_SUPPORTS_REPARSE_POINTS)
