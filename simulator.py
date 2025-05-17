# simulator.py
import csv
import random
import re
from datetime import datetime
from config.config_manager import load_config, save_config, get_csv_path, LOG_DIR

class GameState:
    def __init__(self):
        self.flags = set()
        self.variables = {
            'Reputation': 0,
            'Sanity': 100,
            'Night': 1,
            'IsAtDock': True,
            'Confidence': 0
        }
        self.inventory = []
    
    def SetFlag(self, flag):
        self.flags.add(flag)
        print(f"[FLAG SET] {flag}")
    
    def HasFlag(self, flag):
        return flag in self.flags
    
    def AddSanity(self, value):
        self.variables['Sanity'] = max(0, min(100, self.variables['Sanity'] + value))
        print(f"[SANITY] Changed by {value}. Current: {self.variables['Sanity']}")

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

def load_dialogs(filename):
    """Load dialogs from CSV"""
    dialogs = {}
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
                print(f"Error loading dialog {row.get('ID', 'unknown')}: {str(e)}")
                raise
    return dialogs

def show_dialog(dialogs, start_id, game_state):
    """Display dialog and handle player choice"""
    current_id = start_id
    while current_id in dialogs:
        dialog = dialogs[current_id]
        
        # Show NPC text
        npc_text = select_random_text(dialog['text_pool'])
        print(f"\n{dialog['speaker']} ({dialog['emotion']}): {npc_text}")
        if dialog['audio']:
            print(f"[Sound: {dialog['audio']}]")
        
        # Show general effects
        if dialog['effects']:
            print(f"[EFFECT] {dialog['effects']}")
        
        # Show player choices
        if dialog['player_choices']:
            print("\nAvailable choices:")
            for i, choice in enumerate(dialog['player_choices'], 1):
                condition_info = f" [REQUIRES: {choice['condition']}]" if choice['condition'] else ""
                effect_info = f" [EFFECT: {choice['effect']}]" if choice['effect'] else ""
                print(f"{i}. {choice['text']}{condition_info}{effect_info}")
            
            # Let player choose any option regardless of conditions
            while True:
                try:
                    selected = int(input("Choose option: ")) - 1
                    if 0 <= selected < len(dialog['player_choices']):
                        chosen = dialog['player_choices'][selected]
                        if chosen['effect']:
                            print(f"[CHOICE EFFECT] {chosen['effect']}")
                        current_id = chosen['next_id']
                        break
                    print("Invalid choice!")
                except ValueError:
                    print("Please enter a number!")
        else:
            # End of dialog branch
            print("\n[End of dialog]")
            return

def main():
    print("=== Dialogue Simulator (Simplified) ===")
    csv_path = input("Enter CSV file path: ").strip()
    game_state = GameState()
    
    try:
        dialogs = load_dialogs(csv_path)
        print(f"\nLoaded {len(dialogs)} dialogs")
        
        while True:
            try:
                start_id = int(input("\nEnter dialog ID (0=exit): "))
                if start_id == 0:
                    break
                if start_id in dialogs:
                    show_dialog(dialogs, start_id, game_state)
                else:
                    print("Dialog not found!")
            except ValueError:
                print("Please enter a number!")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
