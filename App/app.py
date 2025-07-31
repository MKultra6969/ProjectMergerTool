import os
import re
import json
from pathlib import Path
from flask import Flask, render_template, request, jsonify
import pathspec

# --- Инициализация Flask ---
app = Flask(__name__, static_folder='static', template_folder='templates')

# --- Списки исключений (теперь они не константы) ---
# Мы загрузим их из файла или используем дефолтные
exclusions = {}
exclusions_file = Path("merger_exclusions.json")


def load_exclusions():
    global exclusions
    if exclusions_file.exists():
        exclusions = json.loads(exclusions_file.read_text(encoding="utf-8"))
    else:
        exclusions = {
            "dirs": [
                "__pycache__", ".git", ".idea", ".vscode", "venv", ".venv", "env",
                "node_modules", "dist", "build", "target", ".pytest_cache",
                ".mypy_cache", "site", "*.egg-info", "static", "templates"
            ],
            "files": ["poetry.lock", "Pipfile.lock", "merged_project.txt", "merger_exclusions.json"],
            "exts": [
                ".pyc", ".pyo", ".pyd", ".so", ".log", ".db", ".sqlite3",
                ".DS_Store", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
                ".mp4", ".mov", ".avi", ".zip", ".tar", ".gz", ".rar", ".env"
            ]
        }


load_exclusions()


def save_exclusions():
    exclusions_file.write_text(json.dumps(exclusions, indent=4, ensure_ascii=False), encoding="utf-8")


# --- Логика сканирования и построения дерева ---
def build_file_tree(dir_path: Path, project_root: Path, gitignore_spec: pathspec.PathSpec | None):
    tree = []
    ignore_dirs_set = set(exclusions["dirs"])
    ignore_files_set = set(exclusions["files"])
    ignore_exts_set = set(exclusions["exts"])

    try:
        items = sorted(dir_path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
        for item in items:

            relative_path = item.relative_to(project_root)

            if gitignore_spec and gitignore_spec.match_file(str(relative_path)):
                continue

            if item.name in ignore_dirs_set:
                continue
            if item.is_file() and (item.name in ignore_files_set or item.suffix in ignore_exts_set):
                continue

            if item.resolve() == Path(__file__).resolve() or item.name == exclusions_file.name:
                continue

            entry = {"name": item.name, "path": str(relative_path)}
            if item.is_dir():
                entry["type"] = "dir"
                children = build_file_tree(item, project_root, gitignore_spec)
                if children:
                    entry["children"] = children
                    tree.append(entry)
            else:
                entry["type"] = "file"
                tree.append(entry)
    except (FileNotFoundError, PermissionError):
        return []
    return tree


LANG_MAP = {
    '.py': 'python',
    '.js': 'javascript',
    '.mjs': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'tsx',
    '.jsx': 'jsx',
    '.rb': 'ruby',
    '.java': 'java',
    '.cs': 'csharp',
    '.php': 'php',
    '.c': 'c',
    '.cpp': 'cpp',
    '.h': 'c',
    '.hpp': 'cpp',
    '.go': 'go',
    '.rs': 'rust',
    '.kt': 'kotlin',
    '.kts': 'kotlin',
    '.swift': 'swift',
    '.html': 'html',
    '.css': 'css',
    '.scss': 'scss',
    '.sass': 'sass',
    '.xml': 'xml',
    '.json': 'json',
    '.yaml': 'yaml',
    '.yml': 'yaml',
    '.md': 'markdown',
    '.sh': 'shell',
    '.bat': 'batch',
    '.ps1': 'powershell',
    '.sql': 'sql',
    'Dockerfile': 'dockerfile',
}

FILE_CONTENT_TRANSLATIONS = {
    "ru": {
        "project_build": "Сборка проекта",
        "project_structure": "СТРУКТУРА ПРОЕКТА (ВКЛЮЧЕННЫЕ ФАЙЛЫ)",
        "file_contents": "СОДЕРЖИМОЕ ФАЙЛОВ",
        "file_header": "Файл",
        "read_error": "Ошибка чтения файла"
    },
    "en": {
        "project_build": "Project Build",
        "project_structure": "PROJECT STRUCTURE (INCLUDED FILES)",
        "file_contents": "FILE CONTENTS",
        "file_header": "File",
        "read_error": "Error reading file"
    }
}


# <--- УНКЦИЯ УДАЛЕНИЯ СЕКРЕТОВ ---
def sanitize_content(content: str) -> str:
    """
    Удаляет потенциальные секреты из текстового контента с помощью регулярных выражений.
    """
    patterns = [
        (r"""(['"]?((?:api|access|secret|private)_?(?:key|token)|token|password)['"]?\s*[:=]\s*)['"][^'"]*['"]""",
         r'\1"[SECRET REMOVED]"'),
        (r"""(^((?:API|ACCESS|SECRET|PRIVATE)_?(?:KEY|TOKEN)|TOKEN|PASSWORD)=)[^\n]*""", r'\1[SECRET REMOVED]'),
    ]

    sanitized_content = content
    for pattern, replacement in patterns:
        sanitized_content = re.sub(pattern, replacement, sanitized_content, flags=re.IGNORECASE | re.MULTILINE)

    return sanitized_content


# <--- ФУНКЦИЯ ОЧИСТКИ ДЛЯ ИИ ---
def clear_for_ai(content: str, file_extension: str) -> str:

    line_comment_patterns = {
        '.py': r'#.*',
        '.js': r'//.*',
        '.ts': r'//.*',
        '.jsx': r'//.*',
        '.tsx': r'//.*',
        '.go': r'//.*',
        '.rs': r'//.*',
        '.java': r'//.*',
        '.cs': r'//.*',
        '.c': r'//.*',
        '.cpp': r'//.*',
        '.h': r'//.*',
        '.hpp': r'//.*',
        '.swift': r'//.*',
        '.kt': r'//.*',
        '.kts': r'//.*',
        '.rb': r'#.*',
        '.php': r'//.*|#.*',
        '.sh': r'#.*',
    }
    block_comment_patterns = {
        'common_c_style': (r'/\*.*?\*/',),
        'python': (r'"""(.*?)"""', r"'''(.*?)'''"),
        'html': (r'<!--.*?-->',),
    }

    if file_extension in ['.py']:
        for pattern in block_comment_patterns['python']:
            content = re.sub(pattern, '', content, flags=re.DOTALL)
    elif file_extension in ['.js', '.ts', '.css', '.c', '.cpp', '.java', '.cs', '.go', '.rs', '.swift', '.kt']:
        for pattern in block_comment_patterns['common_c_style']:
            content = re.sub(pattern, '', content, flags=re.DOTALL)
    elif file_extension in ['.html', '.xml']:
        for pattern in block_comment_patterns['html']:
            content = re.sub(pattern, '', content, flags=re.DOTALL)

    if file_extension in line_comment_patterns:
        content = re.sub(line_comment_patterns[file_extension], '', content)

    content = re.sub(r'\n\s*\n', '\n', content)

    return content.strip()

# --- Маршруты (эндпоинты) ---

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/scan', methods=['POST'])
def scan_directory():
    data = request.json
    path_str = data.get('path', '.')
    use_gitignore = data.get('use_gitignore', True)

    project_path = Path(path_str).expanduser().resolve()

    if not project_path.is_dir():
        return jsonify({"error": "Указанный путь не является директорией"}), 400

    gitignore_spec = None
    if use_gitignore:
        gitignore_file = project_path / '.gitignore'
        if gitignore_file.is_file():
            try:
                with open(gitignore_file, 'r', encoding='utf-8') as f:
                    gitignore_spec = pathspec.PathSpec.from_lines('gitwildmatch', f)
            except Exception:
                pass
    tree = build_file_tree(project_path, project_path, gitignore_spec)
    return jsonify({"tree": tree, "project_name": project_path.name, "project_path": str(project_path)})


# <---   /merge ---


@app.route('/merge', methods=['POST'])
def merge_files():
    data = request.json
    files_to_merge = data.get('files', [])
    project_path_str = data.get('project_path', '.')
    export_format = data.get('format', 'txt')
    lang = data.get('lang', 'ru')
    remove_secrets = data.get('remove_secrets', False)
    clear_for_ai_flag = data.get('clear_for_ai', False)  # Получаем новый флаг

    T = FILE_CONTENT_TRANSLATIONS.get(lang, FILE_CONTENT_TRANSLATIONS['ru'])

    project_path = Path(project_path_str)
    output_filename = f"merged_project.{export_format}"
    output_filepath = Path(app.static_folder) / output_filename

    file_tree_str = generate_text_tree(project_path, files_to_merge)

    try:
        with open(output_filepath, "w", encoding="utf-8", errors="ignore") as f:
            # ... (запись заголовка файла без изменений) ...
            if export_format == 'md':
                f.write(f"# {T['project_build']}: {project_path.name}\n\n")
                f.write(f"## {T['project_structure']}\n\n")
                f.write("```\n")
                f.write(file_tree_str + "\n")
                f.write("```\n\n")
                f.write(f"## {T['file_contents']}\n\n")
            else:
                f.write(f"{T['project_build']}: {project_path.name}\n")
                f.write("=" * 80 + "\n")
                f.write(f"{T['project_structure']}\n")
                f.write("=" * 80 + "\n\n")
                f.write(file_tree_str + "\n\n")
                f.write("=" * 80 + "\n")
                f.write(f"{T['file_contents']}\n")
                f.write("=" * 80 + "\n\n")

            # Содержимое файлов
            for file_rel_path_str in sorted(files_to_merge):
                file_rel_path = Path(file_rel_path_str)
                file_abs_path = (project_path / file_rel_path).resolve()

                if project_path not in file_abs_path.parents and file_abs_path.parent != project_path:
                    continue

                try:
                    file_content = file_abs_path.read_text(encoding="utf-8")

                    # --- ОБНОВЛЕННАЯ ЛОГИКА ОБРАБОТКИ ---
                    if clear_for_ai_flag:
                        # Очистка для ИИ включает удаление секретов
                        content_sanitized = sanitize_content(file_content)
                        file_content = clear_for_ai(content_sanitized, file_rel_path.suffix)
                    elif remove_secrets:
                        file_content = sanitize_content(file_content)
                    # --- КОНЕЦ ОБНОВЛЕННОЙ ЛОГИКИ ---

                except Exception as e:
                    file_content = f"[{T['read_error']}: {e}]"

                # Записываем финальное содержимое
                if file_content:  # Не записываем пустые файлы после очистки
                    if export_format == 'md':
                        lang_tag = LANG_MAP.get(file_rel_path.suffix, '')
                        f.write(f"### `--- {T['file_header']}: {file_rel_path_str} ---`\n\n")
                        f.write(f"```{lang_tag}\n")
                        f.write(file_content)
                        f.write("\n```\n\n")
                    else:
                        f.write(f"--- {T['file_header']}: {file_rel_path_str} ---\n\n")
                        f.write(file_content)
                        f.write("\n\n" + "=" * 80 + "\n\n")

        return jsonify({"success": True, "download_url": f"/static/{output_filename}"})

    except IOError as e:
        return jsonify({"error": f"Ошибка записи в файл: {e}"}), 500


def generate_text_tree(project_path, selected_files):
    tree = {}
    for path_str in selected_files:
        parts = Path(path_str).parts
        current_level = tree
        for part in parts:
            if part not in current_level:
                current_level[part] = {}
            current_level = current_level[part]

    def build_lines(d, prefix=""):
        lines = []
        items = sorted(d.keys())
        for i, name in enumerate(items):
            connector = "└── " if i == len(items) - 1 else "├── "
            lines.append(f"{prefix}{connector}{name}")
            if d[name]:
                new_prefix = prefix + ("    " if i == len(items) - 1 else "│   ")
                lines.extend(build_lines(d[name], new_prefix))
        return lines

    return "\n".join(build_lines(tree))


@app.route('/exclusions', methods=['GET'])
def get_exclusions():
    return jsonify(exclusions)


@app.route('/exclusions', methods=['POST'])
def update_exclusions():
    global exclusions
    data = request.json
    if all(isinstance(data.get(key), list) for key in ["dirs", "files", "exts"]):
        exclusions = data
        save_exclusions()
        return jsonify({"success": True, "message": "Исключения сохранены"})
    return jsonify({"success": False, "error": "Неверный формат данных"}), 400


if __name__ == '__main__':
    print("Перейдите в браузере по адресу http://127.0.0.1:5000")
    app.run(debug=False, port=5000)

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