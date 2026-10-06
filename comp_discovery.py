"""
Обнаружение активных турниров в API ИнфоБаскет.

Логика:
    1. Иерархия API: Сезон -> Федерация -> Раздел (Мужчины/Женщины/...) -> Турнир -> Этапы.
    2. Точка входа — корень БФБ текущего сезона (BFB_ROOT_ID).
    3. Обход дерева вниз до листьев; турнир считается активным, если у него
       есть матчи в календаре рядом с текущей датой (±window_days).
    4. Календарь по родительскому узлу агрегирует матчи всех дочерних этапов,
       поэтому достаточно одного запроса на турнир.

Зачем: пользователю не нужно искать ID турнира — приложение само покажет
играющиеся сейчас соревнования.
"""
import requests
from datetime import datetime

BASE_URL = "https://org.infobasket.su"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://belarus.russiabasket.ru/'
}

# Корень БФБ сезона 2026/2027 (определяется через дерево: 56293 -> БФБ)
BFB_ROOT_ID = 56296


def _get_json(path, params=None, timeout=20):
    """GET-запрос с возвратом JSON или None."""
    try:
        r = requests.get(f"{BASE_URL}/{path}", headers=HEADERS, params=params, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        return data if not isinstance(data, str) else None  # API шлёт "BadRequest" строкой
    except Exception:
        return None


def get_comps_children(comp_id):
    """Дочерние узлы турнира (этапы/группы). Пустой список — узел листовой."""
    data = _get_json(f"Widget/CompIssue/{comp_id}", {'format': 'json', 'lang': 'ru'})
    if not data:
        return []
    return data.get('Comps') or data.get('Children') or []


def get_calendar_games(comp_id, days_back=7, days_forward=7):
    """Матчи турнира (со всеми дочерними этапами) за период вокруг сегодня."""
    data = _get_json(
        "Comp/GetCalendarCarousel/",
        {'comps': comp_id, 'from': f'today-{days_back}', 'to': f'today+{days_forward}', 'format': 'json', 'lang': 'ru'}
    )
    if isinstance(data, list):
        return data
    return []


def find_bfb_root():
    """
    Актуальный корень БФБ: определяется по дереву сезонов через известную команду.
    Fallback на захардкоженный ID.
    """
    try:
        data = _get_json("Widget/GetTeamSeasons/25724", {'format': 'json', 'lang': 'ru'})
        if isinstance(data, list) and data:
            season_id = data[0]['CompID']  # самый свежий сезон
            for child in get_comps_children(season_id):
                if child.get('CompShortNameRu') == 'БФБ':
                    return child['CompID']
    except Exception:
        pass
    return BFB_ROOT_ID


def _walk_tree(comp_id, depth=0, max_depth=5):
    """
    Рекурсивный обход дерева узлов: возвращает список узлов
    (comp_id, name, parent_names).
    """
    children = get_comps_children(comp_id)
    if not children or depth >= max_depth:
        return [(comp_id, '', [])]

    nodes = []
    for child in children:
        cid = child.get('CompID')
        name = child.get('CompShortNameRu') or child.get('CompNameRu') or ''
        for node_cid, _, chain in _walk_tree(cid, depth + 1, max_depth):
            if node_cid == cid:
                nodes.append((cid, name, []))
            else:
                nodes.append((node_cid, '', chain + [name]))
    return nodes


def discover_active_comps(days_back=7, days_forward=7, verbose=False):
    """
    Находит активные турниры БФБ: обходит дерево от корня и проверяет календарь.

    Стратегия (быстрая):
      1. Берём разделы БФБ (Мужчины, Женщины, Юноши, Девушки).
      2. Для каждого раздела берём турниры (BETERA-Чемпионат, Кубок, ...).
      3. Проверяем календарь турнира-родителя (один запрос — все этапы).
      4. Турнир активен, если есть матчи в окне ±N дней.

    Returns:
        list[dict]: {
            'comp_id', 'name', 'section', 'games_count', 'games',
            'nearest_date', 'nearest_game'
        } — отсортирован по количеству игр (по убыванию)
    """
    def log(msg):
        if verbose:
            print(msg)

    root = find_bfb_root()
    log(f"[i] Корень БФБ: {root}")

    sections = get_comps_children(root)
    active = []

    for section in sections:
        sec_id = section.get('CompID')
        sec_name = section.get('CompShortNameRu') or ''
        if not sec_name:
            continue

        # Турниры внутри раздела
        tournaments = get_comps_children(sec_id)
        # Некоторые узлы (например, списки судей) — пропускаем без детей и без матчей
        for t in tournaments:
            t_id = t.get('CompID')
            t_name = t.get('CompShortNameRu') or t.get('CompNameRu') or ''
            if not t_id or not t_name:
                continue

            games = get_calendar_games(t_id, days_back, days_forward)
            log(f"[i] {sec_name} / {t_name} ({t_id}): {len(games)} матчей")

            if not games:
                continue

            # Ближайшая игра: сначала LIVE и сегодня, потом по дате
            def game_sort_key(g):
                status = g.get('GameStatus', 0)
                live_first = 0 if status == 2 else 1
                return (live_first, g.get('GameDateInt', 999999))

            games_sorted = sorted(games, key=game_sort_key)
            nearest = games_sorted[0]

            active.append({
                'comp_id': t_id,
                'name': t_name,
                'section': sec_name,
                'games_count': len(games),
                'games': games_sorted,
                'nearest_date': nearest.get('GameDate', ''),
                'nearest_game': nearest,
            })

    # Сортировка: сначала с бОльшим числом матчей
    active.sort(key=lambda x: x['games_count'], reverse=True)
    return active


def format_comps_list(active_comps):
    """
    Формирует читаемый список активных турниров для отображения.

    Returns:
        list[str]: строки вида "BETERA-Чемпионат (Мужчины) — 17 матчей, ближайший 01.10.2026"
    """
    lines = []
    for c in active_comps:
        live = c['nearest_game'].get('GameStatus') == 2
        suffix = " (сейчас LIVE!)" if live else ""
        lines.append(
            f"{c['name']} ({c['section']}) — {c['games_count']} матчей, ближайший: {c['nearest_date']}{suffix}"
        )
    return lines


if __name__ == "__main__":
    import sys
    db = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    df = int(sys.argv[2]) if len(sys.argv) > 2 else 7

    print("=" * 50)
    print("   АКТИВНЫЕ ТУРНИРЫ БФБ")
    print("=" * 50)
    comps = discover_active_comps(db, df, verbose=True)
    if not comps:
        print("[-] Активных турниров не найдено. Расширьте диапазон дат.")
        sys.exit(0)

    print(f"\n[+] Найдено активных турниров: {len(comps)}\n")
    for i, line in enumerate(format_comps_list(comps)):
        cid = comps[i]['comp_id']
        print(f"  {i} -> {line} | ID: {cid}")