import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime

from stats_parser import run_stats_calculation
from match_parser import ultimate_match_parser
from match_finder import find_recent_matches
from game_tracker import build_game_charts

# --- Настройки страницы ---
st.set_page_config(
    page_title="BBF Parser",
    page_icon="🏀",
    layout="centered"
)

# --- Стили ---
st.markdown("""
<style>
    /* Навигация - адаптивная */
    .nav-container {
        display: flex;
        justify-content: center;
        gap: 0.5rem;
        margin-bottom: 1rem;
        flex-wrap: wrap;
    }
    
    /* Адаптив для мобильных */
    @media (max-width: 768px) {
        .nav-container {
            flex-direction: column;
            align-items: stretch;
        }
        .nav-container .stButton {
            width: 100%;
        }
        .nav-container .stButton > button {
            width: 100%;
        }
    }
    
    /* Для десктопа - в ряд */
    @media (min-width: 769px) {
        .nav-container {
            flex-direction: row;
            justify-content: center;
        }
        .nav-container .stButton {
            min-width: 140px;
        }
    }
    
    .stButton > button {
        background-color: #f0f0f0;
        color: #333;
        font-weight: bold;
        border: 2px solid #ddd;
        border-radius: 0.5rem;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #FF4B4B;
        color: white;
        border-color: #FF4B4B;
        transform: translateY(-2px);
    }
    
    /* Активная кнопка */
    .stButton:has(button[data-baseweb="base-button"]) > button.active {
        background-color: #FF4B4B !important;
        color: white !important;
        border-color: #FF4B4B !important;
        box-shadow: 0 4px 12px rgba(255, 75, 75, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# --- Инициализация session_state ---
if 'page' not in st.session_state:
    st.session_state.page = 'calendar'
if 'selected_game_id' not in st.session_state:
    st.session_state.selected_game_id = ""

# --- Навигация ---
def set_page(page_name):
    st.session_state.page = page_name

# Адаптивная навигация
st.markdown('<div class="nav-container">', unsafe_allow_html=True)
col_nav1, col_nav2, col_nav3, col_nav4 = st.columns(4)
with col_nav1:
    if st.button("📅 Календарь", key="nav_calendar", width="stretch", type="primary" if st.session_state.page == 'calendar' else "secondary"):
        set_page('calendar')
        st.rerun()
with col_nav2:
    if st.button("🏀 Матч", key="nav_match", width="stretch", type="primary" if st.session_state.page == 'match' else "secondary"):
        set_page('match')
        st.rerun()
with col_nav3:
    if st.button("📊 Турнир", key="nav_tournament", width="stretch", type="primary" if st.session_state.page == 'tournament' else "secondary"):
        set_page('tournament')
        st.rerun()
with col_nav4:
    if st.button("ℹ️ О проекте", key="nav_about", width="stretch", type="primary" if st.session_state.page == 'about' else "secondary"):
        set_page('about')
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# ==================== СТРАНИЦА: КАЛЕНДАРЬ ====================
if st.session_state.page == 'calendar':
    st.title("📅 Календарь матчей")
    st.markdown("*Найдите матчи за период и выберите нужный для парсинга*")
    
    comp_id = st.text_input("ID этапа турнира", placeholder="Например: 50758", value="", key="cal_comp_id")
    
    col_days1, col_days2 = st.columns(2)
    with col_days1:
        days_back = st.slider("Дней назад", min_value=1, max_value=60, value=14, key="days_back")
    with col_days2:
        days_forward = st.slider("Дней вперёд", min_value=0, max_value=60, value=14, key="days_forward")
    
    def get_calendar_matches(cid, db, df):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://belarus.russiabasket.ru/'
        }
        url = f"https://org.infobasket.su/Comp/GetCalendarCarousel/?comps={cid}&from=today-{db}&to=today+{df}&format=json&lang=ru"
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            games = response.json()
        except Exception as e:
            st.error(f"Ошибка при запросе к календарю: {e}")
            return None
        
        if not games:
            return None
        
        match_list = []
        for g in games:
            game_id = g.get('GameID')
            status = "ЗАПЛАНИРОВАН"
            score = ""
            if g.get('GameStatus') == 1:
                status = "ЗАВЕРШЕН"
                score = f"{g.get('ScoreA')}:{g.get('ScoreB')}"
            elif g.get('GameStatus') == 2:
                status = "LIVE"
                score = f"{g.get('ScoreA')}:{g.get('ScoreB')}"
            else:
                score = g.get('GameTimeMsk', g.get('GameTime', '??:??'))
            
            match_list.append({
                'ID': game_id,
                'Дата': g.get('GameDate'),
                'День': g.get('DayOfWeekRu'),
                'Хозяева': g.get('ShortTeamNameAru'),
                'Гости': g.get('ShortTeamNameBru'),
                'Счёт/Время': score,
                'Статус': status,
                'Турнир': g.get('CompNameRu')
            })
        
        return pd.DataFrame(match_list)
    
    if st.button("🔍 Найти матчи", key="find_matches", type="primary"):
        if not comp_id:
            st.warning("Введите ID этапа турнира")
        else:
            with st.spinner("Запрос к календарю..."):
                df_matches = get_calendar_matches(comp_id, days_back, days_forward)
            
            if df_matches is not None and not df_matches.empty:
                st.session_state.matches = df_matches
                st.success(f"Найдено матчей: {len(df_matches)}")
                
                # Фильтры по статусу
                status_filter = st.multiselect(
                    "Фильтр по статусу:",
                    options=["ЗАВЕРШЕН", "LIVE", "ЗАПЛАНИРОВАН"],
                    default=["ЗАВЕРШЕН", "LIVE", "ЗАПЛАНИРОВАН"],
                    key="status_filter"
                )
                
                # Отображение таблицы
                df_filtered = df_matches[df_matches['Статус'].isin(status_filter)].reset_index(drop=True)
                
                # Подсветка статусов
                def highlight_status(val):
                    if val == "LIVE":
                        return "background-color: #ffcccc; color: #cc0000; font-weight: bold"
                    elif val == "ЗАВЕРШЕН":
                        return "background-color: #ccffcc; color: #006600"
                    else:
                        return ""
                
                styled_df = df_filtered.style.map(highlight_status, subset=['Статус'])
                st.dataframe(styled_df, hide_index=True, width='stretch')

                # Выбор матча для парсинга
                st.divider()
                st.subheader("🎯 Выбрать матч для парсинга")

                @st.fragment
                def match_selector():
                    if len(df_filtered) > 0:
                        selected_idx = st.selectbox(
                            "Выберите матч:",
                            options=df_filtered.index.tolist(),
                            format_func=lambda x: f"{df_filtered.loc[x, 'Дата']} | {df_filtered.loc[x, 'Хозяева']} vs {df_filtered.loc[x, 'Гости']} ({df_filtered.loc[x, 'Статус']})",
                            key="match_select"
                        )

                        if selected_idx is not None:
                            selected_match = df_filtered.loc[selected_idx]
                            st.session_state.selected_game_id = str(selected_match['ID'])

                            st.info(f"**ID матча:** `{selected_match['ID']}` | **Счёт/Время:** {selected_match['Счёт/Время']}")

                            if st.button("➡️ Перейти к парсингу этого матча", key="go_to_match", type="primary"):
                                set_page('match')
                                st.rerun()
                    
                    else:
                        st.warning("Нет матчей по выбранным фильтрам")
                
                match_selector()

                # Скачать CSV (вне fragment)
                if len(df_filtered) > 0:
                    csv_data = df_matches.to_csv(index=False, encoding='utf-8-sig').encode('utf-8')
                    st.download_button(
                        label="📥 Скачать список матчей (CSV)",
                        data=csv_data,
                        file_name=f"matches_list_{comp_id}.csv",
                        mime="text/csv"
                    )
            else:
                st.error("Матчи не найдены. Проверьте ID этапа или расширьте диапазон дат.")

# ==================== СТРАНИЦА: МАТЧ ====================
elif st.session_state.page == 'match':
    st.title("🏀 Парсинг матча")
    st.markdown("*Детальная статистика игроков и команд*")
    
    # Если ID матча был выбран в календаре — подставляем его
    default_game_id = st.session_state.get('selected_game_id', "")
    
    if default_game_id:
        st.success(f"✅ Выбран матч ID: `{default_game_id}` (из календаря)")

    game_id = st.text_input("ID матча", placeholder="Например: 1016417", value=default_game_id, key="match_game_id")

    # Инициализируем состояние для графиков (сбрасываем при смене ID матча)
    charts_key = f'charts_{game_id}'
    if charts_key not in st.session_state:
        st.session_state[charts_key] = False
    if 'last_game_id' not in st.session_state or st.session_state.last_game_id != game_id:
        st.session_state.last_game_id = game_id
        st.session_state[charts_key] = False

    if st.button("▶ Парсить матч", key="parse_match_btn", type="primary"):
        if not game_id:
            st.warning("Введите ID матча")
        else:
            with st.spinner("Парсинг матча..."):
                players_file = f"match_{game_id}_players.csv"
                teams_file = f"match_{game_id}_teams_total.csv"

                ultimate_match_parser(game_id)

                if os.path.exists(players_file):
                    st.success("✅ Матч распарсен успешно!")

                    col1, col2 = st.columns(2)

                    with col1:
                        with open(players_file, "rb") as f:
                            csv_data = f.read()
                        st.download_button(
                            label="📥 Скачать статистику игроков",
                            data=csv_data,
                            file_name=players_file,
                            mime="text/csv"
                        )

                    with col2:
                        with open(teams_file, "rb") as f:
                            csv_data = f.read()
                        st.download_button(
                            label="📥 Скачать статистику команд",
                            data=csv_data,
                            file_name=teams_file,
                            mime="text/csv"
                        )

                    with st.expander("👁️ Топ-5 игроков по очкам", expanded=True):
                        df = pd.read_csv(players_file, encoding='utf-8-sig')
                        df_players = df[df['Роль'] == 'Игрок'].sort_values('Очки', ascending=False).head(5)
                        st.dataframe(df_players, hide_index=True)
                else:
                    st.error("❌ Не удалось распарсить матч. Проверьте ID.")

    # --- Блок визуализации графиков (вне условия парсинга) ---
    # Показываем только если файлы матча существуют
    players_file = f"match_{game_id}_players.csv" if game_id else None
    if players_file and os.path.exists(players_file):
        st.divider()
        st.subheader("📈 Визуализация матча")
        st.markdown("*Постройте графики прогрессии счёта и разницы в счёте*")

        # Кнопка для построения графиков
        if not st.session_state[charts_key]:
            if st.button("📊 Построить графики", key="build_charts_btn", type="primary"):
                with st.spinner("Генерация графиков..."):
                    result = build_game_charts(game_id, verbose=False)

                    if result:
                        st.session_state[charts_key] = True
                        st.success("✅ Графики построены!")
                        st.rerun()
                    else:
                        st.error("❌ Не удалось построить графики. Возможно, нет данных о событиях матча.")
        else:
            # Отображение графиков
            prog_file = f"match_{game_id}_progression.png"
            diff_file = f"match_{game_id}_difference_solid.png"

            if os.path.exists(prog_file):
                st.image(prog_file, caption="Прогрессия счёта", use_container_width=True)

                with open(prog_file, "rb") as f:
                    st.download_button(
                        label="📥 Скачать график прогрессии",
                        data=f.read(),
                        file_name=prog_file,
                        mime="image/png",
                        key="dl_prog"
                    )

            if os.path.exists(diff_file):
                st.image(diff_file, caption="Разница в счёте (Lead Tracker)", use_container_width=True)

                with open(diff_file, "rb") as f:
                    st.download_button(
                        label="📥 Скачать график разницы",
                        data=f.read(),
                        file_name=diff_file,
                        mime="image/png",
                        key="dl_diff"
                    )

            # Кнопка для сброса и повторной генерации
            if st.button("🔄 Пересоздать графики", key="reset_charts_btn"):
                st.session_state[charts_key] = False
                st.rerun()

# ==================== СТРАНИЦА: ТУРНИР ====================
elif st.session_state.page == 'tournament':
    st.title("📊 Парсинг турнира")
    st.markdown("*Турнирная таблица и шахматка результатов*")
    
    # Ввод ID сезона
    root_id = st.text_input("ID сезона", placeholder="Например: 50788", value="", key="tour_root_id")
    
    def get_stages(rid):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://belarus.russiabasket.ru/'
        }
        url = f"https://org.infobasket.su/Widget/CompIssue/{rid}?format=json&lang=ru"
        try:
            data = requests.get(url, headers=headers).json()
            stages = data.get('Comps', []) or data.get('Children', [])
            if not stages:
                p_comp = data.get('ParentComp', {})
                return [{'id': rid, 'name': p_comp.get('CompShortNameRu', 'Основной этап')}]
            return [{'id': s['CompID'], 'name': s.get('CompShortNameRu') or s.get('CompNameRu')} for s in stages]
        except Exception as e:
            st.error(f"Ошибка при сканировании: {e}")
            return []
    
    if st.button("🔍 Найти этапы", key="find_stages", type="primary"):
        if not root_id:
            st.warning("Введите ID сезона")
        else:
            with st.spinner("Запрос к API..."):
                stages = get_stages(root_id)
            
            if stages:
                st.session_state.stages = stages
                st.success(f"Найдено этапов: {len(stages)}")
            else:
                st.error("Не найдено ни одного этапа. Проверьте ID.")
    
    # Выбор этапа
    if 'stages' in st.session_state and st.session_state.stages:
        stages = st.session_state.stages
        
        stage_options = {f"{i+1}. {s['name']} (ID: {s['id']})": s for i, s in enumerate(stages)}
        selected_label = st.radio("Выберите этап:", list(stage_options.keys()), index=0, key="stage_radio")
        selected_stage = stage_options[selected_label]
        
        st.divider()
        
        if st.button("▶ Запустить парсинг", key="parse_tournament", type="primary"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("Парсинг standings...")
            progress_bar.progress(30)
            
            success = run_stats_calculation(selected_stage['id'], selected_stage['name'])
            
            progress_bar.progress(100)
            
            if success:
                st.success("✅ Парсинг завершён успешно!")
                
                safe_name = selected_stage['name'].replace(" ", "_").replace("/", "-")
                standings_file = f"standings_{selected_stage['id']}_{safe_name}.csv"
                crosstable_file = f"crosstable_{selected_stage['id']}_{safe_name}.csv"
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if os.path.exists(standings_file):
                        with open(standings_file, "rb") as f:
                            csv_data = f.read()
                        st.download_button(
                            label="📥 Скачать standings",
                            data=csv_data,
                            file_name=standings_file,
                            mime="text/csv"
                        )
                        df = pd.read_csv(standings_file, encoding='utf-8-sig')
                        with st.expander("👁️ Предпросмотр"):
                            st.dataframe(df.head(10), hide_index=True)
                
                with col2:
                    if os.path.exists(crosstable_file):
                        with open(crosstable_file, "rb") as f:
                            csv_data = f.read()
                        st.download_button(
                            label="📥 Скачать crosstable",
                            data=csv_data,
                            file_name=crosstable_file,
                            mime="text/csv"
                        )
                        df_ct = pd.read_csv(crosstable_file, encoding='utf-8-sig')
                        with st.expander("👁️ Предпросмотр"):
                            st.dataframe(df_ct.head(10), hide_index=True)
            else:
                st.error("❌ Что-то пошло не так. Возможно, в этом этапе нет данных.")
            
            progress_bar.empty()
            status_text.empty()

# ==================== СТРАНИЦА: О ПРОЕКТЕ ====================
elif st.session_state.page == 'about':
    st.title("ℹ️ О проекте")
    
    st.markdown("""
    **BBF Parser** — инструмент для парсинга баскетбольной статистики с белорусских соревнований.
    
    ### Источники данных
    - Сайт: [belarus.russiabasket.ru](https://belarus.russiabasket.ru/)
    - API: `org.infobasket.su`
    
    ### API Endpoints
    
    | Endpoint | Назначение |
    |----------|------------|
    | `Widget/CompIssue/{id}` | Список этапов сезона |
    | `Widget/CompTeamResults/{id}` | Турнирная таблица (standings) |
    | `Widget/CrossTable/{id}` | Результаты матчей (crosstable) |
    | `Comp/GetCalendarCarousel/` | Календарь матчей |
    | `Widget/GetOnline/{game_id}` | Протокол матча |
    | `Api/GetOnlinePlays/{game_id}` | Play-by-play лог событий |
    
    ### Выходные файлы
    
    **Турнир:**
    - `standings_*.csv` — турнирная таблица
    - `crosstable_*.csv` — шахматка результатов
    
    **Матч:**
    - `match_*_players.csv` — статистика игроков
    - `match_*_teams_total.csv` — статистика команд
    
    **Календарь:**
    - `matches_list_*.csv` — список матчей за период
    
    ### Технологии
    - Python 3.14
    - Streamlit — веб-интерфейс
    - Pandas — обработка данных
    - Requests — HTTP-запросы
    """)
    
    st.divider()
    st.markdown("*Версия: 1.1 | 2026*")
