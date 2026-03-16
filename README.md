# Basketball Parser BBF — Context Guide

## Project Overview

Python-проект для парсинга баскетбольной статистики с белорусских соревнований. Данные извлекаются из API `org.infobasket.su` (используется сайтом `belarus.russiabasket.ru`).

**Основной функционал:**
- Парсинг турнирных таблиц (standings)
- Генерация шахматки результатов (crosstable)
- Детальный парсинг статистики игроков по отдельным матчам
- Экспорт данных в CSV

## Project Structure

```
parser_BBF/
├── main.py           # CLI-интерфейс: выбор сезона и этапа турнира
├── stats_parser.py   # Расчёт standings и crosstable
├── match_parser.py   # Парсинг статистики отдельного матча
├── requirements.txt  # Зависимости Python
├── README.md         # Документация
└── venv/             # Виртуальное окружение
```

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `requests` | 2.32.5 | HTTP-запросы к API |
| `pandas` | 3.0.1 | Обработка данных, CSV-экспорт |
| `numpy` | 2.4.3 | Вычисления (через pandas) |
| `certifi`, `urllib3`, `charset-normalizer`, `idna` | — | SSL и HTTP (зависимости requests) |
| `python-dateutil`, `tzdata`, `six` | — | Утилиты дат (зависимости pandas) |

**Python:** 3.14

## Building and Running

### Setup

```bash
# Активация виртуального окружения
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/macOS

# Установка зависимостей
pip install -r requirements.txt
```

### Usage

**1. Парсинг турнира (standings + crosstable):**
```bash
python main.py
```
- Ввести ID сезона (например, `50788`)
- Выбрать номер этапа из списка
- На выходе: `standings_<ID>_<этап>.csv` и `crosstable_<ID>_<этап>.csv`

**2. Парсинг отдельного матча:**
```bash
python match_parser.py <GAME_ID>
```
Пример: `python match_parser.py 1016417`

На выходе: `match_<ID>_players.csv` и `match_<ID>_teams_total.csv`

## API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `Widget/CompIssue/{id}` | Список этапов сезона |
| `Widget/CompTeamResults/{id}` | Результаты команд (standings) |
| `Widget/CrossTable/{id}` | Результаты матчей (crosstable) |
| `Widget/GetOnline/{game_id}` | Протокол матча |
| `Api/GetOnlinePlays/{game_id}` | Play-by-play лог событий |

**Headers для всех запросов:**
```python
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...',
    'Referer': 'https://belarus.russiabasket.ru/'
}
```

## Output Data Formats

### standings_*.csv
| Column | Description |
|--------|-------------|
| Место | Позиция в таблице |
| Команда | Название + город |
| И | Игры сыграно |
| В | Победы |
| П | Поражения |
| Забито | Очков забито |
| Пропущено | Очков пропущено |
| Очки | Турнирные очки (2 за победу, 1 за поражение) |
| +/- | Разница забитых/пропущенных |
| % | Процент побед |

### crosstable_*.csv
Матрица результатов между командами:
- Формат: `Счёт` + `д` (дома) / `г` (в гостях)
- Для будущих матчей: `(дата)`
- Диагональ: `---`

### match_*_players.csv
| Column | Description |
|--------|-------------|
| Команда, Имя, №, Роль | Информация об игроке |
| Мин | Игровое время (MM:SS) |
| Очки, 2-очк, 3-очк, ШБ | Броски |
| Подборы (O/D/T) | Подборы (атака/защита/всего) |
| ГП, ПХ, ПТ, БШ, Ф, ФС | Голевые, перехваты, потери, блокшоты, фолы, фолы на игроке |
| +/- | Плюс/минус |
| КПИ | Коэффициент полезности |

## Development Conventions

### Code Style
- **Язык комментариев:** Русский
- **Именование:** snake_case для функций и переменных
- **Обработка ошибок:** Try-except блоки с выводом в консоль
- **Вспомогательные функции:** `safe_int()`, `safe_split_shots()` для защиты от None/некорректных данных

### Architecture Patterns
- **Модульность:** Отдельные файлы для разных типов парсинга
- **CLI-интерфейс:** Интерактивный ввод через `input()`
- **Экспорт:** CSV с кодировкой `utf-8-sig` (для Excel)

### Testing Practices
- Тестов не обнаружено
- Верификация через ручной запуск и проверку CSV-файлов

## Known Issues / Notes

1. **API нестабильно:** Структура может измениться (неофициальное API)
2. **Два режима парсинга матчей:**
   - Live/свежие: реконструкция из play-by-play лога (`parse_from_log`)
   - Архивные: готовые данные из JSON (`parse_from_final_json`)
3. **Молодёжная статистика:** Может встречаться в данных, пропускается в шахматке
4. **Расчёт КПИ:** `(Очки + Подборы + Ассисты + Перехваты + Блокшоты + Фолы на) - (Промахи + Потери + Фолы)`

## Git Info

- `.gitignore` исключает: `__pycache__/`, `venv/`, `*.csv`, IDE-файлы, OS-файлы
- Сгенерированные CSV не коммитятся
