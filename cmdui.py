"""
CMDVasilok - a Total Commander style GUI shell for cmd.exe (Windows).

Requirements: Python 3.9+, PyQt6.
Run:  python cmdui.py   (or via run.bat)
"""

import sys
import os
import string
import ctypes
import shutil
import subprocess
from datetime import datetime

from PyQt6 import QtWidgets, QtGui, QtCore

APP_NAME = "CMDVasilok"

# --- Qt6 compatibility: these classes moved between modules across Qt versions ---
# QShortcut: QtWidgets (Qt5) -> QtGui (Qt >= 6.0)
# QFileIconProvider: QtWidgets (Qt < 6.3) -> QtGui (Qt >= 6.3)
if hasattr(QtGui, "QShortcut"):
    QShortcut = QtGui.QShortcut
else:
    QShortcut = QtWidgets.QShortcut

if hasattr(QtGui, "QFileIconProvider"):
    QFileIconProvider = QtGui.QFileIconProvider
else:
    QFileIconProvider = QtWidgets.QFileIconProvider

# ============================================================
# File type associations (Total Commander style).
# mode:
#   "terminal"  -> run a command in the built-in cmd terminal
#   "app"       -> open with the given program
#   "startfile" -> open with the Windows default association
# ============================================================
FILE_ASSOCIATIONS = {
    ".bat":  ("terminal", '"{path}"'),
    ".cmd":  ("terminal", '"{path}"'),
    ".py":   ("terminal", 'python "{path}"'),
    ".pyw":  ("terminal", 'python "{path}"'),
    ".ps1":  ("terminal", 'powershell -NoProfile -ExecutionPolicy Bypass -File "{path}"'),
    ".sh":   ("terminal", 'bash "{path}"'),
    ".txt":  ("app", "notepad.exe"),
    ".log":  ("app", "notepad.exe"),
    ".ini":  ("app", "notepad.exe"),
    ".cfg":  ("app", "notepad.exe"),
    ".conf": ("app", "notepad.exe"),
    ".md":   ("app", "notepad.exe"),
    ".json": ("app", "notepad.exe"),
    ".xml":  ("app", "notepad.exe"),
    ".yml":  ("app", "notepad.exe"),
    ".yaml": ("app", "notepad.exe"),
    ".html": ("startfile", None),
    ".htm":  ("startfile", None),
    ".pdf":  ("startfile", None),
    ".zip":  ("startfile", None),
    ".jpg":  ("startfile", None),
    ".png":  ("startfile", None),
    ".exe":  ("terminal", '"{path}"'),
}

HELP_HTML = """
<h3>CMDVasilok — quick help</h3>
<p>A Total Commander style GUI shell over cmd.exe.</p>
<h4>Hotkeys</h4>
<table cellpadding="4">
<tr><td><b>F1</b></td><td>This help</td></tr>
<tr><td><b>F5</b></td><td>Refresh the file list</td></tr>
<tr><td><b>Enter</b></td><td>Send the terminal command</td></tr>
<tr><td><b>Up / Down</b></td><td>Command history in the terminal</td></tr>
</table>
<h4>Navigation</h4>
<p>Back / Up / Home / Refresh buttons, the address bar
(type a path and press Enter), and the quick access sidebar
(Home folder and all drives). Double-click a folder to enter it,
double-click a file to open it by its type.</p>
<h4>File types</h4>
<table cellpadding="4">
<tr><th>Extension</th><th>Action</th></tr>
{ASSOC_ROWS}
</table>
<p>Anything not listed opens with the Windows default app.
Right-click a file for more actions: open in terminal, copy path,
rename, delete.</p>
<h4>Terminal</h4>
<p>The terminal runs cmd.exe. Navigation keeps it in sync with the
current folder (cd /d). If cmd.exe exits (for example you typed
exit), it is restarted automatically in the same folder.</p>
"""

STYLESHEET = """
QMainWindow, QWidget {
    background-color: #1e1f24;
    color: #e4e4e7;
    font-family: 'Segoe UI';
    font-size: 10pt;
}
QMenuBar {
    background-color: #1e1f24;
    color: #e4e4e7;
}
QMenuBar::item:selected { background-color: #2f6fab; }
QMenu {
    background-color: #2b2d33;
    border: 1px solid #3a3d46;
    border-radius: 4px;
}
QMenu::item { padding: 5px 24px; }
QMenu::item:selected { background-color: #2f6fab; }
QPushButton {
    background-color: #2b2d33;
    color: #e4e4e7;
    border: 1px solid #3a3d46;
    border-radius: 6px;
    padding: 5px 12px;
}
QPushButton:hover { background-color: #3a3d46; }
QPushButton:pressed { background-color: #2f6fab; }
QLineEdit, QTextEdit {
    background-color: #26272d;
    border: 1px solid #3a3d46;
    border-radius: 6px;
    padding: 4px 8px;
}
QLineEdit:focus { border: 1px solid #4f8fdd; }
QListWidget {
    background-color: #232429;
    border: none;
    padding: 4px;
    outline: none;
}
QListWidget::item { padding: 6px; border-radius: 4px; }
QListWidget::item:hover { background-color: #2f3038; }
QListWidget::item:selected { background-color: #2f6fab; }
QTableWidget {
    background-color: #232429;
    border: none;
    gridline-color: #2c2d34;
    selection-background-color: #2f6fab;
    selection-color: #ffffff;
    alternate-background-color: #26272d;
}
QHeaderView::section {
    background-color: #2b2d33;
    color: #c9c9d1;
    border: none;
    padding: 6px;
}
QSplitter::handle { background-color: #14151a; width: 3px; height: 3px; }
QStatusBar { background-color: #26272d; }
QCheckBox { spacing: 6px; }
QToolTip {
    background-color: #2b2d33;
    color: #e4e4e7;
    border: 1px solid #3a3d46;
    padding: 4px;
}
QScrollBar:vertical { background: #232429; width: 10px; margin: 0; }
QScrollBar::handle:vertical {
    background: #3a3d46; border-radius: 5px; min-height: 20px;
}
QScrollBar::handle:vertical:hover { background: #2f6fab; }
QScrollBar:horizontal { background: #232429; height: 10px; margin: 0; }
QScrollBar::handle:horizontal {
    background: #3a3d46; border-radius: 5px; min-width: 20px;
}
QScrollBar::handle:horizontal:hover { background: #2f6fab; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
QLabel#sectionLabel {
    color: #9a9aa5;
    font-size: 9pt;
    padding: 4px 8px 0px 8px;
}
"""


def human_size(size):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{size} B"
        size /= 1024


class CmdUI(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME + " - GUI shell for cmd.exe")
        self.resize(1200, 760)

        self.icon_provider = QFileIconProvider()
        self.process = None
        self.pending_cmd = None
        self.closing = False
        self.cmd_history = []
        self.hist_idx = -1

        self.history = []
        self.hist_pos = -1
        self.current_path = os.getcwd()

        self.build_ui()
        self.load_drives()

        # Start the terminal BEFORE first navigation,
        # so navigate() can send "cd /d ..." into a live cmd
        try:
            self.start_terminal()
        except Exception as e:
            self.write_to_terminal(f"[SYSTEM] Terminal error: {e}\n")
            self.process = None

        self.navigate(self.current_path, record=False)

    # ================= UI =================

    def build_ui(self):
        self.build_menu()

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        root = QtWidgets.QVBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        st = self.style()

        # --- Toolbar: navigation + address bar + search ---
        toolbar = QtWidgets.QHBoxLayout()
        toolbar.setSpacing(6)

        self.btn_back = QtWidgets.QPushButton("Back")
        self.btn_back.setIcon(
            st.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_ArrowBack)
        )
        self.btn_back.setToolTip("Go to the previous folder (in history)")
        self.btn_back.clicked.connect(self.go_back)
        toolbar.addWidget(self.btn_back)

        self.btn_up = QtWidgets.QPushButton("Up")
        self.btn_up.setIcon(
            st.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_ArrowUp)
        )
        self.btn_up.setToolTip("Go to the parent folder")
        self.btn_up.clicked.connect(self.go_up)
        toolbar.addWidget(self.btn_up)

        self.btn_home = QtWidgets.QPushButton("Home")
        self.btn_home.setIcon(
            st.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DirHomeIcon)
        )
        self.btn_home.setToolTip("Go to the user home folder")
        self.btn_home.clicked.connect(self.go_home)
        toolbar.addWidget(self.btn_home)

        self.btn_refresh = QtWidgets.QPushButton("Refresh")
        self.btn_refresh.setIcon(
            st.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_BrowserReload)
        )
        self.btn_refresh.setToolTip("Refresh the file list (F5)")
        self.btn_refresh.clicked.connect(self.refresh)
        toolbar.addWidget(self.btn_refresh)

        self.path_edit = QtWidgets.QLineEdit()
        self.path_edit.setToolTip("Current folder path - edit and press Enter")
        self.path_edit.returnPressed.connect(self.on_path_entered)
        toolbar.addWidget(self.path_edit, 3)

        self.search_edit = QtWidgets.QLineEdit()
        self.search_edit.setPlaceholderText("Search in folder...")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(lambda _t: self.refresh())
        toolbar.addWidget(self.search_edit, 2)

        self.chk_hidden = QtWidgets.QCheckBox("Hidden files")
        self.chk_hidden.toggled.connect(lambda _s: self.refresh())
        toolbar.addWidget(self.chk_hidden)

        root.addLayout(toolbar)

        # --- Splitter: (sidebar + file table) / terminal ---
        v_split = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
        h_split = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        v_split.addWidget(h_split)

        # Sidebar: drives and quick access
        side_widget = QtWidgets.QWidget()
        side_layout = QtWidgets.QVBoxLayout(side_widget)
        side_layout.setContentsMargins(0, 0, 0, 0)
        side_layout.setSpacing(4)

        lbl_quick = QtWidgets.QLabel("Quick access")
        lbl_quick.setObjectName("sectionLabel")
        side_layout.addWidget(lbl_quick)

        self.side_list = QtWidgets.QListWidget()
        self.side_list.itemClicked.connect(self.on_side_click)
        side_layout.addWidget(self.side_list, 1)
        h_split.addWidget(side_widget)

        # File table
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Name", "Size", "Type", "Modified"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.SingleSelection
        )
        self.table.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.itemDoubleClicked.connect(self.on_double_click)
        self.table.itemSelectionChanged.connect(self.on_selection)
        self.table.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        h_split.addWidget(self.table)
        h_split.setStretchFactor(0, 1)
        h_split.setStretchFactor(1, 4)

        # --- Terminal panel ---
        term_widget = QtWidgets.QWidget()
        term_layout = QtWidgets.QVBoxLayout(term_widget)
        term_layout.setContentsMargins(0, 0, 0, 0)
        term_layout.setSpacing(6)

        term_bar = QtWidgets.QHBoxLayout()
        self.lbl_term_status = QtWidgets.QLabel("")
        self.lbl_term_status.setObjectName("sectionLabel")
        term_bar.addWidget(self.lbl_term_status)
        term_bar.addStretch(1)
        btn_clear = QtWidgets.QPushButton("Clear")
        btn_clear.clicked.connect(lambda: self.terminal_output.clear())
        term_bar.addWidget(btn_clear)
        term_layout.addLayout(term_bar)

        self.terminal_output = QtWidgets.QTextEdit()
        self.terminal_output.setReadOnly(True)
        self.terminal_output.setStyleSheet(
            "background-color: #000000; color: #00FF00;"
            "font-family: 'Courier New', monospace; font-size: 10pt;"
            "border: 1px solid #3a3d46; border-radius: 6px;"
        )
        term_layout.addWidget(self.terminal_output, 1)

        self.terminal_input = QtWidgets.QLineEdit()
        self.terminal_input.setPlaceholderText("Type command and press Enter...")
        self.terminal_input.setStyleSheet(
            "background-color: #111111; color: #FFFFFF;"
            "font-family: 'Courier New', monospace; font-size: 10pt;"
        )
        self.terminal_input.returnPressed.connect(self.on_command_entered)
        self.terminal_input.installEventFilter(self)
        term_layout.addWidget(self.terminal_input)

        v_split.addWidget(term_widget)
        v_split.setStretchFactor(0, 3)
        v_split.setStretchFactor(1, 2)

        root.addWidget(v_split, 1)

        self.statusBar().showMessage("Ready")

        # F5 to refresh
        refresh_shortcut = QShortcut(QtGui.QKeySequence("F5"), self)
        refresh_shortcut.activated.connect(self.refresh)

        # F1 for help
        help_shortcut = QShortcut(QtGui.QKeySequence("F1"), self)
        help_shortcut.activated.connect(self.show_help)

    def build_menu(self):
        menu_bar = self.menuBar()

        actions_menu = menu_bar.addMenu("&Actions")
        act_refresh = actions_menu.addAction("Refresh (F5)")
        act_refresh.triggered.connect(self.refresh)
        act_home = actions_menu.addAction("Go Home")
        act_home.triggered.connect(self.go_home)

        help_menu = menu_bar.addMenu("&Help")
        act_help = help_menu.addAction("Help (F1)")
        act_help.triggered.connect(self.show_help)
        help_menu.addSeparator()
        act_about = help_menu.addAction("About")
        act_about.triggered.connect(self.show_about)

    # ================= HELP =================

    def build_help_text(self):
        rows = []
        for ext, (mode, command) in FILE_ASSOCIATIONS.items():
            if mode == "terminal":
                action = f"run in terminal: {command.format(path='...')}"
            elif mode == "app":
                action = f"open with: {command}"
            else:
                action = "open with Windows default app"
            rows.append(f"<tr><td><b>{ext}</b></td><td>{action}</td></tr>")
        return HELP_HTML.replace("{ASSOC_ROWS}", "\n".join(rows))

    def show_help(self):
        box = QtWidgets.QMessageBox(self)
        box.setWindowTitle(APP_NAME + " - Help")
        box.setTextFormat(QtCore.Qt.TextFormat.RichText)
        box.setText(self.build_help_text())
        box.setIcon(QtWidgets.QMessageBox.Icon.Information)
        box.exec()

    def show_about(self):
        QtWidgets.QMessageBox.about(
            self,
            APP_NAME,
            f"<b>{APP_NAME}</b> v1.0<br>"
            "A Total Commander style GUI shell for cmd.exe.<br>"
            "Python " + sys.version.split()[0] + ", PyQt6.",
        )

    # ================= NAVIGATION =================

    def get_drives(self):
        drives = []
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        for i, letter in enumerate(string.ascii_uppercase):
            if bitmask & (1 << i):
                drives.append(letter + ":\\")
        return drives

    def drive_info(self, path):
        try:
            free = ctypes.c_ulonglong()
            total = ctypes.c_ulonglong()
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                ctypes.c_wchar_p(path), ctypes.byref(free),
                ctypes.byref(total), None
            )
            return f"Free: {human_size(free.value)} of {human_size(total.value)}"
        except Exception:
            return ""

    def load_drives(self):
        self.side_list.clear()

        home_item = QtWidgets.QListWidgetItem(
            self.icon_provider.icon(QtCore.QFileInfo(os.path.expanduser("~"))),
            "Home",
        )
        home_item.setData(QtCore.Qt.ItemDataRole.UserRole, os.path.expanduser("~"))
        self.side_list.addItem(home_item)

        for drive in self.get_drives():
            drive_path = drive + "\\"
            item = QtWidgets.QListWidgetItem(
                self.icon_provider.icon(QtCore.QFileInfo(drive_path)),
                drive_path,
            )
            item.setData(QtCore.Qt.ItemDataRole.UserRole, drive_path)
            self.side_list.addItem(item)

    def navigate(self, path, record=True):
        if not os.path.isdir(path):
            QtWidgets.QMessageBox.warning(self, APP_NAME, "Folder does not exist.")
            return
        self.current_path = os.path.abspath(path)
        self.path_edit.setText(self.current_path)
        if record:
            self.history = self.history[: self.hist_pos + 1]
            self.history.append(self.current_path)
            self.hist_pos = len(self.history) - 1
        self.refresh()
        self.send_or_queue(f'cd /d "{self.current_path}"')

    def go_back(self):
        if self.hist_pos > 0:
            self.hist_pos -= 1
            self.current_path = self.history[self.hist_pos]
            self.path_edit.setText(self.current_path)
            self.refresh()
            self.send_or_queue(f'cd /d "{self.current_path}"')

    def go_up(self):
        parent = os.path.dirname(self.current_path)
        if parent != self.current_path:
            self.navigate(parent)

    def go_home(self):
        self.navigate(os.path.expanduser("~"))

    def refresh(self):
        self.table.setRowCount(0)
        self.table.setIconSize(QtCore.QSize(20, 20))
        pattern = self.search_edit.text().lower() if hasattr(self, "search_edit") else ""

        try:
            entries = os.listdir(self.current_path)
        except PermissionError:
            self.statusBar().showMessage("Access denied")
            return

        dirs, files = [], []
        for name in entries:
            if pattern and pattern not in name.lower():
                continue
            path = os.path.join(self.current_path, name)
            if self.is_hidden(path) and not self.chk_hidden.isChecked():
                continue
            if os.path.isdir(path):
                dirs.append((name, path))
            else:
                files.append((name, path))

        dirs.sort(key=lambda x: x[0].casefold())
        files.sort(key=lambda x: x[0].casefold())

        for name, path in dirs:
            self.add_row(name, path, is_dir=True)
        for name, path in files:
            self.add_row(name, path, is_dir=False)

        info = self.drive_info(self.current_path)
        suffix = f" - {info}" if info else ""
        self.statusBar().showMessage(
            f"{len(dirs)} folder(s), {len(files)} file(s) - "
            f"{self.current_path}{suffix}"
        )

    def is_hidden(self, path):
        try:
            st = os.stat(path)
            return bool(getattr(st, "st_file_attributes", 0) & 0x2)
        except OSError:
            return False

    def add_row(self, name, path, is_dir):
        row = self.table.rowCount()
        self.table.insertRow(row)

        icon = self.icon_provider.icon(QtCore.QFileInfo(path))
        name_item = QtWidgets.QTableWidgetItem(icon, name)
        name_item.setData(QtCore.Qt.ItemDataRole.UserRole, path)
        self.table.setItem(row, 0, name_item)

        if is_dir:
            size_text, type_text = "", "Folder"
        else:
            try:
                size_text = human_size(os.path.getsize(path))
            except OSError:
                size_text = ""
            ext = os.path.splitext(name)[1].lstrip(".").upper()
            type_text = (ext + " File") if ext else "File"

        self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(size_text))
        self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(type_text))

        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(path))
            mod_text = mtime.strftime("%d.%m.%Y %H:%M")
        except OSError:
            mod_text = ""
        self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(mod_text))

    def on_path_entered(self):
        self.navigate(self.path_edit.text())

    def on_side_click(self, item):
        self.navigate(item.data(QtCore.Qt.ItemDataRole.UserRole))

    def on_double_click(self, item):
        path = os.path.join(
            self.current_path,
            self.table.item(item.row(), 0).text(),
        )
        if os.path.isdir(path):
            self.navigate(path)
        else:
            self.open_file(path)

    def on_selection(self):
        sel = self.table.selectedItems()
        if sel:
            name = self.table.item(sel[0].row(), 0).text()
            self.statusBar().showMessage(f"Selected: {name}")

    # ================= FILE ASSOCIATIONS =================

    def open_file(self, path):
        """Total Commander style: act by file type."""
        ext = os.path.splitext(path)[1].lower()

        if ext in FILE_ASSOCIATIONS:
            mode, command = FILE_ASSOCIATIONS[ext]
            if mode == "terminal":
                self.write_to_terminal(
                    f"[SYSTEM] Running: {command.format(path=path)}\n"
                )
                self.send_or_queue(command.format(path=path))
                return
            if mode == "app":
                try:
                    subprocess.Popen([command, path])
                    self.statusBar().showMessage(f"Opened with {command}")
                except OSError as e:
                    QtWidgets.QMessageBox.warning(self, APP_NAME, str(e))
                return

        # Fallback: Windows default association
        self.open_with_system(path)

    def open_with_system(self, path):
        try:
            os.startfile(path)
            self.statusBar().showMessage("Opened with system default app")
        except OSError as e:
            QtWidgets.QMessageBox.warning(
                self,
                APP_NAME,
                f"No default association for this file type.\n{e}",
            )

    # ================= CONTEXT MENU =================

    def show_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if not item:
            return
        row = item.row()
        name = self.table.item(row, 0).text()
        path = os.path.join(self.current_path, name)
        is_dir = os.path.isdir(path)

        menu = QtWidgets.QMenu(self)

        if is_dir:
            act_open = menu.addAction("Open folder")
        else:
            ext = os.path.splitext(path)[1].lower()
            if ext in FILE_ASSOCIATIONS and FILE_ASSOCIATIONS[ext][0] == "terminal":
                act_open = menu.addAction(f"Run in Terminal ({ext})")
            elif ext in FILE_ASSOCIATIONS and FILE_ASSOCIATIONS[ext][0] == "app":
                act_open = menu.addAction(f"Open with {FILE_ASSOCIATIONS[ext][1]}")
            else:
                act_open = menu.addAction("Open")
            menu.addAction("Open with system default").triggered.connect(
                lambda: self.open_with_system(path)
            )

        act_term = menu.addAction("Open in Terminal (cd)")
        menu.addSeparator()
        act_copy = menu.addAction("Copy full path")
        menu.addSeparator()
        act_rename = menu.addAction("Rename")
        act_delete = menu.addAction("Delete")

        chosen = menu.exec(self.table.mapToGlobal(pos))
        if chosen is None:
            return

        if chosen is act_open:
            if is_dir:
                self.navigate(path)
            else:
                self.open_file(path)
        elif chosen is act_term:
            self.send_or_queue(f'cd /d "{path}"')
        elif chosen is act_copy:
            QtGui.QGuiApplication.clipboard().setText(path)
            self.statusBar().showMessage("Path copied to clipboard")
        elif chosen is act_rename:
            new_name, ok = QtWidgets.QInputDialog.getText(
                self, "Rename", "New name:", text=name
            )
            if ok and new_name and new_name != name:
                try:
                    os.rename(path, os.path.join(self.current_path, new_name))
                    self.refresh()
                except OSError as e:
                    QtWidgets.QMessageBox.warning(self, APP_NAME, str(e))
        elif chosen is act_delete:
            answer = QtWidgets.QMessageBox.question(
                self, "Delete", f'Delete "{name}"?',
            )
            if answer == QtWidgets.QMessageBox.StandardButton.Yes:
                try:
                    if is_dir:
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                    self.refresh()
                except OSError as e:
                    QtWidgets.QMessageBox.warning(self, APP_NAME, str(e))

    # ================= TERMINAL =================

    def start_terminal(self):
        self.process = QtCore.QProcess(self)
        self.process.setProcessChannelMode(
            QtCore.QProcess.ProcessChannelMode.MergedChannels
        )
        self.process.setWorkingDirectory(self.current_path)
        self.process.readyReadStandardOutput.connect(self.read_terminal)
        self.process.finished.connect(self.on_process_finished)
        self.process.start("cmd.exe")
        if not self.process.waitForStarted(3000):
            self.write_to_terminal("[SYSTEM] Failed to start cmd.exe\n")
            self.process = None
            self.lbl_term_status.setText("Terminal: not running")
            return
        self.lbl_term_status.setText("Terminal: running")
        # Flush commands that arrived before cmd was ready
        if self.pending_cmd:
            self.send_command(self.pending_cmd)
            self.pending_cmd = None

    def read_terminal(self):
        if not self.process:
            return
        data = bytes(self.process.readAllStandardOutput())
        try:
            text = data.decode("cp866")
        except UnicodeDecodeError:
            text = data.decode("utf-8", errors="replace")
        self.write_to_terminal(text)

    def on_process_finished(self):
        self.write_to_terminal("\n[SYSTEM] cmd.exe has exited.\n")
        self.process = None
        self.lbl_term_status.setText("Terminal: not running")
        # Auto-restart cmd.exe (unless the application is closing)
        if not self.closing:
            self.write_to_terminal("[SYSTEM] Restarting cmd.exe...\n")
            QtCore.QTimer.singleShot(300, self.start_terminal)

    def send_command(self, cmd):
        if self.process:
            try:
                self.process.write((cmd + "\r\n").encode("cp866", errors="replace"))
            except Exception:
                self.write_to_terminal("[SYSTEM] Connection to cmd lost.\n")
        else:
            self.write_to_terminal("[SYSTEM] Terminal is not running.\n")

    def send_or_queue(self, cmd):
        # If cmd.exe is not started yet, keep the command until it starts
        if self.process is None:
            self.pending_cmd = cmd
        else:
            self.send_command(cmd)

    def on_command_entered(self):
        cmd = self.terminal_input.text().strip()
        self.terminal_input.clear()
        if not cmd:
            return

        self.cmd_history.append(cmd)
        self.hist_idx = len(self.cmd_history)
        self.write_to_terminal(f"{self.current_path}> {cmd}\n")
        self.send_command(cmd)

    def eventFilter(self, obj, event):
        if obj is self.terminal_input and event.type() == QtCore.QEvent.Type.KeyPress:
            if event.key() == QtCore.Qt.Key.Key_Up:
                if self.cmd_history and self.hist_idx > 0:
                    self.hist_idx -= 1
                    self.terminal_input.setText(self.cmd_history[self.hist_idx])
                return True
            if event.key() == QtCore.Qt.Key.Key_Down:
                if self.hist_idx < len(self.cmd_history):
                    self.hist_idx += 1
                    if self.hist_idx < len(self.cmd_history):
                        self.terminal_input.setText(self.cmd_history[self.hist_idx])
                    else:
                        self.terminal_input.clear()
                return True
        return super().eventFilter(obj, event)

    def write_to_terminal(self, text):
        self.terminal_output.moveCursor(QtGui.QTextCursor.MoveOperation.End)
        self.terminal_output.insertPlainText(text)
        sb = self.terminal_output.verticalScrollBar()
        sb.setValue(sb.maximum())

    def closeEvent(self, event):
        self.closing = True
        if self.process:
            self.process.terminate()
            if not self.process.waitForFinished(1000):
                self.process.kill()
        event.accept()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = CmdUI()
    window.show()
    sys.exit(app.exec())
