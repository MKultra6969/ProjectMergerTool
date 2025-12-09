import os
import re
import json
import argparse
from pathlib import Path
import sys
from flask import Flask, render_template, request, jsonify
import pathspec
app = Flask(__name__, static_folder='static', template_folder='templates')

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

def flatten_file_tree(tree_nodes):
    paths = []
    for node in tree_nodes:
        if node['type'] == 'file':
            paths.append(node['path'])
        elif node['type'] == 'dir' and 'children' in node:
            paths.extend(flatten_file_tree(node['children']))
    return paths

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

def sanitize_content(content: str) -> str:
    patterns = [
        (r"""(['"]?((?:api|access|secret|private)_?(?:key|token)|token|password)['"]?\s*[:=]\s*)['"][^'"]*['"]""",
         r'\1"[SECRET REMOVED]"'),
        (r"""(^((?:API|ACCESS|SECRET|PRIVATE)_?(?:KEY|TOKEN)|TOKEN|PASSWORD)=)[^\n]*""", r'\1[SECRET REMOVED]'),
    ]

    sanitized_content = content
    for pattern, replacement in patterns:
        sanitized_content = re.sub(pattern, replacement, sanitized_content, flags=re.IGNORECASE | re.MULTILINE)

    return sanitized_content

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

def perform_merge_logic(project_path, files_to_merge, output_filepath, export_format, lang, remove_secrets, clear_for_ai_flag):
    project_name = project_path.name
    T = FILE_CONTENT_TRANSLATIONS.get(lang, FILE_CONTENT_TRANSLATIONS['ru'])
    file_tree_str = generate_text_tree(files_to_merge)

    if export_format == 'pdf':
        print("[INFO] PDF export selected. Importing WeasyPrint and Pygments...")
        try:
            from weasyprint import HTML
            from pygments import highlight
            from pygments.lexers import get_lexer_for_filename, TextLexer
            from pygments.formatters import HtmlFormatter
            print("[SUCCESS] Libraries imported.")
        except ImportError:
            raise ImportError("WeasyPrint or Pygments not installed. Run 'pip install WeasyPrint Pygments'.")

        pygments_css = HtmlFormatter(style='default').get_style_defs('.highlight')
        html_parts = [
            '<!DOCTYPE html>', '<html lang="en">', '<head><meta charset="UTF-8">',
            f'<title>{T["project_build"]}: {project_name}</title>',
            '<style>', 'body { font-family: sans-serif; }', 'h1, h2, h3 { color: #333; }',
            'pre { white-space: pre-wrap; word-wrap: break-word; background-color: #f8f8f8; border: 1px solid #ddd; padding: 10px; border-radius: 5px; }',
            'code { font-family: monospace; }', pygments_css, '</style>', '</head><body>',
            f'<h1>{T["project_build"]}: {project_name}</h1>', f'<h2>{T["project_structure"]}</h2>',
            f'<pre><code>{file_tree_str}</code></pre>', f'<h2>{T["file_contents"]}</h2>'
        ]
        for file_rel_path_str in sorted(files_to_merge):
            file_abs_path = project_path / file_rel_path_str
            try:
                file_content = file_abs_path.read_text(encoding="utf-8")
                if clear_for_ai_flag:
                    content_sanitized = sanitize_content(file_content)
                    file_content = clear_for_ai(content_sanitized, file_abs_path.suffix)
                elif remove_secrets:
                    file_content = sanitize_content(file_content)
                if not file_content: continue
                try:
                    lexer = get_lexer_for_filename(file_rel_path_str, stripall=True)
                except Exception:
                    lexer = TextLexer()
                formatter = HtmlFormatter(linenos=True, cssclass="highlight")
                highlighted_code = highlight(file_content, lexer, formatter)
                html_parts.append(f'<h3><code>--- {T["file_header"]}: {file_rel_path_str} ---</code></h3>')
                html_parts.append(highlighted_code)
            except Exception as e:
                html_parts.append(f'<h3><code>--- {T["file_header"]}: {file_rel_path_str} ---</code></h3>')
                html_parts.append(f'<pre>[{T["read_error"]}: {e}]</pre>')
        html_parts.append('</body></html>')
        final_html = "".join(html_parts)
        print("[INFO] HTML generated. Starting PDF conversion...")
        HTML(string=final_html).write_pdf(output_filepath)
        print("[SUCCESS] PDF file written successfully.")

    else:
        print(f"[INFO] {export_format.upper()} export selected. Starting file write...")
        with open(output_filepath, "w", encoding="utf-8", errors="ignore") as f:
            if export_format == 'md':
                f.write(
                    f"# {T['project_build']}: {project_name}\n\n## {T['project_structure']}\n\n```\n{file_tree_str}\n```\n\n## {T['file_contents']}\n\n")
            else:
                f.write(
                    f"{T['project_build']}: {project_name}\n{'=' * 80}\n{T['project_structure']}\n{'=' * 80}\n\n{file_tree_str}\n\n{'=' * 80}\n{T['file_contents']}\n{'=' * 80}\n\n")
            for file_rel_path_str in sorted(files_to_merge):
                file_rel_path = Path(file_rel_path_str)
                file_abs_path = (project_path / file_rel_path).resolve()
                try:
                    file_content = file_abs_path.read_text(encoding="utf-8")
                    if clear_for_ai_flag:
                        content_sanitized = sanitize_content(file_content)
                        file_content = clear_for_ai(content_sanitized, file_rel_path.suffix)
                    elif remove_secrets:
                        file_content = sanitize_content(file_content)
                except Exception as e:
                    file_content = f"[{T['read_error']}: {e}]"
                if file_content:
                    if export_format == 'md':
                        lang_tag = LANG_MAP.get(file_rel_path.suffix, '')
                        f.write(
                            f"### `--- {T['file_header']}: {file_rel_path_str} ---`\n\n```{lang_tag}\n{file_content}\n```\n\n")
                    else:
                        f.write(
                            f"--- {T['file_header']}: {file_rel_path_str} ---\n\n{file_content}\n\n{'=' * 80}\n\n")
        print(f"[SUCCESS] {export_format.upper()} file written successfully.")

@app.route('/merge', methods=['POST'])
def merge_files():
    data = request.json
    files_to_merge = data.get('files', [])
    project_path_str = data.get('project_path', '.')
    project_path = Path(project_path_str)
    project_name = project_path.name
    export_format = data.get('format', 'txt')
    lang = data.get('lang', 'ru')
    remove_secrets = data.get('remove_secrets', False)
    clear_for_ai_flag = data.get('clear_for_ai', False)

    output_filename = f"{project_name}.{export_format}"
    output_filepath = Path(app.static_folder) / output_filename

    try:
        perform_merge_logic(
            project_path=project_path,
            files_to_merge=files_to_merge,
            output_filepath=output_filepath,
            export_format=export_format,
            lang=lang,
            remove_secrets=remove_secrets,
            clear_for_ai_flag=clear_for_ai_flag
        )
        response_data = {"success": True, "download_url": f"/static/{output_filename}"}
        return jsonify(response_data)

    except Exception as e:
        print(f"[ERROR] An error occurred during merge: {e}", flush=True)
        return jsonify({"error": f"Ошибка создания файла: {str(e)}"}), 500

def generate_text_tree(selected_files):
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

def run_cli():
    parser = argparse.ArgumentParser(description="Project Merger Tool - CLI Mode")
    parser.add_argument("--path", "-p", type=str, default=".", help="Путь к папке проекта (по умолчанию текущая)")
    parser.add_argument("--output", "-o", type=str, help="Путь к выходному файлу (по умолчанию: <имя_папки>.txt)")
    parser.add_argument("--format", "-f", choices=['txt', 'md', 'pdf'], default="txt", help="Формат вывода (txt, md, pdf)")
    parser.add_argument("--lang", "-l", choices=['ru', 'en'], default="en", help="Язык заголовков (ru, en)")
    parser.add_argument("--no-gitignore", action="store_true", help="Не использовать .gitignore")
    parser.add_argument("--remove-secrets", action="store_true", help="Удалять секреты (ключи, токены)")
    parser.add_argument("--clear-ai", action="store_true", help="Очистка для ИИ (удалить комментарии и пустые строки)")

    args = parser.parse_args()

    project_path = Path(args.path).resolve()
    if not project_path.is_dir():
        print(f"[ERROR] Директория не найдена: {project_path}")
        sys.exit(1)

    gitignore_spec = None
    if not args.no_gitignore:
        gitignore_file = project_path / '.gitignore'
        if gitignore_file.is_file():
            try:
                with open(gitignore_file, 'r', encoding='utf-8') as f:
                    gitignore_spec = pathspec.PathSpec.from_lines('gitwildmatch', f)
                print("[INFO] .gitignore найден и будет использован.")
            except Exception as e:
                print(f"[WARN] Ошибка чтения .gitignore: {e}")

    print(f"[INFO] Сканирование директории: {project_path}")
    tree = build_file_tree(project_path, project_path, gitignore_spec)
    files_to_merge = flatten_file_tree(tree)

    if not files_to_merge:
        print("[ERROR] Не найдено файлов для склейки (проверьте фильтры и исключения).")
        sys.exit(1)
    
    print(f"[INFO] Найдено файлов: {len(files_to_merge)}")
    if files_to_merge:
        print("[INFO] Первые 5 файлов, которые будут обработаны:")
        for i, f in enumerate(sorted(files_to_merge)):
            if i >= 5:
                print(f"  ... и еще {len(files_to_merge) - i} файлов.")
                break
            print(f"  - {f}")

    if args.output:
        output_filepath = Path(args.output).resolve()
    else:
        output_filename = f"{project_path.name}.{args.format}"
        output_filepath = Path.cwd() / output_filename

    try:
        perform_merge_logic(
            project_path=project_path,
            files_to_merge=files_to_merge,
            output_filepath=output_filepath,
            export_format=args.format,
            lang=args.lang,
            remove_secrets=args.remove_secrets,
            clear_for_ai_flag=args.clear_ai
        )
        print(f"[DONE] Файл успешно сохранен: {output_filepath}")
    except Exception as e:
        print(f"[FAIL] Ошибка при создании файла: {e}")
        sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print("Запуск веб-сервера... (Используйте --help для CLI режима)")
        print("Перейдите в браузере по адресу http://127.0.0.1:5000")
        app.run(debug=False, port=5000)
    else:
        run_cli()

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