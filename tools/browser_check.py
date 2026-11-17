#!/usr/bin/env python3
"""Проверка страницы в настоящем браузере (Playwright, Chromium).

Для каждой ширины (по умолчанию 390, 768, 1024, 1440): скриншот всей страницы, горизонтальная
прокрутка, ошибки консоли и страницы, LCP и CLS. Плюс скриншот первого экрана без JavaScript
и с prefers-reduced-motion. На 390 замер с замедлением процессора в 4 раза.
Пишет report.json и скриншоты в --out. Код 1, если есть горизонтальная прокрутка, ошибки
консоли или метрики вне бюджета.

Пример: python tools/browser_check.py http://localhost:3000 --out qa/run1
        python tools/browser_check.py http://localhost:3000/catalog --widths 390,1440 --video
        python tools/browser_check.py http://localhost:3000 --sweep   # ещё ширины 320–1440 шагом 10
        python tools/browser_check.py --selftest

По умолчанию браузер без окна: он рисует программно (SwiftShader), без видеокарты. Размытие
(backdrop-filter), WebGL, скругления движущихся слоёв и тени там выходят иначе, чем у посетителя.
Для движения, скруглений и WebGL запускай с --headed (окно браузера, видеокарта компьютера) и
смотри на настоящем телефоне. Скрипт пишет в report.json, каким рендером снимал.

Не проверяет: путь посетителя (клики до результата пиши сценарием в проекте), вкус, звук.
Нужен Playwright для Python (pip install playwright) и Chromium или Chrome
(путь можно задать переменной CHROME).
"""
import argparse
import http.server
import json
import os
import pathlib
import shutil
import socketserver
import sys
import tempfile
import threading

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from playwright.sync_api import sync_playwright

VITALS_JS = """
window.__lcp = 0; window.__cls = 0;
try {
  new PerformanceObserver(l => { for (const e of l.getEntries()) window.__lcp = e.startTime; })
    .observe({type: 'largest-contentful-paint', buffered: true});
  new PerformanceObserver(l => { for (const e of l.getEntries()) if (!e.hadRecentInput) window.__cls += e.value; })
    .observe({type: 'layout-shift', buffered: true});
} catch (e) {}
"""


def launch(p, headed=False):
    exe = os.environ.get("CHROME")
    if not exe:
        for c in ("/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser"):
            if os.path.exists(c):
                exe = c
                break
    kw = {"headless": not headed}
    try:
        return p.chromium.launch(**kw)
    except Exception:
        if not exe:
            raise
        return p.chromium.launch(executable_path=exe, **kw)


def check(url, out, widths, lcp_max, cls_max, video, headed=False):
    out = pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)
    report = {"url": url, "widths": {}, "problems": [],
              "render": "окно браузера, видеокарта" if headed else
              "без окна, программный рендер: движение, скругления, размытие и WebGL проверь ещё с --headed"}
    with sync_playwright() as p:
        browser = launch(p, headed)
        for w in widths:
            h = 844 if w < 600 else (1024 if w < 1100 else 900)
            opts = {"viewport": {"width": w, "height": h}}
            if video:
                opts["record_video_dir"] = str(out / f"video_{w}")
            ctx = browser.new_context(**opts)
            ctx.add_init_script(VITALS_JS)
            page = ctx.new_page()
            errors = []
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda e: errors.append(str(e)))
            if w < 600:
                cdp = ctx.new_cdp_session(page)
                cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})
            page.goto(url, wait_until="load")
            page.wait_for_timeout(1500)
            sw = page.evaluate("Math.max(document.documentElement.scrollWidth, document.body ? document.body.scrollWidth : 0)")
            cw = page.evaluate("document.documentElement.clientWidth")
            lcp = page.evaluate("window.__lcp")
            cls = page.evaluate("window.__cls")
            page.screenshot(path=str(out / f"full_{w}.png"), full_page=True)
            row = {"scrollWidth": sw, "clientWidth": cw, "overflow": sw > cw + 1,
                   "lcp_ms": round(lcp), "cls": round(cls, 3), "console_errors": errors[:20],
                   "cpu_throttle": 4 if w < 600 else 1}
            report["widths"][w] = row
            if row["overflow"]:
                report["problems"].append(f"{w}: горизонтальная прокрутка {sw} > {cw}")
            if errors:
                report["problems"].append(f"{w}: ошибки консоли {len(errors)}")
            if not lcp:
                report.setdefault("notes", []).append(f"{w}: LCP не измерен, бюджет загрузки не проверен")
            if lcp and lcp > lcp_max:
                report["problems"].append(f"{w}: LCP {round(lcp)} мс > {lcp_max}")
            if cls > cls_max:
                report["problems"].append(f"{w}: CLS {round(cls, 3)} > {cls_max}")
            ctx.close()
        for name, opts in (("no_js", {"java_script_enabled": False}), ("reduced_motion", {"reduced_motion": "reduce"})):
            ctx = browser.new_context(viewport={"width": 390, "height": 844}, **opts)
            page = ctx.new_page()
            page.goto(url, wait_until="load")
            page.wait_for_timeout(800)
            page.screenshot(path=str(out / f"{name}_390.png"))
            ctx.close()
        browser.close()
    report["ok"] = not report["problems"]
    (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def sweep(url, start=320, stop=1440, step=10, headed=False):
    """Ширины между проверочными: горизонтальная прокрутка на каждой ширине с шагом step.
    Ломается часто не на 390 или 768, а между ними (сайт SOS: ряд значков перенёсся на 410)."""
    bad = []
    with sync_playwright() as p:
        browser = launch(p, headed)
        ctx = browser.new_context(viewport={"width": start, "height": 844})
        page = ctx.new_page()
        page.goto(url, wait_until="load")
        page.wait_for_timeout(800)
        for w in range(start, stop + 1, step):
            page.set_viewport_size({"width": w, "height": 844 if w < 600 else 900})
            page.wait_for_timeout(120)
            sw = page.evaluate("Math.max(document.documentElement.scrollWidth, document.body ? document.body.scrollWidth : 0)")
            cw = page.evaluate("document.documentElement.clientWidth")
            if sw > cw + 1:
                bad.append(w)
        ctx.close()
        browser.close()
    return bad


GOOD = "<!doctype html><meta name=viewport content='width=device-width'><h1>Хорошо</h1><p>Текст.</p>"
BAD = ("<!doctype html><meta name=viewport content='width=device-width'><h1>Плохо</h1>"
       "<div style='width:2000px;height:20px;background:red'></div><script>console.error('сломано')</script>")


MIDDLE = ("<!doctype html><meta name=viewport content='width=device-width'><style>"
          "@media (min-width:400px) and (max-width:420px){.x{width:600px}}</style>"
          "<p>Тест.</p><div class=x style='height:20px;background:red'></div>")


def selftest():
    d = pathlib.Path(tempfile.mkdtemp())
    (d / "good.html").write_text(GOOD, encoding="utf-8")
    (d / "bad.html").write_text(BAD, encoding="utf-8")
    (d / "middle.html").write_text(MIDDLE, encoding="utf-8")
    handler = lambda *a, **k: http.server.SimpleHTTPRequestHandler(*a, directory=str(d), **k)
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        g = check(f"http://127.0.0.1:{port}/good.html", d / "g", [390, 1440], 2500, 0.1, False)
        b = check(f"http://127.0.0.1:{port}/bad.html", d / "b", [390, 1440], 2500, 0.1, False)
        m_fixed = check(f"http://127.0.0.1:{port}/middle.html", d / "m", [390, 768], 2500, 0.1, False)
        m_sweep = sweep(f"http://127.0.0.1:{port}/middle.html", 320, 800, 10)
        g_sweep = sweep(f"http://127.0.0.1:{port}/good.html", 320, 800, 10)
    finally:
        httpd.shutdown()
    ok_good = g["ok"]
    ok_bad = (not b["ok"]) and any("горизонтальная" in x for x in b["problems"]) and any("консоли" in x for x in b["problems"])
    print(f"хорошая страница без проблем -> {'ок' if ok_good else 'ОШИБКА ' + str(g['problems'])}")
    print(f"плохая страница поймана (прокрутка и консоль) -> {'ок' if ok_bad else 'ОШИБКА ' + str(b['problems'])}")
    ok_mid = m_fixed["ok"] and m_sweep and all(400 <= x <= 420 for x in m_sweep) and not g_sweep
    print(f"ширины 390 и 768 пропускают поломку около 410, прогон с шагом её ловит {m_sweep} -> {'ок' if ok_mid else 'ОШИБКА'}")
    shutil.rmtree(d, ignore_errors=True)
    sys.exit(0 if ok_good and ok_bad and ok_mid else 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url", nargs="?")
    ap.add_argument("--out", default="qa")
    ap.add_argument("--widths", default="390,768,1024,1440")
    ap.add_argument("--lcp", type=int, default=2500, help="предел LCP, мс")
    ap.add_argument("--cls", type=float, default=0.1, help="предел CLS")
    ap.add_argument("--video", action="store_true", help="записать видео экрана на каждой ширине")
    ap.add_argument("--sweep", action="store_true", help="ещё прогон ширин 320–1440 с шагом 10: горизонтальная прокрутка между проверочными ширинами")
    ap.add_argument("--headed", action="store_true", help="окно браузера с видеокартой: для движения, скруглений, размытия и WebGL")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
    if not a.url:
        ap.error("укажи адрес или --selftest")
    r = check(a.url, a.out, [int(x) for x in a.widths.split(",")], a.lcp, a.cls, a.video, a.headed)
    if a.sweep:
        bad = sweep(a.url, headed=a.headed)
        r["sweep_overflow_widths"] = bad
        if bad:
            r["problems"].append(f"горизонтальная прокрутка между проверочными ширинами: {bad}")
            r["ok"] = False
    print(json.dumps(r, ensure_ascii=False, indent=2))
    sys.exit(0 if r["ok"] else 1)


if __name__ == "__main__":
    main()
