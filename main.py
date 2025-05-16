# main.py
from config.config_manager import init_config, load_config, save_config
import os
import subprocess

def setup_config():
    """Настройка конфигурации"""
    config = init_config()
    
    print("\n=== Настройка системы диалогов ===")
    csv_path = input("Введите путь к CSV файлу с диалогами: ").strip('"')
    
    if os.path.exists(csv_path):
        config['DEFAULT']['csv_path'] = csv_path
        save_config(config)
        print("Конфигурация сохранена!")
    else:
        print("Ошибка: файл не существует!")
    
    return config

def main_menu():
    """Главное меню управления"""
    print("\n=== Менеджер диалогов ===")
    print("1. Симулятор диалогов")
    print("2. Визуализатор диалогов")
    print("3. Настройки")
    print("0. Выход")
    
    while True:
        choice = input("Выберите действие: ")
        if choice in ['0', '1', '2', '3']:
            return choice
        print("Неверный выбор!")

def main():
    """Основная функция менеджера"""
    config = load_config()
    
    while True:
        choice = main_menu()
        
        if choice == '0':
            print("\nВыход...")
            break
        elif choice == '1':
            print("\nЗапуск симулятора...")
            subprocess.run(['python', 'simulator.py'])
        elif choice == '2':
            print("\nЗапуск визуализатора...")
            subprocess.run(['python', 'visualizer.py'])
        elif choice == '3':
            config = setup_config()

if __name__ == "__main__":
    main()
