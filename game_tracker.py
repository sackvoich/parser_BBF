import requests
import matplotlib
matplotlib.use('Agg')  # Неинтерактивный бэкенд для работы без GUI
import matplotlib.pyplot as plt
import pandas as pd
import sys
import os
from typing import Optional, Tuple

# Глобальные заголовки для всех запросов
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://belarus.russiabasket.ru/'
}


def get_event_abs_time(period: int, time_ds: int) -> float:
    """Превращает децисекунды периода в сквозные минуты матча"""
    if period <= 4:
        # Регулярный чемпионат: 4 четверти по 10 минут
        return (period - 1) * 10 + (time_ds / 600)
    else:
        # Овертаймы по 5 минут
        return 40 + (period - 5) * 5 + (time_ds / 300)


def fetch_game_data(game_id: str) -> Optional[dict]:
    """
    Загружает данные о матче из API.
    
    Returns:
        dict с данными матча или None при ошибке
    """
    online_url = f"https://org.infobasket.su/Widget/GetOnline/{game_id}?format=json&lang=ru"
    try:
        r_json = requests.get(online_url, headers=HEADERS).json()
        return r_json
    except Exception as e:
        print(f"[!] Ошибка при чтении данных матча: {e}")
        return None


def fetch_play_log(game_id: str) -> list:
    """
    Загружает play-by-play лог из запасного эндпоинта.
    
    Returns:
        list событий или пустой список при ошибке
    """
    log_url = f"https://org.infobasket.su/Api/GetOnlinePlays/{game_id}?last=0"
    try:
        log_raw = requests.get(log_url, headers=HEADERS).text.strip('"')
        raw_rows = [e.split(',') for e in log_raw.split(';') if e and len(e.split(',')) > 8]
        
        # Конвертируем сырые строки в словари
        events = []
        for r in raw_rows:
            events.append({
                'PlayPeriod': int(r[2]),
                'PlaySecond': int(r[3]),
                'StartID': int(r[5]),
                'PlayTypeID': int(r[7]),
                'SysStatus': int(r[11])
            })
        return events
    except Exception as e:
        print(f"[!] Ошибка при загрузке лога событий: {e}")
        return []


def extract_events(r_json: dict, game_id: str) -> tuple:
    """
    Извлекает события из JSON или загружает из лога.
    
    Returns:
        (events_list, starts_map, team1_name, team2_name)
    """
    team1_name = r_json['OnlineTeams'][1]['TeamName1']
    team2_name = r_json['OnlineTeams'][2]['TeamName1']
    
    # Маппинг: StartID -> Номер команды
    starts = {s['StartID']: s['TeamNumber'] for s in r_json.get('OnlineStarts', [])}
    
    # Пробуем достать события из самого JSON
    events_list = r_json.get('OnlinePlays', [])
    
    # Если в JSON событий нет, лезем в текстовый лог
    if not events_list:
        print("[i] В основном JSON пусто, загружаю запасной эндпоинт...")
        events_list = fetch_play_log(game_id)
    
    return events_list, starts, team1_name, team2_name


def process_score_events(events: list, starts: dict) -> Optional[dict]:
    """
    Обрабатывает события набора очков и строит прогрессии.
    
    Returns:
        dict с данными для графиков или None если событий нет
    """
    time_points = [0]
    score_a = [0]
    score_b = [0]
    lead_margin = [0]
    curr_a, curr_b = 0, 0
    
    # Сортируем события по времени
    events_sorted = sorted(events, key=lambda x: (x['PlayPeriod'], x['PlaySecond']))
    
    for ev in events_sorted:
        if ev.get('SysStatus') == 0:
            continue  # Пропускаем удаленные события
        
        type_id = ev['PlayTypeID']
        if type_id in [1, 2, 3]:  # Только броски
            pts = {1: 1, 2: 2, 3: 3}[type_id]
            t_num = starts.get(ev['StartID'], 0)
            
            if t_num == 1:
                curr_a += pts
            elif t_num == 2:
                curr_b += pts
            else:
                continue  # Непонятно чьё очко
            
            abs_t = get_event_abs_time(ev['PlayPeriod'], ev['PlaySecond'])
            
            time_points.append(abs_t)
            score_a.append(curr_a)
            score_b.append(curr_b)
            lead_margin.append(curr_a - curr_b)
    
    if len(time_points) < 2:
        return None
    
    return {
        'time_points': time_points,
        'score_a': score_a,
        'score_b': score_b,
        'lead_margin': lead_margin
    }


def create_progression_chart(game_id: str, data: dict, team1_name: str, team2_name: str, 
                             output_path: str) -> str:
    """Создаёт график прогрессии счёта и сохраняет в файл"""
    time_points = data['time_points']
    score_a = data['score_a']
    score_b = data['score_b']
    
    plt.style.use('dark_background')
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    ax1.step(time_points, score_a, label=team1_name, color='#00aaff', linewidth=2, where='post')
    ax1.step(time_points, score_b, label=team2_name, color='#ff4400', linewidth=2, where='post')
    
    for p in [10, 20, 30, 40]:
        plt.axvline(x=p, color='white', linestyle='--', alpha=0.2)
    
    ax1.set_title(f"SCORE TRACKER: {game_id}", fontsize=14, color='white')
    ax1.set_xlabel("Минуты матча")
    ax1.set_ylabel("Очки")
    ax1.legend()
    ax1.grid(True, alpha=0.1)
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    return output_path


def create_lead_chart(game_id: str, data: dict, team1_name: str, team2_name: str,
                      output_path: str) -> str:
    """Создаёт график разницы в счёте и сохраняет в файл"""
    time_points = data['time_points']
    lead_margin = data['lead_margin']
    
    plt.figure(figsize=(12, 5))
    
    lead_series = pd.Series(lead_margin)
    plt.fill_between(time_points, lead_margin, 0,
                     where=(lead_series >= 0),
                     step='post', color='#f0e442', alpha=0.8, label=team1_name)
    plt.fill_between(time_points, lead_margin, 0,
                     where=(lead_series < 0),
                     step='post', color='#0072b2', alpha=0.8, label=team2_name)
    
    plt.axhline(y=0, color='white', linewidth=1)
    
    min_margin = int(min(lead_margin)) - 5
    max_margin = int(max(lead_margin)) + 10
    plt.yticks(range(min_margin, max_margin, 5))
    
    for p in [10, 20, 30, 40]:
        plt.axvline(x=p, color='white', linestyle='--', alpha=0.2)
    
    plt.title(f"LEAD TRACKER: {team1_name} vs {team2_name}", fontsize=14)
    plt.ylabel("РАЗНИЦА В СЧЕТЕ")
    plt.grid(True, axis='y', alpha=0.1)
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_path


def build_game_charts(game_id: str, verbose: bool = True) -> Optional[Tuple[str, str]]:
    """
    Основная функция для построения графиков матча.
    
    Args:
        game_id: ID матча
        verbose: Выводить ли сообщения в консоль
    
    Returns:
        Кортеж (путь_к_графику_прогрессии, путь_к_графику_разницы) или None при ошибке
    """
    if verbose:
        print(f"--- Глубокое сканирование матча {game_id} ---")
    
    # 1. Загружаем данные о матче
    r_json = fetch_game_data(game_id)
    if r_json is None:
        return None
    
    # 2. Извлекаем события
    events, starts, team1_name, team2_name = extract_events(r_json, game_id)
    
    if not events:
        print("[!] События не найдены. Возможно, ход игры для этого матча не записывали.")
        return None
    
    # 3. Обрабатываем события набора очков
    chart_data = process_score_events(events, starts)
    if chart_data is None:
        print("[!] Событий набора очков не найдено.")
        return None
    
    # 4. Создаём графики
    progression_file = f"match_{game_id}_progression.png"
    difference_file = f"match_{game_id}_difference_solid.png"
    
    if verbose:
        print(f"[i] Рисую графики для {team1_name} и {team2_name}...")
    
    create_progression_chart(game_id, chart_data, team1_name, team2_name, progression_file)
    create_lead_chart(game_id, chart_data, team1_name, team2_name, difference_file)
    
    if verbose:
        print(f"--- УСПЕХ! Графики сохранены: {progression_file}, {difference_file} ---")
    
    return progression_file, difference_file


def create_game_charts(game_id: str) -> None:
    """
    Устаревшая функция-обёртка для обратной совместимости.
    Используйте build_game_charts() вместо неё.
    """
    build_game_charts(game_id, verbose=True)


if __name__ == "__main__":
    game_to_track = sys.argv[1] if len(sys.argv) > 1 else "1016420"
    build_game_charts(game_to_track)