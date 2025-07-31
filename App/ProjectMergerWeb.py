import sys
import subprocess
import webbrowser
from threading import Timer
from pathlib import Path
import time
import os

# --- Конфигурация ---
REQUIREMENTS = ["Flask", "pathspec"]
APP_FILE = "app.py"
URL = "http://127.0.0.1:5000"
VENV_DIR = "venv"


def print_banner():
    """Выводит красивый баннер в консоль."""
    banner = r"""

 ██▓███   ███▄ ▄███▓▄▄▄█████▓ █     █░
▓██░  ██▒▓██▒▀█▀ ██▒▓  ██▒ ▓▒▓█░ █ ░█░
▓██░ ██▓▒▓██    ▓██░▒ ▓██░ ▒░▒█░ █ ░█ 
▒██▄█▓▒ ▒▒██    ▒██ ░ ▓██▓ ░ ░█░ █ ░█ 
▒██▒ ░  ░▒██▒   ░██▒  ▒██▒ ░ ░░██▒██▓ 
▒▓▒░ ░  ░░ ▒░   ░  ░  ▒ ░░   ░ ▓░▒ ▒  
░▒ ░     ░  ░      ░    ░      ▒ ░ ░  
░░       ░      ░     ░        ░   ░  
                ░                ░    

    """
    print(banner)
    print("=" * 70)
    print("Project Merger Tool - Web Launcher by MKultra69")
    print("=" * 70)
    print()


def get_venv_python_path():
    """Возвращает путь к исполняемому файлу Python внутри venv."""
    if sys.platform == "win32":
        return Path(VENV_DIR) / "Scripts" / "python.exe"
    else:
        return Path(VENV_DIR) / "bin" / "python"


def setup_environment():
    """
    Проверяет наличие venv и зависимостей. Создает и устанавливает их при необходимости.
    Возвращает True, если окружение готово к запуску, иначе False.
    """
    venv_path = Path(VENV_DIR)
    install_marker = venv_path / ".install_complete"

    if venv_path.is_dir() and install_marker.exists():
        print("[INFO] Виртуальное окружение и зависимости в порядке.")
        return True

    if not venv_path.is_dir():
        print(f"[INFO] Виртуальное окружение не найдено. Создаю '{VENV_DIR}'...")
        try:
            subprocess.check_call([sys.executable, "-m", "venv", VENV_DIR])
            print("[SUCCESS] Виртуальное окружение успешно создано.")
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Не удалось создать виртуальное окружение. Ошибка: {e}")
            return False

    python_in_venv = get_venv_python_path()
    if not python_in_venv.exists():
        print("[ERROR] Не найден исполняемый файл Python в venv!")
        return False

    print("[INFO] Устанавливаем/проверяем зависимости в виртуальном окружении...")
    try:
        for package in REQUIREMENTS:
            print(f"[*] Установка {package}...")
            # Используем pip из venv
            subprocess.check_call([str(python_in_venv), "-m", "pip", "install", package],
                                  stdout=subprocess.DEVNULL,
                                  stderr=subprocess.STDOUT)
        print("\n[SUCCESS] Все зависимости успешно установлены в venv!")
        install_marker.touch()
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Не удалось установить зависимости. Ошибка: {e}")
        return False


def open_browser():
    """Открывает веб-браузер по заданному URL в новой вкладке."""
    print(f"[INFO] Открываю {URL} в вашем браузере...")
    webbrowser.open_new_tab(URL)


def start_app():
    """Запускает основное Flask-приложение, используя Python из venv."""
    app_path = Path(APP_FILE)
    if not app_path.exists():
        print(f"[ERROR] Основной файл приложения '{APP_FILE}' не найден!")
        return

    python_in_venv = get_venv_python_path()
    if not python_in_venv.exists():
        print("[ERROR] Не найден исполняемый файл Python в venv! Не могу запустить приложение.")
        return

    print(f"[INFO] Запускаю Flask-приложение '{APP_FILE}' с помощью Python из venv...")
    print("Для остановки сервера нажмите Ctrl+C в этом окне.")

    Timer(1.5, open_browser).start()

    try:
        subprocess.run([str(python_in_venv), APP_FILE], check=True)
    except KeyboardInterrupt:
        print("\n[INFO] Сервер остановлен пользователем.")
    except Exception as e:
        print(f"\n[ERROR] Приложение завершилось с ошибкой: {e}")


def main():
    """Основная логика лаунчера."""
    print_banner()

    if setup_environment():
        time.sleep(1)
        start_app()
    else:
        print("\n[FAIL] Запуск невозможен из-за ошибки с подготовкой окружения.")

    print("\n" + "=" * 70)
    print("Лаунчер завершил свою работу.")


if __name__ == "__main__":
    main()