# main.py
from config.config_manager import load_config, save_config, get_session_log_path, log_message
import os
import subprocess
import datetime

def setup_config(log_file):
    """Configure system settings"""
    config = load_config()
    
    log_message("=== Configuration setup ===", log_file)
    while True:
        csv_path = input("Enter path to CSV file with dialogs: ").strip('"')
        
        if os.path.exists(csv_path):
            config['DEFAULT']['csv_path'] = csv_path
            save_config(config)
            log_message(f"Configuration saved. CSV path: {csv_path}", log_file)
            print("Configuration saved!")
            return config
        else:
            log_message(f"Invalid path entered: {csv_path}", log_file)
            print("Error: File doesn't exist!")

def main_menu(log_file):
    """Display main management menu"""
    menu_text = """
=== Dialog Manager ===
1. Dialog Simulator
2. Dialog Visualizer
3. Settings
0. Exit
"""
    print(menu_text)
    log_message("Main menu displayed", log_file)
    
    while True:
        choice = input("Select action: ")
        if choice in ['0', '1', '2', '3']:
            log_message(f"User selected option {choice}", log_file)
            return choice
        log_message(f"Invalid input: {choice}", log_file)
        print("Invalid selection!")

def main():
    """Main manager function"""
    log_file = get_session_log_path()
    log_message(f"=== Application started ===", log_file)
    config = load_config()
    
    while True:
        choice = main_menu(log_file)
        
        if choice == '0':
            log_message("Application exited by user", log_file)
            print("\nExiting...")
            break
        elif choice == '1':
            log_message("Launching simulator...", log_file)
            print("\nLaunching simulator...")
            subprocess.run(['python', 'simulator.py', log_file])
        elif choice == '2':
            log_message("Launching visualizer...", log_file)
            print("\nLaunching visualizer...")
            subprocess.run(['python', 'visualizer.py', log_file])
        elif choice == '3':
            log_message("Opening settings...", log_file)
            config = setup_config(log_file)

if __name__ == "__main__":
    main()
