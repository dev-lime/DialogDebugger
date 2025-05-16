# visualizer.py
import csv
import json
import matplotlib.pyplot as plt
import networkx as nx
from config.config_manager import load_config, get_csv_path

def parse_field(value):
    """Парсит поле CSV, обрабатывая JSON или строки"""
    if value == '-' or not value.strip():
        return None
    
    # Обработка списков в квадратных скобках
    if value.startswith('[') and value.endswith(']'):
        try:
            inner = value[1:-1].strip()
            if not inner:
                return []
            return [item.strip(" '\"") for item in inner.split(',')]
        except:
            return value
    
    # Попытка парсинга JSON
    try:
        return json.loads(value.replace("'", '"'))
    except:
        return value

def load_dialogs(filename):
    """Загружает диалоги из CSV файла"""
    dialogs = {}
    with open(filename, 'r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                dialog_id = int(row['ID'])
                dialogs[dialog_id] = {
                    'speaker': row['Speaker'],
                    'text': row['Text'],
                    'choices': parse_field(row['Choices']) or [],
                    'next_ids': parse_field(row['Next_IDs']) or [],
                    'emotion': row['Emotion'],
                    'audio_id': row['AudioID']
                }
            except Exception as e:
                raise ValueError(f"Error in row {row}: {str(e)}")
    return dialogs

def visualize_dialogs(dialogs, output_file='dialogue_graph.png'):
    """Визуализирует дерево диалогов"""
    plt.figure(figsize=(24, 16))
    G = nx.DiGraph()
    
    # Добавляем узлы с атрибутами
    for d_id, data in dialogs.items():
        speaker = data['speaker']
        text = '\n'.join([data['text'][i:i+40] for i in range(0, len(data['text']), 40)])
        label = f"{speaker}\nID: {d_id}\n{text}"
        
        if data['audio_id']:
            label += f"\nAudio: {data['audio_id']}"
        
        color = '#ffcccc' if speaker == 'Player' else '#ccffcc'
        shape = 'box' if speaker == 'Player' else 'ellipse'
        
        G.add_node(d_id, label=label, color=color, shape=shape, 
                  speaker=speaker, emotion=data['emotion'])
    
    # Добавляем связи
    for d_id, data in dialogs.items():
        for choice, next_id in zip(data['choices'], data['next_ids']):
            if next_id in dialogs:
                G.add_edge(d_id, next_id, label=choice[:20])
        
        if not data['choices'] and data['next_ids']:
            for next_id in data['next_ids']:
                if next_id in dialogs:
                    G.add_edge(d_id, next_id)
    
    # Разделяем узлы по типам говорящих
    player_nodes = [n for n in G.nodes if G.nodes[n]['speaker'] == 'Player']
    other_nodes = [n for n in G.nodes if G.nodes[n]['speaker'] != 'Player']
    
    # Создаем слои для лучшего расположения
    pos = {}
    layer_gap = 3.0
    node_gap = 1.5
    
    # Располагаем узлы Player слева, другие справа
    for i, node in enumerate(player_nodes):
        pos[node] = (-layer_gap, -i * node_gap)
    
    for i, node in enumerate(other_nodes):
        pos[node] = (layer_gap, -i * node_gap)
    
    # Рисуем узлы
    nx.draw_networkx_nodes(G, pos, nodelist=player_nodes,
                          node_color='#ffcccc',
                          node_shape='s',
                          node_size=3000)
    
    nx.draw_networkx_nodes(G, pos, nodelist=other_nodes,
                          node_color='#ccffcc',
                          node_shape='o',
                          node_size=3000)
    
    # Рисуем связи
    nx.draw_networkx_edges(G, pos, arrows=True, 
                          arrowstyle='->', 
                          arrowsize=20,
                          width=1.5)
    
    # Подписи узлов
    labels = {n: G.nodes[n]['label'] for n in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels=labels, 
                           font_size=8, 
                           font_family='Arial')
    
    # Подписи связей
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, 
                                edge_labels=edge_labels,
                                font_size=7,
                                bbox=dict(alpha=0))
    
    plt.title("Dialogue Tree Visualization", fontsize=14)
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\nГраф сохранен как: {output_file}")

def main():
    """Основная функция визуализатора"""
    print("=== Визуализатор диалогов ===")
    config = load_config()
    csv_path = get_csv_path(config)
    
    try:
        dialogs = load_dialogs(csv_path)
        print(f"\nЗагружено {len(dialogs)} диалогов")
        output = input("Введите имя файла для сохранения [dialogue_graph.png]: ") or "dialogue_graph.png"
        visualize_dialogs(dialogs, output)
    except Exception as e:
        print(f"\nОшибка: {str(e)}")

if __name__ == "__main__":
    main()
