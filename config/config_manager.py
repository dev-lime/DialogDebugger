# config_manager.py
import configparser
import os
from pathlib import Path

CONFIG_FILE = 'config/config.ini'
LOG_DIR = 'logs'

def ensure_dirs():
    """Создает необходимые директории"""
    Path(LOG_DIR).mkdir(exist_ok=True)

def init_config():
    """Инициализирует конфигурационный файл с настройками по умолчанию"""
    config = configparser.ConfigParser()
    config['DEFAULT'] = {
        'csv_path': '',
        'last_session': ''
    }
    return config

def load_config():
    """Загружает конфигурацию или создает новую"""
    ensure_dirs()
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
    else:
        config = init_config()
        save_config(config)
    return config

def save_config(config):
    """Сохраняет конфигурацию в файл"""
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)

def get_csv_path(config):
    """Получает путь к CSV файлу с проверкой его существования"""
    while True:
        csv_path = config.get('DEFAULT', 'csv_path', fallback='')
        if csv_path and os.path.exists(csv_path):
            return csv_path
        
        print(f"Файл не найден: {csv_path}" if csv_path else "Путь не задан.")
        new_path = input("Введите путь к CSV файлу: ").strip('"')
        if os.path.exists(new_path):
            config['DEFAULT']['csv_path'] = new_path
            save_config(config)
            return new_path
        print("Файл не существует!")
