"""
main.py
-------
OwlTech File Manager — GUI Layer
CS 3502: Operating Systems, Project 3

Architecture:
    GUI Layer (this file)  -->  File Operations Layer (file_ops.py)  -->  OS APIs / System Calls

The GUI never calls OS functions directly. All file system interaction
goes through file_ops.py, which maps to the following system calls:
    open/read/write/close, stat, unlink, rename, mkdir, rmdir, readdir
"""

from importlib.resources import path
import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from pathlib import Path
import file_ops


# ---------------------------------------------------------------------------
# Color / style constants
# ---------------------------------------------------------------------------
BG_DARK     = "#1e1e2e"
BG_PANEL    = "#2a2a3e"
BG_ITEM     = "#313145"
ACCENT      = "#7c6af7"
ACCENT_LITE = "#a89bf9"
FG_MAIN     = "#cdd6f4"
FG_DIM      = "#6c7086"
FG_ERROR    = "#f38ba8"
FG_OK       = "#a6e3a1"
FG_WARN     = "#fab387"
FONT_MONO   = ("Courier New", 10)
FONT_UI     = ("Segoe UI", 10) if os.name == "nt" else ("Helvetica", 10)
FONT_UI_B   = ("Segoe UI", 10, "bold") if os.name == "nt" else ("Helvetica", 10, "bold")
FONT_TITLE  = ("Segoe UI", 13, "bold") if os.name == "nt" else ("Helvetica", 13, "bold")


# ---------------------------------------------------------------------------
# Main application window
# ---------------------------------------------------------------------------

class OwlFileManager(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("OwlTech File Manager — CS 3502")
        self.geometry("1100x700")
        self.minsize(800, 500)
        self.configure(bg=BG_DARK)

        self.current_path = tk.StringVar(value=str(Path.home()))
        self.selected_path: str | None = None   # currently selected item
        self.clipboard: str | None = None        # path queued for copy

        self._build_ui()
        self._refresh()

    # -----------------------------------------------------------------------
    # UI construction
    # -----------------------------------------------------------------------

    def _build_ui(self):
        self._build_menu()
        self._build_toolbar()
        self._build_path_bar()
        self._build_main_panes()
        self._build_status_bar()

    def _build_menu(self):
        mb = tk.Menu(self, bg=BG_PANEL, fg=FG_MAIN,
                     activebackground=ACCENT, activeforeground=FG_MAIN,
                     relief="flat")
        self.config(menu=mb)

        file_menu = tk.Menu(mb, tearoff=0, bg=BG_PANEL, fg=FG_MAIN,
                            activebackground=ACCENT, activeforeground=FG_MAIN)
        file_menu.add_command(label="New File…       Ctrl+N", command=self._cmd_new_file)
        file_menu.add_command(label="New Folder…     Ctrl+Shift+N", command=self._cmd_new_dir)
        file_menu.add_separator()
        file_menu.add_command(label="Open Location…", command=self._cmd_open_location)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)
        mb.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(mb, tearoff=0, bg=BG_PANEL, fg=FG_MAIN,
                            activebackground=ACCENT, activeforeground=FG_MAIN)
        edit_menu.add_command(label="Rename…   F2",   command=self._cmd_rename)
        edit_menu.add_command(label="Copy           Ctrl+C", command=self._cmd_copy)
        edit_menu.add_command(label="Paste          Ctrl+V", command=self._cmd_paste)
        edit_menu.add_separator()
        edit_menu.add_command(label="Delete         Del",   command=self._cmd_delete)
        mb.add_cascade(label="Edit", menu=edit_menu)

        view_menu = tk.Menu(mb, tearoff=0, bg=BG_PANEL, fg=FG_MAIN,
                            activebackground=ACCENT, activeforeground=FG_MAIN)
        view_menu.add_command(label="Refresh  F5", command=self._refresh)
        view_menu.add_command(label="Properties…",  command=self._cmd_properties)
        mb.add_cascade(label="View", menu=view_menu)

        help_menu = tk.Menu(mb, tearoff=0, bg=BG_PANEL, fg=FG_MAIN,
                            activebackground=ACCENT, activeforeground=FG_MAIN)
        help_menu.add_command(label="About", command=self._show_about)
        mb.add_cascade(label="Help", menu=help_menu)

        # Keyboard shortcuts
        self.bind("<Control-n>", lambda e: self._cmd_new_file())
        self.bind("<Control-N>", lambda e: self._cmd_new_dir())
        self.bind("<Control-c>", lambda e: self._cmd_copy())
        self.bind("<Control-v>", lambda e: self._cmd_paste())
        self.bind("<Delete>",    lambda e: self._cmd_delete())
        self.bind("<F2>",        lambda e: self._cmd_rename())
        self.bind("<F5>",        lambda e: self._refresh())

    def _build_toolbar(self):
        tb = tk.Frame(self, bg=BG_PANEL, pady=4)
        tb.pack(fill="x", side="top")

        btn_cfg = dict(bg=BG_ITEM, fg=FG_MAIN, relief="flat",
                       font=FONT_UI, padx=10, pady=4,
                       activebackground=ACCENT, activeforeground=FG_MAIN,
                       cursor="hand2")

        tk.Button(tb, text="⬅ Back",    command=self._cmd_go_up,       **btn_cfg).pack(side="left", padx=2)
        tk.Button(tb, text="🏠 Home",   command=self._cmd_go_home,     **btn_cfg).pack(side="left", padx=2)
        tk.Button(tb, text="🔄 Refresh",command=self._refresh,         **btn_cfg).pack(side="left", padx=2)
        tk.Button(tb, text="📄 New File",command=self._cmd_new_file,   **btn_cfg).pack(side="left", padx=2)
        tk.Button(tb, text="📁 New Folder",command=self._cmd_new_dir,  **btn_cfg).pack(side="left", padx=2)
        tk.Button(tb, text="✏️ Rename",  command=self._cmd_rename,      **btn_cfg).pack(side="left", padx=2)
        tk.Button(tb, text="🗑️ Delete",  command=self._cmd_delete,      **btn_cfg).pack(side="left", padx=2)
        tk.Button(tb, text="📋 Copy",    command=self._cmd_copy,        **btn_cfg).pack(side="left", padx=2)
        tk.Button(tb, text="📌 Paste",   command=self._cmd_paste,       **btn_cfg).pack(side="left", padx=2)

        # Search
        tk.Label(tb, text="🔍", bg=BG_PANEL, fg=FG_MAIN, font=FONT_UI).pack(side="right", padx=(0,2))
        self.search_var = tk.StringVar()
        se = tk.Entry(tb, textvariable=self.search_var, bg=BG_ITEM, fg=FG_MAIN,
                      insertbackground=FG_MAIN, relief="flat", font=FONT_UI, width=20)
        se.pack(side="right", padx=2)
        se.bind("<Return>", lambda e: self._cmd_search())
        tk.Button(tb, text="Search", command=self._cmd_search, **btn_cfg).pack(side="right", padx=2)

    def _build_path_bar(self):
        bar = tk.Frame(self, bg=BG_DARK, pady=3)
        bar.pack(fill="x", side="top")
        tk.Label(bar, text="  Location:", bg=BG_DARK, fg=FG_DIM, font=FONT_UI).pack(side="left")
        path_entry = tk.Entry(bar, textvariable=self.current_path,
                              bg=BG_PANEL, fg=ACCENT_LITE, relief="flat",
                              font=FONT_UI, insertbackground=FG_MAIN)
        path_entry.pack(side="left", fill="x", expand=True, padx=4)
        path_entry.bind("<Return>", lambda e: self._navigate_to(self.current_path.get()))

    def _build_main_panes(self):
        paned = tk.PanedWindow(self, orient="horizontal",
                               bg=BG_DARK, sashwidth=4, sashrelief="flat")
        paned.pack(fill="both", expand=True, padx=4, pady=4)

        # Left: file list
        left = tk.Frame(paned, bg=BG_PANEL)
        paned.add(left, minsize=300)

        tk.Label(left, text="Files & Folders", bg=BG_PANEL, fg=ACCENT_LITE,
                 font=FONT_UI_B, anchor="w", padx=8, pady=4).pack(fill="x")

        cols = ("icon", "name", "size", "modified", "permissions")
        self.tree = ttk.Treeview(left, columns=cols, show="headings",
                                 selectmode="browse")
        self._style_treeview()
        self.tree.heading("icon",        text="")
        self.tree.heading("name",        text="Name")
        self.tree.heading("size",        text="Size")
        self.tree.heading("modified",    text="Modified")
        self.tree.heading("permissions", text="Permissions")
        self.tree.column("icon",        width=28,  stretch=False, anchor="center")
        self.tree.column("name",        width=200, stretch=True)
        self.tree.column("size",        width=75,  stretch=False, anchor="e")
        self.tree.column("modified",    width=130, stretch=False)
        self.tree.column("permissions", width=90,  stretch=False)

        vsb = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>",         self._on_double_click)
        self.tree.bind("<Button-3>",         self._on_right_click)

        # Right: editor + properties
        right = tk.Frame(paned, bg=BG_PANEL)
        paned.add(right, minsize=300)

        nb = ttk.Notebook(right)
        nb.pack(fill="both", expand=True)
        self._style_notebook(nb)

        # Editor tab
        editor_frame = tk.Frame(nb, bg=BG_PANEL)
        nb.add(editor_frame, text="  Editor  ")

        editor_top = tk.Frame(editor_frame, bg=BG_PANEL)
        editor_top.pack(fill="x", pady=4, padx=6)
        self.editor_label = tk.Label(editor_top, text="No file open",
                                     bg=BG_PANEL, fg=FG_DIM, font=FONT_UI, anchor="w")
        self.editor_label.pack(side="left", fill="x", expand=True)
        self.save_btn = tk.Button(editor_top, text="💾 Save",
                                  command=self._cmd_save,
                                  bg=ACCENT, fg=FG_MAIN, relief="flat",
                                  font=FONT_UI, padx=10,
                                  activebackground=ACCENT_LITE,
                                  activeforeground=BG_DARK, cursor="hand2",
                                  state="disabled")
        self.save_btn.pack(side="right")

        self.editor = tk.Text(editor_frame, bg=BG_DARK, fg=FG_MAIN,
                              insertbackground=FG_MAIN, relief="flat",
                              font=FONT_MONO, wrap="none",
                              selectbackground=ACCENT,
                              undo=True)
        esb = ttk.Scrollbar(editor_frame, orient="vertical",   command=self.editor.yview)
        esb_h = ttk.Scrollbar(editor_frame, orient="horizontal", command=self.editor.xview)
        self.editor.configure(yscrollcommand=esb.set, xscrollcommand=esb_h.set)
        esb_h.pack(side="bottom", fill="x")
        esb.pack(side="right",  fill="y")
        self.editor.pack(fill="both", expand=True, padx=4)
        self.editor.bind("<<Modified>>", self._on_editor_modified)
        self._editing_path: str | None = None

        # Properties tab
        props_frame = tk.Frame(nb, bg=BG_PANEL)
        nb.add(props_frame, text="  Properties  ")
        self.props_text = tk.Text(props_frame, bg=BG_DARK, fg=FG_MAIN,
                                  relief="flat", font=FONT_MONO,
                                  state="disabled", padx=8, pady=8)
        self.props_text.pack(fill="both", expand=True)

        def on_tab_change(event):
            target = self.selected_path or self.current_path.get()
            self._load_properties(target)

        nb.bind("<<NotebookTabChanged>>", on_tab_change)

    def _build_status_bar(self):
        sb = tk.Frame(self, bg=BG_PANEL, pady=3)
        sb.pack(fill="x", side="bottom")
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = tk.Label(sb, textvariable=self.status_var, bg=BG_PANEL, fg=FG_MAIN,
                                     font=FONT_UI, anchor="w", padx=8)
        self.status_label.pack(side="left")
        self.item_count_var = tk.StringVar(value="")
        tk.Label(sb, textvariable=self.item_count_var, bg=BG_PANEL, fg=FG_DIM,
                 font=FONT_UI, anchor="e", padx=8).pack(side="right")

    def _style_treeview(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview",
                        background=BG_ITEM, foreground=FG_MAIN,
                        fieldbackground=BG_ITEM, rowheight=24,
                        font=FONT_UI, borderwidth=0)
        style.configure("Treeview.Heading",
                        background=BG_PANEL, foreground=ACCENT_LITE,
                        font=FONT_UI_B, borderwidth=0, relief="flat")
        style.map("Treeview", background=[("selected", ACCENT)],
                  foreground=[("selected", FG_MAIN)])

    def _style_notebook(self, nb):
        style = ttk.Style()
        style.configure("TNotebook",       background=BG_PANEL, borderwidth=0)
        style.configure("TNotebook.Tab",   background=BG_ITEM,  foreground=FG_DIM,
                        padding=[10, 4], font=FONT_UI)
        style.map("TNotebook.Tab",
                  background=[("selected", BG_PANEL)],
                  foreground=[("selected", ACCENT_LITE)])

    # -----------------------------------------------------------------------
    # Navigation & refresh
    # -----------------------------------------------------------------------

    def _navigate_to(self, path: str):
        p = Path(path)
        if not p.exists():
            self._set_status(f"Path not found: {path}", error=True)
            return
        if not p.is_dir():
            p = p.parent
        self.current_path.set(str(p))
        self._refresh()

    def _refresh(self, _event=None, silent=False):
        path = self.current_path.get()
        entries, msg = file_ops.list_directory(path)
        self.tree.delete(*self.tree.get_children())
        if entries is None:
            self._set_status(msg, error=True)
            return
        for e in entries:
            icon = "📁" if e["is_dir"] else "📄"
            size = "" if e["is_dir"] else file_ops._format_size(e["size"])
            self.tree.insert("", "end", iid=e["path"],
                             values=(icon, e["name"], size,
                                     e["modified"], e["permissions"]))
        count = len(entries)
        self.item_count_var.set(f"{count} item{'s' if count != 1 else ''}")
        if not silent:
            self._set_status(f"Loaded: {path}")

    def _cmd_go_up(self):
        p = Path(self.current_path.get())
        if p.parent != p:
            self._navigate_to(str(p.parent))

    def _cmd_go_home(self):
        self._navigate_to(str(Path.home()))

    def _cmd_open_location(self):
        folder = filedialog.askdirectory(initialdir=self.current_path.get())
        if folder:
            self._navigate_to(folder)

    # -----------------------------------------------------------------------
    # Tree events
    # -----------------------------------------------------------------------

    def _on_select(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            self.selected_path = None
            return
        self.selected_path = sel[0]
        self._load_properties(self.selected_path)

    def _on_double_click(self, _event=None):
        if not self.selected_path:
            return
        p = Path(self.selected_path)
        if p.is_dir():
            self._navigate_to(str(p))
        else:
            self._open_in_editor(str(p))

    def _on_right_click(self, event):
        # Select item under cursor
        row = self.tree.identify_row(event.y)
        if row:
            self.tree.selection_set(row)
            self.selected_path = row
        ctx = tk.Menu(self, tearoff=0, bg=BG_PANEL, fg=FG_MAIN,
                      activebackground=ACCENT, activeforeground=FG_MAIN,
                      relief="flat")
        ctx.add_command(label="Open / Navigate",  command=self._on_double_click)
        ctx.add_command(label="Open in Editor",   command=lambda: self._open_in_editor(self.selected_path))
        ctx.add_separator()
        ctx.add_command(label="Rename…",          command=self._cmd_rename)
        ctx.add_command(label="Copy",             command=self._cmd_copy)
        ctx.add_command(label="Paste",            command=self._cmd_paste)
        ctx.add_separator()
        ctx.add_command(label="Delete",           command=self._cmd_delete)
        ctx.add_separator()
        ctx.add_command(label="Properties…",      command=self._cmd_properties)
        ctx.tk_popup(event.x_root, event.y_root)

    # -----------------------------------------------------------------------
    # CRUD commands
    # -----------------------------------------------------------------------

    def _cmd_new_file(self):
        name = simpledialog.askstring("New File", "File name:",
                                      parent=self, initialvalue="untitled.txt")
        if not name:
            return
        path = str(Path(self.current_path.get()) / name)
        ok, msg = file_ops.create_file(path)
        self._set_status(msg, error=not ok)
        if ok:
            self._refresh()
            self._open_in_editor(path)

    def _cmd_new_dir(self):
        name = simpledialog.askstring("New Folder", "Folder name:", parent=self)
        if not name:
            return
        path = str(Path(self.current_path.get()) / name)
        ok, msg = file_ops.create_directory(path)
        self._set_status(msg, error=not ok)
        if ok:
            self._refresh()

    def _open_in_editor(self, path: str):
        if not path or not Path(path).is_file():
            return
        content, msg = file_ops.read_file(path)
        if content is None:
            self._set_status(msg, error=True)
            return
        self.editor.config(state="normal")
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", content)
        self.editor.edit_reset()
        self.editor.edit_modified(False)
        self._editing_path = path
        self.editor_label.config(text=Path(path).name, fg=FG_MAIN)
        self.save_btn.config(state="normal")
        self._set_status(f"Opened: {Path(path).name}")

    def _cmd_save(self):
        if not self._editing_path:
            return
        content = self.editor.get("1.0", "end-1c")
        ok, msg = file_ops.update_file(self._editing_path, content)
        self._set_status(msg, error=not ok)
        if ok:
            self.editor.edit_modified(False)
            self._refresh(silent=True)

    def _on_editor_modified(self, _event=None):
        if self.editor.edit_modified() and self._editing_path:
            name = Path(self._editing_path).name
            self.editor_label.config(text=f"● {name}", fg=FG_WARN)

    def _cmd_rename(self):
        if not self.selected_path:
            self._set_status("No item selected", error=True)
            return
        old_name = Path(self.selected_path).name
        new_name = simpledialog.askstring("Rename", "New name:",
                                          parent=self, initialvalue=old_name)
        if not new_name or new_name == old_name:
            return
        ok, msg = file_ops.rename_item(self.selected_path, new_name)
        self._set_status(msg, error=not ok)
        if ok:
            # Update editor if the renamed file was open
            if self._editing_path == self.selected_path:
                self._editing_path = str(Path(self.selected_path).parent / new_name)
                self.editor_label.config(text=new_name)
            self._refresh()

    def _cmd_delete(self):
        if not self.selected_path:
            self._set_status("No item selected", error=True)
            return
        p = Path(self.selected_path)
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Permanently delete '{p.name}'?\nThis cannot be undone.",
            icon="warning", parent=self
        )
        if not confirm:
            return
        if p.is_dir():
            # Check if non-empty; warn again
            contents = list(p.iterdir()) if p.exists() else []
            if contents:
                force = messagebox.askyesno(
                    "Non-Empty Directory",
                    f"'{p.name}' contains {len(contents)} item(s).\nDelete everything inside?",
                    icon="warning", parent=self
                )
                ok, msg = file_ops.delete_directory(self.selected_path, force=force)
            else:
                ok, msg = file_ops.delete_directory(self.selected_path, force=False)
        else:
            ok, msg = file_ops.delete_file(self.selected_path)
        self._set_status(msg, error=not ok)
        if ok:
            if self._editing_path == self.selected_path:
                self._editing_path = None
                self.editor.delete("1.0", "end")
                self.editor_label.config(text="No file open", fg=FG_DIM)
                self.save_btn.config(state="disabled")
            self.selected_path = None
            self._refresh()

    def _cmd_copy(self):
        if not self.selected_path:
            self._set_status("No item selected", error=True)
            return
        self.clipboard = self.selected_path
        self._set_status(f"Copied to clipboard: {Path(self.selected_path).name}")

    def _cmd_paste(self):
        if not self.clipboard:
            self._set_status("Clipboard is empty", error=True)
            return
        ok, msg = file_ops.copy_item(self.clipboard, self.current_path.get())
        self._set_status(msg, error=not ok)
        if ok:
            self._refresh()

    def _cmd_search(self):
        query = self.search_var.get().strip()
        if not query:
            return
        results = file_ops.search_files(self.current_path.get(), query)
        self._show_search_results(query, results)

    def _cmd_properties(self):
        target = self.selected_path or self.current_path.get()
        self._load_properties(target)
        self.after(50, lambda: self._load_properties(target))

    # -----------------------------------------------------------------------
    # Properties panel
    # -----------------------------------------------------------------------

    def _load_properties(self, path: str):
        meta, msg = file_ops.get_metadata(path)
        self.props_text.config(state="normal")
        self.props_text.delete("1.0", "end")
        if meta is None:
            self.props_text.insert("end", f"Error: {msg}")
        else:
            lines = [
                ("Name",        meta["name"]),
                ("Type",        meta["type"]),
                ("Path",        meta["path"]),
                ("Size",        meta["size"]),
                ("Permissions", meta["permissions"]),
                ("Inode",       str(meta["inode"])),
                ("Hard Links",  str(meta["links"])),
                ("Created",     meta["created"]),
                ("Modified",    meta["modified"]),
                ("Accessed",    meta["accessed"]),
                ("Readable",    "Yes" if meta["readable"] else "No"),
                ("Writable",    "Yes" if meta["writable"] else "No"),
            ]
            self.props_text.insert("end", "── Inode Metadata (via stat() syscall) ──\n\n")
            for label, value in lines:
                self.props_text.insert("end", f"  {label:<13} {value}\n")
            self.props_text.insert("end",
                "\n── Note ──\n"
                "  Filename is NOT stored in the inode.\n"
                "  It lives in the parent directory entry.\n"
                "  The inode stores all metadata above.\n")
        self.props_text.config(state="disabled")

    # -----------------------------------------------------------------------
    # Search results window
    # -----------------------------------------------------------------------

    def _show_search_results(self, query: str, results: list):
        win = tk.Toplevel(self)
        win.title(f"Search: '{query}'")
        win.geometry("700x400")
        win.configure(bg=BG_DARK)

        tk.Label(win, text=f"Results for '{query}'  ({len(results)} found)",
                 bg=BG_DARK, fg=ACCENT_LITE, font=FONT_UI_B,
                 anchor="w", padx=10, pady=6).pack(fill="x")

        cols = ("icon", "name", "size", "modified", "path")
        tree = ttk.Treeview(win, columns=cols, show="headings")
        tree.heading("icon",     text="")
        tree.heading("name",     text="Name")
        tree.heading("size",     text="Size")
        tree.heading("modified", text="Modified")
        tree.heading("path",     text="Full Path")
        tree.column("icon",     width=28,  stretch=False, anchor="center")
        tree.column("name",     width=160, stretch=False)
        tree.column("size",     width=70,  stretch=False, anchor="e")
        tree.column("modified", width=120, stretch=False)
        tree.column("path",     width=300, stretch=True)

        for r in results:
            icon = "📁" if r["is_dir"] else "📄"
            tree.insert("", "end", iid=r["path"],
                        values=(icon, r["name"], r["size"], r["modified"], r["path"]))

        def on_double(event):
            sel = tree.selection()
            if sel:
                p = Path(sel[0])
                win.destroy()
                self._navigate_to(str(p.parent if p.is_file() else p))
                if p.is_file():
                    self._open_in_editor(str(p))

        tree.bind("<Double-1>", on_double)
        vsb = ttk.Scrollbar(win, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True, padx=4, pady=4)

        if not results:
            tk.Label(win, text="No files found.", bg=BG_DARK,
                     fg=FG_DIM, font=FONT_UI).pack(pady=20)

    # -----------------------------------------------------------------------
    # Status bar
    # -----------------------------------------------------------------------
    # Fixed: store direct reference to status label for Windows compatibility
    def _set_status(self, msg: str, error: bool = False):
        self.status_var.set(msg)
        color = FG_ERROR if error else FG_OK
        if hasattr(self, "status_label"):
            self.status_label.config(fg=color)

    # -----------------------------------------------------------------------
    # About dialog
    # -----------------------------------------------------------------------

    def _show_about(self):
        messagebox.showinfo(
            "About OwlTech File Manager",
            "OwlTech File Manager\n"
            "CS 3502: Operating Systems — Project 3\n\n"
            "Demonstrates OS file system concepts:\n"
            "  • File descriptors (open/close)\n"
            "  • Inode metadata (stat syscall)\n"
            "  • CRUD via OS APIs\n"
            "  • Directory traversal\n"
            "  • Atomic rename\n"
            "  • Permission handling\n\n"
            "Built with Python + Tkinter",
            parent=self
        )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = OwlFileManager()
    app.mainloop()
