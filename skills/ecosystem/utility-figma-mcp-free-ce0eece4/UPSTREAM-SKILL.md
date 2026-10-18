---
name: figma-mcp-free
allowed-tools: [Bash, Read, mcp__figma]
description: Визуализация блоков, микросервисов, архитектуры, user flow, UI-мокапов в Figma через MCP на бесплатном Starter-плане. Claude Code / Codex / Cursor создают и редактируют узлы на холсте через Figma Plugin API (не Dev Mode MCP). Интегрирован с your design stack (DESIGN_HARNESS, pantheon-style, impeccable, ui-ux-pro-max), copywriter stack (content-writing, content-writing-ru) и VHumanize для финального текста. Триггеры RU/EN — "нарисуй схему", "визуализируй архитектуру", "блок-схема в figma", "figma diagram", "draw architecture", "visualize microservices", "мокап в figma", "создай wireframe".
composes_with:
  - pantheon-style             # design tokens and aesthetics applied to Figma canvas
  - figma-diagram-visualization # diagram layout algorithm for structured diagrams
  - contentos-pipeline         # copy/text content sourced from ContentOS for UI mockups
---

# Figma MCP Free — your integrated skill

Работает **без платного плана Figma**. Обходим Dev Mode MCP (6 вызовов/мес) через **Figma Plugin API** — бесплатно и без квот. Этот скилл **оркестрирует** design / copy / vhumanize стеки на Figma-холсте: не заменяет их, а включает в правильном порядке.

## Канонические файлы the (workspace registry)

| Файл | Тип | Назначение | URL / fileKey |
|---|---|---|---|
| **Claude Diagrams Greg** | FigJam | Архитектуры, микросервисы, user flow, roadmaps, sprints, mindmaps | `Dsw4ztrhdZ3LIGKs62IUv0` — https://www.figma.com/board/Dsw4ztrhdZ3LIGKs62IUv0/Claude-Diagrams-the |
| **Claude UI Greg** | Design | UI-мокапы your (лендинги, Pantheon, курс, Lumen, клиентские интерфейсы) | `BDXiP8mNc4NeVCa7wNWtFT` — https://www.figma.com/design/BDXiP8mNc4NeVCa7wNWtFT/Claude-UI-the |

**Правило:** по умолчанию работаем в этих двух файлах, Pages внутри — по доменам (`Pantheon`, `Course`, `Lumen`, `re:cover`, `your site`). Новые файлы заводим только когда Page становится тесен или нужен внешний шэринг.

## Когда использовать (триггеры)

- «нарисуй схему / блок-схему / диаграмму в figma», «визуализируй архитектуру / микросервисы / user flow»
- «сделай карточки для backlog / roadmap / sprint»
- «мокап лендинга / экрана / формы в figma», «wireframe / wireframe в figma»
- «экспорт PNG для Notion / README»
- «покажи как это устроено визуально»

## Как выбрать файл (FigJam vs Design)

Плагин `editorType: ["figma", "figjam"]` — работает в обоих, но node-types **разные**:

| Задача | Файл | Почему |
|---|---|---|
| Архитектура, микросервисы, блок-схемы, user flow, roadmaps, mindmaps, sprints | **FigJam** (`Claude Diagrams Greg`) | `ConnectorNode` (стрелки липнут к блокам), `ShapeWithTextNode` (блок+текст одной командой), `StickyNode`, `StampNode`, Sections |
| UI-мокапы, лендинги, интерфейсы, design system | **Design** (`Claude UI Greg`) | Components + Variants + Instance Overrides, полный Auto-layout, pixel-perfect typography, Styles, Variables |
| Смешанное | два файла, разные Pages | В Design нет ConnectorNode; в FigJam нет богатых компонентов |

**FigJam-only MCP-tools:** `create_connections`, `set_default_connector`, `create_shape_with_text`.

## Ограничения Starter (бесплатно)

| Параметр | Лимит | Обход |
|---|---|---|
| Team project files | 3 Design + 3 FigJam | Работаем в **Drafts** (unlimited) ← где и живут файлы the |
| Editor seats | 2 | the + агент = ок |
| Multi-user edit | только view | Один редактор |
| Dev Mode MCP | 6 вызовов/мес | **Не используем — обходим через Plugin API** |
| Figma AI `generate_figma_design` | заблокирован | **Не нужен — рисует Claude Code** |
| Plugin API | без квот | ✅ ядро стека |

---

## Интеграция с your design stack

**SSOT:** `claude/DESIGN_HARNESS.md` (каскад), `claude/SKILL_ORCHESTRATION.md` (конфликты/порядок), `.claude/skills/pantheon-style/SKILL.md` (токены HWAI).

### Каскад для Figma-задач

```
Запрос от Greg
    │
    ▼
[brainstorming]        ← если задача не микро (≥3 блока, ≥1 неизвестное решение)
    │
    ▼
[ui-ux-pro-max]        ← только для UI-мокапов в Design: палитра/шрифты/spacing
    │   (для диаграмм — сразу pantheon-style токены без ui-ux-pro-max)
    ▼
[pantheon-style]       ← HWAI-токены: цвета, шрифты, spacing — default для всех HWAI-артефактов
    │
    ▼
[figma-mcp-free]       ← создание/редактирование узлов через MCP
    │
    ▼
[impeccable /audit]    ← проверка: контраст, типографика, spacing rhythm, anti-AI-slop
    │
    ▼
[impeccable /polish]   ← финальный проход только ПОСЛЕ audit (critique → polish, не обратно)
    │
    ▼
[export_node_as_image] ← PNG → Notion / README / чат
```

### Pantheon-style токены (применять по умолчанию)

Из `.claude/skills/pantheon-style/SKILL.md`. Переводим в Figma fills:

**Dark mode (основная тема HWAI):**
- Background: `#181818`
- Raised surface: `#1e1e1e` (cards), `#252526` (subtle), `#2d2d30` (hover)
- Text: `#e4e4e4` primary, `#b8b8b8` dim, `#8a8a8a` muted, `#6a6a6a` faint
- Borders: `rgba(255,255,255,0.12)` default, `rgba(255,255,255,0.22)` strong — **видимые**, не hairline
- Accent: `#33ffff` cyan

**Light mode:**
- Background: `#fafaf9`
- Accent: `#0891b2` cyan

**Fonts** (в Figma установить локально или взять Web Fonts):
- Display: **Instrument Serif** italic (Google Fonts)
- Body: **Inter**
- Mono: **JetBrains Mono**

**Spacing base:** 4px. Кратные: 4/8/12/16/24/32/48/64.
**Content max:** 1200px для UI-мокапов.

**Правило (HWAI):** любой блок-диаграмма / мокап **по умолчанию** использует эти токены. Отклонение — только если the явно просит другую палитру или это клиентский проект с заданным брендом.

### Conflict resolution (из SKILL_ORCHESTRATION.md §B)

| Ситуация | Правило |
|---|---|
| «сделай ярче» vs «убавь» | Не в одном проходе. По умолчанию **quieter** для production. |
| `distill` vs `overdrive` | Сначала `distill`, при необходимости `overdrive` вторым проходом. |
| `critique` vs `polish` | **Всегда:** критика → затем полировка. Не наоборот. |
| Спешка vs verify | `verification-before-completion` + E2E обязательны перед «готово». |

### impeccable команды (применимые к Figma)

После создания холста **обязательно** прогнать:
- `/audit` — контраст ≥4.5:1 текст, spacing rhythm 4/8, нет Inter+purple gradient (anti-slop)
- `/normalize` — если блоки расползлись по стилям — привести к единому
- `/polish` — финальный проход
- `/critique` — если нужна критика (до polish)

---

## Интеграция с copywriter stack

**SSOT:** `~/.claude/skills/content-writing/SKILL.md` (EN), `~/.claude/skills/content-writing-ru/SKILL.md` (RU), `claude/SKILL_ORCHESTRATION.md` §B (язык = взаимоисключающий финальный текст).

### Язык текста на холсте — правило

1. **Весь текст в Page на одном языке.** Не миксовать RU/EN в одной диаграмме без явного двуязычного режима.
2. **EN-финальный текст** (лендинги, международные презентации, GitHub README диаграммы) → `content-writing` до создания узла, не «придумать подпись на ходу».
3. **RU-финальный текст** (внутренние диаграммы HWAI, презентации the на русском, клиентам RU) → `content-writing-ru`. Не переводить с EN калькой.
4. **Технические подписи** (имена сервисов, порты, методы HTTP, названия таблиц) — lingua franca, не требуют copywriter passes.

### Когда copywriter skill обязателен

| Задача | Skill | Почему |
|---|---|---|
| Заголовки секций лендинга (мокап в Claude UI) | `content-writing` или `content-writing-ru` | Finальный копирайт идёт в прод |
| Карточки ценностных пропозиций, CTA | copywriter | То же |
| Stickers / заметки на FigJam-диаграмме — рабочие заметки the | не нужен | Внутреннее |
| Подписи блоков архитектуры (`pantheon-api`, `Gatus`, `:3055`) | не нужен | Технические имена |
| Описание микросервиса 1–2 строки в ShapeWithText — если отдаём клиенту | copywriter | Публичный артефакт |

### Pipeline (когда на холсте финальный копирайт)

```
Бриф копирайта
    │
    ▼
[content-writing или content-writing-ru]  ← черновик
    │
    ▼
[vhumanize detect]          ← проверка AI-detection
    │
    ▼
[vhumanize humanize_and_check]  ← при AI > 20% — переписать до цели
    │
    ▼
[figma-mcp-free set_text_content]  ← применить финальный текст на холсте
    │
    ▼
[impeccable /audit]         ← typography / контраст / длины строк на узлах
```

---

## Интеграция с VHumanize

**SSOT:** `your reference doc`, `project conventions` правило «feedback_ai_text_check» (MANDATORY).

### Когда обязательно

Любой текст на Figma-холсте, который **пойдёт в прод** (лендинг, презентация клиентам, публичная диаграмма в README / Notion public page, пост в соцсети, рекламный баннер) — пропускаем через VHumanize перед применением в Figma через `set_text_content`.

### Когда не нужно

- Внутренние диаграммы для команды (Proteus Shield workflows, your ops)
- Черновики, which the перепишет руками
- Технические имена узлов

### Endpoint (через MCP proxy, внешний доступ)

```
POST https://your-api.example.com/humanize/detect
POST https://your-api.example.com/humanize/humanize_and_check

Header: Authorization: Bearer <MCP_BEARER_TOKEN>
Body:   {"text": "…"}
```

**Цель:** `ai_probability ≤ 0.20` (метрика из content-writing). Если выше — итерировать `humanize_and_check` до цели, ИЛИ отдать обратно в `content-writing` для переписывания с измененной структурой.

### Edge case

VHumanize лучше работает на EN. Для RU-текста использовать в первую очередь `content-writing-ru` (нативное письмо без калек) — AI-detection на русском менее стабилен, VHumanize как вторичный pass.

---

## Триггеры и маршрутизация (что Claude делает автоматически)

| Фраза the | File | Skills chain |
|---|---|---|
| «нарисуй архитектуру X» | FigJam | pantheon-style tokens → figma-mcp-free → /audit |
| «блок-схема / user flow / roadmap» | FigJam | как выше |
| «мокап лендинга / формы / экрана» | Design | brainstorming → ui-ux-pro-max → pantheon-style → figma-mcp-free → /audit → /polish |
| «мокап + текст CTA для прода» | Design | как выше + content-writing/ru → vhumanize → set_text_content |
| «stickers / заметки по спринту» | FigJam | figma-mcp-free без copywriter |
| «экспорт в PNG» | любой | figma-mcp-free `export_node_as_image` |
| «purify / убери переводный русский» на существующем холсте | любой | content-writing-ru → scan_text_nodes → set_multiple_text_contents |

---

## Установка на машине the (ЗАВЕРШЕНА 2026-04-14)

### Факт-чек установленного

| Компонент | Путь / состояние |
|---|---|
| Bun | `` v1.3.11 |
| Клонированный репо (нужен для socket.ts) | `~/code/cursor-talk-to-figma-mcp/` (grab fork) |
| WebSocket socket server | launchd agent `ai.yourname.figma-socket`, порт **3055** |
| launchd plist | `~/Library/LaunchAgents/ai.yourname.figma-socket.plist` (KeepAlive=true, RunAtLoad=true) |
| MCP регистрация (Claude Code) | `claude mcp add figma --  cursor-talk-to-figma-mcp@latest` — **✓ Connected** |
| MCP регистрация (Cursor) | `~/.cursor/mcp.json` записан |
| Figma Desktop | требуется the — плагины работают только в нём |
| Плагин в файлах | требуется the — install from Community в `Claude Diagrams Greg` и `Claude UI Greg` |

### Команды, которые сработали (копировать для воспроизведения на новой машине)

```bash
# 0. Bun (если нет)
curl -fsSL https://bun.sh/install | bash

# 1. Клонировать grab fork (npm-пакет НЕ содержит src/socket.ts)
mkdir -p ~/code && cd ~/code
git clone --depth=1 https://github.com/grab/cursor-talk-to-figma-mcp
cd cursor-talk-to-figma-mcp && bun install

# 2. launchd plist (см. содержимое в ~/Library/LaunchAgents/ai.yourname.figma-socket.plist)
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/ai.yourname.figma-socket.plist

# 3. MCP для Claude Code
claude mcp add figma --  cursor-talk-to-figma-mcp@latest
claude mcp list   # подтверждение "figma ... ✓ Connected"

# 4. MCP для Cursor (~/.cursor/mcp.json)
# JSON: { "mcpServers": { "figma": { "command": "
#        "args": ["cursor-talk-to-figma-mcp@latest"] } } }

# Debug
launchctl print gui/$(id -u)/ai.yourname.figma-socket | head -20
lsof -iTCP:3055 -sTCP:LISTEN
tail /tmp/figma-socket.log
```

### Подключение к файлу (каждая новая сессия Claude Code)

**Важно:** MCP tools загружаются при старте Claude Code. Если `figma` MCP был добавлен мид-сессионно — перезапусти Claude Code (или открой новый чат).

1. Открыть в Figma Desktop файл (`Claude Diagrams Greg` для FigJam / `Claude UI Greg` для Design).
2. Plugins → *Cursor Talk to Figma MCP* → **Connect**.
3. Плагин покажет **channel ID** (короткая строка).
4. В чате: «Подключись к каналу `<ID>`» — агент вызовет `join_channel <ID>`.
5. Дальше обычные команды (create_rectangle, create_connections, export_node_as_image и т.д.).

### Управление launchd сервисом

```bash
# Stop
launchctl bootout gui/$(id -u)/ai.yourname.figma-socket

# Start (если выгружен)
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/ai.yourname.figma-socket.plist

# Restart (после правки plist)
launchctl bootout gui/$(id -u)/ai.yourname.figma-socket
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/ai.yourname.figma-socket.plist

# Логи
tail -f /tmp/figma-socket.log
tail -f /tmp/figma-socket.err
```

---

## Инструменты MCP (полный список)

**Создание:** `create_rectangle`, `create_frame`, `create_text`, `create_shape_with_text` (FigJam), `create_component_instance`
**Стили:** `set_fill_color`, `set_stroke_color`, `set_corner_radius`
**Текст:** `set_text_content`, `set_multiple_text_contents`, `scan_text_nodes`
**Layout:** `move_node`, `resize_node`, `clone_node`, `delete_node`, `delete_multiple_nodes`
**Auto-layout:** `set_layout_mode`, `set_padding`, `set_axis_align`, `set_layout_sizing`, `set_item_spacing`
**Чтение:** `get_document_info`, `get_selection`, `read_my_design`, `get_node_info`, `get_nodes_info`, `set_focus`, `set_selections`
**Коннекторы/стрелки:** `create_connections`, `set_default_connector`, `get_reactions` (FigJam)
**Аннотации:** `set_annotation`, `set_multiple_annotations`, `get_annotations`, `scan_nodes_by_types`
**Экспорт:** `export_node_as_image` (PNG/SVG)
**Компоненты:** `get_local_components`, `get_instance_overrides`, `set_instance_overrides`, `get_styles`

---

## Verification (obligatory, не happy path)

### Перед «готово» (каждый раз)

- [ ] `get_document_info` — счётчик узлов совпадает с ожидаемым
- [ ] `export_node_as_image` PNG создан и приложен к ответу (или сохранён в артефакты)
- [ ] Для UI-мокапов: `impeccable /audit` прогнан, P0/P1 исправлены
- [ ] Для диаграмм HWAI: блоки совпадают с `your catalog config` (или явно указано, что диаграмма отклоняется)
- [ ] Для финального копирайта на холсте: AI-detection ≤ 20% (vhumanize) для прод-артефактов
- [ ] Language consistency: весь текст на одном языке (или явный двуязычный режим)

### Если что-то не совпадает

Не писать «готово». Дать Greg:
1. Скриншот / PNG
2. Что не прошло чеклист
3. Вариант фикса (1–2 строки)

---

## Типовые промпты-вызовы

**Архитектура (FigJam):**
> Нарисуй в `Claude Diagrams Greg` на Page `Pantheon` архитектуру из `your catalog config`: pantheon-ui, pantheon-api, Gatus, contact-scraper-api. Соедини ConnectorNode по HTTP-потоку, подпиши порты. Pantheon dark tokens (#181818 bg, #e4e4e4 text, #33ffff accent). Экспорт PNG → приложи.

**UI-мокап (Design):**
> В `Claude UI Greg` на Page `Course` сделай hero-секцию для лендинга Claude Code Course: заголовок, сабтайтл, CTA-кнопка, визуал справа. Используй pantheon-style tokens. Копирайт через content-writing-ru → vhumanize (прод). После создания — `impeccable /audit`.

**Обновление текста на существующем холсте:**
> В `Claude UI Greg` Page `Pantheon` пройдись `scan_text_nodes`, прогони тексты через content-writing-ru (фикс калек), затем `set_multiple_text_contents`. Экспорт PNG.

---

## Gotchas & known bugs (SSOT mirror — full entries in `claude/KNOWLEDGE_BASE.md` § Figma Plugin API)

**Агенту читать ПЕРЕД большой сессией создания нод в Figma. Каждая строка — реальный инцидент, не гипотеза.**

| Гоча | Симптом | Фикс |
|---|---|---|
| **`create_connections` с `text: ""` наследует текст default-connector** | Все новые стрелки показывают label, который был у предыдущей (напр. «uses UI») | **Всегда** передавать осмысленный `text` (payload / event name). Если нужен пустой — временно сменить default-connector на такой же пустой |
| **Child coords = relative to parent frame** | Текст внутри sub-frame пропал / клипнут | При `parentId=X`: x, y считаются от origin X (не абсолют). Проверка: `get_node_info` → `absoluteBoundingBox` |
| **`set_default_connector` обязателен первым** | `No default connector set` | Попросить the нарисовать один connector (Shift+L) → `set_default_connector` без аргументов (авто-pick). Сохраняется на сессию, но **теряется при удалении исходного коннектора** |
| **`set_text_content` не работает на CONNECTOR** | `Error: Node is not a text node` | Чтобы изменить label — **delete + recreate** через `create_connections` с новым `text` |
| **FigJam connector hotkey = Shift+L, НЕ K** | `K` ничего не открывает | `Shift+L` ИЛИ иконка стрелки в нижнем toolbar ИЛИ hover края блока → синий `+` |
| **Channel отваливается после idle** | `Must join a channel before sending commands` | Повторный `join_channel <id>` — мгновенно, state не теряется |
| **Plugin работает ТОЛЬКО в Figma Desktop** | В браузере MCP tools не отвечают | Открыть файл в Desktop-приложении, plugin → Connect, взять новый channel ID |
| **Нет `create_page` tool** | Не могу создать новый Figma Page (tab) | Размещать «pages» как sibling-frames на одном canvas, экспортить по отдельности |
| **Connector label position наследуется** | Label далеко от линии (в странном месте) | Default-connector template влияет. Для горизонтальных потоков брать горизонтальный template; для коротких прямых — Figma auto-правит |
| **`move_node` использует parent coords** | Узел «телепортируется» при переносе | Считать `target_abs - parent_abs` перед `move_node`. Или итеративно по `absoluteBoundingBox` |

**Паттерн «defensive create»:**
1. **Frames** — пассуй абсолютные координаты, `parentId` — ТОЛЬКО корневой frame страницы (или nothing для root-уровня).
2. **Text/rects внутри карточек** — всегда **relative** к card's origin. Не пассуй абсолют.
3. **Connections** — всегда передавай **непустой** `text` (payload/event), даже если label кажется лишним. Лишний label в худшем случае добавит информацию; пустой наследует «мусор».
4. **Export** — после большой партии делать `export_node_as_image(page_frame_id)`, визуально проверять, что текст виден и label'ы корректны. Никаких «готово» без этой проверки.

## Troubleshooting

| Симптом | Причина / фикс |
|---|---|
| `Cannot connect to WebSocket` | `bunx …@latest socket` не запущен |
| Plugin «Disconnected» | Socket упал, `lsof -iTCP:3055` |
| `join_channel` ошибка | ID с лишними пробелами |
| Узлы создаются, но не видны | Другой Page — `set_focus` или переключить вручную. **Или** текст с абсолют-координатами внутри под-frame (см. Gotchas) |
| `Font not loaded` | Нужно загрузить шрифт явно (Inter / Instrument Serif / JetBrains Mono) |
| ConnectorNode не работает | Файл Design, не FigJam. Переоткрыть Diagrams |
| ShapeWithText не создаётся | То же — FigJam only |
| Starter upgrade nag | Игнор. Работаем в Drafts + Plugin API |
| Connector показывает чужой label (напр. «uses UI») | Наследование от default-connector. Delete + recreate с непустым `text`. См. Gotchas. |
| `No default connector set` / `Default connector not found` | Нужен существующий connector на canvas. Попроси the нарисовать один (Shift+L), затем `set_default_connector` |
| Текст клипнут / невидим, находится далеко за bounds | `parentId`-child с абсолют-координатами. Пересчитать как relative к parent origin и `move_node`. |

---

## Связанные SSOT

- `claude/DESIGN_HARNESS.md` — design каскад и когда какой skill
- `claude/SKILL_ORCHESTRATION.md` — конфликты skills, порядок, скептик
- `.claude/skills/pantheon-style/SKILL.md` — your токены (цвета/шрифты/spacing)
- `~/.claude/skills/impeccable/` — audit/polish/critique/normalize
- `~/.claude/skills/ui-ux-pro-max/` — design system generator (для UI-мокапов)
- `~/.claude/skills/content-writing/` — EN копирайт
- `~/.claude/skills/content-writing-ru/` — RU копирайт
- `your reference doc` — VHumanize endpoints и auth
- `your catalog config` — источник истины для your микросервис-диаграмм
- `project conventions` — E2E / verification правила
