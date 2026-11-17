#!/usr/bin/env python3
"""Проверка согласованности самого репозитория правил (не проекта сайта).

Запускай перед каждым коммитом в репозиторий. Код 1, если есть ошибки.
Что ловит:
  1. навык без SKILL.md, с неверным name или пустым description, либо не упомянутый в README.md;
  2. скрипт в tools/ без строки в tools/README.md;
  3. ссылки на файлы репозитория (в обратных кавычках и markdown), которых нет;
  4. маркеры слияния git;
  5. два раздела с одинаковым номером «# 03.» в одном файле;
  6. строки, похожие на ключи и токены;
  7. урок в reference/lessons.md без метки «Тип: ... Проект: ... Применять: ...».
Чего не ловит: противоречия по смыслу. Их ищи через grep по ключевым словам и числам правила
(см. CONTRIBUTING.md, разделы 1 и 4).

Пример: python check_repo.py            (корень берётся от места скрипта)
        python check_repo.py /путь/к/копии
"""
import pathlib
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parent.parent
errors = []

# Переименования. Пополняй вместе с таблицей в CONTRIBUTING.md, раздел 6.
RENAMED = {}


def err(path, line, text):
    rel = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
    errors.append(f"{rel}:{line}  {text}" if line else f"{rel}  {text}")


def files(*suffixes):
    for p in sorted(ROOT.rglob("*")):
        if ".git" in p.parts or "projects" in p.parts or "node_modules" in p.parts or not p.is_file() or p.suffix not in suffixes:
            continue
        yield p


def read(p):
    return p.read_text(encoding="utf-8", errors="replace")


# 1. навыки
readme = read(ROOT / "README.md") if (ROOT / "README.md").exists() else ""
skills_dir = ROOT / ".claude" / "skills"
for d in sorted(skills_dir.iterdir()) if skills_dir.exists() else []:
    if not d.is_dir():
        continue
    sk = d / "SKILL.md"
    if not sk.exists():
        err(d, 0, "нет SKILL.md")
        continue
    m = re.match(r"^---\n(.*?)\n---", read(sk), re.S)
    if not m:
        err(sk, 1, "нет блока frontmatter (--- name, description ---)")
        continue
    name = re.search(r"^name:\s*(.+)$", m.group(1), re.M)
    desc = re.search(r"^description:\s*(.+)$", m.group(1), re.M)
    if not name or name.group(1).strip() != d.name:
        err(sk, 2, f"name должен совпадать с папкой «{d.name}»")
    if not desc or not desc.group(1).strip():
        err(sk, 3, "пустой description")
    if d.name not in readme:
        err(ROOT / "README.md", 0, f"навык {d.name} не упомянут в таблице «Что внутри»")

# 2. скрипты
tools_readme = ROOT / "tools" / "README.md"
tr = read(tools_readme) if tools_readme.exists() else ""
for p in sorted((ROOT / "tools").glob("*.py")) if (ROOT / "tools").exists() else []:
    if not p.name.startswith("_") and p.name not in tr:
        err(tools_readme, 0, f"скрипт {p.name} не описан в tools/README.md")

PATH_RE = re.compile(r"^(?:\.\./)*(?:reference|prompts|tools|\.claude)/[\w./-]+$|^(?:CLAUDE|README|CONTRIBUTING)\.md$")
SECRET_RE = re.compile(
    r"sk_[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16}"
    r"|xi-api-key\s*[:=]\s*\S{12,}|ELEVEN\w*\s*=\s*[A-Za-z0-9_-]{16,}"
)

for p in files(".md", ".py"):
    text = read(p)
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        # 4. маркеры слияния
        if line.startswith("<<<<<<< ") or line.startswith(">>>>>>> "):
            err(p, i, "маркер слияния git, конфликт не разрешён")
        # 6. ключи
        if SECRET_RE.search(line):
            err(p, i, "строка похожа на ключ или токен, в репозиторий их не пишем")
        # 3. ссылки на файлы репозитория
        if p.suffix == ".md":
            cands = [m.group(1) for m in re.finditer(r"`([^`\n]+)`", line)]
            cands += [m.group(1) for m in re.finditer(r"\]\(([^)\s]+)\)", line)]
            for c in cands:
                tok = c.split()[0].split("#")[0].rstrip(".,;:")
                if not tok or "*" in tok or "<" in tok or not PATH_RE.match(tok):
                    continue
                tok = tok.rstrip("/")
                if not ((p.parent / tok).exists() or (ROOT / tok.lstrip("./")).exists()
                        or (ROOT / re.sub(r"^(?:\.\./)+", "", tok)).exists()):
                    err(p, i, f"ссылка на несуществующий путь «{tok}»")
    # 5. повторные номера разделов
    if p.suffix == ".md":
        nums = re.findall(r"^# (\d+)\.", text, re.M)
        for n in sorted({n for n in nums if nums.count(n) > 1}):
            err(p, 0, f"два раздела с номером «# {n}.», новые разделы нумеруй датой, не номером")
    # 6. старые имена переименованных навыков и файлов (список в CONTRIBUTING.md, раздел 6)
    if p.name not in ("CONTRIBUTING.md", "check_repo.py"):
        for i, line in enumerate(text.splitlines(), 1):
            for old, new in RENAMED.items():
                if old in line:
                    err(p, i, f"старое имя «{old}», теперь «{new}»")

for old, new in RENAMED.items():
    if (ROOT / ".claude" / "skills" / old).exists():
        err(ROOT / ".claude" / "skills" / old, 0, f"папка со старым именем навыка, перенеси в «{new}»")

# 7. Метки уроков в reference/lessons.md: откуда урок и к каким типам он применяется.
try:
    sys.path.insert(0, str(ROOT / "tools"))
    import lessons_for
    _lp = ROOT / "reference" / "lessons.md"
    if _lp.exists():
        _units, _lerr = lessons_for.parse(_lp.read_text(encoding="utf-8"))
        for _e in _lerr:
            err(_lp, None, "урок: " + _e)
except ImportError:
    err(ROOT / "tools", None, "нет tools/lessons_for.py")

if errors:
    print("ОШИБКИ репозитория:")
    for e in errors:
        print("  " + e)
    print(f"Итого {len(errors)}.")
    sys.exit(1)
print("Репозиторий согласован: навыки, скрипты, ссылки, номера, маркеры слияния, ключи, старые имена, метки уроков.")
