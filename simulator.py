import csv
import os
import random
import re
import sys
from datetime import datetime
from config.config_manager import load_config, get_csv_path, log_message

def parse_player_choice(choice_str):
    """Parse player choice (format: 'Text ➔ID [Condition] {Effect}')"""
    if not choice_str.strip():
        return None

    # Check for automatic transition (only arrow)
    if choice_str.strip() == '➔':
        return {
            'text': '',
            'next_id': None,
            'condition': None,
            'effect': None,
            'is_auto': True
        }
    
    # Check for simple transition (only arrow and ID)
    if re.fullmatch(r'➔\d+', choice_str.strip()):
        next_id = int(choice_str.strip()[1:])
        return {
            'text': '',
            'next_id': next_id,
            'condition': None,
            'effect': None,
            'is_auto': True
        }

    parts = choice_str.split('➔', 1)
    text = parts[0].strip()
    next_id = None
    condition = None
    effect = None

    if len(parts) > 1:
        # Extract next dialog ID
        id_part = parts[1].split()[0]
        next_id = int(id_part) if id_part.isdigit() else None

        # Extract condition and effect if present
        condition_match = re.search(r'\[([^\]]+)\]', choice_str)
        if condition_match:
            condition = condition_match.group(1)

        effect_match = re.search(r'\{(.+?)\}', choice_str)
        if effect_match:
            effect = effect_match.group(1)

    return {
        'text': text,
        'next_id': next_id,
        'condition': condition,
        'effect': effect,
        'is_auto': False  # Regular choice
    }

def load_dialogs(filename, log_file):
    """Load dialogs from CSV file with logging"""
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
                        'choices': [parse_player_choice(c) for c in row['PlayerChoices'].split('|') if c.strip()],
                        'effects': row['Effects'] if row['Effects'] != '-' else None,
                        'emotion': row['Emotion'],
                        'audio': row['Audio'] if row['Audio'] != '-' else None
                    }
                    log_message(f"Loaded dialog {dialog_id}", log_file)
                except Exception as e:
                    error_msg = f"Error loading dialog {row.get('ID', 'unknown')}: {str(e)}"
                    log_message(error_msg, log_file)
        
        log_message(f"Successfully loaded {len(dialogs)} dialogs from {filename}", log_file)
        return dialogs
    except Exception as e:
        error_msg = f"Failed to load dialogs: {str(e)}"
        log_message(error_msg, log_file)
        raise

def select_random_text(text_pool):
    """Select random text from TextPool"""
    variants = [v.strip() for v in text_pool.split('|') if v.strip()]
    return random.choice(variants) if variants else ""

def show_dialog(dialogs, start_id, log_file):
    """Display dialog and handle player choice with logging"""
    current_id = start_id

    while current_id in dialogs:
        dialog = dialogs[current_id]

        # Show NPC text (random from pool)
        npc_text = select_random_text(dialog['text_pool'])
        message = f"{dialog['speaker']} ({dialog['emotion']}): {npc_text}"
        print(f"\n{message}")
        log_message(message, log_file)

        if dialog['audio']:
            audio_msg = f"[Sound: {dialog['audio']}]"
            print(audio_msg)
            log_message(audio_msg, log_file)

        if dialog['effects']:
            effect_msg = f"[EFFECT] {dialog['effects']}"
            print(effect_msg)
            log_message(effect_msg, log_file)

        # End of dialog branch
        if not dialog['choices']:
            end_msg = "\n[End of dialog branch]"
            print(end_msg)
            log_message(end_msg, log_file)
            return

        # Check for automatic transition
        auto_choices = [c for c in dialog['choices'] if c and c.get('is_auto')]
        if len(auto_choices) == len(dialog['choices']):
            # All choices are automatic - perform auto-transition
            chosen = auto_choices[0]  # Take first auto choice
            if chosen['next_id'] is not None:
                current_id = chosen['next_id']
                continue
            else:
                return

        # Show available choices (skip auto choices)
        print("\nAvailable choices:")
        log_message("Available choices:", log_file)
        valid_choices = []
        for i, choice in enumerate(dialog['choices'], 1):
            if choice and not choice.get('is_auto'):
                cond_info = f" [CONDITION: {choice['condition']}]" if choice['condition'] else ""
                eff_info = f" [EFFECT: {choice['effect']}]" if choice['effect'] else ""
                choice_msg = f"{i}. {choice['text']}{cond_info}{eff_info}"
                print(choice_msg)
                log_message(choice_msg, log_file)
                valid_choices.append(choice)

        # Get player choice
        while True:
            try:
                choice = input("\nChoose option (0=exit): ").strip()
                if choice == '0':
                    log_message("User exited dialog", log_file)
                    return

                selected = int(choice) - 1
                if 0 <= selected < len(valid_choices):
                    chosen = valid_choices[selected]

                    if chosen['effect']:
                        effect_msg = f"[APPLIED EFFECT: {chosen['effect']}]"
                        print(effect_msg)
                        log_message(effect_msg, log_file)

                    log_message(f"User selected option {selected+1}, moving to dialog {chosen['next_id']}", log_file)
                    current_id = chosen['next_id']
                    break
                else:
                    print(f"Please enter number 1-{len(valid_choices)}")
            except ValueError:
                print("Please enter a valid number!")

def main():
    """Main function with config and logging"""
    if len(sys.argv) < 2:
        print("Error: Log file path not provided!")
        return
    
    log_file = sys.argv[1]
    log_message("=== Dialogue simulator started ===", log_file)
    print("=== Dialogue Simulator ===")
    
    try:
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
        
        dialogs = load_dialogs(csv_path, log_file)
        
        while True:
            try:
                start_id = int(input("\nEnter dialog ID (0=exit): "))
                if start_id == 0:
                    log_message("Simulator exited by user", log_file)
                    break
                if start_id in dialogs:
                    log_message(f"Starting dialog with ID {start_id}", log_file)
                    show_dialog(dialogs, start_id, log_file)
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
