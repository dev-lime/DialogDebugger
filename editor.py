import sys
import csv
import re
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTreeWidget, QTreeWidgetItem, QLabel, QLineEdit, QTextEdit,
                             QComboBox, QPushButton, QSplitter, QMessageBox, QFileDialog,
                             QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
                             QSpinBox, QToolTip)
from PyQt5.QtCore import Qt

EMOTIONS = ["Neutral", "Happy", "Sad", "Angry", "Surprised", "Fearful", "Disgusted", "Worried", "Hopeful", "Thoughtful"]

class WeightedTextEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Weight", "Text"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 80)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        button_layout = QHBoxLayout()
        add_button = QPushButton("Add Variant")
        add_button.setToolTip("Add new text variant with default weight 1.0")
        add_button.clicked.connect(self.add_variant)
        button_layout.addWidget(add_button)
        
        remove_button = QPushButton("Remove Selected")
        remove_button.setToolTip("Remove selected text variant")
        remove_button.clicked.connect(self.remove_selected)
        button_layout.addWidget(remove_button)
        
        layout.addWidget(self.table)
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def add_variant(self, weight=1.0, text=""):
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        weight_item = QTableWidgetItem()
        weight_item.setData(Qt.DisplayRole, float(weight))
        self.table.setItem(row, 0, weight_item)
        
        self.table.setItem(row, 1, QTableWidgetItem(text))
    
    def remove_selected(self):
        selected = self.table.selectionModel().selectedRows()
        for idx in sorted(selected, key=lambda x: x.row(), reverse=True):
            self.table.removeRow(idx.row())
    
    def get_variants(self):
        variants = []
        for row in range(self.table.rowCount()):
            weight = self.table.item(row, 0).data(Qt.DisplayRole)
            text = self.table.item(row, 1).text().strip() if self.table.item(row, 1) else ""
            
            if not text:
                continue
                
            if float(weight) == 1.0:
                variants.append(text)
            else:
                variants.append(f"{weight}*{text}")
        return variants
    
    def set_variants(self, variants):
        self.table.setRowCount(0)
        for variant in variants:
            # Parse weight if present
            weight_match = re.match(r'^([\d.]+)\*(.+)$', variant)
            if weight_match:
                weight = float(weight_match.group(1))
                text = weight_match.group(2)
            else:
                weight = 1.0
                text = variant
            self.add_variant(weight, text)

class PlayerChoiceEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Text", "Next ID", "Condition"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        button_layout = QHBoxLayout()
        add_button = QPushButton("Add Choice")
        add_button.setToolTip("Add new player choice with default Next ID = 0")
        add_button.clicked.connect(self.add_choice)
        button_layout.addWidget(add_button)
        
        remove_button = QPushButton("Remove Selected")
        remove_button.setToolTip("Remove selected player choice")
        remove_button.clicked.connect(self.remove_selected)
        button_layout.addWidget(remove_button)
        
        auto_button = QPushButton("Add Auto Transition")
        auto_button.setToolTip("Add automatic transition without player choice")
        auto_button.clicked.connect(self.add_auto_transition)
        button_layout.addWidget(auto_button)
        
        layout.addWidget(self.table)
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def add_choice(self, text="", next_id="0", condition=""):
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        self.table.setItem(row, 0, QTableWidgetItem(text))
        self.table.setItem(row, 1, QTableWidgetItem(str(next_id)))
        self.table.setItem(row, 2, QTableWidgetItem(condition))
    
    def add_auto_transition(self):
        self.add_choice("", "1", "")
    
    def remove_selected(self):
        selected = self.table.selectionModel().selectedRows()
        for idx in sorted(selected, key=lambda x: x.row(), reverse=True):
            self.table.removeRow(idx.row())
    
    def get_choices(self):
        choices = []
        for row in range(self.table.rowCount()):
            text = self.table.item(row, 0).text().strip() if self.table.item(row, 0) else ""
            next_id = self.table.item(row, 1).text().strip() if self.table.item(row, 1) else "0"
            condition = self.table.item(row, 2).text().strip() if self.table.item(row, 2) else ""
            
            if not text and not next_id:
                continue
                
            parts = []
            if text:
                parts.append(text)
            if next_id:
                parts.append(f"➔{next_id}")
            if condition:
                parts.append(f"[{condition}]")
            
            choices.append(" ".join(parts))
        
        return choices
    
    def set_choices(self, choices):
        self.table.setRowCount(0)
        for choice in choices:
            # Parse the choice string
            text = ""
            next_id = "0"  # Default Next ID
            condition = ""
            
            # Extract text (before arrow)
            arrow_pos = choice.find("➔")
            if arrow_pos >= 0:
                text = choice[:arrow_pos].strip()
                remaining = choice[arrow_pos+1:]
            else:
                remaining = choice
            
            # Extract next ID
            next_id_part = remaining.split()[0] if remaining else "0"
            next_id = next_id_part.split("[")[0] if next_id_part else "0"
            
            # Extract condition
            condition_start = remaining.find("[")
            condition_end = remaining.find("]") if condition_start >= 0 else -1
            if condition_start >= 0 and condition_end >= 0:
                condition = remaining[condition_start+1:condition_end]
            
            self.add_choice(text, next_id, condition)

class DialogNodeEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_node = None
        self.main_window = parent
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # ID и Speaker
        id_layout = QHBoxLayout()
        id_layout.addWidget(QLabel("ID:"))
        self.id_spin = QSpinBox()
        self.id_spin.setMinimum(1)
        self.id_spin.setMaximum(9999)
        id_layout.addWidget(self.id_spin)
        
        id_layout.addWidget(QLabel("Speaker:"))
        self.speaker_edit = QLineEdit()
        id_layout.addWidget(self.speaker_edit)
        layout.addLayout(id_layout)
        
        # Text Variants
        layout.addWidget(QLabel("Text Variants (with weights):"))
        self.text_variants_editor = WeightedTextEditor()
        layout.addWidget(self.text_variants_editor)
        
        # Emotion, Effects и Audio
        meta_layout = QHBoxLayout()
        
        # Emotion
        emotion_layout = QVBoxLayout()
        emotion_layout.addWidget(QLabel("Emotion:"))
        self.emotion_combo = QComboBox()
        self.emotion_combo.addItems(EMOTIONS)
        emotion_layout.addWidget(self.emotion_combo)
        meta_layout.addLayout(emotion_layout)
        
        # Effects
        effects_layout = QVBoxLayout()
        effects_layout.addWidget(QLabel("Effects:"))
        self.effects_edit = QLineEdit()
        self.effects_edit.setPlaceholderText("SetFlag('X'), AddValue(5)")
        effects_layout.addWidget(self.effects_edit)
        meta_layout.addLayout(effects_layout)
        
        # Audio
        audio_layout = QVBoxLayout()
        audio_layout.addWidget(QLabel("Audio:"))
        self.audio_edit = QLineEdit()
        self.audio_edit.setPlaceholderText("sound_id")
        audio_layout.addWidget(self.audio_edit)
        meta_layout.addLayout(audio_layout)
        
        layout.addLayout(meta_layout)
        
        # Choices
        layout.addWidget(QLabel("Player Choices:"))
        self.choices_editor = PlayerChoiceEditor()
        layout.addWidget(self.choices_editor)
        
        # Кнопки управления
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.setToolTip("Save current dialog node")
        self.save_button.clicked.connect(self.save_node)
        button_layout.addWidget(self.save_button)
        
        self.delete_button = QPushButton("Delete")
        self.delete_button.setToolTip("Delete current dialog node")
        self.delete_button.clicked.connect(self.delete_node)
        button_layout.addWidget(self.delete_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def load_node(self, node_data):
        self.current_node = node_data
        self.id_spin.setValue(node_data['id'])
        self.speaker_edit.setText(node_data['speaker'])
        self.text_variants_editor.set_variants(node_data['text_pool'].split("|") if node_data['text_pool'] else [])
        
        # Установка эмоции с проверкой наличия в списке
        emotion = node_data.get('emotion', 'neutral')
        if emotion in EMOTIONS:
            self.emotion_combo.setCurrentText(emotion)
        else:
            self.emotion_combo.setCurrentIndex(0)
        
        self.effects_edit.setText(node_data.get('effects', '-'))
        self.audio_edit.setText(node_data.get('audio', '-'))
        self.choices_editor.set_choices(node_data.get('choices', []))
    
    def save_node(self):
        if not self.current_node:
            return
            
        new_id = self.id_spin.value()
        old_id = self.current_node['id']
        
        # Check if ID was changed and already exists
        if new_id != old_id and new_id in self.main_window.tree.dialogs:
            QMessageBox.warning(self, "Error", f"Dialog with ID {new_id} already exists!")
            self.id_spin.setValue(old_id)
            return
            
        self.current_node.update({
            'id': new_id,
            'speaker': self.speaker_edit.text(),
            'text_pool': "|".join(self.text_variants_editor.get_variants()),
            'emotion': self.emotion_combo.currentText(),
            'effects': self.effects_edit.text() if self.effects_edit.text() != "-" else "-",
            'audio': self.audio_edit.text() if self.audio_edit.text() != "-" else "-",
            'choices': self.choices_editor.get_choices()
        })
        
        # Update tree item if ID changed
        if new_id != old_id:
            self.main_window.tree.dialogs[new_id] = self.current_node
            del self.main_window.tree.dialogs[old_id]
            for i in range(self.main_window.tree.topLevelItemCount()):
                item = self.main_window.tree.topLevelItem(i)
                if item.dialog_id == old_id:
                    item.dialog_id = new_id
                    item.setText(0, f"{new_id}: {self.current_node['speaker']}")
                    break
        
    def delete_node(self):
        if self.current_node and self.main_window:
            self.main_window.delete_node(self.current_node['id'])
    
    def clear(self):
        self.current_node = None
        self.id_spin.setValue(1)
        self.speaker_edit.clear()
        self.text_variants_editor.set_variants([])
        self.emotion_combo.setCurrentIndex(0)
        self.effects_edit.clear()
        self.audio_edit.clear()
        self.choices_editor.set_choices([])

class DialogTree(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabel("Dialogs")
        self.dialogs = {}
        self.main_window = parent
        self.itemClicked.connect(self.on_item_clicked)
    
    def add_dialog(self, dialog_data):
        item = QTreeWidgetItem([f"{dialog_data['id']}: {dialog_data['speaker']}"])
        item.dialog_id = dialog_data['id']
        
        # Add tooltip with preview info
        preview_text = dialog_data['text_pool'].split("|")[0][:50] + "..." if dialog_data['text_pool'] else ""
        choices = len(dialog_data.get('choices', []))
        tooltip = f"Text: {preview_text}\nChoices: {choices}\nEmotion: {dialog_data.get('emotion', 'neutral')}"
        item.setToolTip(0, tooltip)
        
        self.addTopLevelItem(item)
        self.dialogs[dialog_data['id']] = dialog_data
        return item
    
    def on_item_clicked(self, item, column):
        dialog_id = item.dialog_id
        if self.main_window and hasattr(self.main_window, 'editor'):
            self.main_window.editor.load_node(self.dialogs[dialog_id])
    
    def delete_dialog(self, dialog_id):
        if dialog_id in self.dialogs:
            del self.dialogs[dialog_id]
            
            for i in range(self.topLevelItemCount()):
                item = self.topLevelItem(i)
                if item.dialog_id == dialog_id:
                    self.takeTopLevelItem(i)
                    break

class DialogEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dialog Editor")
        self.setGeometry(100, 100, 1000, 700)
        
        self.init_ui()
        self.new_project()
    
    def init_ui(self):
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        
        splitter = QSplitter(Qt.Horizontal)
        
        # Дерево диалогов
        self.tree = DialogTree(self)
        splitter.addWidget(self.tree)
        
        # Редактор узла
        self.editor = DialogNodeEditor(self)
        splitter.addWidget(self.editor)
        
        splitter.setSizes([200, 800])
        main_layout.addWidget(splitter)
        
        # Панель инструментов
        toolbar = self.addToolBar("Main")
        
        new_action = toolbar.addAction("New")
        new_action.setToolTip("Create new dialog project")
        new_action.triggered.connect(self.new_project)
        
        open_action = toolbar.addAction("Open CSV")
        open_action.setToolTip("Open dialog from CSV file")
        open_action.triggered.connect(self.open_csv)
        
        save_action = toolbar.addAction("Save CSV")
        save_action.setToolTip("Save dialog to CSV file")
        save_action.triggered.connect(self.save_csv)
        
        add_node_action = toolbar.addAction("Add Node")
        add_node_action.setToolTip("Add new dialog node")
        add_node_action.triggered.connect(self.add_dialog_node)
        
        self.setCentralWidget(central_widget)
    
    def new_project(self):
        self.tree.clear()
        self.editor.clear()
        self.current_file = None
        
        # Добавляем стартовый узел
        self.add_dialog_node(start_id=1)
    
    def open_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open CSV File", "", "CSV Files (*.csv)")
        
        if file_path:
            try:
                self.tree.clear()
                self.editor.clear()
                self.current_file = file_path
                
                with open(file_path, 'r', encoding='utf-8-sig') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        dialog_data = {
                            'id': int(row['ID']),
                            'speaker': row['Speaker'],
                            'text_pool': row['TextPool'],
                            'choices': row['PlayerChoices'].split('|') if row['PlayerChoices'] else [],
                            'effects': row['Effects'],
                            'emotion': row['Emotion'],
                            'audio': row['Audio']
                        }
                        self.tree.add_dialog(dialog_data)
                
                QMessageBox.information(self, "Success", f"Loaded {self.tree.topLevelItemCount()} dialogs")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load CSV: {str(e)}")
    
    def save_csv(self):
        if not self.current_file:
            self.current_file, _ = QFileDialog.getSaveFileName(
                self, "Save CSV File", "", "CSV Files (*.csv)")
        
        if self.current_file:
            try:
                dialogs = sorted(self.tree.dialogs.values(), key=lambda x: x['id'])
                
                with open(self.current_file, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['ID', 'Speaker', 'TextPool', 'PlayerChoices', 'Effects', 'Emotion', 'Audio']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    writer.writeheader()
                    
                    for dialog in dialogs:
                        # Prepare data with proper quoting
                        text_pool = dialog.get('text_pool', '')
                        choices = dialog.get('choices', [])
                        effects = dialog.get('effects', '-')
                        audio = dialog.get('audio', '-')
                        
                        # Quote fields that contain special characters
                        row = {
                            'ID': dialog['id'],
                            'Speaker': dialog['speaker'],
                            'TextPool': f'"{text_pool}"' if '|' in text_pool or '*' in text_pool else text_pool,
                            'PlayerChoices': f'{"|".join(choices)}' if any('➔' in c or '[' in c for c in choices) else "|".join(choices),
                            'Effects': effects if effects == '-' else f'"{effects}"',
                            'Emotion': dialog.get('emotion', 'neutral'),
                            'Audio': audio
                        }
                        
                        writer.writerow(row)
                
                QMessageBox.information(self, "Success", f"Dialogs saved to {self.current_file}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save CSV: {str(e)}")
    
    def add_dialog_node(self, start_id=None):
        if start_id is None:
            # Находим следующий доступный ID
            start_id = 1
            while start_id in self.tree.dialogs:
                start_id += 1
        
        new_dialog = {
            'id': start_id,
            'speaker': "New Speaker",
            'text_pool': "",
            'choices': [],
            'effects': "-",
            'emotion': "neutral",
            'audio': "-"
        }
        
        self.tree.add_dialog(new_dialog)
        self.editor.load_node(new_dialog)
    
    def delete_node(self, dialog_id):
        reply = QMessageBox.question(
            self, 'Delete Dialog',
            f"Are you sure you want to delete dialog {dialog_id}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.tree.delete_dialog(dialog_id)
            self.editor.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = DialogEditor()
    editor.show()
    sys.exit(app.exec_())
    