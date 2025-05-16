# simulator.py
import csv
import json
import os
from datetime import datetime
from config.config_manager import load_config, save_config, get_csv_path, LOG_DIR

class GameState:
    def __init__(self):
        self.flags = set()
        self.variables = {
            'Reputation': 0,
            'Sanity': 100,
            'Night': 1,
            'IsAtDock': True
        }
        self.inventory = []
    
    def SetFlag(self, flag):
        self.flags.add(flag)
    
    def HasFlag(self, flag):
        return flag in self.flags
    
    def AddSanity(self, value):
        self.variables['Sanity'] = max(0, min(100, self.variables['Sanity'] + value))
    
    def __getitem__(self, key):
        return self.variables.get(key, 0)
    
    def __str__(self):
        return f"Flags: {self.flags}, Vars: {self.variables}, Inventory: {self.inventory}"

def get_session_log_file():
    """Создает файл лога для текущей сессии"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(LOG_DIR, f"session_{timestamp}.log")

def log_message(log_file, message):
    """Записывает сообщение в лог-файл"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, 'a', encoding='utf-8') as log:
        log.write(f"[{timestamp}] {message}\n")

def parse_field(value):
    """Парсит поле CSV с правильной обработкой списков"""
    if not value or value.strip() == '-':
        return None
    
    value = value.strip()
    
    # Обработка строк в кавычках
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    
    # Обработка списков
    if value.startswith('[') and value.endswith(']'):
        try:
            # Удаляем внешние скобки и разбиваем по запятым
            inner = value[1:-1].strip()
            if not inner:
                return []
            
            # Разбиваем с учетом кавычек
            items = []
            current = []
            in_quotes = False
            quote_char = None
            
            for char in inner:
                if char in ('"', "'") and not in_quotes:
                    in_quotes = True
                    quote_char = char
                elif char == quote_char and in_quotes:
                    in_quotes = False
                    quote_char = None
                elif char == ',' and not in_quotes:
                    items.append(''.join(current).strip())
                    current = []
                else:
                    current.append(char)
            
            if current:
                items.append(''.join(current).strip())
            
            # Удаляем кавычки у элементов
            return [item.strip(" '\"") for item in items]
        except Exception as e:
            print(f"List parsing error: {e}")
            return value
    
    return value

def load_dialogs(filename):
    """Загружает диалоги с правильной обработкой всех полей"""
    dialogs = {}
    with open(filename, 'r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                dialog_id = int(row['ID'])
                choices = parse_field(row['Choices']) or []
                next_ids = parse_field(row['Next_IDs']) or []
                
                # Проверка соответствия количества вариантов и next_ids
                if choices and len(choices) != len(next_ids):
                    print(f"Warning: Dialog {dialog_id} has {len(choices)} choices but {len(next_ids)} next_ids")
                
                dialogs[dialog_id] = {
                    'speaker': row['Speaker'],
                    'text': row['Text'],
                    'choices': choices,
                    'next_ids': next_ids,
                    'condition': parse_field(row['Condition']),
                    'effect': row['Effect'] if row['Effect'] != '-' else None,
                    'emotion': row['Emotion'],
                    'audio_id': row['AudioID'] if row['AudioID'] != '-' else None
                }
            except Exception as e:
                print(f"Error loading dialog {row.get('ID', 'unknown')}: {str(e)}")
                raise
    return dialogs

def check_condition(condition, game_state):
    """Проверяет условие для диалога"""
    # Если условие не задано или прочерк
    if condition is None:
        return True
    
    # Если условие - строка (не условие, а например "...")
    if isinstance(condition, str):
        return True
    
    # Обработка специальных функций
    if isinstance(condition, str) and condition.startswith('HasFlag('):
        flag = condition[8:-1].strip("'\"")
        return game_state.HasFlag(flag)
    
    # Числовые условия
    if isinstance(condition, (int, float)):
        return bool(condition)
    
    # Сложные условия
    try:
        return eval(str(condition), {}, {
            **game_state.variables,
            'HasFlag': game_state.HasFlag
        })
    except:
        return False

def apply_effect(effect, game_state, log_file):
    """Применяет эффект от диалога с улучшенной обработкой ошибок"""
    if not effect or effect == '-':
        return
    
    # Специальные команды
    if effect.startswith('SetFlag('):
        try:
            flag = effect[8:-1].strip("'\"")
            game_state.SetFlag(flag)
            log_message(log_file, f"Set flag: {flag}")
            return
        except Exception as e:
            log_message(log_file, f"Flag error: {str(e)}")
            return
    
    if effect.startswith('AddSanity('):
        try:
            value = int(effect[10:-1])
            game_state.AddSanity(value)
            log_message(log_file, f"Added sanity: {value}")
            return
        except Exception as e:
            log_message(log_file, f"Sanity error: {str(e)}")
            return
    
    # Стандартные эффекты
    try:
        if effect.startswith(('Reputation', 'Sanity', 'Night', 'IsAtDock')):
            exec(effect, {}, game_state.variables)
            log_message(log_file, f"Applied effect: {effect}")
    except Exception as e:
        log_message(log_file, f"Effect error: {str(e)}")
        print(f"Effect error: {str(e)}")

def show_dialog(dialogs, start_id, game_state, log_file):
    """Отображает диалог с правильной обработкой выбора"""
    current_id = start_id
    while current_id in dialogs:
        dialog = dialogs[current_id]
        
        if not check_condition(dialog['condition'], game_state):
            print("\n[Диалог недоступен]")
            return
        
        # Отображение диалога
        print(f"\n{dialog['speaker']} ({dialog['emotion']}): {dialog['text']}")
        if dialog['audio_id']:
            print(f"[Audio: {dialog['audio_id']}]")
        
        # Обработка выбора игрока
        if dialog['speaker'] == "Player" and dialog['choices']:
            print("\nВарианты ответа:")
            for i, (choice, next_id) in enumerate(zip(dialog['choices'], dialog['next_ids']), 1):
                print(f"{i}. {choice}")
            
            while True:
                try:
                    choice = int(input("Выберите вариант: ")) - 1
                    if 0 <= choice < len(dialog['choices']):
                        if dialog['effect']:
                            apply_effect(dialog['effect'], game_state, log_file)
                        current_id = dialog['next_ids'][choice]
                        break
                    print("Неверный выбор! Попробуйте снова.")
                except ValueError:
                    print("Пожалуйста, введите число!")
        else:
            # Для NPC/System диалогов
            if dialog['effect']:
                apply_effect(dialog['effect'], game_state, log_file)
            
            if dialog['next_ids']:
                current_id = dialog['next_ids'][0]
            else:
                print("\n[Конец диалога]")
                return

def main():
    """Основная функция симулятора диалогов"""
    print("=== Симулятор диалогов ===")
    config = load_config()
    csv_path = get_csv_path(config)
    game_state = GameState()
    log_file = get_session_log_file()
    
    log_message(log_file, "=== Начало сессии ===")
    log_message(log_file, f"CSV file: {csv_path}")
    
    try:
        dialogs = load_dialogs(csv_path)
        log_message(log_file, f"Loaded {len(dialogs)} dialogs")
        print(f"\nЗагружено {len(dialogs)} диалогов")
        
        while True:
            try:
                start_id = int(input("\nВведите ID диалога (0=выход): "))
                if start_id == 0:
                    break
                if start_id in dialogs:
                    show_dialog(dialogs, start_id, game_state, log_file)
                else:
                    print("Неверный ID диалога!")
            except ValueError:
                print("Введите число!")
    except Exception as e:
        print(f"\nОшибка: {str(e)}")
        log_message(log_file, f"CRASH: {str(e)}")
    finally:
        log_message(log_file, f"Final state: {game_state}")
        log_message(log_file, "=== Конец сессии ===\n")
        print("\nСмотрите логи в:", log_file)

if __name__ == "__main__":
    main()
