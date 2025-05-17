# simulator.py
import csv
import os
import random
import re
import sys
from datetime import datetime
from config.config_manager import load_config, get_csv_path, log_message

class GameState:
    def __init__(self, log_file):
        self.flags = set()
        self.variables = {
            'Reputation': 0,
            'Sanity': 100,
            'Night': 1,
            'IsAtDock': True,
            'Confidence': 0
        }
        self.inventory = []
        self.log_file = log_file
    
    def set_flag(self, flag):
        """Set game flag and log the action"""
        self.flags.add(flag)
        message = f"[FLAG SET] {flag}"
        print(message)
        log_message(message, self.log_file)
    
    def has_flag(self, flag):
        """Check if flag exists"""
        return flag in self.flags
    
    def add_sanity(self, value):
        """Modify sanity value with bounds checking"""
        self.variables['Sanity'] = max(0, min(100, self.variables['Sanity'] + value))
        message = f"[SANITY] Changed by {value}. Current: {self.variables['Sanity']}"
        print(message)
        log_message(message, self.log_file)

def parse_weighted_text(text_pool):
    """Parse TextPool with weights (format: '1.2*Text|Text')"""
    variants = []
    for part in text_pool.split('|'):
        part = part.strip()
        if not part:
            continue
        
        if '*' in part:
            weight, text = part.split('*', 1)
            variants.append((float(weight.strip()), text.strip()))
        else:
            variants.append((1.0, part.strip()))
    return variants

def select_random_text(text_pool):
    """Select random text from TextPool considering weights"""
    variants = parse_weighted_text(text_pool)
    if not variants:
        return ""
    
    total_weight = sum(w for w, _ in variants)
    rand = random.uniform(0, total_weight)
    cumulative = 0.0
    
    for weight, text in variants:
        cumulative += weight
        if rand <= cumulative:
            return text
    
    return variants[-1][1]

def parse_player_choice(choice_str):
    """Parse player choice (format: 'Text ➔ID [Condition] {Effect}')"""
    choice_str = choice_str.strip()
    if not choice_str:
        return None
    
    # Extract components
    text = choice_str
    next_id = None
    condition = None
    effect = None
    
    # Parse NextID (➔)
    if '➔' in choice_str:
        text, rest = choice_str.split('➔', 1)
        next_id_str = rest.split()[0]
        next_id = int(next_id_str) if next_id_str.isdigit() else None
    
    # Parse condition [ ]
    condition_match = re.search(r'\[([^\]]+)\]', choice_str)
    if condition_match:
        condition = condition_match.group(1).strip()
    
    # Parse effect { }
    effect_match = re.search(r'\{(.+?)\}', choice_str)
    if effect_match:
        effect = effect_match.group(1).strip()
    
    return {
        'text': text.strip(),
        'next_id': next_id,
        'condition': condition,
        'effect': effect
    }

def load_dialogs(filename, log_file):
    """Load dialogs from CSV"""
    dialogs = {}
    try:
        with open(filename, 'r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    dialog_id = int(row['ID'])
                    dialogs[dialog_id] = {
                        'speaker': row['Speaker'],
                        'text_pool': row['TextPool'],
                        'player_choices': [parse_player_choice(c) for c in row['PlayerChoices'].split('|') if c.strip()],
                        'effects': row['Effects'] if 'Effects' in row and row['Effects'] != '-' else None,
                        'emotion': row['Emotion'],
                        'audio': row['Audio'] if 'Audio' in row and row['Audio'] != '-' else None
                    }
                except Exception as e:
                    error_msg = f"Error loading dialog {row.get('ID', 'unknown')}: {str(e)}"
                    log_message(error_msg, log_file)
                    raise
        log_message(f"Successfully loaded {len(dialogs)} dialogs from {filename}", log_file)
        return dialogs
    except Exception as e:
        error_msg = f"Failed to load dialogs: {str(e)}"
        log_message(error_msg, log_file)
        raise

def show_dialog(dialogs, start_id, game_state):
    """Display dialog and handle player choice"""
    current_id = start_id
    while current_id in dialogs:
        dialog = dialogs[current_id]
        
        # Show NPC text
        npc_text = select_random_text(dialog['text_pool'])
        message = f"{dialog['speaker']} ({dialog['emotion']}): {npc_text}"
        print(f"\n{message}")
        log_message(message, game_state.log_file)
        
        if dialog['audio']:
            audio_msg = f"[Sound: {dialog['audio']}]"
            print(audio_msg)
            log_message(audio_msg, game_state.log_file)
        
        # Show general effects
        if dialog['effects']:
            effect_msg = f"[EFFECT] {dialog['effects']}"
            print(effect_msg)
            log_message(effect_msg, game_state.log_file)
        
        # Show player choices
        if dialog['player_choices']:
            print("\nAvailable choices:")
            log_message("Available choices:", game_state.log_file)
            for i, choice in enumerate(dialog['player_choices'], 1):
                condition_info = f" [REQUIRES: {choice['condition']}]" if choice['condition'] else ""
                effect_info = f" [EFFECT: {choice['effect']}]" if choice['effect'] else ""
                choice_msg = f"{i}. {choice['text']}{condition_info}{effect_info}"
                print(choice_msg)
                log_message(choice_msg, game_state.log_file)
            
            # Let player choose any option regardless of conditions
            while True:
                try:
                    selected = int(input("Choose option: ")) - 1
                    if 0 <= selected < len(dialog['player_choices']):
                        chosen = dialog['player_choices'][selected]
                        if chosen['effect']:
                            effect_msg = f"[CHOICE EFFECT] {chosen['effect']}"
                            print(effect_msg)
                            log_message(effect_msg, game_state.log_file)
                        current_id = chosen['next_id']
                        log_message(f"User selected option {selected+1}, moving to dialog {current_id}", game_state.log_file)
                        break
                    print("Invalid choice!")
                    log_message("User entered invalid choice", game_state.log_file)
                except ValueError:
                    print("Please enter a number!")
                    log_message("User entered non-numeric value", game_state.log_file)
        else:
            # End of dialog branch
            end_msg = "\n[End of dialog]"
            print(end_msg)
            log_message(end_msg, game_state.log_file)
            return

def main():
    """Main simulator function"""
    if len(sys.argv) < 2:
        print("Error: Log file path not provided!")
        return
    
    log_file = sys.argv[1]
    log_message("=== Simulator started ===", log_file)
    print("=== Dialogue Simulator ===")
    
    config = load_config()
    csv_path = get_csv_path(config)
    
    if not csv_path or not os.path.exists(csv_path):
        log_message("No valid CSV path in config", log_file)
        csv_path = input("Enter CSV file path: ").strip('"')
        if not os.path.exists(csv_path):
            error_msg = "Error: File does not exist!"
            print(error_msg)
            log_message(error_msg, log_file)
            return
    
    game_state = GameState(log_file)
    
    try:
        dialogs = load_dialogs(csv_path, log_file)
        print(f"\nLoaded {len(dialogs)} dialogs")
        
        while True:
            try:
                start_id = int(input("\nEnter dialog ID (0=exit): "))
                if start_id == 0:
                    log_message("Simulator exited by user", log_file)
                    break
                if start_id in dialogs:
                    log_message(f"Starting dialog with ID {start_id}", log_file)
                    show_dialog(dialogs, start_id, game_state)
                else:
                    error_msg = "Dialog not found!"
                    print(error_msg)
                    log_message(error_msg, log_file)
            except ValueError:
                error_msg = "Please enter a number!"
                print(error_msg)
                log_message(error_msg, log_file)
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(error_msg)
        log_message(error_msg, log_file)

if __name__ == "__main__":
    main()
