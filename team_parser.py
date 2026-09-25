import requests
import pandas as pd

BASE_URL = "https://org.infobasket.su"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://belarus.russiabasket.ru/'
}


def _get_json(path, params=None):
    """Базовый GET-запрос к API с возвратом JSON. Возвращает None при ошибке."""
    url = f"{BASE_URL}/{path}"
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[-] Ошибка запроса {path}: {e}")
        return None


def _fmt(val, default="—"):
    """Безопасное форматирование значения для таблиц (всегда строка)."""
    if val is None or val == "":
        return default
    return str(val)


def get_team_seasons(team_id):
    """
    Список сезонов, в которых команда принимала участие.

    Returns:
        list[dict] с ключами CompID, Year, SeasonName (или None)
    """
    data = _get_json(f"Widget/GetTeamSeasons/{team_id}", {'format': 'json', 'lang': 'ru'})
    if not isinstance(data, list):
        return None
    return data


def get_team_comps(team_id, season_id):
    """
    Турниры команды внутри сезона.

    Returns:
        list[dict] с ключами CompID, Level, CompNameRu (или None)
    """
    data = _get_json(
        f"Widget/GetTeamComps/{team_id}",
        {'season': season_id, 'format': 'json', 'lang': 'ru'}
    )
    if not isinstance(data, list):
        return None
    return data


def get_team_roster(team_id, comp_id):
    """
    Ростер (состав) команды в конкретном турнире: игроки, тренеры, персонал.

    Returns:
        dict (TeamRosterResult) или None
    """
    data = _get_json(
        f"Widget/TeamRoster/{team_id}",
        {'compID': comp_id, 'format': 'json', 'lang': 'ru'}
    )
    if not isinstance(data, dict):
        return None
    return data


def get_team_stats(team_id, comp_id):
    """
    Суммарная статистика игроков команды за турнир.

    Returns:
        dict (TeamStatsResult) или None
    """
    data = _get_json(
        f"Widget/TeamStats/{team_id}",
        {'compID': comp_id, 'format': 'json', 'lang': 'ru'}
    )
    if not isinstance(data, dict):
        return None
    return data


def _person_name(info):
    """Полное имя персоны из блока PersonInfo."""
    if not info:
        return "—"
    full = info.get('PersonFullNameRu')
    if full:
        return full.strip()
    last = info.get('PersonLastNameRu', '')
    first = info.get('PersonFirstNameRu', '')
    name = f"{last} {first}".strip()
    return name or "—"


def pick_best_comp(team_id, season_id):
    """
    Выбирает турнир внутри сезона с наибольшим количеством игр
    (среди турниров Level >= 1, иначе — корневой элемент сезона).

    Returns:
        dict с CompID и CompNameRu (или None)
    """
    comps = get_team_comps(team_id, season_id)
    if not comps:
        return None

    level1 = [c for c in comps if c.get('Level', 0) >= 1]
    candidates = level1 if level1 else comps

    best_comp = None
    best_games = -1
    for c in candidates:
        stats = get_team_stats(team_id, c['CompID'])
        games = (stats or {}).get('GameCount') or 0
        if games > best_games:
            best_games = games
            best_comp = c
    return best_comp or candidates[0]


def build_roster_df(roster):
    """
    DataFrame с игроками из ростера.

    Columns: №, Игрок, Дата рождения, Возраст, Позиция, Рост, Вес,
             Гражданство, Капитан, Статус
    """
    rows = []
    for p in roster.get('Players', []) or []:
        info = p.get('PersonInfo', {})
        rows.append({
            '№': _fmt(p.get('DisplayNumber')),
            'Игрок': _person_name(info),
            'Дата рождения': _fmt(p.get('PersonBirth')),
            'Возраст': _fmt(p.get('Age')),
            'Позиция': _fmt(p.get('Position')),
            'Рост': _fmt(p.get('Height')),
            'Вес': _fmt(p.get('Weight')),
            'Гражданство': _fmt(p.get('CountryName')),
            'Капитан': 'К' if p.get('Capitan') else '',
            'Статус': _fmt(p.get('ActiveStatus'), ''),
        })
    return pd.DataFrame(rows)


def build_coaches_df(roster):
    """
    DataFrame с тренерами и персоналом команды.

    Columns: Роль, №, Имя, Должность, Дата рождения, Возраст, Гражданство, Статус
    """
    rows = []
    for c in roster.get('Coaches', []) or []:
        info = c.get('PersonInfo', {})
        rows.append({
            'Роль': 'Тренер',
            '№': _fmt(c.get('DisplayNumber')),
            'Имя': _person_name(info),
            'Должность': _fmt(c.get('Post')),
            'Дата рождения': _fmt(c.get('PersonBirth')),
            'Возраст': _fmt(c.get('Age')),
            'Гражданство': _fmt(c.get('CountryName')),
            'Статус': _fmt(c.get('ActiveStatus'), ''),
        })
    for s in roster.get('Staff', []) or []:
        info = s.get('PersonInfo', {})
        rows.append({
            'Роль': 'Персонал',
            '№': _fmt(s.get('DisplayNumber')),
            'Имя': _person_name(info),
            'Должность': _fmt(s.get('Post')),
            'Дата рождения': _fmt(s.get('PersonBirth')),
            'Возраст': _fmt(s.get('Age')),
            'Гражданство': _fmt(s.get('CountryName')),
            'Статус': _fmt(s.get('ActiveStatus'), ''),
        })
    return pd.DataFrame(rows)


def build_stats_df(stats):
    """
    DataFrame со статистикой игроков за турнир.

    Columns: №, Игрок, И, Вых, Ст, Очки, Ср.О, 1-х, %Ш, 2-х, %2, 3-х, %3,
             ПД, ПО, ПБ, Перед, Перех, БШ, Пот, Ф, +/-, KPI, Мин
    """
    rows = []
    for p in stats.get('Players', []) or []:
        info = p.get('PersonInfo', {})
        rows.append({
            '№': _fmt(p.get('DisplayNumber')),
            'Игрок': _person_name(info),
            'И': _fmt(p.get('GameCount'), 0),
            'Вых': _fmt(p.get('InGameCount'), 0),
            'Ст': _fmt(p.get('StartCount'), 0),
            'Очки': _fmt(p.get('Points'), 0),
            'Ср.О': _fmt(p.get('AvgPoints')),
            '1-х': _fmt(p.get('Shots1')),
            '%Ш': _fmt(p.get('Shot1Percent')),
            '2-х': _fmt(p.get('Shots2')),
            '%2': _fmt(p.get('Shot2Percent')),
            '3-х': _fmt(p.get('Shots3')),
            '%3': _fmt(p.get('Shot3Percent')),
            'ПД': _fmt(p.get('DefRebound'), 0),
            'ПО': _fmt(p.get('OffRebound'), 0),
            'ПБ': _fmt(p.get('Rebound'), 0),
            'Перед': _fmt(p.get('Assist'), 0),
            'Перех': _fmt(p.get('Steal'), 0),
            'БШ': _fmt(p.get('Blocks'), 0),
            'Пот': _fmt(p.get('Turnover'), 0),
            'Ф': _fmt(p.get('Foul'), 0),
            '+/-': _fmt(p.get('PlusMinus')),
            'KPI': _fmt(p.get('KPI')),
            'Мин': _fmt(p.get('PlayedTime')),
        })
    return pd.DataFrame(rows)


def _fetch_season_block(team_id, season):
    """
    Загружает ростер + статистику команды для одного сезона.

    Returns:
        dict: season, comp, roster, roster_df, coaches_df, stats, stats_df
        или None при ошибке
    """
    comp = pick_best_comp(team_id, season['CompID'])
    if not comp:
        return None

    roster = get_team_roster(team_id, comp['CompID'])
    stats = get_team_stats(team_id, comp['CompID'])
    if roster is None and stats is None:
        return None

    roster = roster or {}
    stats = stats or {}

    return {
        'season': season,
        'comp': comp,
        'roster': roster,
        'roster_df': build_roster_df(roster),
        'coaches_df': build_coaches_df(roster),
        'stats': stats,
        'stats_df': build_stats_df(stats),
    }


def parse_team(team_id, season_id=None, min_games=5, verbose=True):
    """
    Главная функция: парсинг команды — ростер, тренеры, статистика игроков.

    Логика:
      1. Берём указанный сезон (или последний доступный).
      2. Загружаем ростер (игроки + тренеры + персонал) и статистику
         за лучший турнир сезона.
      3. Если статистики мало (игр < min_games или пустая), дополнительно
         загружаем прошлый сезон.

    Args:
        team_id: ID команды
        season_id: ID сезона (CompID из GetTeamSeasons). None = последний
        min_games: порог «мало статистики» для подтягивания прошлого сезона
        verbose: печатать прогресс в консоль

    Returns:
        dict: {
            'team_id', 'team_name', 'seasons',
            'current': блок текущего сезона (или None),
            'previous': блок прошлого сезона (или None),
            'roster_df', 'coaches_df', 'stats_df', 'stats_prev_df',
            'season_name', 'comp_name', 'prev_season_name', 'prev_comp_name'
        }
        или None при ошибке
    """
    def log(msg):
        if verbose:
            print(msg)

    log(f"[?] Загружаю сезоны команды {team_id}...")
    seasons = get_team_seasons(team_id)
    if not seasons:
        log("[-] Сезоны не найдены. Проверьте ID команды.")
        return None

    # Ищем выбранный сезон, иначе берём первый (самый свежий)
    season = None
    if season_id is not None:
        for s in seasons:
            if s['CompID'] == season_id:
                season = s
                break
        if season is None:
            log(f"[-] Сезон {season_id} не найден для команды {team_id}.")
            return None
    else:
        season = seasons[0]

    log(f"[+] Сезон: {season.get('SeasonName')}")
    current = _fetch_season_block(team_id, season)
    if current is None:
        log("[-] Не удалось загрузить данные команды за сезон.")
        return None

    team_name = (current['roster'].get('TeamName') or {}).get('CompTeamNameRu') \
        or (current['roster'].get('TeamName') or {}).get('CompTeamShortNameRu') \
        or f"Команда {team_id}"

    log(f"[+] Команда: {team_name}")
    log(f"[+] Турнир: {current['comp'].get('CompNameRu')}")

    # Оценка достаточности статистики
    games = current['stats'].get('GameCount') or 0
    stats_players = len(current['stats_df'])
    log(f"[+] Игр в турнире: {games}, игроков со статистикой: {stats_players}")

    previous = None
    if games < min_games or stats_players == 0:
        log(f"[!] Статистики мало (< {min_games} игр). Ищу прошлый сезон...")
        # seasons отсортированы от свежих к старым — берём следующий
        try:
            idx = seasons.index(season)
            if idx + 1 < len(seasons):
                prev_season = seasons[idx + 1]
                log(f"[+] Прошлый сезон: {prev_season.get('SeasonName')}")
                previous = _fetch_season_block(team_id, prev_season)
                if previous:
                    log(f"[+] Турнир прошлого сезона: {previous['comp'].get('CompNameRu')}")
            else:
                log("[-] Прошлый сезон не найден.")
        except ValueError:
            pass

    result = {
        'team_id': team_id,
        'team_name': team_name,
        'seasons': seasons,
        'current': current,
        'previous': previous,
        'roster_df': current['roster_df'],
        'coaches_df': current['coaches_df'],
        'stats_df': current['stats_df'],
        'stats_prev_df': previous['stats_df'] if previous else None,
        'season_name': season.get('SeasonName', ''),
        'comp_name': current['comp'].get('CompNameRu', ''),
        'prev_season_name': previous['season'].get('SeasonName', '') if previous else '',
        'prev_comp_name': previous['comp'].get('CompNameRu', '') if previous else '',
    }

    log("[+++] Готово!")
    return result


def save_team_to_csv(result, verbose=True):
    """
    Сохраняет результаты парсинга команды в CSV-файлы.

    Files:
        team_<id>_roster.csv        — ростер (игроки)
        team_<id>_coaches.csv       — тренеры и персонал
        team_<id>_stats_<comp>.csv  — статистика игроков (тек. сезон)
        team_<id>_stats_<comp>.csv  — статистика игроков (прошлый сезон, если есть)
    """
    if not result:
        return []

    team_id = result['team_id']
    files = []

    def _save(df, filename):
        if df is not None and not df.empty:
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            files.append(filename)
            if verbose:
                print(f"[+] Сохранён файл: {filename}")

    _save(result['roster_df'], f"team_{team_id}_roster.csv")
    _save(result['coaches_df'], f"team_{team_id}_coaches.csv")

    cur_comp = result['current']['comp']['CompID']
    _save(result['stats_df'], f"team_{team_id}_stats_{cur_comp}.csv")

    if result['previous']:
        prev_comp = result['previous']['comp']['CompID']
        _save(result['stats_prev_df'], f"team_{team_id}_stats_{prev_comp}.csv")

    return files


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Использование: python team_parser.py <TEAM_ID> [SEASON_ID]")
        print("Пример: python team_parser.py 25724")
        sys.exit(1)

    tid = sys.argv[1]
    sid = sys.argv[2] if len(sys.argv) > 2 else None
    res = parse_team(tid, season_id=sid)
    if res:
        save_team_to_csv(res)
    else:
        print("[-] Не удалось распарсить команду.")