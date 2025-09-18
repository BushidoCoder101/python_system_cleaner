import sys
import os
import shutil
import platform
import subprocess
import time
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QLabel, QCheckBox, QProgressBar, QTextEdit, QGroupBox, QGridLayout,
    QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon
import qtawesome as qta

# Import winshell for Windows-specific functions if the OS is Windows
if platform.system() == "Windows":
    import winshell

# Helper function for converting bytes to a human-readable format
def convert_bytes(size_bytes):
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = 0
    while size_bytes >= 1024 and i < len(size_name) - 1:
        size_bytes /= 1024
        i += 1
    return f"{size_bytes:.2f} {size_name[i]}"

# --- QSS (Qt Style Sheet) for a modern, attractive theme ---
STYLE_SHEET = """
/* Main Window & Widgets */
QWidget {
    background-color: #121212;
    color: #f0f0f0;
    font-family: 'Segoe UI', 'Helvetica', sans-serif;
    font-size: 14px;
}

QMainWindow {
    border: none;
    border-radius: 12px;
}

/* Card-like GroupBoxes */
QGroupBox {
    background-color: #1e1e1e;
    border: 1px solid #333333;
    border-radius: 12px;
    margin-top: 18px;
    padding: 20px;
    font-weight: bold;
    color: #4CAF50;
    font-size: 16px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 10px;
    background-color: #1e1e1e;
    border-radius: 5px;
}

/* Buttons */
QPushButton {
    background-color: #2e2e2e;
    border: 2px solid #4CAF50;
    color: #f0f0f0;
    padding: 16px;
    border-radius: 10px;
    font-weight: bold;
    transition: all 0.3s ease;
}

QPushButton:hover {
    background-color: #3e3e3e;
    border-color: #81C784;
}

QPushButton:pressed {
    background-color: #1e1e1e;
}

QPushButton#startButton {
    background-color: #4CAF50;
    font-size: 18px;
    color: #121212;
    border: none;
}

QPushButton#startButton:hover {
    background-color: #5cb85c;
}

QPushButton:disabled {
    background-color: #222222;
    color: #666666;
    border-color: #555555;
}

/* Checkboxes */
QCheckBox {
    spacing: 10px;
}

QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border: 2px solid #555555;
    border-radius: 5px;
    background-color: #2e2e2e;
}

QCheckBox::indicator:hover {
    border-color: #81C784;
}

QCheckBox::indicator:checked {
    background-color: #4CAF50;
    border: 2px solid #4CAF50;
    image: none; /* Reset image to avoid conflicts with icon */
}

/* Progress Bar */
QProgressBar {
    border: 1px solid #333333;
    border-radius: 10px;
    text-align: center;
    color: #f0f0f0;
    height: 30px;
    background-color: #2e2e2e;
}

QProgressBar::chunk {
    background-color: #4CAF50;
    border-radius: 8px;
    margin: 2px;
}

/* Text Edit for Log */
QTextEdit {
    background-color: #121212;
    border: 1px solid #333333;
    border-radius: 10px;
    padding: 15px;
    color: #b0b0b0;
}

/* Scroll Bar Styling */
QScrollBar:vertical {
    background: #1e1e1e;
    width: 14px;
    margin: 0;
    border: none;
}

QScrollBar::handle:vertical {
    background: #4CAF50;
    min-height: 20px;
    border-radius: 7px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}

QMessageBox {
    background-color: #1e1e1e;
    color: #f0f0f0;
}

QMessageBox QPushButton {
    background-color: #4CAF50;
    border: none;
    color: #121212;
    padding: 8px 16px;
}

QMessageBox QLabel {
    color: #f0f0f0;
}
"""

# --- Worker Thread for Cleanup and Analysis Tasks ---
class Worker(QThread):
    log_message = pyqtSignal(str)
    progress_update = pyqtSignal(int)
    task_finished = pyqtSignal()
    
    def __init__(self, tasks_to_run, is_analysis_mode=False):
        super().__init__()
        self.tasks_to_run = tasks_to_run
        self.is_analysis_mode = is_analysis_mode
        self.os_type = platform.system()
        self.analysis_results = {}

    def run(self):
        try:
            total_tasks = len(self.tasks_to_run)
            for i, task_name in enumerate(self.tasks_to_run):
                self.log_message.emit(f"--- Running task: {task_name.replace('_', ' ').title()} ---")
                
                if task_name == "clean_temp_files":
                    size = self.analyze_temp_files() if self.is_analysis_mode else self.clean_temp_files()
                    self.analysis_results["Temporary Files"] = size
                elif task_name == "empty_trash":
                    size = self.analyze_trash() if self.is_analysis_mode else self.empty_trash()
                    self.analysis_results["Recycle Bin / Trash"] = size
                elif task_name == "clean_caches":
                    size = self.analyze_caches() if self.is_analysis_mode else self.clean_caches()
                    self.analysis_results["System & Browser Caches"] = size
                elif task_name == "clean_prefetch":
                    size = self.analyze_prefetch() if self.is_analysis_mode else self.clean_prefetch()
                    self.analysis_results["Prefetch Files"] = size
                elif task_name == "defragment_disk":
                    if not self.is_analysis_mode:
                        self.defragment_disk()
                    else:
                        self.log_message.emit("Defragmentation is an action, not an analysis target.")
                elif task_name == "find_large_old_files":
                    size = self.analyze_large_old_files() if self.is_analysis_mode else self.find_large_old_files()
                    self.analysis_results["Large & Old Files"] = size
                elif task_name == "remove_empty_dirs":
                    if not self.is_analysis_mode:
                        self.remove_empty_dirs()
                    else:
                        self.log_message.emit("Empty directories do not contribute to disk space. No analysis needed.")
                
                progress = int((i + 1) / total_tasks * 100)
                self.progress_update.emit(progress)
                time.sleep(0.5)
            
            if self.is_analysis_mode:
                self.log_message.emit("Analysis finished.")
            else:
                self.log_message.emit("Cleanup process finished.")
        except Exception as e:
            self.log_message.emit(f"An unexpected error occurred: {e}")
        finally:
            self.task_finished.emit()
    
    # --- Analysis Functions ---
    def analyze_temp_files(self):
        temp_dirs = []
        if self.os_type == "Windows":
            temp_dirs.append(os.environ.get('TEMP', ''))
            temp_dirs.append(os.environ.get('TMP', ''))
        elif self.os_type == "Linux":
            temp_dirs.append('/tmp')
        elif self.os_type == "Darwin":
            temp_dirs.append('/tmp')
            temp_dirs.append(os.path.expanduser('~/Library/Caches'))

        total_size = 0
        for temp_path in temp_dirs:
            if not os.path.exists(temp_path):
                continue
            for dirpath, dirnames, filenames in os.walk(temp_path):
                for f in filenames:
                    file_path = os.path.join(dirpath, f)
                    try:
                        total_size += os.path.getsize(file_path)
                    except (PermissionError, FileNotFoundError):
                        continue
        return total_size

    def analyze_trash(self):
        total_size = 0
        try:
            if self.os_type == "Windows":
                for item in winshell.recycle_bin():
                    total_size += item.size
            elif self.os_type == "Linux":
                trash_path = os.path.expanduser('~/.local/share/Trash/files')
                if os.path.exists(trash_path):
                    for dirpath, dirnames, filenames in os.walk(trash_path):
                        for f in filenames:
                            total_size += os.path.getsize(os.path.join(dirpath, f))
            elif self.os_type == "Darwin":
                trash_path = os.path.expanduser('~/.Trash')
                if os.path.exists(trash_path):
                    for dirpath, dirnames, filenames in os.walk(trash_path):
                        for f in filenames:
                            total_size += os.path.getsize(os.path.join(dirpath, f))
        except Exception as e:
            self.log_message.emit(f"Error analyzing trash: {e}")
        return total_size

    def analyze_caches(self):
        cache_paths = []
        if self.os_type == "Windows":
            cache_paths.append(os.path.expanduser('~\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Cache'))
            cache_paths.append(os.path.expanduser('~\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles'))
        elif self.os_type == "Darwin":
            cache_paths.append(os.path.expanduser('~/Library/Caches'))
        elif self.os_type == "Linux":
            cache_paths.append(os.path.expanduser('~/.cache'))
        
        total_size = 0
        for path in cache_paths:
            if not os.path.exists(path):
                continue
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    file_path = os.path.join(dirpath, f)
                    try:
                        total_size += os.path.getsize(file_path)
                    except (PermissionError, FileNotFoundError):
                        continue
        return total_size

    def analyze_prefetch(self):
        if self.os_type != "Windows":
            return 0
        
        prefetch_path = os.path.join(os.environ.get('WINDIR', ''), 'Prefetch')
        total_size = 0
        if not os.path.exists(prefetch_path):
            return 0
        
        for item in os.listdir(prefetch_path):
            if item.endswith('.pf'):
                try:
                    total_size += os.path.getsize(os.path.join(prefetch_path, item))
                except (PermissionError, FileNotFoundError):
                    continue
        return total_size

    def analyze_large_old_files(self):
        cutoff_date = datetime.now() - timedelta(days=30)
        min_size_mb = 100
        start_path = os.path.expanduser('~')
        total_size = 0
        
        for dirpath, dirnames, filenames in os.walk(start_path):
            for f in filenames:
                file_path = os.path.join(dirpath, f)
                try:
                    file_stats = os.stat(file_path)
                    file_mtime = datetime.fromtimestamp(file_stats.st_mtime)
                    file_size_mb = file_stats.st_size / (1024 * 1024)
                    
                    if file_size_mb > min_size_mb and file_mtime < cutoff_date:
                        total_size += file_stats.st_size
                except (PermissionError, FileNotFoundError):
                    continue
        return total_size

    # --- Cleanup Functions ---
    def clean_temp_files(self):
        temp_dirs = []
        if self.os_type == "Windows":
            temp_dirs.append(os.environ.get('TEMP', ''))
            temp_dirs.append(os.environ.get('TMP', ''))
        elif self.os_type == "Linux":
            temp_dirs.append('/tmp')
        elif self.os_type == "Darwin":
            temp_dirs.append('/tmp')
            temp_dirs.append(os.path.expanduser('~/Library/Caches'))

        total_deleted = 0
        for temp_path in temp_dirs:
            if not os.path.exists(temp_path):
                continue
            
            for item in os.listdir(temp_path):
                item_path = os.path.join(temp_path, item)
                try:
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path, ignore_errors=True)
                    else:
                        os.remove(item_path)
                    total_deleted += 1
                except (PermissionError, OSError) as e:
                    self.log_message.emit(f"Permission error deleting {item_path}: {e}")
                except Exception as e:
                    self.log_message.emit(f"Error deleting {item_path}: {e}")
        self.log_message.emit(f"Cleaned {total_deleted} temporary files/directories.")

    def empty_trash(self):
        try:
            if self.os_type == "Windows":
                winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=False)
                self.log_message.emit("Emptied Recycle Bin on Windows.")
            elif self.os_type == "Linux":
                try:
                    subprocess.run(['trash-empty'], check=True, stdout=subprocess.DEVNULL)
                    self.log_message.emit("Emptied Trash via 'trash-empty'.")
                except FileNotFoundError:
                    self.log_message.emit("The 'trash-cli' tool is not installed. Skipping trash empty.")
            elif self.os_type == "Darwin":
                script = 'tell app "Finder" to empty trash'
                subprocess.run(['osascript', '-e', script], check=True, stdout=subprocess.DEVNULL)
                self.log_message.emit("Emptied Trash on macOS.")
        except Exception as e:
            self.log_message.emit(f"Error emptying trash: {e}")

    def clean_caches(self):
        cache_paths = []
        if self.os_type == "Windows":
            cache_paths.append(os.path.expanduser('~\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Cache'))
            cache_paths.append(os.path.expanduser('~\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles'))
        elif self.os_type == "Darwin":
            cache_paths.append(os.path.expanduser('~/Library/Caches'))
        elif self.os_type == "Linux":
            cache_paths.append(os.path.expanduser('~/.cache'))
        
        total_cleaned = 0
        for path in cache_paths:
            if not os.path.exists(path):
                continue
            
            try:
                for item in os.listdir(path):
                    item_path = os.path.join(path, item)
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path, ignore_errors=True)
                    else:
                        os.remove(item_path)
                self.log_message.emit(f"Cleaned cache: {path}")
                total_cleaned += 1
            except Exception as e:
                self.log_message.emit(f"Error cleaning cache {path}: {e}")
        self.log_message.emit(f"Cleaned {total_cleaned} cache directories.")
        
    def clean_prefetch(self):
        if self.os_type != "Windows":
            self.log_message.emit("Skipping Prefetch cleanup. Only available on Windows.")
            return

        prefetch_path = os.path.join(os.environ.get('WINDIR', ''), 'Prefetch')
        if not os.path.exists(prefetch_path):
            self.log_message.emit("Prefetch directory not found.")
            return
        
        total_deleted = 0
        try:
            for item in os.listdir(prefetch_path):
                if item.endswith('.pf'):
                    item_path = os.path.join(prefetch_path, item)
                    try:
                        os.remove(item_path)
                        total_deleted += 1
                    except (PermissionError, OSError) as e:
                        self.log_message.emit(f"Permission error deleting {item_path}: {e}")
            self.log_message.emit(f"Cleaned {total_deleted} Prefetch files.")
        except (PermissionError, OSError) as e:
            self.log_message.emit(f"Permission error accessing Prefetch directory: {e}. Try running as Administrator.")

    def defragment_disk(self):
        if self.os_type != "Windows":
            self.log_message.emit("Skipping disk defragmentation. Only available on Windows (for HDDs).")
            return
        
        self.log_message.emit("Starting disk defragmentation. This may take a while...")
        try:
            subprocess.run(['defrag', 'C:', '/U'], check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            self.log_message.emit("Finished defragmenting C: drive.")
        except Exception as e:
            self.log_message.emit(f"Error during disk defragmentation: {e}")
            self.log_message.emit("Try running the application as Administrator.")

    def find_large_old_files(self):
        cutoff_date = datetime.now() - timedelta(days=30)
        min_size_mb = 100
        start_path = os.path.expanduser('~')
        
        self.log_message.emit("Scanning for large and old files...")
        
        total_found = 0
        for dirpath, dirnames, filenames in os.walk(start_path):
            for f in filenames:
                file_path = os.path.join(dirpath, f)
                try:
                    file_stats = os.stat(file_path)
                    file_mtime = datetime.fromtimestamp(file_stats.st_mtime)
                    file_size_mb = file_stats.st_size / (1024 * 1024)
                    
                    if file_size_mb > min_size_mb and file_mtime < cutoff_date:
                        self.log_message.emit(f"Found: {file_path} ({file_size_mb:.2f} MB, Modified: {file_mtime.date()})")
                        total_found += 1
                except (PermissionError, FileNotFoundError):
                    continue
        
        if total_found > 0:
            self.log_message.emit(f"Found {total_found} large and old files. Consider reviewing and deleting them manually.")
        else:
            self.log_message.emit("No large or old files found matching criteria.")

    def remove_empty_dirs(self):
        start_path = os.path.expanduser('~')
        deleted_count = 0
        self.log_message.emit("Removing empty directories...")

        for dirpath, dirnames, filenames in os.walk(start_path, topdown=False):
            if not dirnames and not filenames:
                try:
                    os.rmdir(dirpath)
                    self.log_message.emit(f"Deleted empty directory: {dirpath}")
                    deleted_count += 1
                except OSError as e:
                    self.log_message.emit(f"Could not delete {dirpath}: {e}")
        
        self.log_message.emit(f"Removed {deleted_count} empty directories.")

# --- Main Application Window ---
class CleanupApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Advanced System Cleanup Utility")
        self.setGeometry(100, 100, 800, 700)
        self.setMinimumSize(600, 500)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.worker = None

        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet(STYLE_SHEET)
        self.setWindowIcon(qta.icon('fa5s.broom', color='#4CAF50'))

        header_layout = QGridLayout()
        header_icon_label = QLabel()
        header_icon_label.setPixmap(qta.icon('fa5s.cogs', color='#4CAF50').pixmap(50, 50))
        header_label = QLabel("Advanced System Cleanup")
        header_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #4CAF50;")
        header_layout.addWidget(header_icon_label, 0, 0, alignment=Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(header_label, 0, 1, alignment=Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addLayout(header_layout)

        content_layout = QGridLayout()
        content_layout.setContentsMargins(20, 0, 20, 20)
        content_layout.setHorizontalSpacing(20)
        content_layout.setVerticalSpacing(20)
        self.main_layout.addLayout(content_layout)

        options_group = QGroupBox("Cleanup Options")
        options_layout = QVBoxLayout()
        options_group.setLayout(options_layout)

        self.temp_check = QCheckBox(" Clean Temporary Files")
        self.temp_check.setIcon(qta.icon('fa5s.fire-extinguisher', color='white'))
        self.trash_check = QCheckBox(" Empty Recycle Bin / Trash")
        self.trash_check.setIcon(qta.icon('fa5s.trash-alt', color='white'))
        self.cache_check = QCheckBox(" Clean System & Browser Caches")
        self.cache_check.setIcon(qta.icon('fa5s.database', color='white'))
        self.prefetch_check = QCheckBox(" Clean Prefetch Files (Windows Only)")
        self.prefetch_check.setIcon(qta.icon('fa5s.bolt', color='white'))
        self.defrag_check = QCheckBox(" Defragment Disk (Windows HDD Only)")
        self.defrag_check.setIcon(qta.icon('fa5s.retweet', color='white'))
        self.large_old_check = QCheckBox(" Find Large & Old Files")
        self.large_old_check.setIcon(qta.icon('fa5s.search', color='white'))
        self.empty_dirs_check = QCheckBox(" Remove Empty Directories")
        self.empty_dirs_check.setIcon(qta.icon('fa5s.folder-minus', color='white'))

        self.temp_check.setChecked(True)
        self.trash_check.setChecked(True)
        self.cache_check.setChecked(True)

        options_layout.addWidget(self.temp_check)
        options_layout.addWidget(self.trash_check)
        options_layout.addWidget(self.cache_check)
        options_layout.addWidget(self.prefetch_check)
        options_layout.addWidget(self.defrag_check)
        options_layout.addWidget(self.large_old_check)
        options_layout.addWidget(self.empty_dirs_check)
        options_layout.addStretch()
        
        content_layout.addWidget(options_group, 0, 0, 1, 1)

        status_group = QGroupBox("Status & Controls")
        status_layout = QVBoxLayout()
        status_group.setLayout(status_layout)
        
        self.status_label = QLabel("Ready to start cleanup.")
        self.status_label.setStyleSheet("font-weight: bold; font-size: 16px; margin-bottom: 10px;")
        
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p%")

        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.progress_bar)
        
        self.analyze_button = QPushButton(" Analyze System")
        self.analyze_button.setIcon(qta.icon('fa5s.chart-bar', color='#121212'))
        self.analyze_button.setObjectName("analyzeButton")
        self.analyze_button.clicked.connect(self.analyze_system)
        
        self.start_button = QPushButton(" Start Cleanup")
        self.start_button.setIcon(qta.icon('fa5s.play-circle', color='#121212'))
        self.start_button.setObjectName("startButton")
        self.start_button.clicked.connect(self.start_cleanup)

        button_layout = QGridLayout()
        button_layout.addWidget(self.analyze_button, 0, 0)
        button_layout.addWidget(self.start_button, 0, 1)
        status_layout.addLayout(button_layout)
        status_layout.addStretch()
        
        content_layout.addWidget(status_group, 0, 1, 1, 1)

        log_group = QGroupBox("Action Log")
        log_layout = QVBoxLayout()
        log_group.setLayout(log_layout)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        self.main_layout.addWidget(log_group)
        
        self.log_message("Advanced System Cleanup Utility initialized.")
        self.log_message(f"Detected OS: {platform.system()}")

    def get_selected_tasks(self):
        tasks_to_run = []
        if self.temp_check.isChecked():
            tasks_to_run.append("clean_temp_files")
        if self.trash_check.isChecked():
            tasks_to_run.append("empty_trash")
        if self.cache_check.isChecked():
            tasks_to_run.append("clean_caches")
        if self.prefetch_check.isChecked():
            tasks_to_run.append("clean_prefetch")
        if self.defrag_check.isChecked():
            tasks_to_run.append("defragment_disk")
        if self.large_old_check.isChecked():
            tasks_to_run.append("find_large_old_files")
        if self.empty_dirs_check.isChecked():
            tasks_to_run.append("remove_empty_dirs")
        return tasks_to_run

    def log_message(self, message):
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        formatted_message = f"{timestamp} {message}\n"
        self.log_text.insertPlainText(formatted_message)
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

    def analyze_system(self):
        self.start_button.setDisabled(True)
        self.analyze_button.setDisabled(True)
        self.status_label.setText("Analyzing system... 🔍")
        self.log_text.clear()
        
        tasks_to_analyze = self.get_selected_tasks()
        
        self.worker = Worker(tasks_to_analyze, is_analysis_mode=True)
        self.worker.log_message.connect(self.log_message)
        self.worker.progress_update.connect(self.progress_bar.setValue)
        self.worker.task_finished.connect(self.on_analysis_finished)
        self.worker.start()

    def on_analysis_finished(self):
        self.start_button.setDisabled(False)
        self.analyze_button.setDisabled(False)
        self.status_label.setText("Analysis complete.")
        self.progress_bar.setValue(100)
        
        results = self.worker.analysis_results
        
        total_size = sum(results.values())
        formatted_size = convert_bytes(total_size)
        
        report_message = "Analysis Report:\n\n"
        for task, size in results.items():
            if size > 0:
                report_message += f"  - {task}: {convert_bytes(size)}\n"

        if total_size > 0:
            report_message += f"\nTotal Potential Space Savings: {formatted_size} 💾"
            self.log_message(report_message)
            QMessageBox.information(self, "Analysis Complete", report_message)
        else:
            self.log_message("No junk files found in selected categories.")
            QMessageBox.information(self, "Analysis Complete", "No junk files found in selected categories.")
            
        self.worker = None

    def start_cleanup(self):
        tasks_to_run = self.get_selected_tasks()
        
        if not tasks_to_run:
            QMessageBox.warning(self, "No Tasks Selected", "Please select at least one cleanup task to run.")
            return

        self.start_button.setDisabled(True)
        self.analyze_button.setDisabled(True)
        self.start_button.setText(" Cleaning...")
        self.start_button.setIcon(qta.icon('fa5s.sync-alt', color='#121212', animation=qta.Spin(self.start_button)))

        self.progress_bar.setValue(0)
        self.log_text.clear()
        self.log_message("Starting cleanup process...")
        self.status_label.setText("Cleaning is in progress... ⏳")

        self.worker = Worker(tasks_to_run)
        self.worker.log_message.connect(self.log_message)
        self.worker.progress_update.connect(self.progress_bar.setValue)
        self.worker.task_finished.connect(self.on_cleanup_finished)
        self.worker.start()

    def on_cleanup_finished(self):
        self.log_message("Cleanup process finished.")
        self.status_label.setText("Cleanup complete! System is optimized. ✨")
        self.start_button.setDisabled(False)
        self.analyze_button.setDisabled(False)
        self.start_button.setText(" Start Cleanup")
        self.start_button.setIcon(qta.icon('fa5s.play-circle', color='#121212'))
        self.progress_bar.setValue(100)
        self.worker = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CleanupApp()
    window.show()
    sys.exit(app.exec())