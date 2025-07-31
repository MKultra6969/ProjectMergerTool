document.addEventListener('DOMContentLoaded', () => {
    // --- Словари для локализации ---
    const translations = {
        en: {
            mainTitle: "Project Merger Tool",
            scanTitle: "Scanning",
            pathPlaceholder: "Enter project path...",
            selectFolderBtn: "Select Folder",
            scanBtn: "Scan",
            mergeBtn: "Merge Selected Files",
            done: "Done!",
            downloadLink: "Download merged file",
            exclusionsTitle: "Exclusions",
            ignoreDirs: "Ignored directories:",
            ignoreFiles: "Ignored files:",
            ignoreExts: "Ignored extensions:",
            saveExclusionsBtn: "Save Exclusions",
            exclusionsSaved: "Exclusions saved!",
            exclusionsError: "Error saving exclusions.",
            theme: "Theme:",
            githubLinkTitle: "My GitHub",
            websiteLinkTitle: "My Website",
            useGitignore: "Use .gitignore",
            exportFormatTitle: "Export Format",
            removeSecrets: "Remove secrets (keys, tokens)",
            clearForAI: "Clear for AI (remove comments & empty lines)"
        },
        ru: {
            mainTitle: "Project Merger Tool",
            scanTitle: "Сканирование",
            pathPlaceholder: "Введите путь к проекту...",
            selectFolderBtn: "Выбрать папку",
            scanBtn: "Сканировать",
            mergeBtn: "Склеить выбранные файлы",
            done: "Готово!",
            downloadLink: "Скачать собранный файл",
            exclusionsTitle: "Исключения",
            ignoreDirs: "Исключаемые директории:",
            ignoreFiles: "Исключаемые файлы:",
            ignoreExts: "Исключаемые расширения:",
            saveExclusionsBtn: "Сохранить исключения",
            exclusionsSaved: "Исключения сохранены!",
            exclusionsError: "Ошибка сохранения.",
            theme: "Тема:",
            githubLinkTitle: "Мой GitHub",
            websiteLinkTitle: "Мой сайт",
            useGitignore: "Учитывать .gitignore",
            exportFormatTitle: "Формат экспорта",
            removeSecrets: "Удалить секреты (ключи, токены)",
            clearForAI: "Очистить для ИИ (убрать комменты и пустые строки)"
        }
    };

    // --- DOM Элементы ---
    const getEl = (id) => document.getElementById(id);
    const mergePanel = getEl('merge-panel');
    const scanBtn = getEl('scan-btn');
    const mergeBtn = getEl('merge-btn');
    const pathInput = getEl('path-input');
    const fileTreeContainer = getEl('file-tree');
    const projectView = getEl('project-view');
    const projectNameEl = getEl('project-name');
    const resultView = getEl('result');
    const downloadLink = getEl('download-link');
    const errorDiv = getEl('error-message');
    const folderPicker = getEl('folder-picker');
    const folderPickerBtn = getEl('folder-picker-btn');
    const themeToggle = getEl('theme-toggle');
    const langSwitcher = document.querySelector('.lang-switcher');
    const saveExclusionsBtn = getEl('save-exclusions-btn');

    let projectPath = '';


    // --- КОНФЕТТИ ---
    function triggerConfetti() {
    const duration = 5 * 1000; // 5 секунд
    const animationEnd = Date.now() + duration;
    const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 0 };

    function randomInRange(min, max) {
        return Math.random() * (max - min) + min;
    }

    const interval = setInterval(function() {
        const timeLeft = animationEnd - Date.now();

        if (timeLeft <= 0) {
            return clearInterval(interval);
        }

        const particleCount = 50 * (timeLeft / duration);
        // запускаем конфетти с двух сторон
        confetti(Object.assign({}, defaults, { particleCount, origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 } }));
        confetti(Object.assign({}, defaults, { particleCount, origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 } }));
    }, 250);
}

    // --- Локализация ---
    const setLanguage = (lang) => {
        document.documentElement.lang = lang;
        localStorage.setItem('pmt-lang', lang);
        document.querySelectorAll('[data-translate-key]').forEach(el => {
            const key = el.dataset.translateKey;
            if(translations[lang][key]) el.textContent = translations[lang][key];
        });
        document.querySelectorAll('[data-translate-key-placeholder]').forEach(el => {
            const key = el.dataset.translateKeyPlaceholder;
            if(translations[lang][key]) el.placeholder = translations[lang][key];
        });
        document.querySelectorAll('[data-translate-key-title]').forEach(el => {
            const key = el.dataset.translateKeyTitle;
            if(translations[lang][key]) el.title = translations[lang][key];
        });
        langSwitcher.querySelector('.active').classList.remove('active');
        langSwitcher.querySelector(`[data-lang="${lang}"]`).classList.add('active');
    };

    langSwitcher.addEventListener('click', (e) => {
        if (e.target.tagName === 'BUTTON' && e.target.dataset.lang) {
            setLanguage(e.target.dataset.lang);
        }
    });

    // --- Темизация ---
    const setTheme = (theme) => {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('pmt-theme', theme);
        themeToggle.textContent = theme === 'dark' ? '🌙' : '☀️';
    };

    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
        setTheme(currentTheme === 'light' ? 'dark' : 'light');
    });

// --- Логика дерева файлов ---
function renderTree(nodes, container) {
    const ul = document.createElement('ul');
    nodes.forEach(node => {
        const li = document.createElement('li');
        li.dataset.path = node.path;

        const isDir = node.type === 'dir';
        li.className = isDir ? 'dir-item' : 'file-item';

        if (isDir) {
            li.classList.add('collapsed');
        }

        const itemDiv = document.createElement('div');
        itemDiv.className = 'tree-item';

        const toggler = document.createElement('span');
        toggler.className = 'toggler';
        if (!isDir) toggler.style.visibility = 'hidden';

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.checked = true;

        // --- НОВАЯ ЛОГИКА ИКОНОК ЗДЕСЬ ---
        const iconEl = document.createElement('i');
        // Устанавливаем атрибут, который Lucide будет искать
        iconEl.setAttribute('data-lucide', isDir ? 'folder' : 'file-text');
        // --- КОНЕЦ НОВОЙ ЛОГИКИ ---

        const nameSpan = document.createElement('span');
        nameSpan.className = 'item-name';
        nameSpan.textContent = node.name;

        // Собираем строку элемента: переключатель, чекбокс, иконка, имя
        itemDiv.append(toggler, checkbox, iconEl, nameSpan);
        li.appendChild(itemDiv);

        if (isDir && node.children) {
            renderTree(node.children, li);
        }
        ul.appendChild(li);
    });
    container.appendChild(ul);
}

    // --- Обработчики событий дерева (делегирование) ---
    fileTreeContainer.addEventListener('click', (e) => {
        const target = e.target;
        const li = target.closest('li');
        if (!li) return;

        if (target.matches('.item-name, .toggler') && li.classList.contains('dir-item')) {
            li.classList.toggle('collapsed');
        }

        if (target.type === 'checkbox') {
            const isChecked = target.checked;
            li.querySelectorAll('input[type="checkbox"]').forEach(childBox => {
                childBox.checked = isChecked;
                childBox.indeterminate = false;
            });
            updateParentCheckboxes(li);
        }
    });

    function updateParentCheckboxes(element) {
        let current = element.parentElement.closest('li');
        while (current) {
            const childCheckboxes = Array.from(current.querySelectorAll(':scope > ul > li > .tree-item > input[type="checkbox"]'));
            if (childCheckboxes.length === 0) {
                current = current.parentElement.closest('li');
                continue;
            }
            const checkedCount = childCheckboxes.filter(cb => cb.checked).length;
            const indeterminateCount = childCheckboxes.filter(cb => cb.indeterminate).length;
            const parentCheckbox = current.querySelector(':scope > .tree-item > input[type="checkbox"]');

            if (checkedCount === 0 && indeterminateCount === 0) {
                parentCheckbox.checked = false;
                parentCheckbox.indeterminate = false;
            } else if (checkedCount === childCheckboxes.length) {
                parentCheckbox.checked = true;
                parentCheckbox.indeterminate = false;
            } else {
                parentCheckbox.checked = false;
                parentCheckbox.indeterminate = true;
            }
            current = current.parentElement.closest('li');
        }
    }

    // --- Кнопка Сканировать ---
    async function performScan() {
        const path = pathInput.value.trim();
        const useGitignoreCheckbox = getEl('use-gitignore-checkbox');
        if (!path) {
            pathInput.focus();
            return;
        }
    fileTreeContainer.innerHTML = '...';
    projectView.classList.add('hidden');
    mergePanel.classList.add('hidden');
    resultView.classList.add('hidden');
    errorDiv.classList.add('hidden');

        try {
            const response = await fetch('/scan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                path: path,
                use_gitignore: useGitignoreCheckbox.checked // Отправляем состояние галочки
            })
            });
            const data = await response.json();

            fileTreeContainer.innerHTML = '';
            if (response.ok) {
                projectPath = data.project_path;
                projectNameEl.textContent = `${data.project_name}`;
                if(data.tree.length > 0) {
                    renderTree(data.tree, fileTreeContainer);
                    lucide.createIcons();
                    projectView.classList.remove('hidden');
                    mergePanel.classList.remove('hidden');
                } else {
                    errorDiv.textContent = 'В этой директории не найдено файлов для склейки (проверьте исключения).';
                    errorDiv.classList.remove('hidden');
                }
            } else {
                errorDiv.textContent = data.error || 'Произошла неизвестная ошибка.';
                errorDiv.classList.remove('hidden');
            }
        } catch (error) {
            errorDiv.textContent = 'Ошибка сети или сервера.';
            errorDiv.classList.remove('hidden');
        }
    }

    scanBtn.addEventListener('click', performScan);
    pathInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            performScan();
        }
    });

    // --- Кнопка Склеить ---
    mergeBtn.addEventListener('click', async () => {
        const checkedFiles = [];
        fileTreeContainer.querySelectorAll('li.file-item').forEach(li => {
            if (li.querySelector(':scope > .tree-item > input[type="checkbox"]').checked) {
                checkedFiles.push(li.dataset.path);
            }
        });

        if (checkedFiles.length === 0) {
            alert('Выберите хотя бы один файл.');
            return;
        }

            const exportFormat = document.querySelector('input[name="export-format"]:checked').value;
            const currentLang = localStorage.getItem('pmt-lang') || 'ru';
            const removeSecrets = getEl('remove-secrets-checkbox').checked;
            const clearForAI = getEl('clear-for-ai-checkbox').checked;

    try {
        const response = await fetch('/merge', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                files: checkedFiles,
                project_path: projectPath,
                format: exportFormat,
                lang: currentLang,
                remove_secrets: removeSecrets,
                clear_for_ai: clearForAI
            })
        });
            const data = await response.json();

            if (response.ok && data.success) {
                downloadLink.href = data.download_url;
                resultView.classList.remove('hidden');
                resultView.scrollIntoView({ behavior: 'smooth' });
                triggerConfetti();
            } else {
                errorDiv.textContent = data.error || 'Ошибка при склейке файлов.';
                errorDiv.classList.remove('hidden');
            }
        } catch (error) {
            errorDiv.textContent = 'Ошибка сети или сервера.';
            errorDiv.classList.remove('hidden');
        }
    });

    // --- Выбор папки ---
    folderPickerBtn.addEventListener('click', () => folderPicker.click());
    folderPicker.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            const firstFile = e.target.files[0];
            if (firstFile.webkitRelativePath) {
                 const fullPath = firstFile.webkitRelativePath;
                 const pathParts = fullPath.split('/');
                 if (pathParts.length > 1) {
                    pathInput.value = pathParts[0];
                 }
            } else {
                 // Fallback for browsers not supporting webkitRelativePath fully
                 // This is tricky and often not possible for security reasons
                 alert("Your browser doesn't fully support folder selection this way. Please enter the path manually.");
            }
        }
    });

    // --- Логика исключений ---
    const loadExclusions = async () => {
        try {
            const response = await fetch('/exclusions');
            const data = await response.json();
            getEl('ignore-dirs').value = data.dirs.join('\n');
            getEl('ignore-files').value = data.files.join('\n');
            getEl('ignore-exts').value = data.exts.join('\n');
        } catch(e) {
            console.error("Could not load exclusions", e);
        }
    };

    // --- Логика опций обработки ---
    const clearForAICheckbox = getEl('clear-for-ai-checkbox');
    const removeSecretsCheckbox = getEl('remove-secrets-checkbox');

clearForAICheckbox.addEventListener('change', () => {
    if (clearForAICheckbox.checked) {
        removeSecretsCheckbox.checked = true;
        removeSecretsCheckbox.disabled = true; // Блокируем, чтобы нельзя было отключить
    } else {
        removeSecretsCheckbox.disabled = false;
    }
});

    saveExclusionsBtn.addEventListener('click', async () => {
        const exclusions = {
            dirs: getEl('ignore-dirs').value.split('\n').map(s => s.trim()).filter(Boolean),
            files: getEl('ignore-files').value.split('\n').map(s => s.trim()).filter(Boolean),
            exts: getEl('ignore-exts').value.split('\n').map(s => s.trim()).filter(Boolean),
        };
        const response = await fetch('/exclusions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(exclusions)
        });
        const data = await response.json();
        const statusEl = getEl('exclusions-status');
        const lang = localStorage.getItem('pmt-lang') || 'ru';
        if (data.success) {
            statusEl.textContent = translations[lang].exclusionsSaved;
            statusEl.style.color = 'var(--success-color)';
        } else {
            statusEl.textContent = translations[lang].exclusionsError;
            statusEl.style.color = 'var(--error-color)';
        }
        setTimeout(() => statusEl.textContent = '', 3000);
    });


    // --- Инициализация при загрузке страницы ---
    const init = () => {
        const savedTheme = localStorage.getItem('pmt-theme') || 'light';
        const savedLang = localStorage.getItem('pmt-lang') || 'ru';
        setTheme(savedTheme);
        setLanguage(savedLang);
        loadExclusions();
        lucide.createIcons();
    };

    init();
});

