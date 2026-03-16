import requests
import pandas as pd
import json

def universal_basket_parser(game_id):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://belarus.russiabasket.ru/'
    }

    print(f"--- Обработка матча {game_id} ---")
    online_url = f"https://org.infobasket.su/Widget/GetOnline/{game_id}?format=json&lang=ru"
    log_url = f"https://org.infobasket.su/Api/GetOnlinePlays/{game_id}?last=0"

    try:
        r_roster = requests.get(online_url, headers=headers)
        r_roster.raise_for_status()
        roster_data = r_roster.json()
        
        r_log = requests.get(log_url, headers=headers)
        log_raw = r_log.text.strip('"') if r_log.status_code == 200 else ""
    except Exception as e:
        print(f"Ошибка: сервер не отвечает: {e}")
        return

    # Подготавливаем базу
    teams_map = {1: "Команда 1", 2: "Команда 2"}
    for ot in roster_data.get('OnlineTeams', []):
        if ot['TeamNumber'] > 0:
            teams_map[ot['TeamNumber']] = ot.get('TeamName2') or ot.get('TeamName1')

    # Проверяем, есть ли лог событий
    events = [e.split(',') for e in log_raw.split(';') if e and len(e.split(',')) > 8]

    if events:
        print("Нашел лог событий! Реконструирую матч вручную...")
        final_df = parse_from_log(events, roster_data, teams_map)
    else:
        print("Лог пустой (архивный матч). Вытаскиваю данные из готового протокола...")
        final_df = parse_from_final_json(roster_data, teams_map)

    if final_df is not None:
        filename = f"match_{game_id}_stats.csv"
        final_df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"--- ГОТОВО! Файл {filename} создан. ---")
    else:
        print("Не удалось получить данные. Возможно, матч повреждён или отсутствует.")

def parse_from_log(events, roster_data, teams_map):
    """Метод для лайв-матчей (максимальная детализация)"""
    participants = {}
    for start in roster_data.get('OnlineStarts', []):
        s_id = start['StartID']
        if s_id == 0 or start['StartType'] == 4: continue
        participants[s_id] = {
            'Name': (start['PersonName2'] or start['PersonName1']).strip(),
            'No': start['DisplayNumber'],
            'Team': teams_map.get(start['TeamNumber'], "Unknown"),
            'Role': 'Игрок' if start['StartType'] == 1 else 'Тренер',
            'TNum': start['TeamNumber'],
            'Stats': create_stats_obj(), 'last_in': None
        }

    # Добавляем строку КОМАНДА для системных StartID 1 и 2
    for tn in [1, 2]:
        if tn not in participants:
            participants[tn] = {'Name': 'КОМАНДА', 'No': '', 'Team': teams_map[tn], 'Role': 'TEAM', 'TNum': tn, 'Stats': create_stats_obj(), 'last_in': None}

    on_court = {1: set(), 2: set()}
    plays_history = {}
    
    for e in events:
        p_id, _, period, time_ds, _, s_id, parent_id, type_id = map(lambda x: int(x) if x and x.strip('-').isdigit() else 0, e[:8])
        plays_history[p_id] = {'type': type_id, 's_id': s_id, 'team': participants[s_id]['TNum'] if s_id in participants else 0}

        if s_id in participants:
            st = participants[s_id]['Stats']
            if type_id == 8: on_court[participants[s_id]['TNum']].add(s_id); participants[s_id]['last_in'] = time_ds
            elif type_id == 9: 
                if s_id in on_court[participants[s_id]['TNum']]:
                    on_court[participants[s_id]['TNum']].remove(s_id)
                    if participants[s_id]['last_in'] is not None: st['Secs'] += (time_ds - participants[s_id]['last_in']) / 10
            
            # Статы (сокращенно для экономии места здесь)
            if type_id == 1: st['Pts']+=1; st['FTM']+=1; st['FTA']+=1; update_pm(on_court, 1, participants[s_id]['TNum'], participants)
            elif type_id == 2: st['Pts']+=2; st['2PM']+=1; st['2PA']+=1; update_pm(on_court, 2, participants[s_id]['TNum'], participants)
            elif type_id == 3: st['Pts']+=3; st['3PM']+=1; st['3PA']+=1; update_pm(on_court, 3, participants[s_id]['TNum'], participants)
            elif type_id == 4: st['FTA']+=1
            elif type_id == 5: st['2PA']+=1
            elif type_id == 6: st['3PA']+=1
            elif type_id == 25: st['AST']+=1
            elif type_id == 26: st['STL']+=1
            elif type_id == 27: st['BLK']+=1
            elif type_id == 28:
                if parent_id in plays_history and plays_history[parent_id]['team'] == participants[s_id]['TNum']: st['ORB']+=1
                else: st['DRB']+=1
            elif type_id in [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 47]: st['TOV']+=1
            elif 40 <= type_id <= 46: st['PF']+=1
            elif 50 <= type_id <= 54: st['FC']+=1

    # Считаем финальный список
    res = []
    for sid, p in participants.items():
        res.append(format_row(p))
    return pd.DataFrame(res).sort_values(['Команда', 'Роль', 'Очки'], ascending=[True, False, False])

def parse_from_final_json(data, teams_map):
    """Метод для старых матчей (берем готовую стату из JSON)"""
    res = []
    game_teams = data.get('GameTeams', [])
    if not game_teams: return None

    for gt in game_teams:
        t_name = gt.get('TeamName', {}).get('CompTeamShortNameRu', 'Unknown')
        
        # 1. Сначала игроки
        for p in gt.get('Players', []):
            res.append({
                'Команда': t_name, 'Игрок': f"{p.get('LastNameRu', '')} {p.get('FirstNameRu', '')}".strip(),
                '№': p.get('PlayerNumber'), 'Роль': 'Игрок', 'Мин': p.get('PlayedTime'),
                'Очки': p.get('Points'), '2-очк': p.get('Shots2'), '3-очк': p.get('Shots3'),
                'И': p.get('FGShots'), 'ШБ': p.get('Shots1'), 'СЩ': p.get('DefRebound'),
                'ЧЩ': p.get('OffRebound'), 'ВС': p.get('Rebound'), 'ГП': p.get('Assist'),
                'ПХ': p.get('Steal'), 'ПТ': p.get('Turnover'), 'БШ': p.get('Blocks'),
                'Ф': p.get('Foul'), 'ФС': p.get('OpponentFoul'), '+/-': p.get('PlusMinus'), 'КПИ': p.get('Efficiency', 0)
            })
        
        # 2. Потом тренер
        coach = gt.get('Coach', {})
        if coach and coach.get('PersonID'):
            res.append({
                'Команда': t_name, 'Игрок': f"{coach.get('LastNameRu', '')} {coach.get('FirstNameRu', '')}".strip(),
                '№': '', 'Роль': 'Тренер', 'Мин': '0:00', 'Очки': 0, '2-очк': '0/0', '3-очк': '0/0',
                'И': '0/0', 'ШБ': '0/0', 'СЩ': 0, 'ЧЩ': 0, 'ВС': 0, 'ГП': 0, 'ПХ': 0, 'ПТ': 0, 'БШ': 0,
                'Ф': coach.get('Foul', 0), 'ФС': 0, '+/-': 0, 'КПИ': 0
            })

        # 3. Командные статы (подборы и т.д.)
        res.append({
            'Команда': t_name, 'Игрок': 'КОМАНДА', '№': '', 'Роль': 'TEAM', 'Мин': '0:00',
            'Очки': 0, '2-очк': '0/0', '3-очк': '0/0', 'И': '0/0', 'ШБ': '0/0',
            'СЩ': gt.get('TeamDefRebound', 0), 'ЧЩ': gt.get('TeamOffRebound', 0), 'ВС': gt.get('TeamRebound', 0),
            'ГП': 0, 'ПХ': gt.get('TeamSteal', 0), 'ПТ': gt.get('TeamTurnover', 0), 'БШ': 0, 'Ф': 0, 'ФС': 0, '+/-': 0, 'КПИ': 0
        })
    return pd.DataFrame(res)

def create_stats_obj():
    return {'Pts':0, '2PM':0, '2PA':0, '3PM':0, '3PA':0, 'FTM':0, 'FTA':0, 'ORB':0, 'DRB':0, 'AST':0, 'STL':0, 'TOV':0, 'BLK':0, 'PF':0, 'FC':0, 'PM':0, 'Secs':0}

def format_row(p):
    s = p['Stats']
    m_fg = (s['2PA']+s['3PA']) - (s['2PM']+s['3PM'])
    m_ft = s['FTA']-s['FTM']
    eff = (s['Pts'] + s['ORB']+s['DRB'] + s['AST'] + s['STL'] + s['BLK']) - (m_fg + m_ft + s['TOV'] + s['PF'])
    return {
        'Команда': p['Team'], 'Игрок': p['Name'], '№': p['No'], 'Роль': p['Role'],
        'Мин': f"{int(s['Secs']//60)}:{int(s['Secs']%60):02d}", 'Очки': s['Pts'],
        '2-очк': f"{s['2PM']}/{s['2PA']}", '3-очк': f"{s['3PM']}/{s['3PA']}",
        'И': f"{s['2PM']+s['3PM']}/{s['2PA']+s['3PA']}", 'ШБ': f"{s['FTM']}/{s['FTA']}",
        'СЩ': s['DRB'], 'ЧЩ': s['ORB'], 'ВС': s['ORB']+s['DRB'],
        'ГП': s['AST'], 'ПХ': s['STL'], 'ПТ': s['TOV'], 'БШ': s['BLK'],
        'Ф': s['PF'], 'ФС': s['FC'], '+/-': int(s['PM']), 'КПИ': eff
    }

def update_pm(on_court, pts, scoring_team, participants):
    for t_num, squad in on_court.items():
        for sid in squad:
            if t_num == scoring_team: participants[sid]['Stats']['PM'] += pts
            else: participants[sid]['Stats']['PM'] -= pts

if __name__ == "__main__":
    import sys
    # Можно запускать как: py parser.py 1016417
    target_id = sys.argv[1] if len(sys.argv) > 1 else "1016417"
    universal_basket_parser(target_id)