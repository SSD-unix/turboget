#!/usr/bin/env python3
import sys
import os
import shutil
import urllib.request
import zipfile
from datetime import datetime

# Пытаемся подключить автономный Git-движок
try:
    from dulwich import porcelain
    DULWICH_AVAILABLE = True
except ImportError:
    DULWICH_AVAILABLE = False

# --- Оформление (Aviation Style) ---
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header():
    print(f"{Colors.HEADER}{Colors.BOLD}")
    print(r"  _____ _   _ ____  ____   ___   ____ _____ _____ ")
    print(r" |_   _| | | |  _ \| __ ) / _ \ / ___| ____|_   _|")
    print(r"   | | | | | | |_) |  _ \| | | | |  _|  _|   | |  ")
    print(r"   | | | |_| |  _ <| |_) | |_| | |_| | |___  | |  ")
    print(r"   |_|  \___/|_| \_\____/ \___/ \____|_____| |_|  ")
    print(r"                                                  ")
    print(r"         L-410 Edition v0.3 [AUTONOMOUS]          ")
    print(f"{Colors.ENDC}")

# --- Чёрный ящик ---
LOG_FILE = "turboget.log"

def log_blackbox(message, status="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] [{status}] {message}\n")

# --- Логика Авиа-детекта ---
def detect_stream_type(url):
    print(f"{Colors.OKBLUE}[ SYSTEM ]{Colors.ENDC} Analyzing incoming stream...")
    clean_url = url.split('#')[0]
    if clean_url.endswith(".git") or "github.com" in clean_url or "gitlab.com" in clean_url:
        return "GIT_REPO"
    return "RAW_PAYLOAD"

# --- АВТОНОМНЫЙ Модуль Git (Dulwich) ---
def run_pure_git_clone(url, path, stealth=False):
    if not DULWICH_AVAILABLE:
        print(f"{Colors.FAIL}[ ERROR ]{Colors.ENDC} Автономный модуль Dulwich не найден.")
        print("Установите его: sudo pacman -S python-dulwich")
        sys.exit(1)

    print(f"{Colors.OKGREEN}[ CLONE ]{Colors.ENDC} Engaging Pure Python Git Engine (Dulwich)...")

    # Определяем папку назначения
    target_dir = path
    if not target_dir:
        target_dir = url.split("/")[-1].replace(".git", "")
        if not target_dir: # На случай странных URL
            target_dir = "cloned_repo"

    log_blackbox(f"Cloning via Dulwich: {url} to {target_dir}", "GIT_PURE")

    try:
        # Сам процесс клонирования встроенными средствами Python
        porcelain.clone(url, target_dir)
        print(f"{Colors.OKGREEN}[ SUCCESS ]{Colors.ENDC} Cargo delivered to: {target_dir}")

        # Stealth Mode (удаление .git)
        if stealth:
            print(f"{Colors.WARNING}[ STEALTH ]{Colors.ENDC} Scrubbing metadata (.git)...")
            git_dir = os.path.join(target_dir, ".git")
            if os.path.exists(git_dir):
                # В Windows/Linux иногда файлы .git имеют права read-only,
                # поэтому используем обработчик ошибок
                def remove_readonly(func, path, excinfo):
                    os.chmod(path, 0o777)
                    func(path)
                shutil.rmtree(git_dir, onerror=remove_readonly)
            print(f"{Colors.OKGREEN}[ SUCCESS ]{Colors.ENDC} Stealth Mode applied. Pure source only.")
            log_blackbox(f"Stealth Mode applied to {target_dir}", "STEALTH")

    except Exception as e:
        print(f"{Colors.FAIL}[ FAIL ]{Colors.ENDC} Git stream interrupted: {e}")
        log_blackbox(f"Pure Git clone failed: {e}", "FAIL")

# --- АВТОНОМНЫЙ Модуль Загрузки (urllib + zipfile) ---
def run_pure_download(url, extract):
    print(f"{Colors.OKGREEN}[ DOWNLOAD ]{Colors.ENDC} Engaging Built-in Python Downloader...")
    filename = url.split("/")[-1] or "downloaded_payload"

    log_blackbox(f"Downloading via urllib: {url}", "DOWNLOAD_PURE")
    try:
        # Функция для отображения прогресса в стиле приборной панели
        def progress_hook(count, block_size, total_size):
            percent = int(count * block_size * 100 / total_size)
            sys.stdout.write(f"\r{Colors.OKBLUE}[ RADAR ]{Colors.ENDC} Download progress: {percent}%")
            sys.stdout.flush()

        urllib.request.urlretrieve(url, filename, reporthook=progress_hook)
        print(f"\n{Colors.OKGREEN}[ SUCCESS ]{Colors.ENDC} Payload stored as: {filename}")

        # Автономная распаковка встроенным zipfile
        if extract and filename.endswith(".zip"):
            print(f"{Colors.WARNING}[ UNPACK ]{Colors.ENDC} Extracting via built-in zip engine...")
            try:
                with zipfile.ZipFile(filename, 'r') as zip_ref:
                    zip_ref.extractall(".")
                print(f"{Colors.OKGREEN}[ SUCCESS ]{Colors.ENDC} Unpacked successfully.")
            except zipfile.BadZipFile:
                print(f"{Colors.FAIL}[ FAIL ]{Colors.ENDC} Bad ZIP file payload.")

    except Exception as e:
        print(f"\n{Colors.FAIL}[ FAIL ]{Colors.ENDC} Delivery failed: {e}")
        log_blackbox(f"Pure Download failed: {e}", "FAIL")

# --- Главная Диспетчерская ---
def main():
    print_header()

    args = sys.argv[1:]
    if not args:
        print("Usage: python3 turboget.py <URL> [OPTIONS]")
        print("Options:")
        print("  -x            Extract zip after download (Download mode)")
        print("  --stealth     Delete .git folder after clone (Git mode)")
        print("  -o <path>     Custom output path")
        print("\nExample: python3 turboget.py https://github.com/SSD-unix/TESTASTERON_OS --stealth")
        sys.exit(1)

    url = next((arg for arg in args if not arg.startswith('-')), None)
    if not url:
        print(f"{Colors.FAIL}Error: No URL provided.{Colors.ENDC}")
        sys.exit(1)

    extract = "-x" in args
    stealth = "--stealth" in args

    path = None
    if "-o" in args:
        try:
            path = args[args.index("-o") + 1]
        except IndexError:
            pass

    stream_type = detect_stream_type(url)

    if stream_type == "GIT_REPO":
        run_pure_git_clone(url, path, stealth=stealth)
    else:
        run_pure_download(url, extract)

    print("-" * 60)

if __name__ == "__main__":
    main()
