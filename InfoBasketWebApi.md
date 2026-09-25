# InfoBasket WebApi — Полная техническая спецификация
> **Версия документации:** 23.03.2015  
> **Оригинал:** ИнфоБаскет (статистическая система РФБ, АСБ и региональных лиг)  
> **Статус документа:** Препарировано, отфакчекано и переведено в Markdown с подробным разбором архитектурных извращений.

---

## Оглавление

1. [Введение](#1-введение)
2. [Общее описание формата запроса и архитектурный ад](#2-общее-описание-формата-запроса)
3. [Справочники](#3-справочники)
   - [GetCountries](#getcountries)
   - [GetRegions](#getregions)
   - [GetArenas](#getarenas)
4. [Соревнования](#4-соревнования)
   - [TeamStandings](#teamstandings)
   - [RoundRobin](#roundrobin)
   - [CrossTable](#crosstable)
   - [Playoff](#playoff)
   - [Schedule](#schedule)
   - [Results](#results)
   - [Onlines](#onlines)
   - [BestPlayers](#bestplayers)
   - [BestTeams](#bestteams)
   - [GetBestPlayerParameters & GetBestPlayerColumns](#getbestplayerparameters--getbestplayercolumns)
   - [GetBestTeamParameters & GetBestTeamColumns](#getbestteamparameters--getbestteamcolumns)
5. [Игры](#5-игры)
   - [GamePage](#gamepage)
   - [GameBoxScore](#gameboxscore)
6. [Команды](#6-команды)
   - [TeamPage](#teampage)
   - [TeamInfo](#teaminfo)
   - [TeamRoster](#teamroster)
   - [TeamStats](#teamstats)
   - [TeamGames](#teamgames)
   - [GetTeamSeasons](#getteamseasons)
   - [GetTeamComps](#getteamcomps)
   - [GetTeamLogo](#getteamlogo)
7. [Персоны (Игроки, Тренеры, Судьи)](#7-персоны)
   - [GetPersonPhoto](#getpersonphoto)
   - [Player](#player)
   - [PlayerInfo](#playerinfo)
   - [PlayerTeams](#playerteams)
   - [PlayerStats](#playerstats)
   - [Coach](#coach)
   - [CoachInfo](#coachinfo)
   - [CoachTeams](#coachteams)
   - [Referee](#referee)
   - [RefereeInfo](#refereeinfo)
   - [RefereeGames](#refereegames)
8. [Стили оформления (CSS / Bootswatch)](#8-стили-оформления)
9. [Структуры возвращаемых данных (DTO / Модели БД)](#9-структуры-возвращаемых-данных)

---

## 1. Введение

Этот документ описывает API информационной системы **ИнфоБаскет** — древней, как говно мамонта, но незаменимой хуеверти, на которой держится весь российский студенческий (АСБ) и региональный баскетбол.

На момент релиза API жило по двум основным дырам (базам данных):
* `http://www.infobasket.ru/reg/` — База данных региональных соревнований (всякие чемпионаты областей, краев и пердимоноклей).
* `http://www.infobasket.ru/asb/` — База данных Ассоциации студенческого баскетбола (АСБ).

*(Примечание: в реальной жизни протокол сейчас часто форсится на HTTPS, а поддомены могут резолвиться как `reg.infobasket.ru` и `asb.infobasket.ru`, но корни уходят именно в эти URL-ы).*

---

## 2. Общее описание формата запроса

Разрабы этой системы решили совместить ужа с ежом: их бэкенд умеет плеваться как готовыми HTML-виджетами для вставки на сайты убогих спорткомитетов через `<iframe>`, так и чистым JSON для тех мазохистов, кто решил натянуть этот зоопарк на свой фронтенд. Запросы на фотки и логотипы тупо выплевывают бинарный поток картинок (`image/jpeg`, `image/png`).

### Шаблон стандартного запроса:
```http
GET /Api/{QueryName}/{Id}[?parameter1=value1[&parameter2=value2...[&format=json]]]
```

* **`format=json`** — **Священный Грааль**. Если не передать этот параметр, сервер высрет кусок кривой HTML-разметки. Если дописать `&format=json` (или `?format=json`), бэкенд соблаговолит отдать чистый JSON.
* Параметры со значениями по умолчанию в таблицах ниже выделены **жирным шрифтом**.
* **Магическая звездочка (`*`)**: В параметрах ссылок (`gameLink`, `teamLink`, `playerLink` и т.д.) можно передать тупо символ `*`. Тогда бэкенд подставит стандартные URL-ы тестовой страницы самого ИнфоБаскета.

### Шаблон запросов-справочников (начинающихся с `Get`):
```http
GET /Api/Get{QueryName}/[{Id}][?parameter1=value1[&parameter2=value2...]]
```
* **Важное правило:** Запросы, чьё имя начинается с префикса `Get` (например, `GetCountries`, `GetPersonPhoto`), **никогда не возвращают HTML-виджеты**. Они плюются исключительно JSON-ом либо картинками (JPEG/PNG).

### Встраивание виджетов на клиентские сайты:
1. **Через костыльный `<iframe>`** — базовый вариант тех лет.
2. **Через DIV и JS-скрипт** (обещали сделать «позже»):
```html
<div class="InfoBasket WidgetName" data-id="1" data-db="reg"></div>
<script src="http://www.infobasket.ru/Scripts/InfoBasket.js" type="text/javascript"></script>
```

---

## 3. Справочники

Общие справочные данные: страны, города, спортзалы. Никакого HTML, только JSON.

### GetCountries
* **Версия:** `v.1.0`
* **Назначение:** Список стран.
* **Формат ответа:** JSON (Массив объектов `Country`).
* **Эндпоинт:**
  * `/Api/GetCountries` — отдать все страны скопом.
  * `/Api/GetCountries/{Id}` — инфа по конкретной стране.

| Параметр | Тип | Описание |
| :--- | :--- | :--- |
| `Id` | `int` | ID страны в базе |

**Примеры запросов:**
* `http://www.infobasket.ru/reg/Api/GetCountries`
* `http://www.infobasket.ru/asb/Api/GetCountries/1`

---

### GetRegions
* **Версия:** `v.1.0`
* **Назначение:** Список городов и регионов.
* **Формат ответа:** JSON (Массив объектов `Region`).
* **Эндпоинт:**
  * `/Api/GetRegions`
  * `/Api/GetRegions/{Id}`

| Параметр | Тип | Описание |
| :--- | :--- | :--- |
| `Id` | `int` | ID города/региона |
| `start` | `string` | Начальные буквы названия города (автокомплит) |
| `country` | `int` | Фильтр по ID страны |

**Примеры запросов:**
* `http://www.infobasket.ru/reg/Api/GetRegions`
* `http://www.infobasket.ru/asb/Api/GetRegions/1`
* `http://www.infobasket.ru/reg/Api/GetRegions/?start=A`
* `http://www.infobasket.ru/asb/Api/GetRegions/?start=Mo&country=1`

---

### GetArenas
* **Версия:** `v.1.0`
* **Назначение:** Список спортивных арен и залов.
* **Формат ответа:** JSON (Массив объектов `Arena`).
* **Эндпоинт:**
  * `/Api/GetArenas`
  * `/Api/GetArenas/{Id}`

| Параметр | Тип | Описание |
| :--- | :--- | :--- |
| `Id` | `int` | ID арены *(в оригинальной доке авторы упоролись и написали "ID города", но это ID самой арены)* |
| `start` | `string` | Начальные буквы названия арены |
| `country` | `int` | Фильтр по ID страны |
| `region` | `int` | Фильтр по ID региона *(есть в примерах вызова: `?region=1`)* |

**Примеры запросов:**
* `http://www.infobasket.ru/reg/Api/GetArenas`
* `http://www.infobasket.ru/asb/Api/GetArenas/1`
* `http://www.infobasket.ru/reg/Api/GetArenas/?start=А`
* `http://www.infobasket.ru/asb/Api/GetArenas/?region=1`

---

## 4. Соревнования

Турнирные таблицы, расписания, плей-офф, онлайны и индивидуальные топы игроков.

### TeamStandings
* **Версия:** `v.1.0`
* **Назначение:** Универсальная турнирная таблица (положение команд).
* **Формат ответа:** HTML или JSON (Массив `Comp`).
* **Вызов:** `/Api/TeamStandings/{Id}`

| Параметр | Тип | По умолчанию | Описание и допустимые значения |
| :--- | :--- | :--- | :--- |
| `Id` | `int` | — | ID турнира (соревнования) |
| `lang` | `string` | `ru` | Язык ответа: `ru` или `en` |
| `teamLink` | `string` | — | Шаблон ссылки на команду, напр. `'/Api/TeamPage/{id}'` или `*` |
| `style` | `string` | **`Default`** | CSS-стиль оформления виджета (см. раздел [Стили](#8-стили-оформления)) |
| `full` | `string` | **`1`** | `0`, `no`, `false` — краткий вид; **`1`**, `yes`, `true` — полный вид |
| `region` | `string` | **`1`** | `0`, `no`, `false` — скрыть регион; **`1`**, `yes`, `true` — показать регион |
| `percent` | `string` | **`1`** | `0`, `no`, `false` — скрыть процент побед; **`1`**, `yes`, `true` — показать |
| `avgPoints` | `string` | **`1`** | `0`, `no`, `false` — сумма очков; **`1`**, `yes`, `true` — среднее за игру |
| `header` | `string` | — | `0` — скрыть заголовок турнира, `1` — краткий, `2` — полный |

**Примеры:**
* `http://www.infobasket.ru/reg/Api/TeamStandings/4119`
* `http://www.infobasket.ru/reg/Api/TeamStandings/2566?avgPoints=1`
* `http://www.infobasket.ru/asb/Api/TeamStandings/13388`
* `http://www.infobasket.ru/asb/Api/TeamStandings/13373?region=0`

---

### RoundRobin
* **Версия:** `v.1.0`
* **Назначение:** Классическая таблица кругового турнира.
* **Формат ответа:** HTML или JSON (Массив `CompTeam`).
* **Вызов:** `/Api/RoundRobin/{Id}`
* **Параметры:** Идентичны `TeamStandings` (`lang`, `teamLink`, `style`, `full`, `region`, `percent`, `avgPoints`, `header`).

**Примеры:**
* `http://www.infobasket.ru/reg/Api/RoundRobin/4537`
* `http://www.infobasket.ru/reg/Api/RoundRobin/4143?region=0&percent=1&avgPoints=1`
* `http://www.infobasket.ru/asb/Api/RoundRobin/13329?full=0`
* `http://www.infobasket.ru/asb/Api/RoundRobin/13450?header=1`
* `http://www.infobasket.ru/asb/Api/RoundRobin/13450?format=json`

---

### CrossTable
* **Версия:** `v.1.0`
* **Назначение:** Таблица результатов матчей типа "шахматка" (сетка кто с кем как сыграл).
* **Формат ответа:** HTML или JSON (Массив `CrossTeam` / `GameScore`).
* **Вызов:** `/Api/CrossTable/{Id}`

| Параметр | Тип | По умолчанию | Описание |
| :--- | :--- | :--- | :--- |
| `Id` | `int` | — | ID турнира |
| `lang` | `string` | `ru` | `ru` / `en` |
| `teamLink` | `string` | — | Шаблон ссылки на команду |
| `style` | `string` | **`Default`** | CSS тема |
| `full` | `string` | **`1`** | `0`, `no`, `false` — чистая шахматка; **`1`**, `yes`, `true` — полный вид |
| `region` | `string` | **`1`** | `0`/`1` — видимость региона |
| `percent` | `string` | **`1`** | `0`/`1` — процент побед |
| `avgPoints` | `string` | **`1`** | `0` — сумма, `1` — среднее |
| `header` | `string` | — | `0` — скрыть, `1` — краткий, `2` — полный |

**Примеры:**
* `http://www.infobasket.ru/reg/Api/CrossTable/4537`
* `http://www.infobasket.ru/reg/Api/CrossTable/4143?region=0&percent=1&avgPoints=1`
* `http://www.infobasket.ru/asb/Api/CrossTable/13374?full=0`
* `http://www.infobasket.ru/asb/Api/CrossTable/13450?header=1`

---

### Playoff
* **Версия:** `v.1.0`
* **Назначение:** Сетка плей-офф (кубковая стадия на выбывание).
* **Формат ответа:** HTML или JSON (Массив `PlayoffPair`).
* **Вызов:** `/Api/Playoff/{Id}`

| Параметр | Тип | По умолчанию | Описание |
| :--- | :--- | :--- | :--- |
| `Id` | `int` | — | ID турнира |
| `lang` | `string` | `ru` | Язык |
| `teamLink` | `string` | — | Шаблон ссылки |
| `style` | `string` | **`Default`** | Тема оформления |
| `full` | `string` | **`1`** | `0` — краткая сетка; `1` — полная сетка |
| `region` | `string` | **`1`** | Показывать ли регион команды |
| `percent` | `string` | **`1`** | Процент побед |
| `header` | `string` | — | Заголовок турнира (`0`, `1`, `2`) |

**Примеры:**
* `http://www.infobasket.ru/reg/Api/Playoff/4460`
* `http://www.infobasket.ru/reg/Api/Playoff/4459?style=united`
* `http://www.infobasket.ru/reg/Api/Playoff/4080?style=cyborg&region=0`
* `http://www.infobasket.ru/reg/Api/Playoff/2571?style=yeti&header=0&lang=en`
* `http://www.infobasket.ru/reg/Api/Playoff/3261?style=Cerulean`
* `http://www.infobasket.ru/reg/Api/Playoff/3261?style=Sandstone`
* `http://www.infobasket.ru/reg/Api/Playoff/3135?style=Superhero`
* `http://www.infobasket.ru/reg/Api/Playoff/3135?style=Lumen&full=0&header=1`
* `http://www.infobasket.ru/asb/Api/Playoff/21034?style=Sandstone&full=1&header=1`
* `http://www.infobasket.ru/asb/Api/Playoff/21034?format=json`

---

### Schedule
* **Версия:** `v.1.0`
* **Назначение:** Расписание будущих и текущих игр.
* **Формат ответа:** HTML или JSON (Массив `Game`).
* **Вызов:** `/Api/Schedule/{Id}`

| Параметр | Тип | По умолчанию | Описание |
| :--- | :--- | :--- | :--- |
| `Id` | `int` | — | ID турнира |
| `lang` | `string` | `ru` | Язык |
| `style` | `string` | **`Default`** | CSS-тема |
| `from` | `string` | — | Дата «ОТ»: формат `YYYY-MM-DD` или ключевое слово `today` |
| `to` | `string` | — | Дата «ДО»: формат `YYYY-MM-DD` или `today` |
| `max` | `int` | — | Максимальное число строк в ответе (LIMIT) |
| `page` | `int` | — | Пагинация (размер страницы) |
| `teamLink` | `string` | — | Ссылка на команду, напр. `/Api/TeamPage/{id}` |
| `gameLink` | `string` | — | Ссылка на матч, напр. `/Api/Game/{id}` |
| `date` | `string` | — | Формат даты: `0` — скрыть; `1` — `dd.mm.yyyy`; `2` — `dd.mm`; `3` — `dd.mm.yyyy wd` (день недели); `4` — `dd.mm wd`. Отрицательные значения (`-1`, `-2`, `-3`, `-4`) скрывают повторяющиеся даты |
| `time` | `string` | — | Отображение времени: `0` — скрыть; `1` — местное; `2` — московское |
| `region` | `string` | **`1`** | Показывать регион команд (`0`/`1`) |
| `venue` | `string` | — | Колонки места проведения: `0` — скрыть; `1` — город; `2` — арена; `3` — город и арена |
| `comps` | `string` | — | Колонки иерархии турниров через запятую: `c` (чемпионат), `g` (пол/гендер), `l` (лига), `d` (дивизион), `s` (этап), `g` (группа/плей-офф), `r` (раунд). Можно задавать псевдонимы через дефис: `d-Округ,s-Регион` |
| `header` | `string` | — | Заголовок (`0` — скрыть, `1` — краткий, `2` — полный) |

**Примеры:**
* `http://www.infobasket.ru/reg/Api/Schedule/2566`
* `http://www.infobasket.ru/reg/Api/Schedule/4212?lang=ru&all=0&date=1&venue=2&time=1&comps=g,d-ФО&region=1&gameLink=%7Bhttp%7Dreg.infobasket.ru/Game/%7Bid%7D`
* `http://www.infobasket.ru/asb/Api/Schedule/13317?lang=en&style=Cyborg&date=3&max=20`
* `http://www.infobasket.ru/asb/Api/Schedule/13317?lang=en&header=0&venue=3&from=2015-02-25&to=2015-02-25&date=0&header=0`

---

### Results
* **Версия:** `v.1.0`
* **Назначение:** Результаты сыгранных матчей (только завершенные игры и текущий лайв).
* **Формат ответа:** HTML или JSON (Массив `Game`).
* **Вызов:** `/Api/Results/{Id}`
* **Параметры:** Полностью идентичны эндпоинту `Schedule` (`from`, `to`, `max`, `page`, `teamLink`, `gameLink`, `date`, `time`, `region`, `venue`, `comps`, `header`, `style`, `lang`).

**Примеры:**
* `http://www.infobasket.ru/reg/Api/Results/2566`
* `http://www.infobasket.ru/reg/Api/Results/4212?lang=ru&all=0&date=1&venue=2&time=1&comps=g,d-ФО&region=1&gameLink=%7Bhttp%7Dreg.infobasket.ru/Game/%7Bid%7D`
* `http://www.infobasket.ru/asb/Api/Results/13317?lang=en&style=Cyborg&date=3&max=20`
* `http://www.infobasket.ru/asb/Api/Results/13317?lang=en&header=0&venue=3&from=2015-02-25&to=2015-02-25&date=0&header=0`

---

### Onlines
* **Версия:** `v.0.1` *(бета-затычка)*
* **Назначение:** Матчи, которые идут прямо сейчас в режиме реального времени.
* **Формат ответа:** HTML или JSON (Массив `Game`).
* **Вызов:** `/Api/Onlines/{Id}`
* **Параметры:** Набор параметров тот же, что и у `Schedule` (за вычетом дат `from`/`to`, потому что онлайн происходит *прямо сейчас*).

**Примеры:**
* `http://www.infobasket.ru/reg/Api/Onlines/115?comps=g,c`
* `http://www.infobasket.ru/asb/Api/Onlines/12302`

---

### BestPlayers
* **Версия:** `v.1.0`
* **Назначение:** Индивидуальный рейтинг игроков турнира (лидеры по очкам, подборам, передачам и прочему добру).
* **Формат ответа:** HTML или JSON (Массив `BestPlayerResult`).
* **Вызов:** `/Api/BestPlayers/{Id}`

| Параметр | Тип | По умолчанию | Описание |
| :--- | :--- | :--- | :--- |
| `Id` | `int` | — | ID турнира |
| `lang` | `string` | `ru` | Язык |
| `style` | `string` | **`Default`** | CSS тема |
| `param` | `int` | **`1`** | Тип статистического рейтинга (список берется через `GetBestPlayerParameters`). По умолчанию 1 (обычно средняя результативность/очки) |
| `from` | `string` | — | Выборка игр «ОТ» (`YYYY-MM-DD`) |
| `to` | `string` | — | Выборка игр «ДО» (`YYYY-MM-DD`) |
| `max` | `int` | — | Топ-N игроков (LIMIT) |
| `page` | `int` | — | Номер/размер страницы |
| `playerLink`| `string` | — | Шаблон ссылки на профиль игрока |
| `teamLink` | `string` | — | Ссылка на команду |
| `gameLink` | `string` | — | Ссылка на игру |
| `region` | `string` | **`1`** | Показывать регион команды игрока |
| `header` | `string` | — | Заголовок (`0` — скрыть, `1` — краткий, `2` — полный) |

**Примеры:**
* `http://www.infobasket.ru/reg/Api/BestPlayers/2566?param=1&max=5`
* `http://www.infobasket.ru/asb/Api/BestPlayers/13317?param=19&max=10`
* `http://www.infobasket.ru/asb/Api/BestPlayers/13317?param=22&max=10`
* `http://www.infobasket.ru/asb/Api/BestPlayers/13317?param=53&max=10`

---

### BestTeams
* **Версия:** `v.1.0`
* **Назначение:** Командный рейтинг по статистическим показателям.
* **Формат ответа:** HTML или JSON (Массив `BestTeamResult`).
* **Вызов:** `/Api/BestTeams/{Id}`
* **Параметры:** Аналогичны `BestPlayers` (`Id`, `lang`, `style`, `param`, `from`, `to`, `max`, `page`, `teamLink`, `gameLink`, `region`, `header`). Список доступных `param` запрашивается через `GetBestTeamParameters`.

**Примеры:**
* `http://www.infobasket.ru/reg/Api/BestTeams/2566?param=1&max=5`
* `http://www.infobasket.ru/asb/Api/BestTeams/13317?param=19&max=10`
* `http://www.infobasket.ru/asb/Api/BestTeams/13317?param=22&max=10`
* `http://www.infobasket.ru/asb/Api/BestTeams/13317?param=53&max=10`

---

### GetBestPlayerParameters & GetBestPlayerColumns
Служебные методы, чтобы узнать, по каким метрикам вообще можно ранжировать игроков.

#### GetBestPlayerParameters
* **Версия:** `v.1.0`
* **Формат ответа:** JSON (Список объектов `{id, name}`).
* **Вызов:** `/Api/GetBestPlayerParameters`

| Параметр | Тип | Описание |
| :--- | :--- | :--- |
| `lang` | `string` | `ru` / `en` |
| `full` | `string` | `0`, `no`, `false` — краткое наименование параметра; `1`, `yes`, `true` — полное |

*Примеры:*
* `http://www.infobasket.ru/reg/Api/GetBestPlayerParameters`
* `http://www.infobasket.ru/asb/Api/GetBestPlayerParameters/?lang=ru&full=1`

#### GetBestPlayerColumns
* **Версия:** `v.1.0`
* **Формат ответа:** JSON (Массив строк / названий столбцов таблицы).
* **Вызов:** `/Api/GetBestPlayerColumns/{Id}`

| Параметр | Тип | Описание |
| :--- | :--- | :--- |
| `Id` | `int` | ID статистического параметра (тот самый `param` из `BestPlayers`) |
| `lang` | `string` | Язык заголовков |

*Примеры:*
* `http://www.infobasket.ru/reg/Api/GetBestPlayerColumns/1`
* `http://www.infobasket.ru/asb/Api/GetBestPlayerColumns/51?lang=en`

---

### GetBestTeamParameters & GetBestTeamColumns
То же самое, что и выше, только для командной статистики.

#### GetBestTeamParameters
* **Версия:** `v.1.0` | **Формат:** JSON (`{id, name}`)
* **Вызов:** `/Api/GetBestTeamParameters`
* **Параметры:** `lang`, `full` (`0`/`1`).

#### GetBestTeamColumns
* **Версия:** `v.1.0` | **Формат:** JSON (Массив строк)
* **Вызов:** `/Api/GetBestTeamColumns/{Id}`
* **Параметры:** `Id` (тип рейтинга команд), `lang`.

*Примеры:*
* `http://www.infobasket.ru/reg/Api/GetBestTeamParameters`
* `http://www.infobasket.ru/asb/Api/GetBestTeamParameters/?lang=ru&full=1`
* `http://www.infobasket.ru/reg/Api/GetBestTeamColumns/1`
* `http://www.infobasket.ru/asb/Api/GetBestTeamColumns/51?lang=en`

---

## 5. Игры

Детальная статистика конкретного матча (бокс-скор, протокол).

### GamePage
* **Версия:** `v.0.1` *(недопиленный алиас)*
* **Назначение:** Полные данные об игре. В текущей версии API бэкенд тупо перенаправляет вызов на `GameBoxScore`.
* **Формат ответа:** HTML или JSON (`GameStatsResult`).
* **Вызов:** `/Api/GamePage/{Id}`

| Параметр | Тип | По умолчанию | Описание |
| :--- | :--- | :--- | :--- |
| `Id` | `int` | — | ID игры в базе |
| `lang` | `string` | `ru` | Язык |
| `style` | `string` | **`Default`** | CSS тема |
| `teamLink` | `string` | — | Ссылка на команду (`/Api/TeamPage/{id}`) |
| `playerLink`| `string` | — | Ссылка на игрока (`/Api/Player/{id}`) |
| `coachLink` | `string` | — | Ссылка на тренера (`/Api/Coach/{id}`) |
| `refereeLink`| `string`| — | Ссылка на судью (`/Api/Referee/{id}`) |

**Примеры:**
* `http://www.infobasket.ru/reg/Api/GamePage/11566?playerLink=*&coachLink=*`
* `http://www.infobasket.ru/asb/Api/GamePage/45870?teamLink=*`

---

### GameBoxScore
* **Версия:** `v.1.0`
* **Назначение:** Полноценный баскетбольный бокс-скор (статистический протокол матча: игровое время, очки, подборы, фолы, броски со всех дистанций, тренеры, судьи).
* **Формат ответа:** HTML или JSON (`GameStatsResult`).
* **Вызов:** `/Api/GameBoxScore/{Id}`
* **Параметры:** Полностью аналогичны `GamePage`.  
*(Примечание к багам оригинала: на странице 16 авторы скопипастили описание параметров `playerLink`, `coachLink` и `refereeLink` со значением "Ссылка на игру" вместо ссылки на игрока/тренера/судью).*

**Примеры:**
* `http://www.infobasket.ru/reg/Api/GamePage/11566?playerLink=*&coachLink=*`
* `http://www.infobasket.ru/asb/Api/GamePage/45870?teamLink=*`

---

## 6. Команды

Профайлы клубов, ростеры (составы), сезонная статистика и логотипы.

### TeamPage
* **Версия:** `v.0.1`
* **Назначение:** Полная страница команды. В текущей версии тупо возвращает заглушку `GameInfo` / `Team`.
* **Формат ответа:** HTML или JSON (`Team`).
* **Вызов:** `/Api/TeamPage/{Id}`

| Параметр | Тип | Описание |
| :--- | :--- | :--- |
| `Id` | `int` | ID команды |
| `lang` | `string` | Язык |
| `style` | `string` | CSS тема |
| `teamLink` | `string` | Ссылка на команду |
| `playerLink`| `string` | Ссылка на игрока |
| `coachLink` | `string` | Ссылка на тренера |
| `gameLink` | `string` | Ссылка на игру *(в оригинале опечатка: `/Api/Referee/{id}`)* |

---

### TeamInfo
* **Версия:** `v.1.0`
* **Назначение:** Краткая визитная карточка команды.
* **Формат ответа:** HTML или JSON (`Team`).
* **Вызов:** `/Api/TeamInfo/{Id}` *(в доке на стр. 18 авторы накосячили и в строке вызова написали `/Api/TeamPage/1`)*.
* **Параметры:** `Id`, `lang`, `style`.

**Примеры:**
* `http://www.infobasket.ru/reg/Api/TeamInfo/2525?playerLink=*&coachLink=*`
* `http://www.infobasket.ru/asb/Api/TeamInfo/1?teamLink=*`

---

### TeamRoster
* **Версия:** `v.1.0`
* **Назначение:** Ростер (состав) команды в конкретном турнире/сезоне.
* **Формат ответа:** HTML или JSON (`TeamRosterResult`).
* **Вызов:** `/Api/TeamRoster/{Id}`

| Параметр | Тип | По умолчанию | Описание |
| :--- | :--- | :--- | :--- |
| `Id` | `int` | — | ID команды |
| `compID` | `int` | — | ID турнира или сезона |
| `lang` | `string` | `ru` | Язык |
| `style` | `string` | **`Default`** | CSS тема |
| `playerLink`| `string` | — | Шаблон ссылки на игрока |
| `coachLink` | `string` | — | Шаблон ссылки на тренера |
| `header` | `string` | — | `0` — скрыть, `1` — краткий заголовок команды, `2` — полный |

**Примеры:**
* `http://www.infobasket.ru/reg/Api/TeamRoster/2525?playerLink=*&coachLink=*`
* `http://www.infobasket.ru/asb/Api/TeamRoster/1?teamLink=*`

---

### TeamStats
* **Версия:** `v.1.0`
* **Назначение:** Суммарная статистика команды в турнире.
* **Формат ответа:** HTML или JSON (`TeamStatsResult`).
* **Вызов:** `/Api/TeamStats/{Id}`
* **Параметры:** Аналогичны `TeamRoster` (`Id`, `compID`, `lang`, `style`, `playerLink`, `coachLink`, `header`).

**Примеры:**
* `http://www.infobasket.ru/reg/Api/TeamStats/2525?playerLink=*&coachLink=*`
* `http://www.infobasket.ru/asb/Api/TeamStats/1?teamLink=*`

---

### TeamGames
* **Версия:** `v.1.0`
* **Назначение:** Список всех матчей команды в турнире.
* **Формат ответа:** HTML или JSON (Массив `Game`).
* **Вызов:** `/Api/TeamGames/{Id}`

| Параметр | Тип | По умолчанию | Описание |
| :--- | :--- | :--- | :--- |
| `Id` | `int` | — | ID команды |
| `compID` | `int` | — | ID турнира |
| `lang` | `string` | `ru` | Язык |
| `style` | `string` | **`Default`** | CSS тема |
| `teamLink` | `string` | — | Ссылка на команду |
| `gameLink` | `string` | — | Ссылка на игру (`/Api/GamePage/{id}`) |
| `header` | `string` | — | Заголовок команды (`0`, `1`, `2`) |

**Примеры:**
* `http://www.infobasket.ru/reg/Api/TeamGames/2525?gameLink=*&teamLink=*`
* `http://www.infobasket.ru/asb/Api/TeamGames/1?gameLink=*`

---

### GetTeamSeasons
* **Версия:** `v.1.0`
* **Назначение:** Список сезонов, в которых команда принимала участие (нужно для селекторов фильтрации перед запросом `TeamRoster`).
* **Формат ответа:** JSON (Массив объектов `{CompID, Year, SeasonName}`).
* **Вызов:** `/Api/GetTeamSeasons/{Id}`

| Параметр | Тип | Описание |
| :--- | :--- | :--- |
| `Id` | `int` | ID команды |

**Примеры:**
* `http://www.infobasket.ru/reg/Api/GetTeamSeasons/2525`
* `http://www.infobasket.ru/asb/Api/GetTeamSeasons/1`

---

### GetTeamComps
* **Версия:** `v.1.0`
* **Назначение:** Турниры команды внутри определенного сезона (для передачи в `TeamStats`).
* **Формат ответа:** JSON (Массив `TeamCompResult`).
* **Вызов:** `/Api/GetTeamComps/{Id}`

| Параметр | Тип | Описание |
| :--- | :--- | :--- |
| `Id` | `int` | ID команды |
| `season` | `int` | ID сезона (`CompID`, полученный из `GetTeamSeasons`) |

*(Примечание: в примерах оригинальной доки разрабы скопипастили урл от `GetTeamSeasons`, но реальный эндпоинт — `/Api/GetTeamComps/{Id}?season={seasonID}`).*

---

### GetTeamLogo
* **Версия:** `v.1.0`
* **Назначение:** Отдает бинарник логотипа клуба.
* **Формат ответа:** `image/png` (PNG поток).
* **Вызов:** `/Api/GetTeamLogo/{Id}`

| Параметр | Тип | По умолчанию | Описание |
| :--- | :--- | :--- | :--- |
| `Id` | `int` | — | ID команды |
| `full` | `string` | **`0`** | `0`, `no`, `false` — иконка 60x60; `1`, `yes`, `true` — полноразмерная 150x150 (размеры рекомендованные, по факту как залили) |

**Примеры:**
* `http://www.infobasket.ru/asb/Api/GetTeamLogo/7`
* `http://www.infobasket.ru/asb/Api/GetTeamLogo/6?full=1`

---

## 7. Персоны

Люди баскетбольного мира: игроки, коучи, судьи. Профайлы, статистика и фотки.

### GetPersonPhoto
* **Версия:** `v.1.0`
* **Назначение:** Фотография морды лица человека (игрока, тренера, судьи).
* **Формат ответа:** `image/jpeg` (JPEG поток).
* **Вызов:** `/Api/GetPersonPhoto/{Id}`

| Параметр | Тип | Описание |
| :--- | :--- | :--- |
| `Id` | `int` | ID персоны (`PersonID`) |

**Примеры:**
* `http://www.infobasket.ru/reg/Api/GetPersonPhoto/15934`
* `http://www.infobasket.ru/asb/Api/GetPersonPhoto/1770`

---

### Игроки: Player, PlayerInfo, PlayerTeams, PlayerStats

#### Player
* **Версия:** `v.0.1` | **Формат:** HTML / JSON (`Person`)
* **Вызов:** `/Api/Player/{Id}`
* **Параметры:** `Id` (ID персоны), `lang`, `style`, `teamLink`.

#### PlayerInfo
* **Версия:** `v.1.0` | **Формат:** HTML / JSON (`Person`)
* **Вызов:** `/Api/PlayerInfo/{Id}`
* **Параметры:** `Id`, `lang`, `style`.

#### PlayerTeams
* **Версия:** `v.1.0` | **Формат:** HTML / JSON (Массив `TeamPlayer`)
* **Назначение:** Список команд, за которые бегал игрок, с разбивкой по сезонам.
* **Вызов:** `/Api/PlayerTeams/{Id}`
* **Параметры:** `Id`, `lang`, `style`, `teamLink`, `header` (`0`/`1`/`2`).

#### PlayerStats
* **Версия:** `v.1.0` | **Формат:** HTML / JSON (`PlayerStatsResult`)
* **Назначение:** Полная сводная статистика игрока.
* **Вызов:** `/Api/PlayerStats/{Id}`
* **Параметры:** `Id`, `lang`, `style`, `teamLink`, `gameLink`, `header` (`0`/`1`/`2`).

**Примеры для игроков:**
* `http://www.infobasket.ru/reg/Api/Player/15934`
* `http://www.infobasket.ru/asb/Api/PlayerStats/1770?teamLink=*`

---

### Тренеры: Coach, CoachInfo, CoachTeams

#### Coach
* **Версия:** `v.0.1` | **Формат:** HTML / JSON (`Person`)
* **Вызов:** `/Api/Coach/{Id}`
* **Параметры:** `Id`, `lang`, `style`, `teamLink`.

#### CoachInfo
* **Версия:** `v.1.0` | **Формат:** HTML / JSON (`Person`)
* **Вызов:** `/Api/CoachInfo/{Id}`
* **Параметры:** `Id`, `lang`, `style`.

#### CoachTeams
* **Версия:** `v.1.0` | **Формат:** HTML / JSON (Массив `TeamCoach`)
* **Назначение:** Клубы, которые тренировал данный специалист, по сезонам.
* **Вызов:** `/Api/CoachTeams/{Id}` *(в доке на стр. 24 в вызове опечатка `/Api/PlayerTeams/1000`)*.
* **Параметры:** `Id`, `lang`, `style`, `teamLink`, `header` (`0`/`1`/`2`).

**Примеры для тренеров:**
* `http://www.infobasket.ru/reg/Api/CoachInfo/15934`
* `http://www.infobasket.ru/asb/Api/CoachTeams/1770?teamLink=*`

---

### Судьи: Referee, RefereeInfo, RefereeGames

#### Referee
* **Версия:** `v.0.1` | **Формат:** HTML / JSON (`Person`)
* **Вызов:** `/Api/Referee/{Id}`
* **Параметры:** `Id`, `lang`, `style`, `teamLink`.

#### RefereeInfo
* **Версия:** `v.1.0` | **Формат:** HTML / JSON (`Person`)
* **Вызов:** `/Api/RefereeInfo/{Id}`
* **Параметры:** `Id`, `lang`, `style`.

#### RefereeGames
* **Версия:** `v.1.0` | **Формат:** HTML / JSON (Массив `GameReferee`)
* **Назначение:** Матчи, которые обслуживал данный судья.
* **Вызов:** `/Api/RefereeGames/{Id}`
* **Параметры:** `Id`, `compID` (ID турнира), `lang`, `style`, `teamLink`, `gameLink`.

**Примеры для судей:**
* `http://www.infobasket.ru/reg/Api/RefereeInfo/15934`
* `http://www.infobasket.ru/asb/Api/RefereeGames/1770`

---

## 8. Стили оформления

Если дергать эндпоинты без `format=json`, сервер вернет HTML с подключенными стилями Bootstrap 3 с сайта [Bootswatch](http://bootswatch.com). 

Передавать через параметр `?style=ИмяСтиля`.

* **По умолчанию:** `Default`
* **Доступные бесплатные темы Bootswatch:**
  * `Cerulean`
  * `Cosmo`
  * `Cyborg`
  * `Darkly`
  * `Flatly`
  * `Journal`
  * `Lumen`
  * `Paper`
  * `Readable`
  * `Sandstone`
  * `Simplex`
  * `Slate`
  * `Spacelab`
  * `Superhero`
  * `United`
  * `Yeti`

> *Разработчики предупреждают: использовать эти стили стоит исключительно при интеграции виджетов через `<iframe>`, иначе верстка чужого сайта разлетится к чертям. Собственные стили ИнфоБаскета на момент 2015 года находились в перманентной разработке.*

---

## 9. Структуры возвращаемых данных

Ниже представлены сырые C#-подобные структуры данных (DTO), выплевываемые сериализатором в JSON при указании `format=json`.

> ⚠️ **Внимание:** Структуры получены напрямую из Entity Framework и содержат кучу системных полей (`SysStatus`, `SysLastChanged`, навигационные свойства связей). Разрабы настоятельно рекомендуют не трогать недокументированные внутренние кишки. Знак вопроса `?` означает `Nullable` (поле может прилететь как `null`).

### Базовые справочники

```csharp
// Страна
public class Country
{
    public int CountryID { get; set; }
    public Guid CountryGUID { get; set; }
    public string CountryNameRu { get; set; }
    public string CountryNameEn { get; set; }
    public string CountryCodeISO { get; set; }
    public string CountryCodeIOC { get; set; }
    public string CountryFullNameRu { get; set; }
    public string CountryFullNameEn { get; set; }
    public int? CountryPartOfWorld { get; set; }     // Часть света
    public bool CountryFormer { get; set; }          // Бывшая/историческая страна (типа СССР)
    public bool CountryHide { get; set; }            // Скрыта ли
    public string CountryPhoneCode { get; set; }     // Телефонный код
    public byte SysStatus { get; set; }
    public DateTime? SysLastChanged { get; set; }
}

// Регион / Город
public class Region
{
    public int RegionID { get; set; }
    public Guid RegionGUID { get; set; }
    public int? RegionParent { get; set; }           // Родительский регион (область для города)
    public int RegionType { get; set; }
    public string RegionNameRu { get; set; }
    public string RegionNameEn { get; set; }
    public int? RegionCountry { get; set; }          // Ссылка на CountryID
    public int? RegionTimeZone { get; set; }         // Смещение часового пояса
    public string RegionTimeZoneID { get; set; }
    public bool RegionParentShow { get; set; }
    public int? RegionNode { get; set; }
    public int? RegionNodeDistance { get; set; }
    public byte SysStatus { get; set; }
    public DateTime SysLastChanged { get; set; }
    public Game[] Games { get; set; }
}

// Арена / Спортивный зал
public class Arena
{
    public int ArenaID { get; set; }
    public Guid ArenaGUID { get; set; }
    public int? ArenaRegion { get; set; }           // Ссылка на RegionID
    public string ArenaNameRu { get; set; }
    public string ArenaNameEn { get; set; }
    public string ArenaFullNameRu { get; set; }
    public string ArenaFullNameEn { get; set; }
    public int? ArenaMaxAttendance { get; set; }     // Вместимость зала
    public short ArenaStatus { get; set; }
    public byte SysStatus { get; set; }
    public DateTime SysLastChanged { get; set; }
    public Game[] Games { get; set; }
}
```

---

### Команды и должности

```csharp
// Команда (Клуб)
public class Team
{
    public int TeamID { get; set; }
    public int TeamType { get; set; }
    public string TeamNameRu { get; set; }
    public string TeamNameEn { get; set; }
    public string TeamShortNameRu { get; set; }
    public string TeamShortNameEn { get; set; }
    public string TeamAbcNameRu { get; set; }
    public string TeamAbcNameEn { get; set; }
    public byte TeamGender { get; set; }             // Пол: мужская / женская
    public int? TeamTypeIcon { get; set; }
    public int? TeamRegion { get; set; }
    public int? TeamCountry { get; set; }
    public int? TeamArena { get; set; }
    public int? TeamOrg { get; set; }                // Организация/ВУЗ
    public int TeamLogo { get; set; }
    public int TeamUniform1 { get; set; }            // Основной цвет формы
    public int TeamUniform2 { get; set; }            // Гостевой цвет формы
    public int? TeamPlayersBirthYear { get; set; }   // Ограничение по году рождения (для молодежек)
    public short TeamStatus { get; set; }
    public byte SysStatus { get; set; }
    public DateTime? SysLastChanged { get; set; }
    
    // Навигационные свойства EF
    public TeamType TeamType1 { get; set; }
    public CompTeamName[] CompTeamNames { get; set; }
    public TeamCoach[] TeamCoaches { get; set; }
    public TeamPlayer[] TeamPlayers { get; set; }
}

public class TeamType
{
    public int TeamTypeID { get; set; }
    public string TeamTypeNameRu { get; set; }
    public string TeamTypeNameEn { get; set; }
    public byte SysStatus { get; set; }
    public DateTime SysLastChanged { get; set; }
    public Team[] Teams { get; set; }
}

// Должность в штабе (главный тренер, ассистент, врач и т.д.)
public class Duty
{
    public int DutyID { get; set; }
    public string DutyNameRu { get; set; }
    public string DutyNameEn { get; set; }
    public string DutyShortNameRu { get; set; }
    public string DutyShortNameEn { get; set; }
    public int DutyOccupation { get; set; }
    public short DutyOrder { get; set; }
    public bool DutyDefault { get; set; }
    public byte SysStatus { get; set; }
    public DateTime SysLastChanged { get; set; }
    public Occupation Occupation { get; set; }
    public TeamCoach[] TeamCoaches { get; set; }
    public GameReferee[] GameReferees { get; set; }
}
```

---

### Персоны (Игроки, Тренеры, Судьи)

```csharp
// Общий профайл человека
public class Person
{
    public int PersonID { get; set; }
    public string PersonLastNameRu { get; set; }
    public string PersonFirstNameRu { get; set; }
    public string PersonSecondNameRu { get; set; }    // Отчество
    public string PersonFullNameRu { get; set; }
    public string PersonLastNameEn { get; set; }
    public string PersonFirstNameEn { get; set; }
    public string PersonSecondNameEn { get; set; }
    public string PersonFullNameEn { get; set; }
    public string PersonNickNameRu { get; set; }
    public string PersonNickNameEn { get; set; }
    public byte PersonGender { get; set; }
    public DateTime? PersonBirthday { get; set; }
    public short? PersonBirthYear { get; set; }
    public string PersonBirth { get; set; }
    public float? PersonHeight { get; set; }          // Рост (см)
    public float? PersonWeight { get; set; }          // Вес (кг)
    public int? PersonBornIn { get; set; }            // Место рождения (город)
    public int? PersonBornInRegion { get; set; }      // Регион рождения
    public int? PersonCountry { get; set; }           // Гражданство
    public int? PersonRegion { get; set; }
    public short PersonStatus { get; set; }
    public byte SysStatus { get; set; }
    public DateTime SysLastChanged { get; set; }
    
    public Coach[] Coaches { get; set; }
    public Player[] Players { get; set; }
    public Referee[] Referees { get; set; }
    public Country Country { get; set; }
}

// Сущность: Игрок
public class Player
{
    public int PlayerID { get; set; }
    public int PersonID { get; set; }
    public int? PlayerPosition { get; set; }          // Амплуа (защитник, центровой...)
    public int? PlayerRank { get; set; }              // Разряд/звание (КМС, МС...)
    public byte? PlayerHand { get; set; }             // Рабочая рука (правша/левша)
    public bool IsNaturalized { get; set; }           // Натурализованный легионер
    public short PlayerStatus { get; set; }
    public byte SysStatus { get; set; }
    public DateTime SysLastChanged { get; set; }
    
    public Person Person { get; set; }
    public Position Position { get; set; }
    public PersonRank PersonRank { get; set; }
    public TeamPlayer[] TeamPlayers { get; set; }
}

// Сущность: Тренер
public class Coach
{
    public int CoachID { get; set; }
    public int PersonID { get; set; }
    public int? CoachRank { get; set; }               // Тренерская категория
    public short CoachStatus { get; set; }
    public byte SysStatus { get; set; }
    public DateTime SysLastChanged { get; set; }
    
    public Person Person { get; set; }
    public PersonRank PersonRank { get; set; }
    public TeamCoach[] TeamCoaches { get; set; }
}

// Сущность: Судья (Арбитр)
public class Referee
{
    public int RefereeID { get; set; }
    public int PersonID { get; set; }
    public int RefereeOccupation { get; set; }
    public int? RefereeRank { get; set; }             // Судейская категория (ФИБА, 1 категория...)
    public int? RefereeRegionID { get; set; }
    public short RefereeStatus { get; set; }
    public byte SysStatus { get; set; }
    public DateTime SysLastChanged { get; set; }
    
    public Person Person { get; set; }
    public GameReferee[] GameReferees { get; set; }
    public PersonRank PersonRank { get; set; }
    public Region Region { get; set; }
}
```

---

### Привязки персон к командам и играм

```csharp
// Игрок в составе команды
public class TeamPlayer
{
    public int TeamPlayerID { get; set; }
    public int TeamID { get; set; }
    public int PlayerID { get; set; }
    public int? CompID { get; set; }                  // Турнир, на который заявлен
    public byte TeamCapitan { get; set; }             // Флаг капитана команды
    public short TeamPlayerNumber { get; set; }       // Игровой номер на майке
    public int TeamPlayerStatus { get; set; }
    public byte SysStatus { get; set; }
    public DateTime? SysLastChanged { get; set; }
    
    public Player Player { get; set; }
    public Team Team { get; set; }
    public TeamPersonStatus PersonStatus { get; set; }
    public Comp Comp { get; set; }
}

// Тренер в штабе команды
public class TeamCoach
{
    public int TeamCoachID { get; set; }
    public int TeamID { get; set; }
    public int CoachID { get; set; }
    public int CompID { get; set; }
    public short TeamCoachNumber { get; set; }
    public int? TeamCoachDuty { get; set; }           // Ссылка на DutyID (должность)
    public int TeamCoachStatus { get; set; }
    public byte SysStatus { get; set; }
    public DateTime? SysLastChanged { get; set; }
    
    public Coach Coach { get; set; }
    public Team Team { get; set; }
    public TeamPersonStatus PersonStatus { get; set; }
    public Duty Duty { get; set; }
    public Comp Comp { get; set; }
}

// Судья, назначенный на матч
public class GameReferee
{
    public int GameRefID { get; set; }
    public int GameID { get; set; }
    public short GameRefOrder { get; set; }           // Старшинство (старший судья, комиссар...)
    public int GameRefDuty { get; set; }
    public int? RefereeID { get; set; }
    public double? GameRefMark { get; set; }          // Оценка за судейство матча
    public string GameRefNote { get; set; }           // Замечания по игре
    public byte SysStatus { get; set; }
    public DateTime SysLastChanged { get; set; }
    
    public Game Game { get; set; }
    public Referee Referee { get; set; }
}
```

---

### Турниры и команды турниров

```csharp
// Турнир / Соревнование
public class Comp
{
    public int CompID { get; set; }
    public int CompIDparent { get; set; }             // Родительский турнир (иерархия этапов)
    public int CompType { get; set; }
    public int CompSort { get; set; }
    public int CompRound { get; set; }
    public string CompShortNameRu { get; set; }
    public string CompShortNameEn { get; set; }
    public string CompFullNameRu { get; set; }
    public string CompFullNameEn { get; set; }
    public string CompAbcNameRu { get; set; }
    public string CompAbcNameEn { get; set; }
    public byte CompGender { get; set; }              // М / Ж
    public DateTime? CompStartDate { get; set; }
    public DateTime? CompFinalDate { get; set; }
    public int CompState { get; set; }
    public bool CompPublic { get; set; }              // Виден ли публично
    public int? CompLogo { get; set; }
    public short CompLapCount { get; set; }           // Количество кругов
    public short CompSystem { get; set; }             // Система проведения
    public byte CompStandingSort { get; set; }        // Правило сортировки таблицы
    public bool CompStandingNeedUpdate { get; set; }  // Требуется пересчет таблицы
    public int CompRules { get; set; }
    public int GameRulesID { get; set; }
    public int? CompOrg { get; set; }                 // Организатор турнира
    public bool UseOrgColontitle { get; set; }
    public string CompApproveNoteRu { get; set; }
    public string CompApproveNoteEn { get; set; }
    public string CompFooterNoteRu { get; set; }
    public string CompFooterNoteEn { get; set; }
    public short StatsMinGames { get; set; }          // Мин. игр для попадания в рейтинг
    public short StatsMinGoals1 { get; set; }
    public short StatsMinGoals2 { get; set; }
    public short StatsMinGoals3 { get; set; }
    public string ForegroundColor { get; set; }       // HEX-цвета для оформления
    public string BackgroundColor { get; set; }
    public byte SysStatus { get; set; }
    public DateTime SysLastChanged { get; set; }
    
    public CompGame[] CompGames { get; set; }
    public Comp[] Children { get; set; }              // Дочерние этапы/подгруппы
    public Comp Parent { get; set; }
    public CompTeam[] CompTeams { get; set; }
}

// Команда в конкретном турнире
public class CompTeam
{
    public int CompTeamID { get; set; }
    public int CompID { get; set; }
    public short CompTeamStart { get; set; }
    public int CompTeamNameID { get; set; }
    public short? CompTeamPlace { get; set; }         // Текущее/итоговое место
    public int? CompTeamPrevComp { get; set; }
    public short? CompTeamPrevPlace { get; set; }
    public short CompTeamNotForStanding { get; set; } // Вне зачета (да/нет)
    public byte SysStatus { get; set; }
    public DateTime SysLastChanged { get; set; }
    
    public GameTeam[] GameTeams { get; set; }
    public CompTeamName CompTeamName { get; set; }
    public CompTeamStanding[] CompTeamStandings { get; set; }
    public Comp Comp { get; set; }
}

// Строка положения команды в таблице
public class CompTeamStanding
{
    public int CompTeamStandingID { get; set; }
    public int CompTeamID { get; set; }
    public short? StandingGame { get; set; }           // Всего игр сыграно
    public short? StandingWin { get; set; }            // Победы
    public short? StandingDraw { get; set; }           // Ничьи (бывает в детских/специфичных регламентах)
    public short? StandingLose { get; set; }           // Поражения
    public short? StandingForfeit { get; set; }        // «Баранки» / Технические поражения (лишение очков)
    public double? StandingPoints { get; set; }        // Набранные турнирные очки
    public short? StandingGoalPlus { get; set; }       // Забитые мячи
    public short? StandingGoalMinus { get; set; }      // Пропущенные мячи
    public decimal? StandingGoalDifference { get; set;}// Разница мячей
    public short? StandingPenalty { get; set; }        // Штрафные очки
    public bool StandingIsPlay { get; set; }
    public byte SysStatus { get; set; }
    public DateTime SysLastChanged { get; set; }
    public CompTeam CompTeam { get; set; }
}

// Наименование команды в рамках турнира (может отличаться от базового)
public class CompTeamName
{
    public int CompTeamNameID { get; set; }
    public int? TeamID { get; set; }
    public int TeamType { get; set; }
    public string CompTeamShortNameRu { get; set; }
    public string CompTeamShortNameEn { get; set; }
    public string CompTeamNameRu { get; set; }
    public string CompTeamNameEn { get; set; }
    public string CompTeamRegionNameRu { get; set; }
    public string CompTeamRegionNameEn { get; set; }
    public string CompTeamAbcNameRu { get; set; }
    public string CompTeamAbcNameEn { get; set; }
    public DateTime? CompTeamNameChanged { get; set; }
    public bool CompTeamNameDefault { get; set; }
    public byte SysStatus { get; set; }
    public DateTime SysLastChanged { get; set; }
    public CompTeam[] CompTeams { get; set; }
    public Team Team { get; set; }
}
```

---

### Матчи и статистика игры

```csharp
// Игра (Матч)
public class Game
{
    public int GameID { get; set; }
    public Guid? GameGUID { get; set; }
    public DateTime? GameDate { get; set; }
    public DateTime? GameTime { get; set; }
    public DateTime? GameDateTime { get; set; }
    public string GameNumber { get; set; }            // Порядковый номер матча в турнире
    public int? GameRegion { get; set; }
    public int? GameArena { get; set; }
    public int? GameRules { get; set; }
    public short GameForfeit { get; set; }            // Техническое поражение
    public int? GameAttendance { get; set; }          // Количество зрителей на трибунах
    public int? GameStatus { get; set; }              // Не начался / идет / завершен
    public byte GameStatsStatus { get; set; }         // Статус внесения статы
    public int? GameIDnew { get; set; }
    public byte SysStatus { get; set; }
    public DateTime SysLastChanged { get; set; }
    public DateTime? GameDateTimeMoscow { get; set; } // Московское время матча
    
    public GamePeriod[] GamePeriods { get; set; }     // Четверти / овертаймы
    public GameReferee[] GameReferees { get; set; }
    public GameTeam[] GameTeams { get; set; }
    public Region Region { get; set; }
    public Arena Arena { get; set; }
}

// Участие команды в матче (Хозяева / Гости)
public class GameTeam
{
    public int GameTeamID { get; set; }
    public int GameID { get; set; }
    public byte GameTeamNumber { get; set; }          // 1 — Команда А (хозяева), 2 — Команда Б (гости)
    public int? CompTeamID { get; set; }
    public int CompTeamStart { get; set; }
    public int? TeamID { get; set; }
    public int? GameTeamScore { get; set; }           // Итоговый счет команды
    public byte? TeamUniformNumber { get; set; }      // Цвет формы в матче
    public byte SysStatus { get; set; }
    public DateTime SysLastChanged { get; set; }
    public CompTeam CompTeam { get; set; }
    public Game Game { get; set; }
}

// Пара плей-офф
public class PlayoffPair
{
    public int Round { get; set; }                    // 1/8, 1/4, 1/2, финал
    public int Sort { get; set; }
    public string RoundNameRu { get; set; }
    public string RoundNameEn { get; set; }
    public CompTeamName TeamName1 { get; set; }
    public CompTeamName TeamName2 { get; set; }
    public int? Score1 { get; set; }                  // Победы первой команды в серии
    public int? Score2 { get; set; }                  // Победы второй команды в серии
    public bool IsFinal { get; set; }                 // Завершена ли серия
    public int Winner { get; set; }                   // Победитель пары
}

// Элемент для шахматки
public class GameScore
{
    public int GameID { get; set; }
    public string Score { get; set; }                 // Счет матча, напр. "85:72"
    public string GameDate { get; set; }
    public int Team1Place { get; set; }
    public int Team2Place { get; set; }
    public int HomeTeam { get; set; }
}

// Строка рейтинга лучших игроков
public class BestPlayerResult
{
    public int Rank { get; set; }                     // Место в топе
    public Person Person { get; set; }
    public CompTeamName TeamName { get; set; }
    public Game Game { get; set; }
    public int GameCount { get; set; }                // Количество сыгранных матчей
    public double Res { get; set; }                   // Значение метрики (например, 24.5 очка)
    public string PreRes { get; set; }
}

// Строка рейтинга лучших команд
public class BestTeamResult
{
    public int Rank { get; set; }
    public CompTeamName TeamName { get; set; }
    public Game Game { get; set; }
    public int GameCount { get; set; }
    public double Res { get; set; }
    public string PreRes { get; set; }
}
```

---

### Детальная статистика матча (GameBoxScore Result)

```csharp
// Полный протокол матча
public class GameStatsResult
{
    public int GameID { get; set; }
    public string GameDate { get; set; }
    public string GameTime { get; set; }
    public string GameNumber { get; set; }
    public string VenueRu { get; set; }
    public string VenueEn { get; set; }
    public int? Attendance { get; set; }
    public string Score { get; set; }                 // Итоговый счет: "78:65"
    public string ScoreByPeriods { get; set; }        // Счет по четвертям: "20:15, 18:22, 25:10, 15:18"
    public GameRefereeResult[] Referees { get; set; }
    public GameTeamResult[] Teams { get; set; }
    public GameTeamResult TeamA { get; set; }         // Хозяева
    public GameTeamResult TeamB { get; set; }         // Гости
}

// Командная статистика в матче
public class GameTeamResult
{
    public int TeamNumber { get; set; }               // 1 или 2
    public int TeamID { get; set; }
    public CompTeamName TeamName { get; set; }
    public int Score { get; set; }
    public int Points { get; set; }
    
    // Броски: 1 - штрафные, 2 - 2-очковые, 3 - 3-очковые
    public int Shot1 { get; set; }                    // Брошено штрафных
    public int Goal1 { get; set; }                    // Забито штрафных
    public int Shot2 { get; set; }                    // Брошено двухочковых
    public int Goal2 { get; set; }                    // Забито двухочковых
    public int Shot3 { get; set; }                    // Брошено трехочковых
    public int Goal3 { get; set; }                    // Забито трехочковых
    
    public string Shots1 { get; set; }                // Строка вида "15/20"
    public string Shot1Percent { get; set; }          // Процент попадания: "75.0%"
    public string Shots2 { get; set; }                // "22/45"
    public string Shot2Percent { get; set; }
    public string Shots3 { get; set; }                // "8/24"
    public string Shot3Percent { get; set; }
    
    public int Assist { get; set; }                   // Голевые передачи
    public int Blocks { get; set; }                   // Блок-шоты
    public int DefRebound { get; set; }               // Подборы в защите
    public int OffRebound { get; set; }               // Подборы в нападении
    public int Rebound { get; set; }                  // Всего подборов
    public int Steal { get; set; }                    // Перехваты
    public int Turnover { get; set; }                 // Потери
    
    // Командные показатели (не записанные на конкретных игроков)
    public int? TeamDefRebound { get; set; }
    public int? TeamOffRebound { get; set; }
    public int? TeamRebound { get; set; }
    public int? TeamSteal { get; set; }
    public int? TeamTurnover { get; set; }
    
    public int Foul { get; set; }                     // Фолы команды
    public int OpponentFoul { get; set; }             // Фолы соперника
    public int Seconds { get; set; }                  // Сыгранное время в секундах
    public string PlayedTime { get; set; }            // Форматированное время: "200:00"
    public int? PlusMinus { get; set; }
    
    public GameCoachResult Coach { get; set; }
    public GamePlayerResult[] Players { get; set; }
    public GameCoachResult[] Coaches { get; set; }
}

// Индивидуальная статистика игрока в конкретном матче
public class GamePlayerResult
{
    public int? PersonID { get; set; }
    public int TeamNumber { get; set; }
    public int PlayerNumber { get; set; }
    public string DisplayNumber { get; set; }         // Номер на майке (строка, т.к. бывает "00")
    public string LastNameRu { get; set; }
    public string LastNameEn { get; set; }
    public string FirstNameRu { get; set; }
    public string FirstNameEn { get; set; }
    public string PersonNameRu { get; set; }
    public string PersonNameEn { get; set; }
    public int Capitan { get; set; }                  // Капитан (1/0)
    public string PersonBirth { get; set; }
    public int? PosID { get; set; }                   // Амплуа
    public string CountryCodeIOC { get; set; }
    public string CountryNameRu { get; set; }
    public string CountryNameEn { get; set; }
    public string RankRu { get; set; }
    public string RankEn { get; set; }
    public float? Height { get; set; }
    public float? Weight { get; set; }
    
    // Метрики результативности
    public int? Points { get; set; }
    public int? Shot1 { get; set; }
    public int? Goal1 { get; set; }
    public string Shots1 { get; set; }
    public string Shot1Percent { get; set; }
    public int? Shot2 { get; set; }
    public int? Goal2 { get; set; }
    public string Shots2 { get; set; }
    public string Shot2Percent { get; set; }
    public int? Shot3 { get; set; }
    public int? Goal3 { get; set; }
    public string Shots3 { get; set; }
    public string Shot3Percent { get; set; }
    
    public int? Assist { get; set; }
    public int? Blocks { get; set; }
    public int? DefRebound { get; set; }
    public int? OffRebound { get; set; }
    public int? Rebound { get; set; }
    public int? Steal { get; set; }
    public int? Turnover { get; set; }
    public int? Foul { get; set; }                    // Собственные персональные замечания
    public int? OpponentFoul { get; set; }            // Сфолили на нем
    public int? PlusMinus { get; set; }               // Показатель плюс-минус (+/-)
    public int Seconds { get; set; }                  // Время на паркете в секундах
    public string PlayedTime { get; set; }            // "28:45"
    public bool IsStart { get; set; }                 // Игрок стартовой пятерки
    public string StartMark { get; set; }             // Звездочка или маркер старта
}

// Статистика тренера в матче (в основном его косяки и фолы)
public class GameCoachResult
{
    public int? PersonID { get; set; }
    public int TeamNumber { get; set; }
    public int PlayerNumber { get; set; }
    public string DisplayNumber { get; set; }
    public string LastNameRu { get; set; }
    public string LastNameEn { get; set; }
    public string FirstNameRu { get; set; }
    public string FirstNameEn { get; set; }
    public string PersonNameRu { get; set; }
    public string PersonNameEn { get; set; }
    public string PersonBirth { get; set; }
    public int? PosID { get; set; }
    public string CountryCodeIOC { get; set; }
    public string CountryNameRu { get; set; }
    public string CountryNameEn { get; set; }
    public string RankRu { get; set; }
    public string RankEn { get; set; }
    public int? FoulC { get; set; }                   // Технические фолы тренера (Coach)
    public int? FoulB { get; set; }                   // Технические фолы скамейки (Bench)
    public int? FoulD { get; set; }                   // Дисквалифицирующие фолы (Disqualifying)
    public int? Foul { get; set; }                    // Сумма фолов штаба
}

// Судья в матче
public class GameRefereeResult
{
    public int StartID { get; set; }
    public int RefNumber { get; set; }
    public int? PersonID { get; set; }
    public string PersonNameRu { get; set; }
    public string PersonNameEn { get; set; }
    public string CountryCodeIOC { get; set; }
    public string CountryNameRu { get; set; }
    public string CountryNameEn { get; set; }
    public string RankRu { get; set; }
    public string RankEn { get; set; }
    public int? PostID { get; set; }
    public string PostRu { get; set; }                // Амплуа: старший судья, комиссар, секундометрист...
    public string PostEn { get; set; }
}
```

---

### Ростеры и сезонные агрегаты команд

```csharp
// Заявочный лист команды
public class TeamRosterResult
{
    public int TeamID { get; set; }
    public CompTeamName TeamName { get; set; }
    public TeamRosterPlayerResult[] Players { get; set; }
    public TeamRosterCoachResult[] Coaches { get; set; }
    public string AvgAge { get; set; }                // Средний возраст состава (лет)
    public string AvgHeight { get; set; }             // Средний рост состава (см)
    public string AvgWeight { get; set; }             // Средний вес состава (кг)
}

public class TeamRosterPlayerResult
{
    public int? PersonID { get; set; }
    public int PlayerNumber { get; set; }
    public string DisplayNumber { get; set; }
    public string LastNameRu { get; set; }
    public string LastNameEn { get; set; }
    public string FirstNameRu { get; set; }
    public string FirstNameEn { get; set; }
    public string PersonNameRu { get; set; }
    public string PersonNameEn { get; set; }
    public int Capitan { get; set; }
    public string PersonBirth { get; set; }
    public int? Age { get; set; }
    public int? PosID { get; set; }
    public string PositionRu { get; set; }
    public string PositionEn { get; set; }
    public string CountryCodeIOC { get; set; }
    public string CountryNameRu { get; set; }
    public string CountryNameEn { get; set; }
    public string RankRu { get; set; }
    public string RankEn { get; set; }
    public float? Height { get; set; }
    public float? Weight { get; set; }
    public bool IsActive { get; set; }                // Активен ли в заявке
    public string ActiveStatusRu { get; set; }
    public string ActiveStatusEn { get; set; }
}

public class TeamRosterCoachResult
{
    public int? PersonID { get; set; }
    public int CoachNumber { get; set; }
    public string DisplayNumber { get; set; }
    public string LastNameRu { get; set; }
    public string LastNameEn { get; set; }
    public string FirstNameRu { get; set; }
    public string FirstNameEn { get; set; }
    public string PersonNameRu { get; set; }
    public string PersonNameEn { get; set; }
    public string PersonBirth { get; set; }
    public int? Age { get; set; }
    public int? PostID { get; set; }
    public string PostRu { get; set; }
    public string PostEn { get; set; }
    public string CountryCodeIOC { get; set; }
    public string CountryNameRu { get; set; }
    public string CountryNameEn { get; set; }
    public string RankRu { get; set; }
    public string RankEn { get; set; }
    public bool IsActive { get; set; }
    public string ActiveStatusRu { get; set; }
    public string ActiveStatusEn { get; set; }
}

public class TeamCompResult
{
    public int CompID { get; set; }
    public int Level { get; set; }
    public string CompNameRu { get; set; }
    public string CompNameEn { get; set; }
}

// Агрегированная статистика команды за весь турнир
public class TeamStatsResult
{
    public int TeamID { get; set; }
    public CompTeamName TeamName { get; set; }
    public int Points { get; set; }
    public int Shot1 { get; set; }
    public int Goal1 { get; set; }
    public int Shot2 { get; set; }
    public int Goal2 { get; set; }
    public int Shot3 { get; set; }
    public int Goal3 { get; set; }
    public string Shots1 { get; set; }
    public string Shot1Percent { get; set; }
    public string Shots2 { get; set; }
    public string Shot2Percent { get; set; }
    public string Shots3 { get; set; }
    public string Shot3Percent { get; set; }
    public int Assist { get; set; }
    public int Blocks { get; set; }
    public int DefRebound { get; set; }
    public int OffRebound { get; set; }
    public int Rebound { get; set; }
    public int Steal { get; set; }
    public int Turnover { get; set; }
    public int? TeamDefRebound { get; set; }
    public int? TeamOffRebound { get; set; }
    public int? TeamRebound { get; set; }
    public int? TeamSteal { get; set; }
    public int? TeamTurnover { get; set; }
    public int Foul { get; set; }
    public int OpponentFoul { get; set; }
    public int Seconds { get; set; }
    public string PlayedTime { get; set; }
    public int? PlusMinus { get; set; }
    public TeamStatsPlayerResult[] Players { get; set; }
    public TeamStatsCoachResult[] Coaches { get; set; }
}

public class TeamStatsPlayerResult
{
    public int? PersonID { get; set; }
    public int PlayerNumber { get; set; }
    public string DisplayNumber { get; set; }
    public string LastNameRu { get; set; }
    public string LastNameEn { get; set; }
    public string FirstNameRu { get; set; }
    public string FirstNameEn { get; set; }
    public string PersonNameRu { get; set; }
    public string PersonNameEn { get; set; }
    public int? Points { get; set; }
    public int? Shot1 { get; set; }
    public int? Goal1 { get; set; }
    public string Shots1 { get; set; }
    public string Shot1Percent { get; set; }
    public int? Shot2 { get; set; }
    public int? Goal2 { get; set; }
    public string Shots2 { get; set; }
    public string Shot2Percent { get; set; }
    public int? Shot3 { get; set; }
    public int? Goal3 { get; set; }
    public string Shots3 { get; set; }
    public string Shot3Percent { get; set; }
    public int? Assist { get; set; }
    public int? Blocks { get; set; }
    public int? DefRebound { get; set; }
    public int? OffRebound { get; set; }
    public int? Rebound { get; set; }
    public int? Steal { get; set; }
    public int? Turnover { get; set; }
    public int? Foul { get; set; }
    public int? OpponentFoul { get; set; }
    public int? PlusMinus { get; set; }
    public int Seconds { get; set; }
    public string PlayedTime { get; set; }
    public int InGameCount { get; set; }              // Сколько раз выходил на площадку
    public int GameCount { get; set; }                // Всего игр команды в турнире
    public int StartCount { get; set; }               // Сколько раз выходил в стартовой пятерке
}

public class TeamStatsCoachResult
{
    public int? PersonID { get; set; }
    public int PlayerNumber { get; set; }
    public string DisplayNumber { get; set; }
    public string LastNameRu { get; set; }
    public string LastNameEn { get; set; }
    public string FirstNameRu { get; set; }
    public string FirstNameEn { get; set; }
    public string PersonNameRu { get; set; }
    public string PersonNameEn { get; set; }
    public int? FoulC { get; set; }
    public int? FoulB { get; set; }
    public int? FoulD { get; set; }
    public int? Foul { get; set; }
    public int GameCount { get; set; }
}
```

---

### Агрегированная статистика игрока за карьеру/турнир

```csharp
// Суммарная статистика игрока
public class PlayerStatsResult
{
    public int PersonID { get; set; }
    public int GameCount { get; set; }
    public int InGameCount { get; set; }
    public int StartCount { get; set; }
    public int Points { get; set; }
    public int Shot1 { get; set; }
    public int Goal1 { get; set; }
    public int Shot2 { get; set; }
    public int Goal2 { get; set; }
    public int Shot3 { get; set; }
    public int Goal3 { get; set; }
    public string Shots1 { get; set; }
    public string Shot1Percent { get; set; }
    public string Shots2 { get; set; }
    public string Shot2Percent { get; set; }
    public string Shots3 { get; set; }
    public string Shot3Percent { get; set; }
    public int Assist { get; set; }
    public int Blocks { get; set; }
    public int DefRebound { get; set; }
    public int OffRebound { get; set; }
    public int Rebound { get; set; }
    public int Steal { get; set; }
    public int Turnover { get; set; }
    public int Foul { get; set; }
    public int OpponentFoul { get; set; }
    public int Seconds { get; set; }
    public string PlayedTime { get; set; }
    public int? PlusMinus { get; set; }
}

// Конкретная игра в списке матчей игрока
public class PlayerGameResult
{
    public int PersonID { get; set; }
    public Game Game { get; set; }
    public string GameDate { get; set; }
    public CompTeamName TeamNameA { get; set; }
    public CompTeamName TeamNameB { get; set; }
    public int PlayerNumber { get; set; }
    public string DisplayNumber { get; set; }
    public int? Points { get; set; }
    public int? Shot1 { get; set; }
    public int? Goal1 { get; set; }
    public int? Shot2 { get; set; }
    public int? Goal2 { get; set; }
    public int? Shot3 { get; set; }
    public int? Goal3 { get; set; }
    public string Shots1 { get; set; }
    public string Shot1Percent { get; set; }
    public string Shots2 { get; set; }
    public string Shot2Percent { get; set; }
    public string Shots3 { get; set; }
    public string Shot3Percent { get; set; }
    public int? Assist { get; set; }
    public int? Blocks { get; set; }
    public int? DefRebound { get; set; }
    public int? OffRebound { get; set; }
    public int? Rebound { get; set; }
    public int? Steal { get; set; }
    public int? Turnover { get; set; }
    public int? Foul { get; set; }
    public int? OpponentFoul { get; set; }
    public int Seconds { get; set; }
    public string PlayedTime { get; set; }
    public int? PlusMinus { get; set; }
    public bool IsStart { get; set; }
    public string StartMark { get; set; }
}
```

***

### Резюме для фронтендера и бэкендера:
Если будешь парсить этот бэкенд, держи в голове три золотых правила:
1. Всегда и везде, сука, дописывай в Query String **`format=json`**, иначе парсер подавится куском кривого HTML со стилем `Cyborg`.
2. Не верь типам из официальной PDF-ки на 100%: половина числовых полей на самом деле прилетают строками (особенно проценты `75.0%` и время `28:45`), а половина полей, помеченных как `int`, в реальности `null`, потому что в региональных лигах секретарю за столиком часто впадлу нажимать на кнопки фолов тренера.
3. Опечатки в путях в оригинальной доке (`CoachTeams`, `TeamInfo`) поправлены выше в нормальный человеческий вид.