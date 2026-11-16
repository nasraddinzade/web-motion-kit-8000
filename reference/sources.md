# Источники

Прочитано 17.11.2026. Код не запускали и не ставили, взяты идеи и правила. Если лицензия некоммерческая или не указана, берём только идеи, без копирования кода и текста.

| # | Источник | Что это | Лицензия | Что взяли | Чего не брали |
|---|---|---|---|---|---|
| 1 | github.com/anthropics/skills, frontend-design | официальный навык дизайна интерфейса | Apache-2.0 | предмет решает первый экран, план из 4–6 цветов и ролей шрифта, список умолчаний сгенерированного дизайна, смелость в одном месте | — |
| 2 | github.com/Leonxlnx/taste-skill | самый популярный сторонний навык вкуса сайтов | MIT | чеклист готовности 2.5 (`ui-hardening.md`, раздел 7); вид бизнеса решает эффекты, одна секция на экран, равные края, ховеры, эффекты только для техники, фото для мест | свой проверяющий скрипт и хук остановки без согласия |
| 3 | github.com/MengTo/Skills (no-ai-design-slop, audit-ai-design-slop, build-awwwards-quality-sites, cinematic-scroll-storytelling, scroll-world-storytelling, scroll-scrubbed-visual-sequence, scroll-scrubbed-word-reveal, build-threejs-scroll-worlds, 3d-virtual-tour, optimize-web-animations, iterate-until-verified, globe-gl, игровые навыки) | большой набор навыков веба и 3D | MIT | почти всё про прокрутку, мир по прокрутке, тур, остановку вне экрана, шаблонность, проверку на ширинах | привязку к их браузеру и сервисам картинок |
| 4 | github.com/greensock/gsap-skills | официальные навыки GSAP | MIT | ставить в проект; transform и opacity, батчинг, stagger | — |
| 5 | github.com/cloudai-x/threejs-skills | three.js r186, R3F 9.8, drei 10.7, gltf-transform 4.5 | MIT | замер через renderer.info, вызовы отрисовки, инстансы, LOD, сжатие моделей | — |
| 6 | github.com/emalorenzo/three-agent-skills | 70+ правил R3F | MIT (в навыке) | не вызывать setState в useFrame, delta, отрисовка по требованию, видимость вместо перемонтирования | — |
| 7 | github.com/EnzeD/r3f-skills | навыки R3F по темам | не указана в файле | только обзор тем | текст и код |
| 8 | github.com/majidmanzarpour/threejs-game-skills | игры на three.js, режиссёр и специалисты | MIT | объём по словам человека, играбельный цикл первым, независимая проверка | генерацию ассетов по умолчанию |
| 9 | github.com/maplibre/maplibre-agent-skills | официальные навыки MapLibre | MIT | источники тайлов, PMTiles, рельеф, картография подписей | — |
| 10 | github.com/pbakaus/impeccable | дизайн-словарь и детектор шаблонности | Apache-2.0 | список шаблонных приёмов; привычки из craft-floor (`slop-patterns.md`); нагрузка на голову, устойчивость, базовые вещи сайта (`ui-hardening.md`); раздел animate (`motion-ui.md`). Прочитаны craft-floor, foundations, critique-rubric, harden, animate, polish, typeset, layout (заголовки) | команды целиком, CLI, живой режим |
| 11 | github.com/vercel-labs/agent-skills | правила веб-интерфейсов и React | MIT (в навыках) | общая проверка интерфейса | — |
| 12 | github.com/Ga14ctic/awwwards-skill | оркестратор навыков для сайтов уровня Awwwards | MIT | идея конвейера из фаз | его набор чужих пакетов |
| 13 | developers.google.com/maps/documentation/tile/policies и 3d-tiles | правила Map Tiles API | правила | запреты на хранение, анализ, обязательная атрибуция | — |
| 14 | mapsplatform.google.com, вопросы о Photorealistic 3D Tiles | разъяснения Google | правила | бренд и данные в атрибуции, запрет программных измерений | — |
| 15 | web.dev/articles/vitals | Core Web Vitals | — | LCP 2,5 с, INP 200 мс, CLS 0,1 | — |
| 16 | 12 роликов из Instagram о сайтах с анимацией (разбор в соседнем репозитории: clip-maker-8000/reference/reel-references.md) | реклама генераторов и библиотек промтов | чужие видео, не храним | сайт-кино по кадрам, 3D-сцены, карты на 3D-тайлах | обещания «один промт = сайт» |
| 17 | github.com/emilkowalski/skills (emil-design-eng, animate, choreograph, review-animations, break-ui) | навыки дизайн-инженера Эмиля Ковальского | MIT | решение «двигать ли», кривые, длительности, физика, хореография группы, формат «было, стало, почему» (`motion-ui.md`); худшие данные (`ui-hardening.md`) | навыки целиком, Swift, Expo, Sonner |
