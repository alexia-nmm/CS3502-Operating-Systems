"""
file_ops.py
-----------
File Operations Layer for OwlTech File Manager.
All OS-level interactions are isolated here, separate from the GUI.
Maps directly to OS system calls:
    open/close  -> open(), read(), write(), close()
    stat        -> os.stat()
    unlink      -> os.remove()
    rename      -> os.rename()
    mkdir/rmdir -> os.mkdir(), shutil.rmtree()
    readdir     -> os.listdir()
"""

import os
import shutil
import stat
from pathlib import Path
from datetime import datetime


# ---------------------------------------------------------------------------
# File CRUD
# ---------------------------------------------------------------------------

def create_file(path: str, content: str = "") -> tuple[bool, str]:
    """
    Create a new file with optional content.
    OS actions: open() with O_CREAT | O_EXCL, write(), close()
    Returns (success, message).
    """
    p = Path(path)
    if p.exists():
        return False, f"File already exists: {p.name}"
    try:
        with open(p, "x", encoding="utf-8") as fh:
            if content:
                fh.write(content)
        return True, f"Created: {p.name}"
    except PermissionError:
        return False, f"Permission denied: cannot create '{p.name}'"
    except OSError as e:
        return False, f"Error creating file: {e.strerror}"


def read_file(path: str) -> tuple[str | None, str]:
    """
    Read and return file contents.
    OS actions: open(), read(), close()
    Returns (content_or_None, message).
    """
    p = Path(path)
    if not p.exists():
        return None, "File not found"
    if not p.is_file():
        return None, "Path is a directory, not a file"
    try:
        with open(p, "r", encoding="utf-8", errors="replace") as fh:
            content = fh.read()
        return content, "OK"
    except PermissionError:
        return None, f"Permission denied: cannot read '{p.name}'"
    except OSError as e:
        return None, f"Error reading file: {e.strerror}"


def update_file(path: str, content: str) -> tuple[bool, str]:
    """
    Overwrite an existing file with new content.
    OS actions: open() with O_WRONLY | O_TRUNC, write(), close()
    Returns (success, message).
    """
    p = Path(path)
    if not p.exists():
        return False, "File not found"
    if not os.access(p, os.W_OK):
        return False, f"Permission denied: '{p.name}' is read-only"
    try:
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(content)
        return True, f"Saved: {p.name}"
    except PermissionError:
        return False, f"Permission denied: cannot write '{p.name}'"
    except OSError as e:
        return False, f"Error saving file: {e.strerror}"


def delete_file(path: str) -> tuple[bool, str]:
    """
    Delete a file.
    OS actions: unlink() — decrements inode reference count; deletes if zero.
    Returns (success, message).
    """
    p = Path(path)
    if not p.exists():
        return False, "File not found"
    if not p.is_file():
        return False, "Path is a directory — use delete_directory()"
    try:
        os.remove(p)   # maps to unlink() syscall
        return True, f"Deleted: {p.name}"
    except PermissionError:
        return False, f"Permission denied: cannot delete '{p.name}'"
    except OSError as e:
        return False, f"Error deleting file: {e.strerror}"


def rename_item(old_path: str, new_name: str) -> tuple[bool, str]:
    """
    Rename a file or directory.
    OS actions: rename() — atomic on UNIX-like systems.
    Returns (success, message).
    """
    old = Path(old_path)
    new = old.parent / new_name
    if not old.exists():
        return False, "Item not found"
    if new.exists():
        return False, f"'{new_name}' already exists"
    if not new_name or any(c in new_name for c in r'\/:*?"<>|'):
        return False, "Invalid name: contains illegal characters"
    try:
        os.rename(old, new)   # atomic rename() syscall
        return True, f"Renamed to: {new_name}"
    except PermissionError:
        return False, f"Permission denied: cannot rename '{old.name}'"
    except OSError as e:
        return False, f"Error renaming: {e.strerror}"


# ---------------------------------------------------------------------------
# Directory operations
# ---------------------------------------------------------------------------

def create_directory(path: str) -> tuple[bool, str]:
    """
    Create a new directory (and any missing parents).
    OS actions: mkdir() syscall.
    """
    p = Path(path)
    if p.exists():
        return False, f"'{p.name}' already exists"
    try:
        p.mkdir(parents=True, exist_ok=False)
        return True, f"Directory created: {p.name}"
    except PermissionError:
        return False, f"Permission denied: cannot create directory here"
    except OSError as e:
        return False, f"Error creating directory: {e.strerror}"


def delete_directory(path: str, force: bool = False) -> tuple[bool, str]:
    """
    Delete a directory.
    force=False: only if empty (rmdir syscall).
    force=True:  recursive delete (rmdir + unlink on all children).
    """
    p = Path(path)
    if not p.exists():
        return False, "Directory not found"
    if not p.is_dir():
        return False, "Path is not a directory"
    try:
        if force:
            shutil.rmtree(p)
        else:
            os.rmdir(p)   # fails with ENOTEMPTY if not empty
        return True, f"Deleted directory: {p.name}"
    except OSError as e:
        if e.errno == 39 or "not empty" in str(e).lower():
            return False, "Directory is not empty. Delete contents first or use force delete."
        return False, f"Error deleting directory: {e.strerror}"


def list_directory(path: str) -> tuple[list[dict] | None, str]:
    """
    List directory contents with metadata.
    OS actions: opendir(), readdir(), stat() per entry.
    Returns list of dicts with keys: name, path, is_dir, size, modified, permissions.
    """
    p = Path(path)
    if not p.exists():
        return None, "Directory not found"
    if not p.is_dir():
        return None, "Path is not a directory"
    if not os.access(p, os.R_OK):
        return None, f"Permission denied: cannot list '{p}'"
    try:
        entries = []
        for item in sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            try:
                s = item.stat()   # stat() syscall — reads inode metadata
                entries.append({
                    "name": item.name,
                    "path": str(item),
                    "is_dir": item.is_dir(),
                    "size": s.st_size,
                    "modified": datetime.fromtimestamp(s.st_mtime).strftime("%Y-%m-%d %H:%M"),
                    "permissions": _format_permissions(s.st_mode),
                    "readable": os.access(item, os.R_OK),
                    "writable": os.access(item, os.W_OK),
                })
            except PermissionError:
                entries.append({
                    "name": item.name,
                    "path": str(item),
                    "is_dir": item.is_dir(),
                    "size": 0,
                    "modified": "unknown",
                    "permissions": "?????????",
                    "readable": False,
                    "writable": False,
                })
        return entries, "OK"
    except PermissionError:
        return None, f"Permission denied: cannot read directory"
    except OSError as e:
        return None, f"Error listing directory: {e.strerror}"


def get_metadata(path: str) -> tuple[dict | None, str]:
    """
    Retrieve file/directory metadata from the inode via stat() syscall.
    The inode stores: size, permissions, timestamps, owner.
    """
    p = Path(path)
    if not p.exists():
        return None, "Path not found"
    try:
        s = p.stat()   # stat() syscall
        return {
            "name": p.name,
            "path": str(p.resolve()),
            "type": "Directory" if p.is_dir() else "File",
            "size": _format_size(s.st_size),
            "size_bytes": s.st_size,
            "permissions": _format_permissions(s.st_mode),
            "created": datetime.fromtimestamp(s.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
            "modified": datetime.fromtimestamp(s.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            "accessed": datetime.fromtimestamp(s.st_atime).strftime("%Y-%m-%d %H:%M:%S"),
            "inode": s.st_ino,
            "links": s.st_nlink,
            "readable": os.access(p, os.R_OK),
            "writable": os.access(p, os.W_OK),
        }, "OK"
    except PermissionError:
        return None, "Permission denied"
    except OSError as e:
        return None, f"Error reading metadata: {e.strerror}"


def copy_item(src: str, dst_dir: str) -> tuple[bool, str]:
    """
    Copy a file or directory into a destination directory.
    """
    src_p = Path(src)
    dst_p = Path(dst_dir) / src_p.name
    if not src_p.exists():
        return False, "Source not found"
    if dst_p.exists():
        return False, f"'{src_p.name}' already exists in destination"
    try:
        if src_p.is_dir():
            shutil.copytree(src_p, dst_p)
        else:
            shutil.copy2(src_p, dst_p)
        return True, f"Copied '{src_p.name}' to destination"
    except PermissionError:
        return False, "Permission denied"
    except OSError as e:
        return False, f"Error copying: {e.strerror}"


def search_files(directory: str, query: str) -> list[dict]:
    """
    Recursively search for files/dirs whose names contain query (case-insensitive).
    """
    results = []
    q = query.lower()
    try:
        for item in Path(directory).rglob("*"):
            if q in item.name.lower():
                try:
                    s = item.stat()
                    results.append({
                        "name": item.name,
                        "path": str(item),
                        "is_dir": item.is_dir(),
                        "size": _format_size(s.st_size),
                        "modified": datetime.fromtimestamp(s.st_mtime).strftime("%Y-%m-%d %H:%M"),
                    })
                except (PermissionError, OSError):
                    pass
    except (PermissionError, OSError):
        pass
    return results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _format_permissions(mode: int) -> str:
    """Convert stat mode bits to rwxrwxrwx string."""
    chars = []
    for who in (stat.S_IRUSR, stat.S_IWUSR, stat.S_IXUSR,
                stat.S_IRGRP, stat.S_IWGRP, stat.S_IXGRP,
                stat.S_IROTH, stat.S_IWOTH, stat.S_IXOTH):
        chars.append("x" if mode & who else "-")
    # fill r/w/x pattern
    result = ""
    labels = "rwxrwxrwx"
    for i, c in enumerate(chars):
        result += labels[i] if mode & [
            stat.S_IRUSR, stat.S_IWUSR, stat.S_IXUSR,
            stat.S_IRGRP, stat.S_IWGRP, stat.S_IXGRP,
            stat.S_IROTH, stat.S_IWOTH, stat.S_IXOTH
        ][i] else "-"
    return result


def _format_size(size_bytes: int) -> str:
    """Human-readable file size."""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"
