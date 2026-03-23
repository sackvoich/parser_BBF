import requests
import sys
from stats_parser import run_stats_calculation
from game_tracker import build_game_charts

def get_stages(root_id):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://belarus.russiabasket.ru/'
    }
    url = f"https://org.infobasket.su/Widget/CompIssue/{root_id}?format=json&lang=ru"
    
    print(f"\n[?] Опрашиваю сезон {root_id} на наличие этапов...")
    try:
        data = requests.get(url, headers=headers).json()
        # Ищем этапы в Comps или Children
        stages = data.get('Comps', []) or data.get('Children', [])
        
        if not stages:
            # Если это уже конечный этап
            p_comp = data.get('ParentComp', {})
            return [{'id': root_id, 'name': p_comp.get('CompShortNameRu', 'Основной этап')}]
        
        return [{'id': s['CompID'], 'name': s.get('CompShortNameRu') or s.get('CompNameRu')} for s in stages]
    except Exception as e:
        print(f"[-] Ошибка при сканировании: {e}")
        return []

def main():
    # Проверка аргументов командной строки для генерации графиков
    if len(sys.argv) > 1 and sys.argv[1] == '--charts':
        if len(sys.argv) > 2:
            game_id = sys.argv[2]
            print("=" * 40)
            print("   BASKETBALL GAME CHARTS GENERATOR v1.0")
            print("=" * 40)
            build_game_charts(game_id)
            return
        else:
            print("Использование: python main.py --charts <GAME_ID>")
            print("Пример: python main.py --charts 1016417")
            return

    print("="*40)
    print("   BASKETBALL STAGE SELECTOR v1.0")
    print("="*40)
    
    root_id = input("\n[!] Введи ID сезона (например, 50758): ").strip()
    if not root_id:
        print("[-] Поле пустое. Введите ID сезона.")
        return

    stages = get_stages(root_id)

    if not stages:
        print("[-] Не найдено ни одного этапа. Проверьте ID.")
        return

    print("\n[+] Найдены следующие этапы:")
    for i, s in enumerate(stages):
        print(f"  {i} -> {s['name']} (ID: {s['id']})")

    try:
        choice = int(input("\n[?] Введи номер этапа для парсинга: "))
        if 0 <= choice < len(stages):
            selected = stages[choice]
            print(f"\n[!] Запускаю расчет для: {selected['name']}...")

            success = run_stats_calculation(selected['id'], selected['name'])

            if success:
                print(f"\n[+++] ГОТОВО! Проверяй файлы standings и crosstable для '{selected['name']}'.")
            else:
                print("\n[-] Что-то пошло не так при расчете. Возможно, данных в этом этапе нет.")
        else:
            print("[-] Такого номера нет в списке.")
    except ValueError:
        print("[-] Вводить надо цифру.")

if __name__ == "__main__":
    main()