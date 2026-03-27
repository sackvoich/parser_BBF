import requests
import pandas as pd
import sys

def safe_int(val):
    if val is None: return 0
    try: return int(val)
    except: return 0

def parse_fouls(game_id, verbose=True):
    """
    Парсит фолы матча и возвращает DataFrame.
    
    Args:
        game_id: ID матча
        verbose: Если True — выводит сообщения в консоль
    
    Returns:
        pd.DataFrame с данными о фолах или None при ошибке
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://belarus.russiabasket.ru/'
    }

    if verbose:
        print(f"--- Охота на фолы в матче {game_id} (Гибридный режим) ---")

    # 1. Тянем основной JSON (там и ростер, и лог для архива)
    online_url = f"https://org.infobasket.su/Widget/GetOnline/{game_id}?format=json&lang=ru"
    try:
        response = requests.get(online_url, headers=headers)
        r_data = response.json()

        # Названия команд
        teams = {1: "Home", 2: "Away"}
        for ot in r_data.get('OnlineTeams', []):
            if ot['TeamNumber'] > 0:
                teams[ot['TeamNumber']] = (ot.get('TeamName2') or ot.get('TeamName1')).strip()

        # Кто есть кто по StartID
        participants = {}
        for s in r_data.get('OnlineStarts', []):
            participants[s['StartID']] = {
                'Name': (s.get('PersonName2') or s.get('PersonName1') or "НЕИЗВЕСТНЫЙ").strip(),
                'Team': teams.get(s['TeamNumber'], "Unknown"),
                'No': s.get('DisplayNumber', ''),
                'Role': 'Игрок' if s.get('StartType') == 1 else 'Тренер'
            }

        # Пытаемся взять лог прямо из JSON (Архивный вариант)
        events_list = r_data.get('OnlinePlays', [])

    except Exception as e:
        if verbose:
            print(f"[-] Пиздец с ростером: {e}")
        return None

    # 2. Если в JSON лога нет, пробуем старый добрый Api/GetOnlinePlays (Лайв вариант)
    if not events_list:
        if verbose:
            print("[!] В основном JSON пусто, пробую вытрясти сырой лог...")
        log_url = f"https://org.infobasket.su/Api/GetOnlinePlays/{game_id}?last=0"
        try:
            log_raw = requests.get(log_url, headers=headers).text.strip('"')
            raw_rows = [e.split(',') for e in log_raw.split(';') if e and len(e.split(',')) > 8]

            for r in raw_rows:
                events_list.append({
                    'PlayPeriod': safe_int(r[2]),
                    'PlaySecond': safe_int(r[3]),
                    'StartID': safe_int(r[5]),
                    'PlayTypeID': safe_int(r[7]),
                    'SysStatus': safe_int(r[11])
                })
        except:
            pass

    if not events_list:
        if verbose:
            print("[-] Глухо как в танке. Данных о ходе игры нет ни в одном кармане.")
        return None

    # Словарик типов фолов
    FOUL_MAP = {
        40: "P (Личный)", 41: "U (Неспортивный)", 42: "T (Технический игроку)",
        43: "D (Дисквалифицирующий)", 44: "C (Технический тренеру)",
        45: "B (Технический скамейке)", 46: "F (Обоюдный/Драка)"
    }

    fouls_report = []

    # Сортируем по времени, чтобы отчет был хронологическим
    events_sorted = sorted(events_list, key=lambda x: (x.get('PlayPeriod', 0), x.get('PlaySecond', 0)))

    for ev in events_sorted:
        if ev.get('SysStatus') == 0: continue # Пропускаем удаленный мусор

        type_id = ev.get('PlayTypeID')
        if type_id and 40 <= type_id <= 46:
            s_id = ev.get('StartID')
            who = participants.get(s_id, {'Name': f'ID:{s_id}', 'Team': '?', 'No': '?', 'Role': '?'})

            time_ds = ev.get('PlaySecond', 0)
            mins = int(time_ds // 600)
            secs = int((time_ds % 600) // 10)

            fouls_report.append({
                'Период': ev.get('PlayPeriod'),
                'Время': f"{mins:02d}:{secs:02d}",
                'Команда': who['Team'],
                '№': who['No'],
                'Имя': who['Name'],
                'Роль': who['Role'],
                'Тип фола': FOUL_MAP.get(type_id, f"Фол ({type_id})")
            })

    if not fouls_report:
        if verbose:
            print("Ни одного фола не найдено. Либо это была игра джентльменов, либо лог битый.")
        return None

    df = pd.DataFrame(fouls_report)
    return df


def save_fouls_to_csv(df, game_id, verbose=True):
    """
    Сохраняет DataFrame с фолами в CSV файл.
    
    Args:
        df: DataFrame с данными о фолах
        game_id: ID матча
        verbose: Если True — выводит сообщения в консоль
    
    Returns:
        Имя файла или None при ошибке
    """
    if df is None or df.empty:
        return None
    
    filename = f"match_{game_id}_fouls.csv"
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    
    if verbose:
        print("\n" + "!"*60)
        print(f"СПИСОК ГРЕХОВ СОБРАН! Найдено фолов: {len(df)}")
        print(df.to_string(index=False))
        print("!"*60)
        print(f"\nФайл готов: {filename}")
    
    return filename


def parse_all_fouls(game_id, verbose=True):
    """
    Старая функция для обратной совместимости (CLI).
    Парсит фолы и сохраняет в CSV.
    """
    df = parse_fouls(game_id, verbose=verbose)
    if df is not None:
        save_fouls_to_csv(df, game_id, verbose=verbose)


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "1016460"
    parse_all_fouls(target)