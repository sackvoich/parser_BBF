"""
Парсинг основной информации матча и протокола событий play-by-play.

Выходные файлы:
    match_<ID>_info.csv  — основная информация (счёт, периоды, место, зрители, судьи)
    match_<ID>_pbp.csv   — полный протокол событий play-by-play
"""
import requests
import pandas as pd
import sys

from match_parser import get_match_summary

BASE_URL = "https://org.infobasket.su"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://belarus.russiabasket.ru/'
}

# === Игровые типы событий (PlayTypeID) ===

# Забитые броски: тип -> очки
SCORE_MAP = {1: 1, 2: 2, 3: 3}

# Промахи
MISS_MAP = {
    4: "Штрафной (промах)",
    5: "2-очковый (промах)",
    6: "3-очковый (промах)",
}

# Фолы
FOUL_MAP = {
    40: "Фол P (личный)",
    41: "Фол U (неспортивный)",
    42: "Фол T (технический игроку)",
    43: "Фол D (дисквалифицирующий)",
    44: "Фол C (технический тренеру)",
    45: "Фол B (технический скамейке)",
    46: "Фол F (обоюдный)",
}

# Потери
TURNOVER_TYPES = set(range(10, 21)) | {47}

# Служебные маркеры протокола (дублируют игровые события, по умолчанию скрыты)
MARKER_TYPES = {7, 24, 29, 30, 31, 32, 33, 59, 60, 61, 62, 63, 69, 70, 71, 72, 73}

GAME_STATUS_MAP = {0: "Запланирован", 1: "Завершён", 2: "LIVE"}


def _safe_int(val):
    if val is None:
        return 0
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


def _period_label(period):
    """Человекочитаемое название периода."""
    if period <= 4:
        return f"{period}-я четверть"
    return f"Овертайм {period - 4}"


def _remaining_time(period, ds):
    """
    Конвертирует прошедшие децисекунды периода в оставшееся время MM:SS.
    Четверти — 10 минут (6000 дс), овертаймы — 5 минут (3000 дс).
    """
    length = 6000 if period <= 4 else 3000
    rem = max(0, length - _safe_int(ds))
    return f"{rem // 600:02d}:{(rem % 600) // 10:02d}"


def _describe(type_id, ev, participants, play_team):
    """Текстовое описание события по его типу."""
    if type_id in SCORE_MAP:
        return {1: "Штрафной забит (+1)", 2: "2-очковый забит (+2)", 3: "3-очковый забит (+3)"}[type_id]
    if type_id in MISS_MAP:
        return MISS_MAP[type_id]
    if type_id == 8:
        return "Выход на площадку"
    if type_id == 9:
        return "Уход с площадки (замена)"
    if type_id == 21:
        return "Начало периода"
    if type_id == 22:
        return "Конец периода"
    if type_id == 23:
        return "Тайм-аут"
    if type_id == 25:
        return "Переда (ассист)"
    if type_id == 26:
        return "Перехват"
    if type_id == 27:
        return "Блок-шот"
    if type_id == 28:
        # Подбор: по parent-событию (броску) определяем, чей это подбор
        parent = ev.get('ParentPlayID') or None
        own_team = participants.get(ev.get('StartID') or 0, {}).get('TNum')
        if parent and own_team and play_team.get(parent) == own_team:
            return "Подбор в нападении"
        return "Подбор в защите"
    if type_id in FOUL_MAP:
        return FOUL_MAP[type_id]
    if type_id in TURNOVER_TYPES:
        return "Потеря мяча"
    if 50 <= type_id <= 54:
        return "Фол соперника (получен)"
    if type_id in (0, 100):
        return "Конец матча"
    return f"Событие ({type_id})"


def _fetch_events(game_id, data):
    """
    Достаёт события матча: сначала из OnlinePlays JSON,
    при пустоте — из запасного текстового лога Api/GetOnlinePlays.
    """
    events = list(data.get('OnlinePlays', []) or [])
    if events:
        return events

    log_url = f"{BASE_URL}/Api/GetOnlinePlays/{game_id}?last=0"
    try:
        log_raw = requests.get(log_url, headers=HEADERS, timeout=30).text.strip('"')
        for e in log_raw.split(';'):
            r = e.split(',')
            if len(r) > 8:
                events.append({
                    'PlayID': _safe_int(r[0]),
                    'PlayPeriod': _safe_int(r[2]),
                    'PlaySecond': _safe_int(r[3]),
                    'StartID': _safe_int(r[5]),
                    'ParentPlayID': _safe_int(r[6]) or None,
                    'PlayTypeID': _safe_int(r[7]),
                    'SysStatus': _safe_int(r[11]),
                })
    except Exception:
        pass
    return events


def parse_play_by_play(game_id, include_markers=False, verbose=True):
    """
    Строит полный протокол событий матча (play-by-play).

    Args:
        game_id: ID матча
        include_markers: показывать служебные маркерные события
        verbose: печатать прогресс в консоль

    Returns:
        pd.DataFrame с колонками:
        П/п, Период, Время, Счёт, Команда, №, Игрок, Роль, Событие, Тип
        или None при ошибке / отсутствии событий
    """
    if verbose:
        print(f"--- Play-by-play протокол матча {game_id} ---")

    online_url = f"{BASE_URL}/Widget/GetOnline/{game_id}?format=json&lang=ru"
    try:
        data = requests.get(online_url, headers=HEADERS, timeout=30).json()
    except Exception as e:
        if verbose:
            print(f"[-] Ошибка загрузки матча: {e}")
        return None

    # Названия команд
    teams_map = {1: "Команда 1", 2: "Команда 2"}
    for ot in data.get('OnlineTeams', []) or []:
        if ot.get('TeamNumber') in (1, 2):
            name = (ot.get('TeamName2') or ot.get('TeamName1') or '').strip()
            if name:
                teams_map[ot['TeamNumber']] = name

    # Участники (игроки и тренеры): StartID -> инфо
    participants = {}
    for s in data.get('OnlineStarts', []) or []:
        s_id = s.get('StartID')
        if s_id == 0 or s.get('StartType') == 4:  # 4 = судейская бригада
            continue
        participants[s_id] = {
            'Name': (s.get('PersonName2') or s.get('PersonName1') or '—').strip(),
            'Team': teams_map.get(s.get('TeamNumber'), '—'),
            'TNum': s.get('TeamNumber'),
            'No': s.get('DisplayNumber', ''),
            'Role': 'Игрок' if s.get('StartType') == 1 else 'Тренер',
        }

    events = _fetch_events(game_id, data)
    if not events:
        if verbose:
            print("[-] Событий матча не найдено.")
        return None

    # Только актуальные события, сортировка по хронологии
    events = [e for e in events if e.get('SysStatus') != 0]
    events.sort(key=lambda x: (x.get('PlayPeriod', 0), x.get('PlaySecond', 0), x.get('PlayID', 0)))

    # Карта PlayID -> команда события (нужна для определения типа подбора)
    play_team = {}
    for e in events:
        p_id = e.get('PlayID')
        if p_id is None:
            continue
        s_id = e.get('StartID') or 0
        if s_id in participants:
            play_team[p_id] = participants[s_id]['TNum']
        elif s_id in (1, 2):
            play_team[p_id] = s_id

    rows = []
    score_a, score_b = 0, 0
    n = 0
    for ev in events:
        type_id = ev.get('PlayTypeID') or 0
        if type_id in MARKER_TYPES and not include_markers:
            continue

        period = ev.get('PlayPeriod') or 1
        ds = ev.get('PlaySecond') or 0
        s_id = ev.get('StartID') or 0

        # Набранные очки -> текущий счёт
        points = SCORE_MAP.get(type_id, 0)
        if points:
            t_num = participants.get(s_id, {}).get('TNum')
            if t_num == 1:
                score_a += points
            elif t_num == 2:
                score_b += points

        # Участник события
        p = participants.get(s_id)
        if p:
            team, name, num, role = p['Team'], p['Name'], p['No'], p['Role']
        elif s_id in (1, 2):
            team = teams_map.get(s_id, f"Команда {s_id}")
            name, num, role = '—', '', 'Команда'
        else:
            team, name, num, role = '—', '—', '', '—'

        n += 1
        rows.append({
            'П/п': n,
            'Период': _period_label(period),
            'Время': _remaining_time(period, ds),
            'Счёт': f"{score_a}:{score_b}",
            'Команда': team,
            '№': num,
            'Игрок': name,
            'Роль': role,
            'Событие': _describe(type_id, ev, participants, play_team),
            'Тип': type_id,
        })

    if not rows:
        if verbose:
            print("[-] Игровых событий не найдено.")
        return None

    df = pd.DataFrame(rows)
    if verbose:
        print(f"[+] Событий в протоколе: {len(df)}")
    return df


def build_summary_df(game_id, summary=None):
    """
    DataFrame с основной информацией матча (Параметр / Значение).

    Args:
        game_id: ID матча
        summary: готовый dict от get_match_summary() (если None — загружается)

    Returns:
        pd.DataFrame или None
    """
    if summary is None:
        summary = get_match_summary(game_id)
    if not summary:
        return None

    status = GAME_STATUS_MAP.get(summary.get('game_status', 0), 'Неизвестно')
    rows = [
        ('ID матча', game_id),
        ('Турнир', summary.get('tournament', '')),
        ('Дата и время', summary.get('datetime', '')),
        ('Команда 1', summary.get('team_a', '')),
        ('Команда 2', summary.get('team_b', '')),
        ('Счёт', summary.get('score_final', '')),
        ('Счёт по периодам', summary.get('score_periods', '')),
        ('Место проведения', summary.get('location', '')),
        ('Зрители', summary.get('spectators', '')),
        ('Судьи', summary.get('referees', '')),
        ('Комиссар', summary.get('commissioner', '')),
        ('Статус матча', status),
    ]
    return pd.DataFrame(rows, columns=['Параметр', 'Значение'])


def save_summary_to_csv(df, game_id, verbose=True):
    """Сохраняет основную информацию матча в match_<ID>_info.csv."""
    if df is None or df.empty:
        return None
    filename = f"match_{game_id}_info.csv"
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    if verbose:
        print(f"[+] Сохранён файл: {filename}")
    return filename


def save_pbp_to_csv(df, game_id, verbose=True):
    """Сохраняет протокол событий в match_<ID>_pbp.csv."""
    if df is None or df.empty:
        return None
    filename = f"match_{game_id}_pbp.csv"
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    if verbose:
        print(f"[+] Сохранён файл: {filename} (событий: {len(df)})")
    return filename


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python pbp_parser.py <GAME_ID> [--all]")
        print("Пример: python pbp_parser.py 1016417")
        print("  --all — включить служебные маркерные события")
        sys.exit(1)

    target = sys.argv[1]
    show_markers = '--all' in sys.argv

    summary_df = build_summary_df(target)
    save_summary_to_csv(summary_df, target)

    pbp_df = parse_play_by_play(target, include_markers=show_markers)
    if pbp_df is not None:
        save_pbp_to_csv(pbp_df, target)
    else:
        print("[-] Не удалось построить протокол событий.")