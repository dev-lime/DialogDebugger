# config/config_manager.py
import configparser
import os
from pathlib import Path
from datetime import datetime

CONFIG_FILE = 'config/config.ini'
LOG_DIR = 'logs'

def ensure_dirs():
    """Create necessary directories"""
    os.makedirs('config', exist_ok=True)
    Path(LOG_DIR).mkdir(exist_ok=True)

def init_config():
    """Initialize config file with default settings"""
    config = configparser.ConfigParser()
    config['DEFAULT'] = {
        'csv_path': '',
        'last_session': ''
    }
    return config

def load_config():
    """Load configuration or create new one if doesn't exist"""
    ensure_dirs()
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
    else:
        config = init_config()
        save_config(config)
    return config

def save_config(config):
    """Save configuration to file"""
    ensure_dirs()
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)

def get_csv_path(config):
    """Get CSV file path with existence check"""
    return config.get('DEFAULT', 'csv_path', fallback='')

def get_session_log_path():
    """Generate unique log file path with timestamp"""
    ensure_dirs()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"{LOG_DIR}/session_{timestamp}.log"
    return log_file

def log_message(message, log_file):
    """Log message to specified log file"""
    ensure_dirs()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")
