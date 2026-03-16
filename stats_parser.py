import requests
import pandas as pd

def run_stats_calculation(comp_id, stage_name="tournament"):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://belarus.russiabasket.ru/'
    }

    # 1. Список команд (Standings)
    s_url = f"https://org.infobasket.su/Widget/CompTeamResults/{comp_id}?format=json&lang=ru"
    try:
        standings_data = requests.get(s_url, headers=headers).json()
    except Exception as e:
        print(f"[-] Ошибка загрузки турнирки: {e}")
        return False

    team_map = {} # ID -> Название (которое пойдет в шахматку)
    calculated_stats = {}
    team_order_ids = []

    for item in standings_data:
        t_id = item['TeamID']
        t_info = item.get('CompTeamName', {})
        # Берем максимально полное имя для маппинга, чтобы не было путаницы
        t_name = (t_info.get('CompTeamShortNameRu') or t_info.get('CompTeamNameRu') or "Unknown").strip()
        city = t_info.get('CompTeamRegionNameRu', '')
        full_display_name = f"{t_name} ({city})" if city else t_name
        
        team_map[t_id] = t_name
        team_order_ids.append(t_id)
        calculated_stats[t_id] = {
            'Команда': full_display_name, 
            'И': 0, 'В': 0, 'П': 0, 'Забито': 0, 'Пропущено': 0, 'Очки': 0
        }

    # 2. Игры (CrossTable)
    c_url = f"https://org.infobasket.su/Widget/CrossTable/{comp_id}?format=json&lang=ru"
    try:
        cross_data = requests.get(c_url, headers=headers).json()
    except Exception as e:
        print(f"[-] Ошибка загрузки шахматки: {e}")
        return False

    # Сначала считаем турнирку
    processed_games = set()
    for game in cross_data:
        g_id = game.get('GameID')
        if g_id in processed_games: continue
        processed_games.add(g_id)

        if game.get('WinTeam', 0) == 0: continue
        t1_id, t2_id = game['Team1id'], game['Team2id']
        
        try:
            score_parts = game['Score'].split(':')
            s1, s2 = int(score_parts[0]), int(score_parts[1])
        except: continue

        for tid, s_own, s_opp, is_win in [(t1_id, s1, s2, game['WinTeam']==1), (t2_id, s2, s1, game['WinTeam']==2)]:
            if tid in calculated_stats:
                ts = calculated_stats[tid]
                ts['И'] += 1; ts['Забито'] += s_own; ts['Пропущено'] += s_opp
                if is_win: ts['В'] += 1; ts['Очки'] += 2
                else: ts['П'] += 1; ts['Очки'] += 1

    # 3. Формируем DataFrame турнирки
    final_rows = []
    for t_id in team_order_ids:
        ts = calculated_stats[t_id]
        ts['+/-'] = ts['Забито'] - ts['Пропущено']
        ts['%'] = round((ts['В'] / ts['И'] * 100)) if ts['И'] > 0 else 0
        final_rows.append(ts)

    df_s = pd.DataFrame(final_rows).sort_values(['Очки', '+/-'], ascending=[False, False])
    df_s.insert(0, 'Место', range(1, len(df_s) + 1))
    
    # Обновляем порядок имен для шахматки на основе итоговых мест
    sorted_team_names = [team_map[tid] for tid in df_s.index.map(lambda x: team_order_ids[x])]
    # Но проще взять из отсортированного DF
    sorted_names = df_s['Команда'].apply(lambda x: x.split(' (')[0]).tolist()

    # 4. Сборка шахматки (Безопасная версия)
    matrix = pd.DataFrame("", index=sorted_names, columns=sorted_names)
    for t in sorted_names: 
        if t in matrix.index: matrix.loc[t, t] = "---"

    processed_games.clear()
    for game in cross_data:
        g_id = game.get('GameID')
        if g_id in processed_games: continue
        processed_games.add(g_id)
        
        t1_name = team_map.get(game['Team1id'])
        t2_name = team_map.get(game['Team2id'])
        
        # Если имен нет в матрице (например, из-за молодежки), добавляем их на лету или скипаем
        if not t1_name or not t2_name or t1_name not in matrix.index or t2_name not in matrix.index:
            continue
            
        score = game['Score'] if game['WinTeam'] > 0 else f"({game['GameDate']})"
        h_flag = game.get('HomeTeam', 1)
        
        # Записываем
        try:
            matrix.loc[t1_name, t2_name] = (matrix.loc[t1_name, t2_name] + "\n" + score + (" д" if h_flag == 1 else " г")).strip()
            matrix.loc[t2_name, t1_name] = (matrix.loc[t2_name, t1_name] + "\n" + score + (" г" if h_flag == 1 else " д")).strip()
        except KeyError:
            continue

    # 5. Сохранение
    safe_name = stage_name.replace(" ", "_").replace("/", "-")
    df_s.to_csv(f"standings_{comp_id}_{safe_name}.csv", index=False, encoding='utf-8-sig')
    matrix.to_csv(f"crosstable_{comp_id}_{safe_name}.csv", encoding='utf-8-sig')
    return True