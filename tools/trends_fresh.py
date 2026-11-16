#!/usr/bin/env python3
"""Свежесть сведений о моде: не просрочен ли reference/trends.md.

Файл держит строку «Пересмотреть до: ГГГГ-ММ-ДД». Если сегодня позже, код 1 и подсказка:
перед направлением найти свежие тенденции (поиск, не память), обновить файл по CONTRIBUTING.md.

Пример: python trends_fresh.py                 (берёт ../reference/trends.md, дата сегодня)
        python trends_fresh.py --today 2027-03-01
        python trends_fresh.py --selftest      (проверка самого скрипта на заведомо плохом входе)
"""
import argparse
import datetime as dt
import pathlib
import re
import sys
import tempfile

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

RE = re.compile(r"Пересмотреть до:\s*(\d{4}-\d{2}-\d{2})")


def check(path, today):
    text = pathlib.Path(path).read_text(encoding="utf-8")
    m = RE.search(text)
    if not m:
        print(f"{path}: нет строки «Пересмотреть до: ГГГГ-ММ-ДД»")
        return 1
    due = dt.date.fromisoformat(m.group(1))
    if today > due:
        print(f"ПРОСРОЧЕНО: сведения о моде надо было пересмотреть до {due}, сегодня {today}.")
        print("Перед направлением найди свежие тенденции поиском (не по памяти), обнови reference/trends.md")
        print("и дату пересмотра по CONTRIBUTING.md, потом продолжай.")
        return 1
    print(f"Сведения о моде свежие, пересмотр до {due} (осталось {(due - today).days} дн.).")
    return 0


def selftest():
    with tempfile.TemporaryDirectory() as d:
        p = pathlib.Path(d) / "t.md"
        p.write_text("Пересмотреть до: 2026-01-01\n", encoding="utf-8")
        bad = check(p, dt.date(2026, 6, 1))
        good = check(p, dt.date(2025, 12, 1))
        p.write_text("без даты\n", encoding="utf-8")
        nodate = check(p, dt.date(2026, 6, 1))
    ok = bad == 1 and good == 0 and nodate == 1
    print("САМОПРОВЕРКА", "пройдена" if ok else "ПРОВАЛЕНА")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", default=str(pathlib.Path(__file__).resolve().parent.parent / "reference" / "trends.md"))
    ap.add_argument("--today")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    sys.exit(check(a.path, dt.date.fromisoformat(a.today) if a.today else dt.date.today()))
