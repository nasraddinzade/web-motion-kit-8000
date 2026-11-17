# Скрипты

Зависимости: Python 3.10+, ffmpeg в PATH, для `browser_check.py` Playwright для Python и Chromium или Chrome (путь в переменной `CHROME`) (путь можно задать переменной `FFMPEG`). Запускай из корня репозитория или проекта, пути передавай аргументами.

| Скрипт | Что делает | Запуск |
|---|---|---|
| `frames.py` | видео → кадры WebP для прокрутки по кадрам, `manifest.json` с весом, лист кадров | `python tools/frames.py видео.mp4 --out frames/desktop --width 1600 --fps 30` · `--selftest` |
| `browser_check.py` | страница в настоящем браузере: ширины 390–1440, горизонтальная прокрутка, ошибки консоли, LCP и CLS с замедлением процессора на 390, первый экран без JavaScript и без анимации, видео экрана по `--video`, окно с видеокартой по `--headed`, горизонтальная прокрутка на всех ширинах 320–1440 шагом 10 по `--sweep` | `python tools/browser_check.py http://localhost:3000 --out qa/run1` · `--selftest` |
| `trends_fresh.py` | не просрочены ли сведения о моде в `reference/trends.md` | `python tools/trends_fresh.py`, `--selftest` |
| `lessons_for.py` | уроки нужного типа проекта из `reference/lessons.md` и проверка, что у каждого урока есть метка типа | `python lessons_for.py --type сайт --titles` · `--check` · `--selftest` |
| `check_repo.py` | проверка самого репозитория правил: навыки и скрипты в индексах, битые ссылки, маркеры слияния, повторные номера, похожие на ключи строки | `python tools/check_repo.py` |

Чего скрипты не делают: не проверяют вкус и путь посетителя. Это `web-qa` в настоящем браузере. Проверки конкретного проекта (Playwright, замеры) пишутся в проекте, каждую сначала прогоняй на заведомо плохом входе.
