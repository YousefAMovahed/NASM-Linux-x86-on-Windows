import sys
import os
import platform
import subprocess
import tempfile
import shutil
import json
import base64
from cryptography.fernet import Fernet

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QVBoxLayout, QHBoxLayout,
    QPushButton, QWidget, QSplitter, QLabel, QFileDialog, QMessageBox,
    QToolBar, QStatusBar, QLineEdit, QSpinBox
)
from PyQt6.QtCore import Qt, QRegularExpression
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont, QAction, QKeySequence


# ============================================================
# Syntax Highlighter
# ============================================================
class AssemblyHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569CD6"))
        keyword_format.setFontWeight(QFont.Weight.Bold)

        register_format = QTextCharFormat()
        register_format.setForeground(QColor("#9CDCFE"))

        directive_format = QTextCharFormat()
        directive_format.setForeground(QColor("#C586C0"))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6A9955"))
        comment_format.setFontItalic(True)

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#CE9178"))

        label_format = QTextCharFormat()
        label_format.setForeground(QColor("#DCDCAA"))

        keywords = [
            r'\bmov\b', r'\badd\b', r'\bsub\b', r'\bmul\b', r'\bdiv\b', r'\bjmp\b',
            r'\bcmp\b', r'\bje\b', r'\bjne\b', r'\bjg\b', r'\bjl\b', r'\bjge\b',
            r'\bjle\b', r'\bcall\b', r'\bret\b', r'\bpush\b', r'\bpop\b', r'\bsyscall\b',
            r'\bint\b', r'\binc\b', r'\bdec\b', r'\bxor\b', r'\bor\b', r'\band\b',
            r'\bshl\b', r'\bshr\b', r'\bnop\b', r'\blea\b', r'\bimul\b', r'\bidiv\b'
        ]
        for kw in keywords:
            self.highlighting_rules.append((
                QRegularExpression(kw, QRegularExpression.PatternOption.CaseInsensitiveOption),
                keyword_format
            ))

        registers = [
            r'\brax\b', r'\brbx\b', r'\brcx\b', r'\brdx\b', r'\brsi\b', r'\brdi\b',
            r'\brbp\b', r'\brsp\b', r'\br8\b', r'\br9\b', r'\br10\b', r'\br11\b',
            r'\br12\b', r'\br13\b', r'\br14\b', r'\br15\b', r'\beax\b', r'\bebx\b',
            r'\becx\b', r'\bedx\b', r'\bax\b', r'\bbx\b', r'\bcx\b', r'\bdx\b',
            r'\bal\b', r'\bbl\b', r'\bcl\b', r'\bdl\b', r'\bah\b', r'\bbh\b', r'\bch\b', r'\bdh\b'
        ]
        for reg in registers:
            self.highlighting_rules.append((
                QRegularExpression(reg, QRegularExpression.PatternOption.CaseInsensitiveOption),
                register_format
            ))

        directives = [
            r'\bsection\b', r'\bglobal\b', r'\bextern\b', r'\bdb\b', r'\bdw\b',
            r'\bdd\b', r'\bdq\b', r'\bequ\b', r'\bresb\b', r'\bresw\b', r'\bresd\b', r'\bresq\b'
        ]
        for d in directives:
            self.highlighting_rules.append((
                QRegularExpression(d, QRegularExpression.PatternOption.CaseInsensitiveOption),
                directive_format
            ))

        self.highlighting_rules.append((QRegularExpression(r'".*"'), string_format))
        self.highlighting_rules.append((QRegularExpression(r"'.*'"), string_format))
        self.highlighting_rules.append((QRegularExpression(r'^[A-Za-z_][A-Za-z0-9_]*:'), label_format))
        self.highlighting_rules.append((QRegularExpression(r';.*'), comment_format))

    def highlightBlock(self, text):
        for pattern, fmt in self.highlighting_rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)


# ============================================================
# Main IDE Window
# ============================================================
class AssemblyZeroConfigIDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_file_path = None
        self.is_modified = False

        self.setWindowTitle("Assembly Studio - Pro Edition")
        self.setGeometry(100, 100, 1100, 850)

        self.init_theme()
        self.init_ui()
        self.init_menu_and_toolbar()

        self.editor.textChanged.connect(self.on_text_changed)
        self.update_window_title()

    # --------------------------------------------------------
    # UI Setup
    # --------------------------------------------------------
    def init_theme(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; }
            QMenuBar { background-color: #3c3c3c; color: #cccccc; font-family: 'Segoe UI'; font-size: 10pt; }
            QMenuBar::item:selected { background-color: #505050; color: white; }
            QMenu { background-color: #252526; color: #cccccc; border: 1px solid #3c3c3c; }
            QMenu::item:selected { background-color: #0e639c; color: white; }
            QToolBar { background-color: #333333; border-bottom: 1px solid #252526; spacing: 5px; padding: 3px; }
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 10px;
                font-family: 'Consolas', 'Fira Code', 'Courier New', monospace;
                font-size: 13pt;
            }
            QLineEdit { background-color: #3c3c3c; color: #f1f1f1; border: 1px solid #555555; border-radius: 3px; padding: 4px; font-family: 'Segoe UI'; }
            QLabel { color: #cccccc; font-weight: bold; font-family: 'Segoe UI', Arial, sans-serif; font-size: 10pt; padding-top: 4px; padding-bottom: 4px; }
            QSplitter::handle { background-color: #2d2d2d; }
            QStatusBar { background-color: #007acc; color: white; font-family: 'Segoe UI'; font-size: 9pt; }
            QMessageBox { background-color: #252526; color: #d4d4d4; font-family: 'Segoe UI'; }
            QMessageBox QPushButton { background-color: #3e3e42; color: white; border: 1px solid #555555; padding: 5px 15px; border-radius: 3px; }
            QMessageBox QPushButton:hover { background-color: #505050; }
        """)

    def init_ui(self):
        main_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

        self.search_panel = QWidget()
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(5, 2, 5, 2)
        self.search_panel.setLayout(search_layout)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search code (Press Enter for next)...")
        self.search_input.returnPressed.connect(self.find_text)

        find_btn = QPushButton("Find Next")
        find_btn.setStyleSheet("background-color: #3e3e42; color: white; border: none; padding: 4px 10px; border-radius: 3px; font-family: 'Segoe UI';")
        find_btn.clicked.connect(self.find_text)

        close_search_btn = QPushButton("✕")
        close_search_btn.setStyleSheet("background-color: transparent; color: #ff5555; font-weight: bold; border: none;")
        close_search_btn.clicked.connect(self.hide_search_panel)

        search_layout.addWidget(QLabel("🔍 Find:"))
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(find_btn)
        search_layout.addWidget(close_search_btn)
        search_layout.addStretch()
        self.search_panel.setVisible(False)
        layout.addWidget(self.search_panel)

        self.editor = QTextEdit()
        self.editor.setPlaceholderText(
            "; Write your x86_64 Linux Assembly code here...\n"
            "; NOTE: You are targeting Linux ELF64 (use syscalls, not Windows APIs!)\n"
        )
        self.highlighter = AssemblyHighlighter(self.editor.document())

        self.input_box = QTextEdit()
        self.input_box.setPlaceholderText("Standard Input (stdin) - Provide inputs here before execution if required...")

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet("color: #4af626; background-color: #111111; font-family: 'Consolas', monospace;")

        def create_section(title, widget):
            container = QWidget()
            vbox = QVBoxLayout()
            vbox.setContentsMargins(0, 0, 0, 0)
            vbox.addWidget(QLabel(title))
            vbox.addWidget(widget)
            container.setLayout(vbox)
            return container

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(create_section(" 📝 CODE EDITOR", self.editor))
        splitter.addWidget(create_section(" ⌨️ STANDARD INPUT (STDIN)", self.input_box))
        splitter.addWidget(create_section(" 🖥️ OUTPUT CONSOLE", self.console))

        splitter.setSizes([550, 120, 180])
        layout.addWidget(splitter)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def init_menu_and_toolbar(self):
        new_act = QAction("📄 New File", self)
        new_act.setShortcut(QKeySequence.StandardKey.New)
        new_act.triggered.connect(self.new_file)

        open_act = QAction("📂 Open File...", self)
        open_act.setShortcut(QKeySequence.StandardKey.Open)
        open_act.triggered.connect(self.open_file)

        save_act = QAction("💾 Save", self)
        save_act.setShortcut(QKeySequence.StandardKey.Save)
        save_act.triggered.connect(self.save_file)

        save_as_act = QAction("📝 Save As...", self)
        save_as_act.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_act.triggered.connect(self.save_file_as)

        exit_act = QAction("❌ Exit", self)
        exit_act.setShortcut(QKeySequence("Ctrl+Q"))
        exit_act.triggered.connect(self.close)

        find_act = QAction("🔍 Find", self)
        find_act.setShortcut(QKeySequence.StandardKey.Find)
        find_act.triggered.connect(self.show_search_panel)

        run_act = QAction("▶ RUN CODE", self)
        run_act.setShortcut(QKeySequence("F5"))
        run_act.triggered.connect(self.compile_and_run)

        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")
        file_menu.addAction(new_act)
        file_menu.addAction(open_act)
        file_menu.addAction(save_act)
        file_menu.addAction(save_as_act)
        file_menu.addSeparator()
        file_menu.addAction(exit_act)

        edit_menu = menu_bar.addMenu("&Edit")
        edit_menu.addAction(find_act)

        build_menu = menu_bar.addMenu("&Build")
        build_menu.addAction(run_act)

        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        toolbar.addAction(new_act)
        toolbar.addAction(open_act)
        toolbar.addAction(save_act)
        toolbar.addSeparator()

        toolbar.addWidget(QLabel(" ⏱️ Timeout: "))
        self.timeout_spinner = QSpinBox()
        self.timeout_spinner.setRange(1, 20)
        self.timeout_spinner.setValue(5)
        self.timeout_spinner.setSuffix("s")
        self.timeout_spinner.setStyleSheet(
            "QSpinBox { background-color: #3c3c3c; color: #ffffff; border: 1px solid #555555; border-radius: 3px; padding: 3px; font-weight: bold; min-width: 55px; }"
        )
        toolbar.addWidget(self.timeout_spinner)
        toolbar.addSeparator()

        run_button = QPushButton("▶ Run Code (F5)")
        run_button.setStyleSheet(
            "QPushButton { background-color: #0e639c; color: white; border: none; padding: 5px 15px; font-weight: bold; border-radius: 3px; font-family: 'Segoe UI'; } QPushButton:hover { background-color: #1177bb; }"
        )
        run_button.setCursor(Qt.CursorShape.PointingHandCursor)
        run_button.clicked.connect(self.compile_and_run)
        toolbar.addWidget(run_button)

        toolbar.addSeparator()

        grade_button = QPushButton("🎯 Evaluate Assignment")
        grade_button.setStyleSheet(
            "QPushButton { background-color: #28a745; color: white; border: none; padding: 5px 15px; font-weight: bold; border-radius: 3px; font-family: 'Segoe UI'; } QPushButton:hover { background-color: #218838; }"
        )
        grade_button.setCursor(Qt.CursorShape.PointingHandCursor)
        grade_button.clicked.connect(self.run_auto_grader)
        toolbar.addWidget(grade_button)

    # --------------------------------------------------------
    # Basic editor actions
    # --------------------------------------------------------
    def show_search_panel(self):
        self.search_panel.setVisible(True)
        self.search_input.setFocus()
        self.search_input.selectAll()

    def hide_search_panel(self):
        self.search_panel.setVisible(False)
        self.editor.setFocus()

    def find_text(self):
        text = self.search_input.text()
        if text:
            if not self.editor.find(text):
                cursor = self.editor.textCursor()
                cursor.movePosition(cursor.MoveOperation.Start)
                self.editor.setTextCursor(cursor)
                self.editor.find(text)

    def on_text_changed(self):
        if not self.is_modified:
            self.is_modified = True
            self.update_window_title()

    def update_window_title(self):
        file_name = os.path.basename(self.current_file_path) if self.current_file_path else "Untitled.asm"
        modified_flag = " •" if self.is_modified else ""
        self.setWindowTitle(f"{file_name}{modified_flag} - Assembly Studio Pro")
        self.status_bar.showMessage(f"File: {self.current_file_path}" if self.current_file_path else "Untitled File")

    def maybe_save(self):
        if not self.is_modified:
            return True
        ret = QMessageBox.question(
            self,
            "Save Changes?",
            "The document has been modified.\nDo you want to save your changes?",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
        )
        if ret == QMessageBox.StandardButton.Save:
            return self.save_file()
        elif ret == QMessageBox.StandardButton.Cancel:
            return False
        return True

    def new_file(self):
        if self.maybe_save():
            self.editor.clear()
            self.current_file_path = None
            self.is_modified = False
            self.update_window_title()

    def open_file(self):
        if self.maybe_save():
            file_path, _ = QFileDialog.getOpenFileName(self, "Open Assembly File", "", "Assembly Files (*.asm *.s);;All Files (*)")
            if file_path:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.editor.setPlainText(f.read())
                self.current_file_path = file_path
                self.is_modified = False
                self.update_window_title()

    def save_file(self):
        if self.current_file_path:
            try:
                with open(self.current_file_path, "w", encoding="utf-8") as f:
                    f.write(self.editor.toPlainText())
                self.is_modified = False
                self.update_window_title()
                return True
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save file:\n{str(e)}")
                return False
        return self.save_file_as()

    def save_file_as(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File As", "", "Assembly Files (*.asm);;All Files (*)")
        if file_path:
            if not file_path.endswith(".asm") and "." not in os.path.basename(file_path):
                file_path += ".asm"
            self.current_file_path = file_path
            return self.save_file()
        return False

    # --------------------------------------------------------
    # Safe Tool Paths for Executable (Nuitka Ready)
    # --------------------------------------------------------
    def get_tool_paths(self):
        # This section ensures that even in the exe version, the tools folder path is found correctly
        if getattr(sys, 'frozen', False) or hasattr(sys, 'importers'):
            base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
        os_type = platform.system()
        format_flag = "elf64"

        if os_type == "Windows":
            nasm = os.path.join(base_dir, "tools", "win", "nasm.exe")
            linker = os.path.join(base_dir, "tools", "win", "ld.lld.exe")
            blink = os.path.join(base_dir, "tools", "win", "blink.exe")
            return nasm, linker, blink, format_flag
        else:
            system_ld = shutil.which("ld")
            linker = system_ld if system_ld else os.path.join(base_dir, "tools", "linux", "ld")
            nasm = shutil.which("nasm") or os.path.join(base_dir, "tools", "linux", "nasm")
            return nasm, linker, None, format_flag

    # --------------------------------------------------------
    # Base command runner (Sanitizes Inputs properly)
    # --------------------------------------------------------
    def _run_cmd(self, cmd, input_text=None, timeout=10, cwd=None):
        if input_text is not None:
            # Remove \r and safely convert to binary to prevent Windows from altering the input
            input_bytes = input_text.replace('\r', '').encode('utf-8')
        else:
            input_bytes = None

        res = subprocess.run(
            cmd,
            input=input_bytes,
            capture_output=True,
            timeout=timeout,
            cwd=cwd
        )
        
        # Convert outputs back to strings for easier display
        res.stdout = res.stdout.decode('utf-8', errors='replace') if res.stdout else ""
        res.stderr = res.stderr.decode('utf-8', errors='replace') if res.stderr else ""
        
        return res

    # --------------------------------------------------------
    # Clean Execution (Student Facing)
    # --------------------------------------------------------
    def compile_and_run(self):
        code = self.editor.toPlainText().strip()
        user_input = self.input_box.toPlainText()

        if not code:
            self.console.setText("❌ Editor error: There is no code to run. Please write your code first.")
            return

        os_type = platform.system()
        nasm_path, linker_path, blink_path, format_flag = self.get_tool_paths()
        max_time = self.timeout_spinner.value()

        self.console.clear()

        # =================================================================
        # 1. Environment diagnostics and runtime health check
        # =================================================================
        self.console.append("🔍 Checking runtime environment health...")
        
        missing_files = []
        required_tools = {
            "Compiler (NASM)": nasm_path,
            "Linker (LLD)": linker_path
        }
        
        if os_type == "Windows":
            required_tools["Emulator (Blink)"] = blink_path
            # Check for critical DLLs alongside the emulator
            blink_dir = os.path.dirname(blink_path) if blink_path else ""
            required_tools["Linux core library (cygwin1.dll)"] = os.path.join(blink_dir, "cygwin1.dll")
            required_tools["Compiler library (cyggcc_s-seh-1.dll)"] = os.path.join(blink_dir, "cyggcc_s-seh-1.dll")

        # Check for the physical existence of files
        for name, path in required_tools.items():
            if not path or not os.path.exists(path):
                missing_files.append(name)

        if missing_files:
            self.console.append("\n❌ Environment error: The following files were not found on your system:")
            for mf in missing_files:
                self.console.append(f"   - {mf}")
            self.console.append("\n💡 Guide: Critical program files have been removed. Your antivirus may have blocked them. Please reinstall the software and add it to your antivirus whitelist.")
            return

        # Test emulator execution (to catch hidden Windows errors when loading dependencies)
        if os_type == "Windows":
            try:
                # Run a simple command only to test whether the Blink engine starts correctly
                test_run = self._run_cmd([blink_path, "-h"], timeout=3)
                if test_run.returncode == 3221225781:  # Known 0xC0000135 error code
                    self.console.append("\n❌ Critical system error (0xC0000135):")
                    self.console.append("The emulator cannot run. The basic Windows prerequisites are not installed on your system.")
                    self.console.append("💡 Guide: Please install the Visual C++ Redistributable package on your Windows system.")
                    return
            except PermissionError:
                self.console.append("\n❌ Permission denied:")
                self.console.append("The operating system does not allow the emulator to run. Please run the program as Administrator.")
                return
            except Exception as e:
                self.console.append(f"\n❌ Unknown error while checking the emulator: {str(e)}")
                return
                
        self.console.append("✅ The runtime environment is completely healthy.\n" + "-" * 50)
        self.console.append("⚙️ Preparing and building...")
        # =================================================================
        
        # --- NEW CWD LOGIC: پیدا کردن پوشه هدف برای ذخیره و خواندن فایل‌ها ---
        if self.current_file_path:
            # اگر فایل ذخیره شده است، مسیر همان فایل به عنوان محیط کاری تعیین می‌شود
            work_dir = os.path.dirname(os.path.abspath(self.current_file_path))
        else:
            # اگر فایل هنوز ذخیره نشده، یک پوشه workspace در کنار خود نرم‌افزار می‌سازیم
            if getattr(sys, 'frozen', False) or hasattr(sys, 'importers'):
                base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            else:
                base_dir = os.path.dirname(os.path.abspath(__file__))
            work_dir = os.path.join(base_dir, "workspace")
            os.makedirs(work_dir, exist_ok=True)

        # نام‌گذاری فایل‌های موقت بیلد با پیشوند نقطه (برای مخفی بودن موقت)
        asm_file = os.path.join(work_dir, ".temp_run.asm")
        obj_file = os.path.join(work_dir, ".temp_run.o")
        exe_file = os.path.join(work_dir, ".temp_run.elf")

        try:
            # نوشتن کد داخل فایل اسمبلی موقت در همان پوشه هدف
            with open(asm_file, "w", encoding="utf-8") as f:
                f.write(code)

            # 1. Compile
            nasm_res = self._run_cmd([nasm_path, "-f", format_flag, asm_file, "-o", obj_file], timeout=10, cwd=work_dir)
            if nasm_res.returncode != 0:
                self.console.append("\n❌ Syntax error in assembly code (NASM Error):")
                self.console.append(nasm_res.stderr.strip() or nasm_res.stdout.strip())
                return

            # 2. Link
            link_res = self._run_cmd([linker_path, "-m", "elf_x86_64", obj_file, "-o", exe_file], timeout=10, cwd=work_dir)
            if link_res.returncode != 0:
                self.console.append("\n❌ Linker error:")
                self.console.append(link_res.stderr.strip() or link_res.stdout.strip())
                return

            # 3. Run
            self.console.append("▶️ Starting program execution...\n" + "-" * 50)
            
            # چون cwd روی work_dir تنظیم شده، شبیه‌ساز را فقط با نام فایل صدا می‌زنیم
            if os_type == "Windows":
                run_cmd = [blink_path, "-m", ".temp_run.elf"]
            else:
                run_cmd = ["./.temp_run.elf"]

            try:
                # اجرای نهایی با تنظیم دقیق پوشه کاری. هر فایلی در کد اسمبلی ساخته شود اینجا قرار می‌گیرد
                run_res = self._run_cmd(run_cmd, input_text=user_input, timeout=max_time, cwd=work_dir)
                
                # Only print the program's standard STDOUT
                if run_res.stdout:
                    self.console.append(run_res.stdout)
                
                # If the program itself produced an internal error
                if run_res.stderr:
                    self.console.append("\n[Program error (STDERR)]\n" + run_res.stderr.strip())

                self.console.append("-" * 50)
                if run_res.returncode != 0:
                    self.console.append(f"⚠️ The program ended with an unusual error code: {run_res.returncode}")
                else:
                    self.console.append("✅ Execution completed successfully (Exit Code 0).")

            except subprocess.TimeoutExpired:
                self.console.append(f"⏳ Execution time error: Infinite loop? The program was stopped after {max_time} seconds.")
            except FileNotFoundError:
                self.console.append("❌ System error: The final file to run was not found.")
            except Exception as e:
                self.console.append(f"❌ Unexpected system error: {e}")

        finally:
            # پاک‌سازی فایل‌های کامپایل شده برای جلوگیری از شلوغ شدن پوشه دانشجو
            # فایل‌هایی که توسط خود دانشجو با سیستم‌کال اسمبلی ساخته شده‌اند (مثل text.txt) دست‌نخورده باقی می‌مانند
            for f in [asm_file, obj_file, exe_file]:
                if os.path.exists(f):
                    try:
                        os.remove(f)
                    except Exception:
                        pass
    # --------------------------------------------------------
    # Auto-grader (Security untouched, silently processed)
    # --------------------------------------------------------
    def run_auto_grader(self):
        code = self.editor.toPlainText().strip()
        if not code:
            QMessageBox.warning(self, "Error", "Please write your assembly code first.")
            return

        file_path, _ = QFileDialog.getOpenFileName(self, "Open Assignment File", "", "Data Files (*.dat)")
        if not file_path:
            return

        self.console.clear()
        self.console.append("🚀 Loading secure test cases...")

        try:
            secret_key = base64.urlsafe_b64encode(b"UniversityOfTehranAssemblyClass!".ljust(32, b'0'))
            cipher = Fernet(secret_key)

            with open(file_path, "rb") as f:
                encrypted_data = f.read()

            decrypted_data = cipher.decrypt(encrypted_data).decode("utf-8")
            test_cases = json.loads(decrypted_data)
        except Exception:
            self.console.append("❌ Invalid assignment file or it has been tampered with.")
            return

        os_type = platform.system()
        nasm_path, linker_path, blink_path, format_flag = self.get_tool_paths()
        max_time = self.timeout_spinner.value()

        if not os.path.exists(nasm_path) or not os.path.exists(linker_path):
            self.console.append("❌ Critical system error: Evaluation tools were not found.")
            return

        with tempfile.TemporaryDirectory() as temp_dir:
            asm_file = os.path.join(temp_dir, "program.asm")
            obj_file = os.path.join(temp_dir, "program.o")
            exe_file = os.path.join(temp_dir, "program.elf")

            with open(asm_file, "w", encoding="utf-8") as f:
                f.write(code)

            try:
                nasm_res = self._run_cmd([nasm_path, "-f", format_flag, asm_file, "-o", obj_file], timeout=10)
                if nasm_res.returncode != 0:
                    self.console.append("❌ Your code has a syntax error. Please run it normally first.")
                    return
            except Exception:
                self.console.append("❌ Error while running the compiler.")
                return

            try:
                link_res = self._run_cmd([linker_path, "-m", "elf_x86_64", obj_file, "-o", exe_file], timeout=10)
                if link_res.returncode != 0:
                    self.console.append("❌ Your code has a link error.")
                    return
            except Exception:
                self.console.append("❌ Error while running the linker.")
                return

            run_cmd = [blink_path, "-m", "program.elf"] if os_type == "Windows" else ["./program.elf"]
            passed_count = 0
            
            self.console.append(f"🔍 Running {len(test_cases)} hidden tests...\n")

            for i, test in enumerate(test_cases):
                try:
                    res = self._run_cmd(run_cmd, input_text=test.get("input", ""), timeout=max_time, cwd=temp_dir)
                    student_out = (res.stdout or "").strip()
                    expected_out = (test.get("expected_output", "")).strip()

                    if student_out == expected_out:
                        self.console.append(f"✅ Test {i+1} : Passed")
                        passed_count += 1
                    else:
                        self.console.append(f"❌ Test {i+1} : Failed (Wrong Answer)")
                except subprocess.TimeoutExpired:
                    self.console.append(f"⏳ Test {i+1} : Time limit error (more than {max_time} seconds)")
                except Exception:
                    self.console.append(f"⚠️ Test {i+1} : Unexpected runtime error")
            
            self.console.append("-" * 40)
            self.console.append(f"📊 Final result: {passed_count} out of {len(test_cases)} tests passed successfully.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AssemblyZeroConfigIDE()
    window.show()
    sys.exit(app.exec())