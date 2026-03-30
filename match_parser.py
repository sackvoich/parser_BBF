import requests
import pandas as pd
import json
import sys

# Глобальная функция-"презерватив" для защиты от NoneType
def safe_int(val):
    if val is None: return 0
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


def get_match_summary(game_id):
    """
    Извлекает общую информацию о матче (Match Header) из JSON-ответа GetOnline.
    
    Args:
        game_id: ID матча
        
    Returns:
        dict с полями: tournament, datetime, location, spectators, score_final,
                       score_periods, referees, commissioner, team_a, team_b
        или None при ошибке
    """
    import re
    from datetime import datetime as dt
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://belarus.russiabasket.ru/'
    }
    
    url = f"https://org.infobasket.su/Widget/GetOnline/{game_id}?format=json&lang=ru"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"[-] Ошибка при загрузке данных матча: {e}")
        return None
    
    # === 1. Дата и время ===
    online = data.get('Online', {})
    
    def parse_ms_date(val):
        """Конвертирует /Date(1234567890000)/ в читаемую дату"""
        if not val:
            return None
        match = re.search(r'/Date\((-?\d+)\)/', str(val))
        if match:
            ts = int(match.group(1)) / 1000
            return dt.fromtimestamp(ts)
        return None
    
    game_date_raw = online.get('GameDate', '')
    game_time_raw = online.get('GameTime', '')
    
    # Парсим дату и время
    game_date_dt = parse_ms_date(game_date_raw)
    game_time_dt = parse_ms_date(game_time_raw)
    
    # Формируем строку
    if game_date_dt and game_time_dt:
        # Дата из GameDate, время из GameTime
        datetime_str = f"{game_date_dt.strftime('%d.%m.%Y')} {game_time_dt.strftime('%H:%M')}"
    elif game_date_dt:
        datetime_str = game_date_dt.strftime('%d.%m.%Y %H:%M')
    elif game_time_dt:
        datetime_str = game_time_dt.strftime('%d.%m.%Y %H:%M')
    else:
        # Пробуем взять строковые значения как fallback
        datetime_str = f"{str(game_date_raw)} {str(game_time_raw)}".strip()
    
    # === 2. Место проведения (город + арена) ===
    arena = online.get('ArenaRu', '') or online.get('Venue1', '')
    city = online.get('CityRu', '') or online.get('City', '')
    
    # Очищаем от лишних пробелов и запятых
    if arena:
        arena = str(arena).strip().rstrip(',').strip()
    if city:
        city = str(city).strip().rstrip(',').strip()
    
    if city and arena and city not in arena:
        location = f"{city}, {arena}"
    elif arena:
        location = arena
    elif city:
        location = city
    else:
        location = "Не указано"
    
    # === 3. Зрители ===
    attendance = online.get('Attendance')
    if attendance is None or attendance == 0:
        spectators = "Нет данных"
    else:
        spectators = str(attendance)
    
    # === 4. Турнир ===
    # Берём с верхнего уровня data, а не из Online
    comp_name = data.get('CompNameRu', '') or online.get('CompNameRu', '')
    league_name = data.get('LeagueNameRu', '') or online.get('LeagueNameRu', '')
    
    if comp_name and league_name:
        tournament = f"{league_name}, {comp_name}"
    elif league_name:
        tournament = league_name
    elif comp_name:
        tournament = comp_name
    else:
        tournament = "Не указано"
    
    # === 5. Команды (из OnlineTeams) ===
    team_a = "Команда 1"
    team_b = "Команда 2"
    team_a_id = None
    team_b_id = None
    
    for ot in data.get('OnlineTeams', []):
        team_num = ot.get('TeamNumber')
        team_name = (ot.get('TeamName2') or ot.get('TeamName1') or '').strip()
        team_city = ot.get('TeamCityRu', '') or ot.get('TeamRegionNameRu', '')
        full_name = f"{team_name} ({team_city})" if team_city else team_name
        
        if team_num == 1:
            team_a = full_name if full_name else "Команда 1"
            team_a_id = ot.get('TeamID')
        elif team_num == 2:
            team_b = full_name if full_name else "Команда 2"
            team_b_id = ot.get('TeamID')
    
    # === 6. Итоговый счёт ===
    # Сначала пробуем взять из Online (для LIVE матчей)
    score_a = online.get('ScoreA')
    score_b = online.get('ScoreB')
    
    # Если нет, берём из GameTeams (для завершённых матчей)
    if score_a is None or score_b is None:
        game_teams = data.get('GameTeams', [])
        if game_teams:
            # Ищем команду 1 и команду 2
            for gt in game_teams:
                if gt.get('TeamNumber') == 1:
                    score_a = gt.get('Score', 0)
                elif gt.get('TeamNumber') == 2:
                    score_b = gt.get('Score', 0)
    
    score_a = score_a or 0
    score_b = score_b or 0
    score_final = f"{score_a}:{score_b}"

    # === 7. Счёт по периодам ===
    periods_parts = []
    for period in data.get('OnlinePeriods', []):
        # Пробуем разные варианты имён полей
        p_num = period.get('PeriodNumber') or period.get('Period') or 0
        p_score_a = period.get('ScoreA') or period.get('Team1Score') or 0
        p_score_b = period.get('ScoreB') or period.get('Team2Score') or 0
        
        # Если есть ScoreA и ScoreB — добавляем период
        if p_num > 0 and (p_score_a or p_score_b):
            periods_parts.append(f"{p_score_a}:{p_score_b}")
    
    # Если OnlinePeriods пуст, пробуем взять из GameTeams[].Periods
    if not periods_parts:
        game_teams = data.get('GameTeams', [])
        if len(game_teams) >= 2:
            periods_a = {p.get('Period'): p.get('Score') for p in game_teams[0].get('Periods', []) if p.get('Period')}
            periods_b = {p.get('Period'): p.get('Score') for p in game_teams[1].get('Periods', []) if p.get('Period')}
            
            all_periods = sorted(set(periods_a.keys()) | set(periods_b.keys()))
            for p_num in all_periods:
                s_a = periods_a.get(p_num, 0)
                s_b = periods_b.get(p_num, 0)
                periods_parts.append(f"{s_a}:{s_b}")

    score_periods = ", ".join(periods_parts) if periods_parts else "—"
    
    # === 8. Судейская бригада (из OnlineStarts, StartType == 4) ===
    referees_list = []
    commissioner = None
    
    for start in data.get('OnlineStarts', []):
        if start.get('StartType') != 4:
            continue
        
        person_name = (start.get('PersonName2') or start.get('PersonName1') or '').strip()
        pos_id = start.get('PosID', 0)
        
        if pos_id in [101, 102, 103]:
            if person_name:
                referees_list.append(person_name)
        elif pos_id == 104:
            if person_name:
                commissioner = person_name
    
    referees_str = ", ".join(referees_list) if referees_list else "Не назначены"
    commissioner_str = commissioner if commissioner else "Не назначен"

    return {
        "tournament": tournament,
        "datetime": datetime_str,
        "location": location,
        "spectators": spectators,
        "score_final": score_final,
        "score_periods": score_periods,
        "referees": referees_str,
        "commissioner": commissioner_str,
        "team_a": team_a,
        "team_b": team_b,
        "team_a_id": team_a_id,
        "team_b_id": team_b_id,
        "game_status": data.get('GameStatus', 0)  # 0=запланирован, 1=завершён, 2=live
    }
    
def safe_split_shots(val):
    """Разбивает строку типа '3/8' на попадания и попытки"""
    if val is None or not isinstance(val, str) or '/' not in val:
        return 0, 0
    try:
        m, a = map(int, val.split('/'))
        return m, a
    except:
        return 0, 0

def ultimate_match_parser(game_id):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://belarus.russiabasket.ru/'
    }

    print(f"--- Вскрываем матч {game_id} ---")
    online_url = f"https://org.infobasket.su/Widget/GetOnline/{game_id}?format=json&lang=ru"
    log_url = f"https://org.infobasket.su/Api/GetOnlinePlays/{game_id}?last=0"

    try:
        r_roster = requests.get(online_url, headers=headers)
        roster_data = r_roster.json()
        r_log = requests.get(log_url, headers=headers)
        log_raw = r_log.text.strip('"') if r_log.status_code == 200 else ""
    except Exception as e:
        print(f"Пиздец, сервер накрылся: {e}")
        return

    teams_map = {1: "Команда 1", 2: "Команда 2"}
    for ot in roster_data.get('OnlineTeams', []):
        if ot['TeamNumber'] > 0:
            teams_map[ot['TeamNumber']] = (ot.get('TeamName2') or ot.get('TeamName1')).strip()

    events = [e.split(',') for e in log_raw.split(';') if e and len(e.split(',')) > 8]

    if events:
        print("Лог на месте, считаю вручную...")
        player_df, team_df = parse_from_log(events, roster_data, teams_map)
    else:
        print("Лога нет, высасываю готовую стату из архива...")
        player_df, team_df = parse_from_final_json(roster_data, teams_map)

    if player_df is not None:
        player_df.to_csv(f"match_{game_id}_players.csv", index=False, encoding='utf-8-sig')
        team_df.to_csv(f"match_{game_id}_teams_total.csv", index=False, encoding='utf-8-sig')
        print(f"--- УСПЕХ! match_{game_id}_players.csv и match_{game_id}_teams_total.csv ---")

def parse_from_log(events, roster_data, teams_map):
    participants = {}
    for start in roster_data.get('OnlineStarts', []):
        s_id = start['StartID']
        if s_id == 0 or start['StartType'] == 4: continue
        participants[s_id] = {
            'Name': (start['PersonName2'] or start['PersonName1']).strip(),
            'No': start['DisplayNumber'],
            'Team': teams_map.get(start['TeamNumber'], "Unknown"),
            'TNum': start['TeamNumber'],
            'Role': 'Игрок' if start['StartType'] == 1 else 'Тренер',
            'Stats': create_stats_obj(), 'last_in': None
        }

    team_entities = {1: {'Name': 'КОМАНДА', 'Stats': create_stats_obj()}, 2: {'Name': 'КОМАНДА', 'Stats': create_stats_obj()}}
    on_court, plays_history = {1: set(), 2: set()}, {}

    for e in events:
        p_id, _, _, time_ds, _, s_id, parent_id, type_id = map(lambda x: int(x) if x and x.strip('-').isdigit() else 0, e[:8])
        t_num = participants[s_id]['TNum'] if s_id in participants else (s_id if s_id in [1, 2] else 0)
        if t_num == 0: continue
        plays_history[p_id] = {'type': type_id, 'team': t_num}
        st = participants[s_id]['Stats'] if s_id in participants else team_entities[t_num]['Stats']
        
        if type_id == 8 and s_id in participants: on_court[t_num].add(s_id); participants[s_id]['last_in'] = time_ds
        elif type_id == 9 and s_id in participants:
            if s_id in on_court[t_num]:
                on_court[t_num].remove(s_id)
                if participants[s_id]['last_in'] is not None: st['Secs'] += (time_ds - participants[s_id]['last_in']) / 10
        
        if type_id == 1: st['Pts']+=1; st['FTM']+=1; st['FTA']+=1; update_pm(on_court, 1, t_num, participants)
        elif type_id == 2: st['Pts']+=2; st['2PM']+=1; st['2PA']+=1; update_pm(on_court, 2, t_num, participants)
        elif type_id == 3: st['Pts']+=3; st['3PM']+=1; st['3PA']+=1; update_pm(on_court, 3, t_num, participants)
        elif type_id == 4: st['FTA']+=1
        elif type_id == 5: st['2PA']+=1
        elif type_id == 6: st['3PA']+=1
        elif type_id == 25: st['AST']+=1
        elif type_id == 26: st['STL']+=1
        elif type_id == 27: st['BLK']+=1
        elif type_id == 28:
            if parent_id in plays_history and plays_history[parent_id]['team'] == t_num: st['ORB']+=1
            else: st['DRB']+=1
        elif type_id in [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 47]: st['TOV']+=1
        elif 40 <= type_id <= 46: st['PF']+=1
        elif 50 <= type_id <= 54: st['FC']+=1

    p_rows = [format_row(p, p['Name'], p['Role'], p['Team'], p['No']) for p in participants.values()]
    t_rows = []
    for tn in [1, 2]:
        team_p_stats = [p['Stats'] for p in participants.values() if p['TNum'] == tn]
        total_st = create_stats_obj()
        for s in team_p_stats + [team_entities[tn]['Stats']]:
            for k in total_st: total_st[k] += s[k]
        t_rows.append(format_row({'Stats': total_st}, "ИТОГО", "TEAM", teams_map[tn], ""))
    return pd.DataFrame(p_rows), pd.DataFrame(t_rows)

def parse_from_final_json(data, teams_map):
    p_res, t_res = [], []
    game_teams = data.get('GameTeams', [])
    if not game_teams: return None, None

    for gt in game_teams:
        t_name = gt.get('TeamName', {}).get('CompTeamShortNameRu', 'Unknown')
        for p in gt.get('Players', []):
            p_res.append(map_final_json_row(p, t_name, 'Игрок'))
        c = gt.get('Coach', {})
        if c.get('PersonID'): p_res.append(map_final_json_row(c, t_name, 'Тренер'))
        
        # Команда ИТОГО (Safe access)
        t_res.append({
            'Команда': t_name, 'Очки': safe_int(gt.get('Points')),
            '2-очк': gt.get('Shots2', '0/0'), '3-очк': gt.get('Shots3', '0/0'), 'ШБ': gt.get('Shots1', '0/0'),
            'Подборы (O/D/T)': f"{safe_int(gt.get('OffRebound'))}/{safe_int(gt.get('DefRebound'))}/{safe_int(gt.get('Rebound'))}",
            'ГП': safe_int(gt.get('Assist')), 'ПХ': safe_int(gt.get('Steal')), 'ПТ': safe_int(gt.get('Turnover')),
            'БШ': safe_int(gt.get('Blocks')), 'Ф': safe_int(gt.get('Foul')), 'КПИ': safe_int(gt.get('Efficiency'))
        })
    return pd.DataFrame(p_res), pd.DataFrame(t_res)

def create_stats_obj():
    return {'Pts':0, '2PM':0, '2PA':0, '3PM':0, '3PA':0, 'FTM':0, 'FTA':0, 'ORB':0, 'DRB':0, 'AST':0, 'STL':0, 'TOV':0, 'BLK':0, 'PF':0, 'FC':0, 'PM':0, 'Secs':0}

def format_row(p, name, role, team, no):
    s = p['Stats']
    pts, orb, drb = safe_int(s.get('Pts')), safe_int(s.get('ORB')), safe_int(s.get('DRB'))
    ast, stl, blk, tov, pf, fs = safe_int(s.get('AST')), safe_int(s.get('STL')), safe_int(s.get('BLK')), safe_int(s.get('TOV')), safe_int(s.get('PF')), safe_int(s.get('FC'))
    m_fg = (safe_int(s.get('2PA')) + safe_int(s.get('3PA'))) - (safe_int(s.get('2PM')) + safe_int(s.get('3PM')))
    m_ft = safe_int(s.get('FTA')) - safe_int(s.get('FTM'))
    eff = (pts + (orb + drb) + ast + stl + blk + fs) - (max(0, m_fg) + max(0, m_ft) + tov + pf)
    return {
        'Команда': team, 'Имя': name, '№': no, 'Роль': role,
        'Мин': f"{safe_int(s.get('Secs'))//60:02d}:{safe_int(s.get('Secs'))%60:02d}", 
        'Очки': pts, '2-очк': f"{s.get('2PM')}/{s.get('2PA')}", '3-очк': f"{s.get('3PM')}/{s.get('3PA')}",
        'ШБ': f"{s.get('FTM')}/{s.get('FTA')}", 'Подборы (O/D/T)': f"{orb}/{drb}/{orb+drb}",
        'ГП': ast, 'ПХ': stl, 'ПТ': tov, 'БШ': blk, 'Ф': pf, 'ФС': fs, '+/-': safe_int(s.get('PM')), 'КПИ': eff
    }

def map_final_json_row(p, team, role):
    m2, a2 = safe_split_shots(p.get('Shots2'))
    m3, a3 = safe_split_shots(p.get('Shots3'))
    m1, a1 = safe_split_shots(p.get('Shots1'))
    pts, trb, ast, stl = safe_int(p.get('Points')), safe_int(p.get('Rebound')), safe_int(p.get('Assist')), safe_int(p.get('Steal'))
    blk, tov, pf, fs = safe_int(p.get('Blocks')), safe_int(p.get('Turnover')), safe_int(p.get('Foul')), safe_int(p.get('OpponentFoul'))
    m_fg = (a2 + a3) - (m2 + m3)
    m_ft = a1 - m1
    eff = (pts + trb + ast + stl + blk + fs) - (max(0, m_fg) + max(0, m_ft) + tov + pf)
    return {
        'Команда': team, 'Имя': f"{p.get('LastNameRu', '')} {p.get('FirstNameRu', '')}".strip(),
        '№': p.get('PlayerNumber', ''), 'Роль': role, 'Мин': p.get('PlayedTime', '0:00'),
        'Очки': pts, '2-очк': p.get('Shots2', '0/0'), '3-очк': p.get('Shots3', '0/0'), 'ШБ': p.get('Shots1', '0/0'),
        'Подборы (O/D/T)': f"{safe_int(p.get('OffRebound'))}/{safe_int(p.get('DefRebound'))}/{trb}",
        'ГП': ast, 'ПХ': stl, 'ПТ': tov, 'БШ': blk, 'Ф': pf, 'ФС': fs, '+/-': safe_int(p.get('PlusMinus')), 'КПИ': eff
    }

def update_pm(on_court, pts, scoring_team, participants):
    for t_num, squad in on_court.items():
        for sid in squad:
            if sid in participants:
                if t_num == scoring_team: participants[sid]['Stats']['PM'] += pts
                else: participants[sid]['Stats']['PM'] -= pts

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "1016420"
    ultimate_match_parser(target)