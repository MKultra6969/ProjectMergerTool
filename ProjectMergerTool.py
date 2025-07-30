import os
import argparse
from pathlib import Path

def color(text, style):
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "bold": "\033[1m",
        "reset": "\033[0m",
    }
    return f"{colors.get(style, '')}{text}{colors['reset']}"

def print_logo():
    yellow = "\033[93m"
    reset = "\033[0m"
    logo = r"""
|\  /      |\  /|        /|\  
| \/       | \/ |       / | \ 
|       _  | /\ |   _  /  |  \
|      |_| |/  \|  |_|    |   
| /\       |    |         |   
|/  \      |    |         |   

Project Merger Tool by MKultra69
"""
    print(f"{yellow}{logo}{reset}")


# --- локаль ---
LANGUAGES = {
    "en": {
        "menu_title": "===== PROJECT MERGER TOOL =====",
        "choose_option": "Choose an option:",
        "lang_prompt": "Choose language / Выберите язык:\n[1] English\n[2] Русский\n> ",
        "defaulting_to": "Defaulting to English...",
        "invalid_option": "Invalid option. Try again.",
        "option_1": "[1] Scan current directory",
        "option_2": "[2] Set custom directory",
        "option_3": "[3] Edit exclusions",
        "option_4": "[4] Start merging",
        "option_0": "[0] Exit",
        "edit_exclusions": "--- Edit exclusions ---",
        "edit_dirs": "[1] Ignored directories",
        "edit_files": "[2] Ignored files",
        "edit_exts": "[3] Ignored extensions",
        "back": "[0] Back",
        "current_list": "Current: ",
        "add_prompt": "Enter item to add (or blank to cancel): ",
        "remove_prompt": "Enter item to remove (or blank to cancel): ",
        "added": "Added.",
        "removed": "Removed.",
        "nothing_changed": "Nothing changed.",
        "merging": "Merging project...",
        "output_written": "✅ Success! Project merged into a single file.",
        "file_count": "Files written:",
        "bad_path": "Error: Not a valid directory.",
        "write_error": "❌ Error writing output file:",
        "project_dir": "Project Directory:",
        "output_file": "Output File:",
        "enter_path": "Enter full path: "
    },
    "ru": {
        "menu_title": "===== СКЛЕЙКА ПРОЕКТА =====",
        "choose_option": "Выберите пункт меню:",
        "lang_prompt": "Choose language / Выберите язык:\n[1] English\n[2] Русский\n> ",
        "defaulting_to": "По умолчанию выбран английский...",
        "invalid_option": "Неверный ввод. Попробуйте ещё раз.",
        "option_1": "[1] Склеить текущую директорию",
        "option_2": "[2] Указать другую директорию",
        "option_3": "[3] Редактировать исключения",
        "option_4": "[4] Начать склейку",
        "option_0": "[0] Выход",
        "edit_exclusions": "--- Редактирование исключений ---",
        "edit_dirs": "[1] Исключаемые директории",
        "edit_files": "[2] Исключаемые файлы",
        "edit_exts": "[3] Исключаемые расширения",
        "back": "[0] Назад",
        "current_list": "Текущий список: ",
        "add_prompt": "Введите элемент для добавления (пусто — отмена): ",
        "remove_prompt": "Введите элемент для удаления (пусто — отмена): ",
        "added": "Добавлено.",
        "removed": "Удалено.",
        "nothing_changed": "Без изменений.",
        "merging": "Склеиваем проект...",
        "output_written": "✅ Успешно! Проект склеен в один файл.",
        "file_count": "Файлов добавлено:",
        "bad_path": "Ошибка: недопустимая директория.",
        "write_error": "❌ Ошибка при записи в файл:",
        "project_dir": "Директория проекта:",
        "output_file": "Файл вывода:",
        "enter_path": "Введите полный путь: "
    }
}

# --- Дефолтные исключения ---
default_ignore_dirs = {
    "__pycache__", ".git", ".idea", ".vscode", "venv", ".venv", "env",
    "node_modules", "dist", "build", "target", ".pytest_cache", ".mypy_cache",
    "site", "*.egg-info", ".kilocode", "plugins", "vulns", "logs", "static"
}
default_ignore_files = {"poetry.lock", "Pipfile.lock"}
default_ignore_exts = {
    ".pyc", ".pyo", ".pyd", ".so", ".log", ".db", ".sqlite3", ".DS_Store",
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".mp4", ".mov", ".avi",
    ".zip", ".tar", ".gz", ".rar", ".env"
}

ignore_dirs = set(default_ignore_dirs)
ignore_files = set(default_ignore_files)
ignore_exts = set(default_ignore_exts)
lang = LANGUAGES["en"]
project_path = Path(".").resolve()
output_file = Path("merged_project.txt").resolve()


def ask(prompt):
    return input(prompt).strip()


def edit_set(s: set, label: str):
    print(f"{color(lang['current_list'], 'blue')}{', '.join(sorted(s))}\n")
    print(f"[1] Add {label}")
    print(f"[2] Remove {label}")
    print(lang["back"])

    choice = ask(color("> ", "bold"))
    if choice == "1":
        item = ask(lang["add_prompt"])
        if item:
            s.add(item)
            print(color(lang["added"], "green"))
        else:
            print(color(lang["nothing_changed"], "yellow"))
    elif choice == "2":
        item = ask(lang["remove_prompt"])
        if item in s:
            s.remove(item)
            print(color(lang["removed"], "green"))
        else:
            print(color(lang["nothing_changed"], "yellow"))


# --- Tree Generator ---
def generate_tree(startpath: Path, prefix=""):
    tree_lines = []
    try:
        items = sorted(list(startpath.iterdir()))
    except FileNotFoundError:
        return []

    local_ignore = ignore_files.copy()
    if output_file.is_relative_to(project_path):
        local_ignore.add(output_file.name)

    items = [
        item for item in items
        if item.name not in ignore_dirs and item.name not in local_ignore
    ]

    for i, item in enumerate(items):
        is_last = (i == len(items) - 1)
        connector = "└── " if is_last else "├── "

        if item.is_dir():
            tree_lines.append(f"{prefix}{connector}{item.name}/")
            new_prefix = prefix + ("    " if is_last else "│   ")
            tree_lines.extend(generate_tree(item, new_prefix))
        else:
            if item.suffix not in ignore_exts:
                tree_lines.append(f"{prefix}{connector}{item.name}")

    return tree_lines


# --- File Walker ---
def get_project_files():
    local_ignore = ignore_files.copy()
    if output_file.is_relative_to(project_path):
        local_ignore.add(output_file.name)

    for root, dirs, files in os.walk(project_path, topdown=True):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        current = Path(root)

        for file in sorted(files):
            if file in local_ignore:
                continue
            path = current / file
            if path.suffix in ignore_exts:
                continue
            yield path


# --- Merger ---
def merge_project():
    print(color(lang["merging"], "yellow"))

    try:
        with open(output_file, "w", encoding="utf-8", errors="ignore") as f:
            f.write("=" * 80 + "\n")
            f.write(" " * 25 + "PROJECT STRUCTURE OVERVIEW\n")
            f.write("=" * 80 + "\n\n")
            f.write("Project: " + project_path.name + "\n")
            f.write("\n".join(generate_tree(project_path)) + "\n\n\n")

            f.write("=" * 80 + "\n")
            f.write(" " * 30 + "FILE CONTENTS\n")
            f.write("=" * 80 + "\n\n")

            count = 0
            for file in get_project_files():
                rel = file.relative_to(project_path)
                f.write(f"--- File: {rel} ---\n")
                try:
                    f.write(file.read_text(encoding="utf-8"))
                except Exception as e:
                    f.write(f"[Error reading file: {e}]\n")
                f.write("\n" + "=" * 80 + "\n\n")
                count += 1

        print(color(f"{lang['output_written']} -> {output_file}", "green"))
        print(color(f"{lang['file_count']} {count}", "green"))

    except IOError as e:
        print(color(f"{lang['write_error']} {e}", "red"))


# --- меню ---
def main_menu():
    global project_path, output_file

    while True:
        print("\n" + color(lang["menu_title"], "yellow"))
        print(color(lang["project_dir"], "blue"), project_path)
        print(color(lang["output_file"], "blue"), output_file.name)
        print()
        print(lang["option_1"])
        print(lang["option_2"])
        print(lang["option_3"])
        print(lang["option_4"])
        print(lang["option_0"])
        print()

        choice = ask(color(lang["choose_option"] + " ", "bold"))
        if choice == "1":
            project_path = Path(".").resolve()
        elif choice == "2":
            custom = ask(lang["enter_path"])
            p = Path(custom).expanduser().resolve()
            if p.is_dir():
                project_path = p
            else:
                print(color(lang["bad_path"], "red"))
        elif choice == "3":
            print("\n" + color(lang["edit_exclusions"], "yellow"))
            print(lang["edit_dirs"])
            print(lang["edit_files"])
            print(lang["edit_exts"])
            print(lang["back"])
            sub = ask(color("> ", "bold"))
            if sub == "1":
                edit_set(ignore_dirs, "directory")
            elif sub == "2":
                edit_set(ignore_files, "file")
            elif sub == "3":
                edit_set(ignore_exts, "extension")
        elif choice == "4":
            merge_project()
        elif choice == "0":
            break
        else:
            print(color(lang["invalid_option"], "red"))


# --- main ---
def main():
    global lang
    print_logo()

    try:
        choice = ask(lang["lang_prompt"])
        if choice == "2":
            lang = LANGUAGES["ru"]
        elif choice != "1":
            print(color(lang["defaulting_to"], "yellow"))
    except (KeyboardInterrupt, EOFError):
        print(f"\n{color('Exiting.', 'yellow')}")
        return
    except Exception:
        print(color(lang["defaulting_to"], "yellow"))

    main_menu()


if __name__ == "__main__":
    main()

# With hate
# +═════════════════════════════════════════════════════════════════════════+
# ║      ███▄ ▄███▓ ██ ▄█▀ █    ██  ██▓    ▄▄▄█████▓ ██▀███   ▄▄▄           ║
# ║     ▓██▒▀█▀ ██▒ ██▄█▒  ██  ▓██▒▓██▒    ▓  ██▒ ▓▒▓██ ▒ ██▒▒████▄         ║
# ║     ▓██    ▓██░▓███▄░ ▓██  ▒██░▒██░    ▒ ▓██░ ▒░▓██ ░▄█ ▒▒██  ▀█▄       ║
# ║     ▒██    ▒██ ▓██ █▄ ▓▓█  ░██░▒██░    ░ ▓██▓ ░ ▒██▀▀█▄  ░██▄▄▄▄██      ║
# ║     ▒██▒   ░██▒▒██▒ █▄▒▒█████▓ ░██████▒  ▒██▒ ░ ░██▓ ▒██▒ ▓█   ▓██▒     ║
# ║     ░ ▒░   ░  ░▒ ▒▒ ▓▒░▒▓▒ ▒ ▒ ░ ▒░▓  ░  ▒ ░░   ░ ▒▓ ░▒▓░ ▒▒   ▓▒█░     ║
# ║     ░  ░      ░░ ░▒ ▒░░░▒░ ░ ░ ░ ░ ▒  ░    ░      ░▒ ░ ▒░  ▒   ▒▒ ░     ║
# ║     ░      ░   ░ ░░ ░  ░░░ ░ ░   ░ ░     ░        ░░   ░   ░   ▒        ║
# ║            ░   ░  ░      ░         ░  ░            ░           ░  ░     ║
# ║                                                                         ║
# +═════════════════════════════════════════════════════════════════════════+
# ║                               MKultra69                                 ║
# +═════════════════════════════════════════════════════════════════════════+