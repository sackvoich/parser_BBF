import requests
import pandas as pd
from datetime import datetime

def find_recent_matches(comp_id, days_back=14, days_forward=14):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://belarus.russiabasket.ru/'
    }

    # Параметры from и to позволяют серверу самому отфильтровать даты
    # Формат: today-N или today+N
    url = f"https://org.infobasket.su/Comp/GetCalendarCarousel/?comps={comp_id}&from=today-{days_back}&to=today+{days_forward}&format=json&lang=ru"

    print(f"--- Сканирую календарь (период: -{days_back} / +{days_forward} дней) ---")
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        games = response.json()
    except Exception as e:
        print(f"[-] Не удалось достучаться до календаря: {e}")
        return

    if not games:
        print("[-] В этом диапазоне матчей не найдено. Либо лига вымерла, либо ID не тот.")
        return

    match_list = []

    for g in games:
        game_id = g.get('GameID')
        # Формируем статус: если игра прошла - счет, если нет - время
        status = "ЗАПЛАНИРОВАН"
        score = ""
        if g.get('GameStatus') == 1: # Завершено
            status = "ЗАВЕРШЕН"
            score = f"{g.get('ScoreA')}:{g.get('ScoreB')}"
        elif g.get('GameStatus') == 2: # В процессе
            status = "LIVE"
            score = f"{g.get('ScoreA')}:{g.get('ScoreB')}"
        else:
            score = g.get('GameTimeMsk', g.get('GameTime', '??:??'))

        match_list.append({
            'ID матча': game_id,
            'Дата': g.get('GameDate'),
            'День': g.get('DayOfWeekRu'),
            'Хозяева': g.get('ShortTeamNameAru'),
            'Гости': g.get('ShortTeamNameBru'),
            'Счет/Время': score,
            'Статус': status,
            'Турнир': g.get('CompNameRu')
        })

    # Превращаем в красивую таблицу
    df = pd.DataFrame(match_list)
    
    # Выводим в консоль для быстрого копирования
    print("\n" + "="*80)
    print(df[['ID матча', 'Дата', 'Хозяева', 'Гости', 'Счет/Время', 'Статус']].to_string(index=False))
    print("="*80)

    # На всякий случай сохраняем в CSV, чтобы под рукой было
    filename = f"matches_list_{comp_id}.csv"
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"\n[+] Список также сохранен в файл: {filename}")

if __name__ == "__main__":
    # 50758 - ID всего сезона
    # Можно менять диапазон дней прямо тут
    import sys
    cid = sys.argv[1] if len(sys.argv) > 1 else "50758"
    find_recent_matches(cid, days_back=14, days_forward=14)