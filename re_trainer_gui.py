#!/usr/bin/env python3
# qvert_trainer.py v5.0 - QVERT || ROCm RE Trainer (HIP+Vulkan)
# GOLDEN RULE: TRUE 1-CLICK EXPERIENCE - ZERO MANUAL STEPS
import os, sys, json, hashlib, shutil, subprocess, threading, datetime, tempfile, glob, re, importlib.util, platform
from pathlib import Path
from typing import Optional, Callable, Dict, List, Any

# ============================================
# PROJECT BRANDING
# ============================================
PROJECT_NAME = "QVERT"
PROJECT_VERSION = "5.0"
PROJECT_TAGLINE = "ROCm RE Trainer"

# ============================================
# BANNER & LOGGING
# ============================================
def print_banner():
    print(f"\n{'='*70}")
    print(f"  ██████╗ ██╗   ██╗██╗   ██╗███████╗██████╗ ████████╗")
    print(f" ██╔═══██╗██║   ██║██║   ██║██╔════╝██╔══██╗╚══██╔══╝")
    print(f" ██║   ██║██║   ██║██║   ██║█████╗  ██████╔╝   ██║   ")
    print(f" ██║▄▄ ██║╚██╗ ██╔╝██║   ██║██╔══╝  ██╔══██╗   ██║   ")
    print(f" ╚██████╔╝ ╚████╔╝ ╚██████╔╝███████╗██║  ██║   ██║   ")
    print(f"  ╚══▀▀═╝   ╚═══╝   ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝   ")
    print(f"  ││ ROCm RE Trainer v5.0 ││ True 1-Click Experience")
    print(f"{'='*70}\n")

print_banner()

# ============================================
# INTELLIGENT DEPENDENCY MANAGEMENT
# ============================================
def get_python_info():
    """Gather comprehensive Python environment info"""
    return {
        'executable': sys.executable,
        'version': f"{sys.version_info.major}.{sys.version_info.minor}",
        'in_venv': (hasattr(sys, 'real_prefix') or 
                   (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)),
        'platform': platform.system(),
        'machine': platform.machine()
    }

def check_package_installed(package_name):
    """Check if package exists WITHOUT importing (avoids side effects)"""
    try:
        spec = importlib.util.find_spec(package_name.replace("-", "_"))
        return spec is not None
    except:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "show", package_name],
                capture_output=True, timeout=10
            )
            return result.returncode == 0
        except:
            return False

def get_pip_install_cmd(package_name, py_info):
    """Generate optimal pip install command with multiple fallback strategies"""
    cmd = [sys.executable, "-m", "pip", "install", package_name, "-q"]
    cmd.append("--no-cache-dir")
    cmd.extend(["--retries", "5", "--timeout", "300"])
    
    if package_name == 'torch':
        rocm_paths = ['/opt/rocm', '/usr/lib/rocm', '/opt/amdgpu']
        rocm_version = "6.0"
        for path in rocm_paths:
            if os.path.exists(path):
                version_file = os.path.join(path, 'include', 'rocm-core', 'rocm_version.txt')
                if os.path.exists(version_file):
                    with open(version_file) as f:
                        rocm_version = f.read().strip()[:3]
                    break
        cmd = [
            sys.executable, "-m", "pip", "install",
            "torch", "torchvision", "torchaudio",
            "--index-url", f"https://download.pytorch.org/whl/rocm{rocm_version}",
            "--no-cache-dir", "--retries", "5", "--timeout", "300"
        ]
    
    elif package_name == 'unsloth':
        cmd = [
            sys.executable, "-m", "pip", "install",
            "unsloth @ git+https://github.com/unslothai/unsloth.git",
            "--no-cache-dir", "--retries", "5", "--timeout", "300"
        ]
    
    return cmd

def install_with_progress(package_name, display_name=None):
    """Install package with detailed progress output and 3-layer fallback"""
    if display_name is None:
        display_name = package_name
    
    py_info = get_python_info()
    
    print(f"\n{'='*65}")
    print(f"[>] Installing {display_name}...")
    print(f"{'='*65}")
    
    cmd = get_pip_install_cmd(package_name, py_info)
    print(f"[>] Method 1: Standard install")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode == 0:
            print(f"[✓] {display_name} installed successfully")
            return True
        print(f"[!] Method 1 failed: {result.stderr[:200]}")
    except subprocess.TimeoutExpired:
        print(f"[!] Method 1 timed out (600s)")
    except Exception as e:
        print(f"[!] Method 1 error: {e}")
    
    print(f"\n{'='*65}")
    print(f"[>] Method 2: Adding --break-system-packages flag...")
    cmd.append("--break-system-packages")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode == 0:
            print(f"[✓] {display_name} installed successfully")
            return True
        print(f"[!] Method 2 failed: {result.stderr[:200]}")
    except Exception as e:
        print(f"[!] Method 2 error: {e}")
    
    print(f"\n{'='*65}")
    print(f"[>] Method 3: Upgrading pip first...")
    
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pip", "-q"],
            capture_output=True, timeout=120
        )
        print(f"[>] Pip upgraded, retrying {display_name}...")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode == 0:
            print(f"[✓] {display_name} installed successfully")
            return True
        print(f"[!] Method 3 failed: {result.stderr[:200]}")
    except Exception as e:
        print(f"[!] Method 3 error: {e}")
    
    print(f"\n{'='*65}")
    print(f"[❌] CRITICAL: Failed to install {display_name}")
    print(f"{'='*65}\n")
    return False

def ensure_all_dependencies():
    """Install ALL required packages automatically with progress tracking"""
    critical_packages = [('PyQt6', 'PyQt6')]
    ml_packages = [
        ('torch', 'PyTorch (ROCm)'),
        ('unsloth', 'Unsloth (LoRA)'),
        ('transformers', 'Transformers'),
        ('peft', 'PEFT'),
        ('datasets', 'Datasets'),
        ('trl', 'TRL'),
        ('accelerate', 'Accelerate'),
        ('huggingface_hub', 'HuggingFace Hub'),
    ]
    all_packages = critical_packages + ml_packages
    failed = []
    
    print(f"\n{'='*70}")
    print(f"📦 DEPENDENCY CHECK - {len(all_packages)} packages to verify")
    print(f"{'='*70}")
    
    missing = []
    for import_name, display_name in all_packages:
        if check_package_installed(import_name):
            print(f"[✓] {display_name:30s} - Already installed")
        else:
            print(f"[✗] {display_name:30s} - Missing")
            missing.append((import_name, display_name))
    
    if not missing:
        print(f"\n{'='*70}")
        print(f"✅ ALL DEPENDENCIES SATISFIED - Launching {PROJECT_NAME}...")
        print(f"{'='*70}\n")
        return True
    
    print(f"\n{'='*70}")
    print(f"⚠️  {len(missing)} package(s) need installation")
    print(f"{'='*70}")
    print(f"\n{PROJECT_NAME} will now auto-install missing packages.")
    print(f"This may take 10-30 minutes depending on your connection.\n")
    print(f"[>] Auto-proceeding with installation in 3 seconds...")
    threading.Event().wait(3)
    
    for import_name, display_name in missing:
        success = install_with_progress(import_name, display_name)
        if not success:
            failed.append(display_name)
            print(f"\n{'='*70}")
            print(f"[❌] Installation failed for {display_name}")
            print(f"{'='*70}")
            
            if import_name == 'PyQt6':
                print(f"\n[!!!] CRITICAL: PyQt6 is required for GUI")
                print(f"[!!!] Please run manually: pip install PyQt6\n")
                return False
            
            print(f"\n[⚠️]  {display_name} installation failed")
            print(f"[⚠️]  Training features may be limited\n")
            response = input(f"Continue anyway? (y/n): ").strip().lower()
            if response != 'y':
                return False
    
    if failed:
        print(f"\n{'='*70}")
        print(f"⚠️  WARNING: Some packages failed to install: {', '.join(failed)}")
        print(f"{'='*70}")
        if 'PyQt6' not in failed:
            print(f"\n[>] Launching with limited functionality...\n")
            return True
        return False
    
    print(f"\n{'='*70}")
    print(f"✅ ALL DEPENDENCIES INSTALLED SUCCESSFULLY")
    print(f"{'='*70}")
    print(f"\n[>] Restarting {PROJECT_NAME} with fresh imports...\n")
    os.execv(sys.executable, [sys.executable] + sys.argv)
    return True

if not ensure_all_dependencies():
    print(f"\n{'='*70}")
    print(f"[❌] {PROJECT_NAME} cannot start due to missing dependencies")
    print(f"{'='*70}\n")
    sys.exit(1)

# ============================================
# IMPORTS (After successful dependency install)
# ============================================
try:
    from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                                 QGridLayout, QLabel, QLineEdit, QPushButton, QComboBox, 
                                 QCheckBox, QScrollArea, QFrame, QProgressBar, QTextEdit, 
                                 QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
                                 QMessageBox, QFileDialog, QSizePolicy, QSpacerItem, QGroupBox,
                                 QStatusBar, QSplitter, QToolBar, QMenu, QSystemTrayIcon)
    from PyQt6.QtGui import QFont, QColor, QIcon, QPainter, QPainterPath, QLinearGradient, QCursor, QDesktopServices, QPalette, QBrush, QAction
    from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QUrl
    PYQT_AVAILABLE = True
except ImportError as e:
    print(f"[❌] PyQt6 import failed after installation: {e}")
    print(f"[>] This should not happen. Please report this bug.")
    sys.exit(1)

# ============================================
# QVERT DARK THEME CONSTANTS
# ============================================
BG_DARK = "#0a0e27"
BG_PANEL = "#1a1f2e"
BG_CARD = "#162032"
BG_HOVER = "#1f2940"
ACCENT_CYAN = "#00d4ff"
ACCENT_BLUE = "#00b4d8"
TEXT_PRIMARY = "#e0e6ed"
TEXT_SECONDARY = "#94a3b8"
SUCCESS = "#10b981"
WARNING = "#f59e0b"
ERROR = "#ef4444"
BORDER_GLOW = "rgba(0, 212, 255, 0.3)"

# ============================================
# QSS STYLESHEET (Qvert Professional Theme)
# ============================================
QVERT_QSS = f"""
QWidget {{
    background-color: {BG_DARK};
    color: {TEXT_PRIMARY};
    font-family: "Segoe UI", "Inter", system-ui, sans-serif;
    font-size: 10pt;
}}
QMainWindow {{ background-color: {BG_DARK}; }}
QTabWidget::pane {{
    border: 1px solid {BG_PANEL};
    border-radius: 8px;
    background-color: {BG_DARK};
}}
QTabBar::tab {{
    background-color: {BG_PANEL};
    color: {TEXT_SECONDARY};
    padding: 12px 24px;
    margin-right: 2px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    min-width: 120px;
}}
QTabBar::tab:selected {{
    background-color: {BG_CARD};
    color: {ACCENT_CYAN};
    border-bottom: 2px solid {ACCENT_CYAN};
}}
QTabBar::tab:hover:!selected {{
    background-color: {BG_HOVER};
    color: {TEXT_PRIMARY};
}}
QPushButton {{
    background-color: {ACCENT_CYAN};
    color: {BG_DARK};
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    font-weight: bold;
    font-size: 10pt;
}}
QPushButton:hover {{ background-color: {ACCENT_BLUE}; }}
QPushButton:pressed {{ background-color: #0891b2; }}
QPushButton:disabled {{
    background-color: {BG_PANEL};
    color: {TEXT_SECONDARY};
}}
QPushButton#workflowBtn {{
    background-color: {BG_CARD};
    border: 2px solid {TEXT_SECONDARY};
    color: {TEXT_SECONDARY};
    padding: 15px;
    min-width: 100px;
    min-height: 80px;
    border-radius: 8px;
}}
QPushButton#workflowBtn:hover {{
    border-color: {ACCENT_CYAN};
    background-color: {BG_HOVER};
}}
QPushButton#workflowBtn#active {{
    border-color: {ACCENT_CYAN};
    background-color: #1a2a4a;
    color: {ACCENT_CYAN};
}}
QPushButton#workflowBtn#complete {{
    border-color: {SUCCESS};
    background-color: #1a3a2a;
    color: {SUCCESS};
}}
QPushButton#workflowBtn#error {{
    border-color: {ERROR};
    background-color: #3a1a1a;
    color: {ERROR};
}}
QLineEdit {{
    background-color: {BG_CARD};
    border: 1px solid {BG_PANEL};
    border-radius: 6px;
    padding: 8px 12px;
    color: {TEXT_PRIMARY};
    selection-background-color: {ACCENT_CYAN};
    selection-color: {BG_DARK};
}}
QLineEdit:focus {{ border: 1px solid {ACCENT_CYAN}; }}
QLineEdit:hover {{ border: 1px solid {BG_HOVER}; }}
QComboBox {{
    background-color: {BG_CARD};
    border: 1px solid {BG_PANEL};
    border-radius: 6px;
    padding: 8px 12px;
    color: {TEXT_PRIMARY};
    min-height: 35px;
}}
QComboBox:hover {{ border: 1px solid {BG_HOVER}; }}
QComboBox:focus {{ border: 1px solid {ACCENT_CYAN}; }}
QComboBox::drop-down {{ border: none; width: 30px; }}
QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {ACCENT_CYAN};
    margin-right: 10px;
}}
QComboBox QAbstractItemView {{
    background-color: {BG_CARD};
    border: 1px solid {BG_PANEL};
    selection-background-color: {ACCENT_CYAN};
    selection-color: {BG_DARK};
}}
QCheckBox {{
    color: {TEXT_PRIMARY};
    spacing: 8px;
    padding: 5px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid {BG_PANEL};
    background-color: {BG_CARD};
}}
QCheckBox::indicator:checked {{
    background-color: {ACCENT_CYAN};
    border-color: {ACCENT_CYAN};
}}
QCheckBox::indicator:hover {{ border-color: {ACCENT_CYAN}; }}
QScrollArea {{ border: none; background-color: transparent; }}
QScrollBar:vertical {{
    background-color: {BG_PANEL};
    width: 10px;
    border-radius: 5px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background-color: {BG_CARD};
    border-radius: 5px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{ background-color: {BG_HOVER}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QTableWidget {{
    background-color: {BG_CARD};
    alternate-background-color: {BG_PANEL};
    border: 1px solid {BG_PANEL};
    border-radius: 8px;
    gridline-color: {BG_PANEL};
    color: {TEXT_PRIMARY};
}}
QTableWidget::item {{ padding: 8px; border: none; }}
QTableWidget::item:selected {{
    background-color: {ACCENT_CYAN};
    color: {BG_DARK};
}}
QHeaderView::section {{
    background-color: {BG_PANEL};
    color: {ACCENT_CYAN};
    padding: 10px;
    border: none;
    border-bottom: 2px solid {BG_CARD};
    font-weight: bold;
    font-size: 10pt;
}}
QLabel {{
    color: {TEXT_PRIMARY};
    background-color: transparent;
}}
QLabel#titleLabel {{
    font-size: 14pt;
    font-weight: bold;
    color: {ACCENT_CYAN};
}}
QLabel#sectionLabel {{
    font-size: 11pt;
    font-weight: bold;
    color: {ACCENT_CYAN};
}}
QLabel#secondaryLabel {{
    color: {TEXT_SECONDARY};
    font-size: 9pt;
}}
QTextEdit#logConsole {{
    background-color: #0f1419;
    border: 1px solid {BG_PANEL};
    border-radius: 8px;
    color: {ACCENT_CYAN};
    font-family: "Consolas", "Monaco", monospace;
    font-size: 10pt;
    padding: 10px;
}}
QFrame#card {{
    background-color: {BG_CARD};
    border: 1px solid {BG_PANEL};
    border-radius: 8px;
}}
QFrame#panel {{
    background-color: {BG_PANEL};
    border: 1px solid {BG_DARK};
    border-radius: 8px;
}}
QGroupBox {{
    font-weight: bold;
    color: {ACCENT_CYAN};
    border: 2px solid {BG_PANEL};
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
    color: {ACCENT_CYAN};
}}
QProgressBar {{
    background-color: {BG_PANEL};
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: center;
}}
QProgressBar::chunk {{
    background-color: {ACCENT_CYAN};
    border-radius: 4px;
}}
QToolTip {{
    background-color: {BG_CARD};
    color: {ACCENT_CYAN};
    border: 1px solid {ACCENT_CYAN};
    border-radius: 4px;
    padding: 8px;
    font-size: 9pt;
}}
QStatusBar {{
    background-color: {BG_PANEL};
    color: {TEXT_SECONDARY};
    border-top: 1px solid {BG_DARK};
}}
QMenuBar {{
    background-color: {BG_PANEL};
    color: {TEXT_PRIMARY};
}}
QMenuBar::item:selected {{ background-color: {BG_HOVER}; }}
QMenu {{
    background-color: {BG_CARD};
    border: 1px solid {BG_PANEL};
}}
QMenu::item:selected {{
    background-color: {ACCENT_CYAN};
    color: {BG_DARK};
}}
"""

# ============================================
# DATA STRUCTURES
# ============================================
HARDWARE_DATA = [
    {"GPU": "RX 7900 XTX/XT", "VRAM": "24GB", "ROCm": "6.0+", "Arch": "RDNA3", "Notes": "Official Support (gfx1100)"},
    {"GPU": "RX 7800/7700", "VRAM": "16-12GB", "ROCm": "6.0+", "Arch": "RDNA3", "Notes": "Official Support (gfx1100)"},
    {"GPU": "RX 6900/6800", "VRAM": "16GB", "ROCm": "6.0+", "Arch": "RDNA2", "Notes": "Unofficial (gfx1030)"},
    {"GPU": "RX 6700 XT", "VRAM": "12GB", "ROCm": "6.0+", "Arch": "RDNA2", "Notes": "Unofficial (gfx1030)"},
    {"GPU": "Instinct MI300", "VRAM": "192GB", "ROCm": "6.0+", "Arch": "CDNA3", "Notes": "Full Datacenter Support"},
    {"GPU": "Instinct MI250", "VRAM": "128GB", "ROCm": "5.6+", "Arch": "CDNA2", "Notes": "Full Datacenter Support"},
]

WORKFLOW_STEPS = [
    {"id": 0, "name": "Setup", "desc": "Build llama.cpp with HIP/Vulkan backend", "icon": "⚙️"},
    {"id": 1, "name": "Prep", "desc": "Prepare REx86 dataset for training", "icon": "📊"},
    {"id": 2, "name": "Train", "desc": "Fine-tune LoRA adapters on ROCm GPUs", "icon": "🎯"},
    {"id": 3, "name": "Merge", "desc": "Merge LoRA adapters with base model", "icon": "🔗"},
    {"id": 4, "name": "Export", "desc": "Convert to GGUF and quantize", "icon": "📦"},
    {"id": 5, "name": "Infer", "desc": "Run inference on merged model", "icon": "🚀"},
]

# ============================================
# CONFIG MANAGER
# ============================================
class ConfigManager:
    def __init__(self, path="qvert_config.json"):
        self.path = path
        self.defaults = {
            "hf_token": os.getenv("HF_TOKEN", ""), 
            "base_model": "Qwen/Qwen2.5-Coder-7B-Instruct",
            "rex86_path": "./REx86", 
            "dataset_path": "./dataset/re_dataset.jsonl",
            "adapter_path": "./re_lora_adapter", 
            "merged_path": "./merged_re_model",
            "gguf_path": "./re_model_q4.gguf", 
            "llama_cpp_path": "./llama.cpp",
            "batch_size": 8, 
            "max_steps": 600, 
            "lr": "2e-4", 
            "seq_len": 8192,
            "gfx_version": "11.0.0", 
            "dry_run": False,
            "inference_backend": "HIP (ROCm)"
        }
        self.data = self.load()
    
    def load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path) as f:
                    loaded = json.load(f)
                    merged = {**self.defaults, **loaded}
                    return self.validate_config(merged)
            except Exception as e:
                print(f"[!] Config load failed: {e}")
        backup_path = self.path + ".backup"
        if os.path.exists(backup_path):
            try:
                print("[>] Loading from backup config...")
                with open(backup_path) as f:
                    return self.validate_config({**self.defaults, **json.load(f)})
            except: pass
        print("[>] Using default configuration")
        return self.defaults.copy()
    
    def validate_config(self, cfg):
        for key, default in self.defaults.items():
            if key not in cfg:
                cfg[key] = default
            elif type(cfg[key]) != type(default):
                try:
                    cfg[key] = type(default)(cfg[key])
                except:
                    cfg[key] = default
        return cfg
    
    def save(self):
        try:
            if os.path.exists(self.path):
                shutil.copy2(self.path, self.path + ".backup")
            tmp = self.path + ".tmp"
            with open(tmp, "w") as f:
                json.dump(self.data, f, indent=2)
            shutil.move(tmp, self.path)
            self.version_commit()
            return True
        except Exception as e:
            print(f"[!] Config save failed: {e}")
            if os.path.exists(self.path + ".backup"):
                shutil.copy2(self.path + ".backup", self.path)
            return False
    
    def version_commit(self):
        try:
            if not os.path.exists(".git"):
                subprocess.run(["git","init"], check=True, capture_output=True, timeout=5)
            if not os.path.exists(".gitignore"):
                with open(".gitignore","w") as f:
                    f.write("*.tmp\n__pycache__/\n*.gguf\n*.bin\n*.safetensors\n.venv/\nmodels/\n*.backup\n")
            subprocess.run(["git","add", self.path, ".gitignore"], check=True, capture_output=True, timeout=5)
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            subprocess.run(["git","commit","-m",f"{PROJECT_NAME} Config {ts}"], check=True, capture_output=True, timeout=5)
        except Exception as e:
            print(f"[!] Git versioning failed (non-critical): {e}")

# ============================================
# WORKER THREAD
# ============================================
class WorkerThread(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    progress_signal = pyqtSignal(int)
    
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.max_retries = 3
    
    def run(self):
        for attempt in range(self.max_retries):
            try:
                self.func(*self.args, **self.kwargs, log_cb=self.log_signal.emit)
                self.finished_signal.emit(True, "Completed")
                return
            except Exception as e:
                if attempt < self.max_retries - 1:
                    self.log_signal.emit(f"[!] Attempt {attempt + 1} failed, retrying...")
                    self.msleep(1000)
                else:
                    self.finished_signal.emit(False, str(e))
                    return

# ============================================
# CUSTOM WIDGETS
# ============================================
class GlowButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
    def enterEvent(self, event):
        super().enterEvent(event)

class WorkflowStepButton(QPushButton):
    def __init__(self, step_data, parent=None):
        super().__init__(parent)
        self.step_id = step_data["id"]
        self.step_name = step_data["name"]
        self.step_icon = step_data["icon"]
        self.step_desc = step_data["desc"]
        self.setObjectName("workflowBtn")
        self.setFixedSize(120, 100)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setToolTip(step_data["desc"])
        self.update_display("pending")
        
    def update_display(self, status):
        try:
            icons = {"pending": "⏸️", "active": "▶️", "complete": "✅", "error": "❌"}
            self.setProperty("status", status)
            self.setText(f"{icons.get(status, '⏸️')}\n{self.step_id}. {self.step_name}")
            self.style().unpolish(self)
            self.style().polish(self)
        except Exception as e:
            print(f"[!] Button update failed: {e}")

# ============================================
# TABS
# ============================================
class TrainerTab(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.entries = {}
        self.build_ui()
    
    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        config_group = QGroupBox("Configuration")
        config_layout = QGridLayout()
        cfg = self.app.cfg_mgr.data
        row = 0
        for key, value in cfg.items():
            if key in ["dry_run", "inference_backend"]: continue
            label = QLabel(key.replace("_", " ").title())
            label.setObjectName("sectionLabel")
            entry = QLineEdit(str(value))
            entry.setFixedHeight(35)
            config_layout.addWidget(label, row, 0)
            config_layout.addWidget(entry, row, 1)
            self.entries[key] = entry
            row += 1
        self.backend_combo = QComboBox()
        self.backend_combo.addItems(["HIP (ROCm)", "Vulkan"])
        self.backend_combo.setCurrentText(cfg.get("inference_backend", "HIP (ROCm)"))
        config_layout.addWidget(QLabel("Backend"), row, 0)
        config_layout.addWidget(self.backend_combo, row, 1)
        self.dry_run_cb = QCheckBox("Dry Run")
        self.dry_run_cb.setChecked(cfg.get("dry_run", False))
        config_layout.addWidget(self.dry_run_cb, row+1, 0, 1, 2)
        config_group.setLayout(config_layout)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(config_group)
        layout.addWidget(scroll)
        btn_layout = QHBoxLayout()
        for text, sid in [("0. Setup",0), ("1. Prep",1), ("2. Train",2), ("3. Merge",3), ("4. Export",4), ("5. Infer",5)]:
            btn = GlowButton(text)
            btn.clicked.connect(lambda checked, s=sid: self.run_step(s))
            btn_layout.addWidget(btn)
        btn_layout.addStretch()
        save_btn = GlowButton("💾 Save")
        save_btn.clicked.connect(self.save_config)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)
    
    def get_config(self):
        cfg = {k: e.text() for k, e in self.entries.items()}
        cfg["dry_run"] = self.dry_run_cb.isChecked()
        cfg["inference_backend"] = self.backend_combo.currentText()
        return cfg
    
    def run_step(self, step_id):
        cfg = self.get_config()
        self.app.cfg_mgr.data.update(cfg)
        self.app.update_workflow(step_id, "active")
        funcs = {
            0: lambda: self.app.system.ensure_llama_cpp(cfg["llama_cpp_path"], cfg["inference_backend"]),
            1: lambda: self.app.pipeline.prep_data(cfg),
            2: lambda: self.app.pipeline.train_lora(cfg),
            3: lambda: self.app.pipeline.merge_model(cfg),
            4: lambda: self.app.pipeline.export_gguf(cfg),
            5: lambda: self.app.pipeline.infer(cfg),
        }
        worker = WorkerThread(funcs[step_id])
        worker.log_signal.connect(self.app.append_log)
        worker.finished_signal.connect(lambda ok, msg: self.on_step_complete(step_id, ok, msg))
        worker.start()
    
    def on_step_complete(self, step_id, success, msg):
        if success:
            self.app.append_log(f"[✓] Step {step_id} completed")
            self.app.update_workflow(step_id, "complete")
        else:
            self.app.append_log(f"[!] Step {step_id} failed: {msg}")
            self.app.update_workflow(step_id, "error")
            QMessageBox.critical(self, "Error", msg)
    
    def save_config(self):
        self.app.cfg_mgr.data.update(self.get_config())
        self.app.cfg_mgr.save()
        QMessageBox.information(self, "Saved", "Config versioned")

class HubTab(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.build_ui()
    
    def build_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("🌐 Search HuggingFace")
        title.setObjectName("titleLabel")
        layout.addWidget(title)
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("Search models...")
        layout.addWidget(self.search_entry)
        search_btn = GlowButton("🔍 Search")
        search_btn.clicked.connect(self.search_models)
        layout.addWidget(search_btn)
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Model", "Likes", "Private"])
        layout.addWidget(self.table)
        btn_layout = QHBoxLayout()
        dl_btn = GlowButton("⬇️ Download")
        dl_btn.clicked.connect(self.download_model)
        btn_layout.addWidget(dl_btn)
        set_btn = GlowButton("➡️ Set Base")
        set_btn.clicked.connect(self.set_base_model)
        btn_layout.addWidget(set_btn)
        layout.addLayout(btn_layout)
    
    def search_models(self):
        def run():
            try:
                from huggingface_hub import list_models
                models = list(list_models(search=self.search_entry.text(), filter="text-generation", limit=50))
                self.app.main_thread_signal.emit(lambda: self.populate_results(models))
            except Exception as e:
                self.app.append_log(f"[!] Search failed: {e}")
        threading.Thread(target=run, daemon=True).start()
    
    def populate_results(self, models):
        self.table.setRowCount(len(models))
        for i, m in enumerate(models):
            self.table.setItem(i, 0, QTableWidgetItem(m.id))
            self.table.setItem(i, 1, QTableWidgetItem(str(m.likes)))
            self.table.setItem(i, 2, QTableWidgetItem("Yes" if getattr(m, 'private', False) else "No"))
    
    def download_model(self):
        sel = self.table.currentRow()
        if sel < 0: return
        repo_id = self.table.item(sel, 0).text()
        def run():
            try:
                from huggingface_hub import snapshot_download
                path = snapshot_download(repo_id, token=self.app.cfg_mgr.data.get("hf_token"), ignore_patterns=["*.gguf"])
                self.app.append_log(f"[✓] Downloaded: {path}")
            except Exception as e:
                self.app.append_log(f"[!] Download failed: {e}")
        threading.Thread(target=run, daemon=True).start()
    
    def set_base_model(self):
        sel = self.table.currentRow()
        if sel < 0: return
        repo_id = self.table.item(sel, 0).text()
        trainer = self.app.tabs.widget(0)
        trainer.entries["base_model"].setText(repo_id)
        self.app.append_log(f"[✓] Base model set: {repo_id}")
        self.app.tabs.setCurrentIndex(0)

class HardwareTab(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.build_ui()
    
    def build_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("💻 AMD ROCm Compatibility")
        title.setObjectName("titleLabel")
        layout.addWidget(title)
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["GPU", "VRAM", "ROCm", "Arch", "Notes"])
        table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        table.setRowCount(len(HARDWARE_DATA))
        for i, row in enumerate(HARDWARE_DATA):
            for j, key in enumerate(["GPU", "VRAM", "ROCm", "Arch", "Notes"]):
                table.setItem(i, j, QTableWidgetItem(row[key]))
        layout.addWidget(table)

# ============================================
# MAIN WINDOW
# ============================================
class MainWindow(QMainWindow):
    main_thread_signal = pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{PROJECT_NAME} || {PROJECT_TAGLINE} (HIP+Vulkan)")
        self.setMinimumSize(1200, 900)
        self.setStyleSheet(QVERT_QSS)
        self.cfg_mgr = ConfigManager()
        self.system = SystemManager()
        self.pipeline = Pipeline()
        self.init_ui()
        self.append_log(f"[✓] {PROJECT_NAME} v{PROJECT_VERSION} Ready - TRUE 1-CLICK EXPERIENCE")
        self.append_log(f"[Debug] Base Model: {self.cfg_mgr.data.get('base_model')}")
        self.main_thread_signal.connect(lambda fn: fn())
    
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        self.tabs = QTabWidget()
        self.trainer_tab = TrainerTab(self)
        self.hub_tab = HubTab(self)
        self.hw_tab = HardwareTab(self)
        self.tabs.addTab(self.trainer_tab, "🔧 Trainer")
        self.tabs.addTab(self.hub_tab, "🌐 Model Hub")
        self.tabs.addTab(self.hw_tab, "💻 Hardware Info")
        main_layout.addWidget(self.tabs)
        workflow_frame = QFrame()
        workflow_frame.setObjectName("panel")
        workflow_layout = QHBoxLayout(workflow_frame)
        self.workflow_buttons = {}
        for i, step in enumerate(WORKFLOW_STEPS):
            btn = WorkflowStepButton(step)
            btn.clicked.connect(lambda checked, sid=step["id"]: self.on_workflow_click(sid))
            self.workflow_buttons[step["id"]] = btn
            workflow_layout.addWidget(btn)
            if i < len(WORKFLOW_STEPS) - 1:
                arrow = QLabel("→")
                arrow.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 24pt;")
                arrow.setFixedWidth(30)
                workflow_layout.addWidget(arrow)
        main_layout.addWidget(workflow_frame)
        self.workflow_status = QLabel("▶️ Ready")
        self.workflow_status.setObjectName("sectionLabel")
        self.workflow_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.workflow_status)
        self.log_console = QTextEdit()
        self.log_console.setObjectName("logConsole")
        self.log_console.setReadOnly(True)
        self.log_console.setMaximumHeight(200)
        main_layout.addWidget(self.log_console)
    
    def append_log(self, msg):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_console.append(f"[{timestamp}] {msg}")
    
    def update_workflow(self, step_id, status):
        if step_id in self.workflow_buttons:
            self.workflow_buttons[step_id].update_display(status)
            if status == "active":
                self.workflow_status.setText(f"▶️ Running: {WORKFLOW_STEPS[step_id]['name']}")
                self.workflow_status.setStyleSheet(f"color: {WARNING}; font-weight: bold;")
            elif status == "complete":
                self.workflow_status.setText(f"✅ Completed: {WORKFLOW_STEPS[step_id]['name']}")
                self.workflow_status.setStyleSheet(f"color: {SUCCESS};")
            elif status == "error":
                self.workflow_status.setText(f"❌ Error: {WORKFLOW_STEPS[step_id]['name']}")
                self.workflow_status.setStyleSheet(f"color: {ERROR}; font-weight: bold;")
    
    def on_workflow_click(self, step_id):
        QMessageBox.information(self, WORKFLOW_STEPS[step_id]["name"], WORKFLOW_STEPS[step_id]["desc"])

# ============================================
# SYSTEM MANAGER
# ============================================
class SystemManager:
    @staticmethod
    def ensure_llama_cpp(path, backend, log_cb=None):
        build_dir = f"{path}/build"
        marker_file = f"{build_dir}/.backend_marker"
        rebuild = not os.path.exists(f"{build_dir}/bin/main")
        if os.path.exists(marker_file):
            with open(marker_file, 'r') as f:
                if f.read().strip() != backend: rebuild = True
        if not rebuild:
            if log_cb: log_cb("[✓] llama.cpp already built")
            return
        if os.path.exists(build_dir): shutil.rmtree(build_dir)
        os.makedirs(build_dir, exist_ok=True)
        if not os.path.exists(f"{path}/.git"):
            if log_cb: log_cb("[>] Cloning llama.cpp...")
            subprocess.run(["git", "clone", "--depth=1", "https://github.com/ggerganov/llama.cpp", path], check=True, timeout=300)
        flags = ["-DGGML_HIPBLAS=1"] if "HIP" in backend else ["-DGGML_VULKAN=1"]
        if "HIP" in backend:
            flags.extend(["-DCMAKE_C_COMPILER=/opt/rocm/llvm/bin/clang", "-DCMAKE_CXX_COMPILER=/opt/rocm/llvm/bin/clang++"])
        if log_cb: log_cb(f"[>] Compiling ({backend})...")
        subprocess.run(["cmake", ".."] + flags, cwd=build_dir, check=True, timeout=300)
        subprocess.run(["make", "-j", str(os.cpu_count() or 4)], cwd=build_dir, check=True, timeout=600)
        with open(marker_file, 'w') as f: f.write(backend)
        if log_cb: log_cb(f"[✓] llama.cpp built for {backend}")

# ============================================
# PIPELINE
# ============================================
class Pipeline:
    def prep_data(self, cfg, log_cb=None):
        if cfg.get("dry_run"): return
        os.makedirs(os.path.dirname(cfg["dataset_path"]), exist_ok=True)
        count = 0
        with open(cfg["dataset_path"], "w") as out:
            for f in glob.glob(os.path.join(cfg["rex86_path"], "*.json")):
                if "inspect" in f: continue
                data = json.load(open(f))
                items = data if isinstance(data, list) else [data]
                for item in items:
                    prompt = f"{item.get('instruction','')}\n\n{item.get('input','')}"
                    resp = item.get('output','')
                    if prompt and resp:
                        out.write(json.dumps({"instruction": prompt, "output": resp}) + "\n")
                        count += 1
        if log_cb: log_cb(f"[✓] Prepared {count} samples")
    
    def train_lora(self, cfg, log_cb=None):
        """KEY: ROCm env vars set BEFORE unsloth import"""
        if cfg.get("dry_run"): return
        os.environ["HF_TOKEN"] = cfg["hf_token"]
        os.environ["HSA_OVERRIDE_GFX_VERSION"] = cfg["gfx_version"]
        os.environ["HIP_VISIBLE_DEVICES"] = "0,1"
        os.environ["PYTORCH_ROCM_ARCH"] = "gfx1100"
        if log_cb: log_cb(f"[>] Loading {cfg['base_model']}...")
        import unsloth
        from unsloth import FastLanguageModel
        from trl import SFTTrainer
        from transformers import TrainingArguments
        from datasets import load_dataset
        import torch
        model, tok = FastLanguageModel.from_pretrained(cfg["base_model"], max_seq_length=int(cfg["seq_len"]), load_in_4bit=True, trust_remote_code=True)
        model = FastLanguageModel.get_peft_model(model, r=16, lora_alpha=16, target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"])
        ds = load_dataset("json", data_files=cfg["dataset_path"], split="train")
        trainer = SFTTrainer(model=model, tokenizer=tok, train_dataset=ds, dataset_text_field="output", max_seq_length=int(cfg["seq_len"]),
            args=TrainingArguments(per_device_train_batch_size=int(cfg["batch_size"]), gradient_accumulation_steps=2, max_steps=int(cfg["max_steps"]),
            learning_rate=float(cfg["lr"]), fp16=not torch.cuda.is_bf16_supported(), bf16=torch.cuda.is_bf16_supported(),
            output_dir=cfg["adapter_path"], optim="adamw_8bit", logging_steps=10))
        trainer.train()
        model.save_pretrained(cfg["adapter_path"])
        tok.save_pretrained(cfg["adapter_path"])
        if log_cb: log_cb("[✓] LoRA trained")
    
    def merge_model(self, cfg, log_cb=None):
        if cfg.get("dry_run"): return
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer
        model = AutoModelForCausalLM.from_pretrained(cfg["base_model"], device_map="auto", trust_remote_code=True)
        model = PeftModel.from_pretrained(model, cfg["adapter_path"])
        model = model.merge_and_unload()
        model.save_pretrained(cfg["merged_path"])
        AutoTokenizer.from_pretrained(cfg["base_model"]).save_pretrained(cfg["merged_path"])
        if log_cb: log_cb("[✓] Model merged")
    
    def export_gguf(self, cfg, log_cb=None):
        if cfg.get("dry_run"): return
        SystemManager.ensure_llama_cpp(cfg["llama_cpp_path"], cfg["inference_backend"], log_cb)
        cpp_bin = f"{cfg['llama_cpp_path']}/build/bin"
        subprocess.run(["python", f"{cfg['llama_cpp_path']}/convert-hf-to-gguf.py", cfg["merged_path"], "--outfile", cfg["gguf_path"].replace("_q4",""), "--outtype", "f16"], check=True)
        subprocess.run([f"{cpp_bin}/quantize", cfg["gguf_path"].replace("_q4",""), cfg["gguf_path"], "Q4_K_M"], check=True)
        if log_cb: log_cb("[✓] GGUF exported")
    
    def infer(self, cfg, log_cb=None):
        if cfg.get("dry_run"): return
        backend = cfg["inference_backend"]
        prompt = "Write a header comment for this x86 assembly:\n\nxor %eax, %eax\n"
        binary = f"{cfg['llama_cpp_path']}/build/bin/main"
        env = os.environ.copy()
        env["HSA_OVERRIDE_GFX_VERSION"] = cfg["gfx_version"]
        if "HIP" in backend: env["HIP_VISIBLE_DEVICES"] = "0,1"
        else: env["GGML_VULKAN"] = "1"
        res = subprocess.run([binary, "-m", cfg["gguf_path"], "-ngl", "99", "-p", prompt, "-n", "512"], capture_output=True, text=True, env=env)
        if log_cb: log_cb(f"\n[Inference]\n{res.stdout}")

# ============================================
# MAIN ENTRY POINT
# ============================================
if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"\n{'='*70}")
        print(f"[❌] Critical Error: {e}")
        print(f"{'='*70}")
        print(f"\nPlease report this bug with the full error message.\n")
        sys.exit(1)
