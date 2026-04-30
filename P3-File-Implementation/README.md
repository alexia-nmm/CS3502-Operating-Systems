# OwlTech File Manager — CS 3502 Project 3

## Requirements

- Python 3.10 or higher (uses `str | None` union syntax)
- Tkinter (included with most Python installations)
- No external dependencies

### Verify Tkinter is available
```
python -m tkinter
```
A small window should appear. If not, install it:
- Ubuntu/Debian: `sudo apt-get install python3-tk`
- macOS (Homebrew): `brew install python-tk`
- Windows: Reinstall Python and check "tcl/tk" during setup

---

## How to Run

```
python main.py
```

Both files must be in the same directory:
```
owltech-filemanager/
    main.py       ← GUI layer
    file_ops.py   ← File operations layer (OS API calls)
```

---

## Features

### Core (required)
| Operation  | How to trigger                                      |
|------------|-----------------------------------------------------|
| CREATE     | Toolbar "New File" / "New Folder", or File menu     |
| READ       | Double-click any file to open in editor             |
| UPDATE     | Edit in the editor panel, click "Save"              |
| DELETE     | Select item, click "Delete" or press Del key        |
| RENAME     | Select item, click "Rename" or press F2             |
| NAVIGATE   | Double-click folders, Back button, or type a path   |

### Additional
- File search (toolbar search box)
- Copy/paste files and directories
- Properties panel showing inode metadata (stat() syscall)
- Right-click context menus
- Keyboard shortcuts: Ctrl+N, Ctrl+Shift+N, Ctrl+C, Ctrl+V, Del, F2, F5
- Permission checking before operations
- Confirmation dialogs for destructive operations
- Error messages mapped from POSIX error codes

---

## Architecture

```
GUI Layer (main.py)
    |
    v
File Operations Layer (file_ops.py)
    |
    v
OS APIs — Python os / pathlib / shutil modules
    |
    v
System Calls — open(), read(), write(), close(),
               stat(), unlink(), rename(), mkdir(), rmdir()
```

---

## Testing Checklist

- [ ] Create a file with content
- [ ] Read the file back in editor
- [ ] Edit and save changes
- [ ] Rename the file
- [ ] Create a directory
- [ ] Copy a file into the directory
- [ ] Navigate into and out of the directory
- [ ] Delete a file (with confirmation)
- [ ] Delete a non-empty directory (force delete prompt)
- [ ] Search for a file by name
- [ ] View inode properties panel
- [ ] Attempt to open a system file (permission denied)
- [ ] Create a file with special characters in name
- [ ] Test with an empty file (0 bytes)
