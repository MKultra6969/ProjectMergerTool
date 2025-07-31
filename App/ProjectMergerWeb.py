import sys
import subprocess
import webbrowser
from threading import Timer
from pathlib import Path
import time

REQUIREMENTS = ["Flask", "pathspec"]
APP_FILE = "app.py"
URL = "http://127.0.0.1:5000"
INSTALL_MARKER_FILE = ".install_complete"


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


def check_and_install_dependencies():
    """
    Проверяет, были ли зависимости установлены ранее. Если нет,
    устанавливает их и создает файл-маркер.
    """
    marker_path = Path(INSTALL_MARKER_FILE)

    if marker_path.exists():
        print("[INFO] Зависимости уже были установлены. Пропускаем установку.")
        return True

    print("[INFO] Первая установка. Проверяем и устанавливаем зависимости...")

    try:
        for package in REQUIREMENTS:
            print(f"[*] Установка {package}...")
            # Используем subprocess для вызова pip
            # sys.executable гарантирует, что мы используем pip от текущего интерпретатора Python
            subprocess.check_call([sys.executable, "-m", "pip", "install", package],
                                  stdout=subprocess.DEVNULL,  # Скрываем успешный вывод
                                  stderr=subprocess.STDOUT)  # Перенаправляем ошибки в stdout

        print("\n[SUCCESS] Все зависимости успешно установлены!")
        # Создаем файл-маркер после успешной установки
        marker_path.touch()
        return True

    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Не удалось установить зависимости. Ошибка: {e}")
        print("Пожалуйста, попробуйте установить их вручную:")
        for package in REQUIREMENTS:
            print(f"pip install {package}")
        return False
    except Exception as e:
        print(f"\n[ERROR] Произошла непредвиденная ошибка: {e}")
        return False


def open_browser():
    """Открывает веб-браузер по заданному URL."""
    print(f"[INFO] Открываю {URL} в вашем браузере...")
    webbrowser.open_new_tab(URL)


def start_app():
    """Запускает основное Flask-приложение."""
    app_path = Path(APP_FILE)
    if not app_path.exists():
        print(f"[ERROR] Основной файл приложения '{APP_FILE}' не найден!")
        return

    print(f"[INFO] Запускаю Flask-приложение: {APP_FILE}")
    print("Для остановки сервера нажмите Ctrl+C в этом окне.")

    # Запускаем открытие браузера с небольшой задержкой,
    # чтобы дать серверу время на старт.
    Timer(1.5, open_browser).start()

    try:
        # Запускаем app.py как подпроцесс
        subprocess.run([sys.executable, APP_FILE], check=True)
    except KeyboardInterrupt:
        print("\n[INFO] Сервер остановлен пользователем.")
    except Exception as e:
        print(f"\n[ERROR] Приложение завершилось с ошибкой: {e}")


def main():
    """Основная логика лаунчера."""
    print_banner()
    if check_and_install_dependencies():
        time.sleep(1)  # Небольшая пауза для наглядности
        start_app()
    else:
        print("\n[FAIL] Запуск невозможен из-за ошибок с зависимостями.")

    print("\n" + "=" * 70)
    print("Лаунчер завершил свою работу.")


if __name__ == "__main__":
    main()