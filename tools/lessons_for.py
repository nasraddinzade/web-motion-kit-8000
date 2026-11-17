#!/usr/bin/env python3
"""Уроки нужного типа из reference/lessons.md и проверка меток.

У каждого урока сразу под заголовком строка метки:
  Тип: сайт. Проект: Glow. Применять: сайт.
  Тип: 3D-сцена. Проект: X. Применять: 3D-сцена, игра.
  Тип: общее. Проект: репозиторий. Применять: все.
«Тип» откуда урок, «Применять» к каким типам он относится. «общее» значит ко всем.

  python lessons_for.py --type сайт            уроки для рекламы и общие
  python lessons_for.py --type игра
  python lessons_for.py --type сайт --titles   только заголовки
  python lessons_for.py --check                   у каждого урока верная метка (код 1, если нет)
  python lessons_for.py --selftest                проверка самого скрипта на плохом и хорошем входе
"""
import argparse, pathlib, re, sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

TYPES = ["сайт", "история по прокрутке", "3D-сцена", "карта", "игра"]
SUBTYPES = {}
GENERAL = "общее"
# Заголовок урока, которому метка обязательна: дата, номер раздела «# 01.», «Версия», «Дополнение».
REQUIRED = re.compile(r"^#{1,2} (\d{4}-\d{2}-\d{2}|\d{2}\.|Версия|Дополнение)")
HEADING = re.compile(r"^#{1,3} ")
TAG = re.compile(r"^Тип: (.+?)\. Проект: (.+?)\. Применять: (.+?)\.\s*$")
ITEM = re.compile(r"^(\S.*?)(?: \((.+)\))?$")


def parse_item(text):
    m = ITEM.match(text.strip())
    return (m.group(1), m.group(2)) if m else (text.strip(), None)


def tag_errors(kind, sub, where):
    errs = []
    if kind not in TYPES and kind != GENERAL:
        errs.append(f"{where}: неизвестный тип «{kind}», можно: {', '.join(TYPES + [GENERAL])}")
    if sub and (kind not in SUBTYPES or sub not in SUBTYPES[kind]):
        errs.append(f"{where}: неизвестный подтип «{sub}» у типа «{kind}»")
    return errs


def parse(text):
    """Единицы уроков: заголовок с меткой и текст до следующего заголовка с меткой."""
    lines = text.splitlines()
    units, errors, cur = [], [], None
    for i, line in enumerate(lines):
        if not HEADING.match(line):
            if cur:
                cur["body"].append(line)
            continue
        tag = None
        for j in range(i + 1, min(i + 4, len(lines))):
            if lines[j].strip():
                tag = TAG.match(lines[j].strip())
                break
        if tag:
            kind, sub = parse_item(tag.group(1))
            apply = [parse_item(x) for x in tag.group(3).split(",")]
            where = f"строка {i + 1}"
            errors += tag_errors(kind, sub, where)
            for a, s in apply:
                if a != "все":
                    errors += tag_errors(a, s, where + ", Применять")
            cur = {"title": line.lstrip("# ").strip(), "line": i + 1, "type": (kind, sub),
                   "project": tag.group(2), "apply": apply, "body": [line]}
            units.append(cur)
        else:
            if REQUIRED.match(line):
                errors.append(f"строка {i + 1}: у урока нет строки «Тип: ... Проект: ... Применять: ...» сразу под заголовком: {line[:70]}")
            if cur:
                cur["body"].append(line)
    return units, errors


def applies(unit, kind, sub):
    for a, s in unit["apply"]:
        if a in ("все", GENERAL):
            return True
        if a == kind and (s is None or sub is None or s == sub):
            return True
    return False


def selftest():
    good = "# 01. Урок\nТип: игра. Проект: А. Применять: игра, общее.\nтекст\n## 2026-01-01. Второй\nТип: сайт. Проект: Б. Применять: сайт.\nтекст\n"
    bad1 = "## 2026-01-01. Без метки\nтекст\n"
    bad2 = "## 2026-01-01. Чужой тип\nТип: мультик. Проект: В. Применять: сайт.\n"
    u, e = parse(good)
    ok = not e and len(u) == 2 and [x["title"][:2] for x in u if applies(x, "сайт", None)] == ["01", "20"]
    ok = ok and [x["title"][:2] for x in u if applies(x, "игра", None)] == ["01"]
    ok = ok and parse(bad1)[1] and parse(bad2)[1]
    print("selftest:", "ок" if ok else "ПРОВАЛ")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=str(pathlib.Path(__file__).resolve().parent.parent / "reference" / "lessons.md"))
    ap.add_argument("--type")
    ap.add_argument("--subtype")
    ap.add_argument("--titles", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    units, errors = parse(pathlib.Path(a.file).read_text(encoding="utf-8"))
    if a.check or not a.type:
        for e in errors:
            print(e)
        print(f"уроков с меткой: {len(units)}, ошибок: {len(errors)}")
        return 1 if errors else 0
    if a.type not in TYPES:
        print(f"неизвестный тип «{a.type}», можно: {', '.join(TYPES)}")
        return 1
    chosen = [u for u in units if applies(u, a.type, a.subtype)]
    print(f"Уроки для типа «{a.type}{' (' + a.subtype + ')' if a.subtype else ''}»: {len(chosen)} из {len(units)}. Уроки других типов сюда не вошли и без причины не применяются.\n")
    for u in chosen:
        if a.titles:
            k, s = u["type"]
            print(f"строка {u['line']}: {u['title']}  [из: {k}{' (' + s + ')' if s else ''}, {u['project']}]")
        else:
            print("\n".join(u["body"]).rstrip() + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
