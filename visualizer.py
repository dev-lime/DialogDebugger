# visualizer.py
import csv
import os
import re
import matplotlib.pyplot as plt
import networkx as nx
import sys
from config.config_manager import load_config, get_csv_path, log_message
from datetime import datetime

def parse_range(input_str, max_id):
    """Parse input range like '1-3,5,7-9' into list of IDs"""
    if not input_str.strip():
        return list(range(1, max_id + 1))  # Return all IDs if empty input
    
    ids = set()
    parts = input_str.split(',')
    
    for part in parts:
        part = part.strip()
        if '-' in part:
            start, end = map(int, part.split('-'))
            ids.update(range(start, end + 1))
        elif part.isdigit():
            ids.add(int(part))
    
    # Filter IDs that exist in the dialogs
    return sorted(id for id in ids if 1 <= id <= max_id)

def parse_choices(value):
    """Parse player choices in format 'Text ➔NextID [Condition]|...'"""
    if value == '-' or not value.strip():
        return [], []
    
    choices = []
    next_ids = []
    
    for choice in value.split('|'):
        choice = choice.strip()
        if not choice:
            continue
            
        # Parse choice structure
        match = re.match(r'^(.+?)➔(\d+)(?:\s*\[(.+?)\])?$', choice)
        if match:
            text = match.group(1).strip()
            next_id = int(match.group(2))
            condition = match.group(3) or ""
            
            choices.append(f"{text} [{condition}]" if condition else text)
            next_ids.append(next_id)
    
    return choices, next_ids

def parse_textpool(value):
    """Parse NPC reply variants with weights"""
    if value == '-' or not value.strip():
        return []
    
    variants = []
    for variant in value.split('|'):
        variant = variant.strip()
        if not variant:
            continue
            
        # Check for weight
        if '*' in variant:
            weight, text = variant.split('*', 1)
            try:
                weight = float(weight.strip())
            except ValueError:
                weight = 1.0
            variants.append(f"{weight}*{text.strip()}")
        else:
            variants.append(variant.strip())
    
    return variants

def load_dialogs(filename, log_file):
    """Load dialogs from CSV file"""
    dialogs = {}
    try:
        with open(filename, 'r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    dialog_id = int(row['ID'])
                    choices, next_ids = parse_choices(row['PlayerChoices'])
                    
                    dialogs[dialog_id] = {
                        'speaker': row['Speaker'],
                        'text_pool': parse_textpool(row['TextPool']),
                        'choices': choices,
                        'next_ids': next_ids,
                        'effects': row['Effects'],
                        'emotion': row['Emotion'],
                        'audio': row['Audio']
                    }
                except Exception as e:
                    error_msg = f"Error in row {row}: {str(e)}"
                    log_message(error_msg, log_file)
                    raise
        log_message(f"Successfully loaded {len(dialogs)} dialogs from {filename}", log_file)
        return dialogs
    except Exception as e:
        error_msg = f"Failed to load dialogs: {str(e)}"
        log_message(error_msg, log_file)
        raise

def visualize_dialogs(dialogs, output_file, log_file, selected_ids=None):
    """Visualize dialogue tree with improved layout"""
    log_message("Starting visualization process", log_file)
    plt.figure(figsize=(30, 20))
    G = nx.DiGraph()
    
    # Filter dialogs if specific IDs are selected
    if selected_ids:
        dialogs = {k: v for k, v in dialogs.items() if k in selected_ids}
        log_message(f"Visualizing selected IDs: {selected_ids}", log_file)
    
    # Add nodes with attributes
    for d_id, data in dialogs.items():
        speaker = data['speaker']
        
        # Build node label
        text_pool = '\n'.join(data['text_pool'][:3])  # Show first 3 variants
        if len(data['text_pool']) > 3:
            text_pool += '\n...'
            
        label = f"{speaker}\nID: {d_id}"
        if text_pool:
            label += f"\n---\n{text_pool}"
            
        if data['effects'] and data['effects'] != '-':
            label += f"\n---\nEffects: {data['effects']}"
            
        if data['audio'] and data['audio'] != '-':
            label += f"\nAudio: {data['audio']}"
        
        color = '#ffcccc' if speaker == 'Player' else '#ccffcc'
        shape = 'box' if speaker == 'Player' else 'ellipse'
        
        G.add_node(d_id, label=label, color=color, shape=shape, 
                  speaker=speaker, emotion=data['emotion'])
    
    # Add edges with choices (only between selected nodes)
    for d_id, data in dialogs.items():
        for choice, next_id in zip(data['choices'], data['next_ids']):
            if next_id in dialogs:
                G.add_edge(d_id, next_id, label=choice[:15])  # Shorter edge labels
        
        # For NPC nodes without player choices
        if not data['choices'] and data['next_ids']:
            for next_id in data['next_ids']:
                if next_id in dialogs:
                    G.add_edge(d_id, next_id)
    
    # Improved layout using graphviz
    try:
        pos = nx.nx_agraph.graphviz_layout(G, prog='dot')
        log_message("Using graphviz layout", log_file)
    except:
        # Fallback layout if graphviz isn't available
        log_message("Graphviz not found, using spring layout instead", log_file)
        print("Graphviz not found, using spring layout instead")
        pos = nx.spring_layout(G, k=1.5, iterations=50)
    
    # Separate node types
    player_nodes = [n for n in G.nodes if G.nodes[n]['speaker'] == 'Player']
    npc_nodes = [n for n in G.nodes if G.nodes[n]['speaker'] != 'Player']
    
    # Draw nodes with different styles
    nx.draw_networkx_nodes(G, pos, nodelist=player_nodes,
                         node_color='#ffcccc',
                         node_shape='s',
                         node_size=4000,
                         alpha=0.9)
    
    nx.draw_networkx_nodes(G, pos, nodelist=npc_nodes,
                         node_color='#ccffcc',
                         node_shape='o',
                         node_size=4000,
                         alpha=0.9)
    
    # Draw edges with arrows
    nx.draw_networkx_edges(G, pos, arrows=True,
                         arrowstyle='->',
                         arrowsize=25,
                         width=2,
                         edge_color='#555555',
                         alpha=0.7)
    
    # Node labels
    node_labels = {n: G.nodes[n]['label'] for n in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels=node_labels,
                          font_size=9,
                          font_family='Arial',
                          font_weight='bold')
    
    # Edge labels (choices)
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos,
                               edge_labels=edge_labels,
                               font_size=8,
                               font_color='#aa0000',
                               bbox=dict(alpha=0.7))
    
    plt.title("Dialogue Tree Visualization", fontsize=16, pad=20)
    plt.axis('off')
    
    # Adjust layout to prevent overlap
    plt.tight_layout(pad=3.0)
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    success_msg = f"\nGraph saved as: {output_file}"
    print(success_msg)
    log_message(success_msg, log_file)

def main():
    """Main visualization function"""
    if len(sys.argv) < 2:
        print("Error: Log file path not provided!")
        return
    
    log_file = sys.argv[1]
    log_message("=== Visualizer started ===", log_file)
    print("=== Dialogue Visualizer ===")
    
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
    
    try:
        dialogs = load_dialogs(csv_path, log_file)
        print(f"\nLoaded {len(dialogs)} dialogue nodes (IDs: 1-{max(dialogs.keys())})")
        log_message(f"Loaded {len(dialogs)} dialogue nodes", log_file)
        
        # Get ID range input
        range_prompt = "Enter dialog IDs to visualize (e.g. '1-3,5,7-9' or leave empty for all): "
        id_range = input(range_prompt).strip()
        selected_ids = parse_range(id_range, max(dialogs.keys())) if id_range else None
        
        output = input("Enter output filename [graph.png]: ") or "graph.png"
        log_message(f"Output file set to: {output}", log_file)
        visualize_dialogs(dialogs, output, log_file, selected_ids)
    except Exception as e:
        error_msg = f"\nError: {str(e)}"
        print(error_msg)
        log_message(error_msg, log_file)

if __name__ == "__main__":
    main()
