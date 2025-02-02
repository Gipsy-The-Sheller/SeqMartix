import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QListWidget, QTableWidget,
                             QTableWidgetItem, QFileDialog, QLabel, QListWidgetItem,
                             QInputDialog, QMessageBox, QSplitter, QLineEdit, QDialog, QTextEdit)
from PyQt5.QtCore import Qt, QEvent, QThread, pyqtSignal
from Bio import SeqIO, Entrez
import os


# Set your email here
Entrez.email = "your_email@example.com"

# class LogDialog(QDialog):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.setWindowTitle("Download Log")
#         self.setModal(True)
#         self.resize(400, 300)
#         layout = QVBoxLayout(self)
#         self.log_text = QTextEdit(self)
#         self.log_text.setReadOnly(True)
#         layout.addWidget(self.log_text)

#     def append_log(self, message):
#         self.log_text.append(message)

class DownloadThread(QThread):
    log_signal = pyqtSignal(str)
    
    def __init__(self, sequences, table, parent=None):
        super().__init__(parent)
        self.sequences = sequences
        self.table = table

    def run(self):
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    accession = item.text().strip()
                    if accession:
                        try:
                            with Entrez.efetch(db="nucleotide", id=accession, rettype="gb", retmode="text") as handle:
                                record = SeqIO.read(handle, "genbank")
                                full_id = record.id + " " + record.description[len(record.id):].strip()
                                self.sequences[full_id] = str(record.seq)
                                self.log_signal.emit(f"[LOG] Downloaded sequence: {full_id}")
                        except Exception as e:
                            self.log_signal.emit(f"[ERROR] Failed to download {accession}: {e}")

class SequenceItem(QListWidgetItem):
    def __init__(self, name, sequence):
        super().__init__(name)
        self.sequence = sequence
        # Enable drag
        self.setFlags(self.flags() | Qt.ItemIsDragEnabled)

class CustomTableWidget(QTableWidget):
    def __init__(self, main_window, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main_window = main_window

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            current_row = self.currentRow()
            current_col = self.currentColumn()
            if current_row < self.rowCount() - 1:
                self.setCurrentCell(current_row + 1, current_col)
            else:
                # If it's the last row, add a new row
                self.main_window.addRow()
                self.setCurrentCell(current_row + 1, current_col)
            event.accept()
        elif event.key() == Qt.Key_Tab:
            current_row = self.currentRow()
            current_col = self.currentColumn()
            if current_col < self.columnCount() - 1:
                self.setCurrentCell(current_row, current_col + 1)
            else:
                # If it's the last column, move to the first column of the next row
                if current_row < self.rowCount() - 1:
                    self.setCurrentCell(current_row + 1, 0)
                else:
                    # If it's the last row, add a new row
                    self.main_window.addRow()
                    self.setCurrentCell(current_row + 1, 0)
            event.accept()
        else:
            super().keyPressEvent(event)

    def insertFromMimeData(self, source):
        if source.hasText():
            text = source.text()
            rows = text.split('\n')
            current_row = self.currentRow()
            current_col = self.currentColumn()
            for row_data in rows:
                if row_data.strip() == "":
                    continue
                columns = row_data.split('\t')  # Split by tab to handle multiple columns
                for col_data in columns:
                    if current_col >= self.columnCount():
                        self.main_window.addColumn()
                    self.setItem(current_row, current_col, QTableWidgetItem(col_data))
                    current_col += 1
                current_row += 1
                current_col = self.currentColumn()  # Reset to the starting column for the next row
                if current_row >= self.rowCount():
                    self.main_window.addRow()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sequence Concatenator")
        self.sequences = {}
        self.initUI()
        
    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Use QSplitter instead of QHBoxLayout
        splitter = QSplitter(Qt.Horizontal, central_widget)
        
        # Left layout
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        import_btn = QPushButton("Import FASTA")
        import_btn.clicked.connect(self.importFasta)
        download_btn = QPushButton("Download from NCBI")
        download_btn.clicked.connect(self.downloadFromNCBI)
        self.seq_list = QListWidget()
        # Enable drag
        self.seq_list.setDragEnabled(True)
        self.seq_list.setDragDropMode(QListWidget.DragOnly)
        
        left_layout.addWidget(import_btn)
        left_layout.addWidget(download_btn)
        left_layout.addWidget(QLabel("Available Sequences:"))
        left_layout.addWidget(self.seq_list)
        
        # Right layout
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        table_controls = QHBoxLayout()
        add_row_btn = QPushButton("Add Row")
        add_col_btn = QPushButton("Add Column")
        rename_row_btn = QPushButton("Rename Row")
        rename_col_btn = QPushButton("Rename Column")
        export_btn = QPushButton("Export Files")
        format_btn = QPushButton("Format Cells")
        
        add_row_btn.clicked.connect(self.addRow)
        add_col_btn.clicked.connect(self.addColumn)
        rename_row_btn.clicked.connect(self.renameRow)
        rename_col_btn.clicked.connect(self.renameColumn)
        export_btn.clicked.connect(self.exportFiles)
        format_btn.clicked.connect(self.formatCells)
        
        table_controls.addWidget(add_row_btn)
        table_controls.addWidget(add_col_btn)
        table_controls.addWidget(rename_row_btn)
        table_controls.addWidget(rename_col_btn)
        table_controls.addWidget(export_btn)
        table_controls.addWidget(format_btn)
        
        self.table = CustomTableWidget(self)
        self.table.setRowCount(5)
        self.table.setColumnCount(3)
        
        # 设置表格内容的字体大小
        font = self.table.font()
        font.setPointSize(8)  # 将字号设置为8，可以根据需要调整
        self.table.setFont(font)
        
        # Enable drop
        self.table.setAcceptDrops(True)
        self.table.setDragDropMode(QTableWidget.DropOnly)
        
        # Initialize table headers
        for i in range(self.table.columnCount()):
            self.table.setHorizontalHeaderItem(i, QTableWidgetItem(f"Partition_{i+1}"))
        for i in range(self.table.rowCount()):
            self.table.setVerticalHeaderItem(i, QTableWidgetItem(f"Sequence_{i+1}"))
        
        # Connect double-click signals to rename functions
        self.table.horizontalHeader().sectionDoubleClicked.connect(self.renameColumn)
        self.table.verticalHeader().sectionDoubleClicked.connect(self.renameRow)
        
        right_layout.addLayout(table_controls)
        right_layout.addWidget(self.table)
        
        # Add widgets to splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        
        # Set initial sizes for the splitter
        splitter.setSizes([200, 600])  # Adjust these values to set the initial proportion

        # Set the layout for the central widget
        layout = QVBoxLayout(central_widget)
        layout.addWidget(splitter)

        # Enable drag for the sequence list
        self.seq_list.setDragEnabled(True)
        self.seq_list.setDragDropMode(QListWidget.DragOnly)
        
        # Enable drop for the table
        self.table.setAcceptDrops(True)
        self.table.setDragDropMode(QTableWidget.DropOnly)
        self.table.viewport().setAcceptDrops(True)  # Ensure the viewport accepts drops

        # Install event filter if necessary
        self.table.installEventFilter(self)

    def formatCells(self):
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    text = item.text()
                    lines = text.split('\n')
                    # Ensure there are enough rows to accommodate the lines
                    while row + len(lines) > self.table.rowCount():
                        self.addRow()
                    for i, line in enumerate(lines):
                        if i == 0:
                            item.setText(line)  # Set the first line in the current cell
                        else:
                            # Move subsequent lines to the cells below
                            self.table.setItem(row + i, col, QTableWidgetItem(line))

    def downloadFromNCBI(self):
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    accession = item.text().strip()
                    if accession:
                        try:
                            with Entrez.efetch(db="nucleotide", id=accession, rettype="gb", retmode="text") as handle:
                                record = SeqIO.read(handle, "genbank")
                                full_id = record.id + " " + record.description[len(record.id):].strip()
                                self.sequences[full_id] = str(record.seq)
                                self.seq_list.addItem(SequenceItem(full_id, str(record.seq)))
                                # Update the table cell with the full sequence ID
                                item.setText(full_id)
                                print(f"[LOG] Downloaded sequence: {full_id}")
                        except Exception as e:
                            print(f"[ERROR] Failed to download {accession}: {e}")
        
        self.download_thread = DownloadThread(self.sequences, self.table)
        self.download_thread.start()

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            pos = event.pos()
            row = self.table.rowAt(pos.y())
            col = self.table.columnAt(pos.x())
            
            # Check if the drop is within a valid cell
            if row >= 0 and col >= 0 and row < self.table.rowCount() and col < self.table.columnCount():
                # Get dragged sequence item
                source_item = self.seq_list.currentItem()
                if source_item:
                    new_item = QTableWidgetItem(source_item.text())
                    # Store the sequence in the item's data
                    new_item.setData(Qt.UserRole, source_item.sequence)
                    self.table.setItem(row, col, new_item)
                    print(f"[LOG] Added sequence {source_item.text()} to position ({row}, {col})")
                    # Print the current dataset after each successful drop
                    self.printCurrentDataset()
                event.accept()
            else:
                event.ignore()
        else:
            event.ignore()
        
    def importFasta(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select FASTA files", "", "FASTA files (*.fas *.fasta)")
        for file in files:
            for record in SeqIO.parse(file, "fasta"):
                # Save full sequence ID with spaces
                full_id = record.id + " " + record.description[len(record.id):].strip()
                self.sequences[full_id] = str(record.seq)
                self.seq_list.addItem(SequenceItem(full_id, str(record.seq)))
                print(f"[LOG] Imported sequence: {full_id}")
                
    def addRow(self):
        current_rows = self.table.rowCount()
        self.table.setRowCount(current_rows + 1)
        self.table.setVerticalHeaderItem(current_rows, QTableWidgetItem(f"Sequence_{current_rows+1}"))
        print(f"[LOG] Added new row, current rows: {current_rows + 1}")
        
    def addColumn(self):
        current_cols = self.table.columnCount()
        self.table.setColumnCount(current_cols + 1)
        self.table.setHorizontalHeaderItem(current_cols, QTableWidgetItem(f"Partition_{current_cols+1}"))
        print(f"[LOG] Added new column, current columns: {current_cols + 1}")

    def renameRow(self, index=None):
        if index is None:
            index = self.table.currentRow()
        if index >= 0 and index < self.table.rowCount():
            item = self.table.verticalHeaderItem(index)
            if item:
                text, ok = QInputDialog.getText(self, "Rename Row", "Enter new name:", 
                                                text=item.text())
                if ok and text:
                    self.table.setVerticalHeaderItem(index, QTableWidgetItem(text))
                    print(f"[LOG] Renamed row {index + 1} to: {text}")

    def renameColumn(self, index=None):
        if index is None:
            index = self.table.currentColumn()
        if index >= 0 and index < self.table.columnCount():
            item = self.table.horizontalHeaderItem(index)
            if item:
                text, ok = QInputDialog.getText(self, "Rename Column", "Enter new name:",
                                                text=item.text())
                if ok and text:
                    self.table.setHorizontalHeaderItem(index, QTableWidgetItem(text))
                    print(f"[LOG] Renamed column {index + 1} to: {text}")
                
    def printCurrentDataset(self):
        print("\n[CURRENT DATASET]")
        for row in range(self.table.rowCount()):
            row_data = []
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    sequence = item.data(Qt.UserRole)
                    if sequence:
                        row_data.append(f"{len(sequence)}bp")
                    else:
                        row_data.append("empty")
                else:
                    row_data.append("empty")
            print(f"Row {row+1}: {' | '.join(row_data)}")
        print()
        
    def exportFiles(self):
        self.printCurrentDataset()
        try:
            save_dir = QFileDialog.getExistingDirectory(self, "Select Save Directory")
            if not save_dir:
                return
                
            # Export individual gene files
            for col in range(self.table.columnCount()):
                sequences = []
                partition_item = self.table.horizontalHeaderItem(col)
                partition_name = partition_item.text() if partition_item else f"Partition_{col+1}"
                has_sequences = False
                
                for row in range(self.table.rowCount()):
                    item = self.table.item(row, col)
                    if item:
                        sequence_name = item.text()
                        sequence = self.sequences.get(sequence_name)
                        if sequence:
                            row_item = self.table.verticalHeaderItem(row)
                            row_name = row_item.text() if row_item else f"Sequence_{row+1}"
                            sequences.append(f">{row_name}\n{sequence}\n")
                            has_sequences = True
                
                if has_sequences:
                    file_path = os.path.join(save_dir, f"{partition_name}.fas")
                    with open(file_path, "w", encoding='utf-8') as f:
                        f.writelines(sequences)
                    print(f"[LOG] Exported partition file: {file_path}")
                        
            # Export NEXUS file
            nexus_path = os.path.join(save_dir, "concatenated.nex")
            with open(nexus_path, "w", encoding='utf-8') as f:
                f.write("#NEXUS\n")
                f.write("BEGIN DATA;\n")
                
                # Calculate total chars and get sequence lengths
                total_chars = 0
                col_lengths = []
                for col in range(self.table.columnCount()):
                    col_len = 0
                    for row in range(self.table.rowCount()):
                        item = self.table.item(row, col)
                        if item:
                            sequence_name = item.text()
                            sequence = self.sequences.get(sequence_name)
                            if sequence:
                                col_len = len(sequence)
                                break
                    col_lengths.append(col_len)
                    total_chars += col_len
                
                # Get valid sequence count
                valid_rows = 0
                for row in range(self.table.rowCount()):
                    for col in range(self.table.columnCount()):
                        item = self.table.item(row, col)
                        if item and self.sequences.get(item.text()):
                            valid_rows += 1
                            break
                            
                f.write(f"DIMENSIONS NTAX={valid_rows} NCHAR={total_chars};\n")
                f.write("FORMAT DATATYPE=DNA MISSING=? GAP=-;\n")
                f.write("MATRIX\n")
                
                # Output sequence matrix
                for row in range(self.table.rowCount()):
                    seq = ""
                    has_sequence = False
                    for col in range(self.table.columnCount()):
                        item = self.table.item(row, col)
                        if item:
                            sequence_name = item.text()
                            sequence = self.sequences.get(sequence_name)
                            if sequence:
                                seq += sequence
                                has_sequence = True
                            else:
                                seq += "?" * col_lengths[col]  # Fill with '?' for missing genes
                        else:
                            seq += "?" * col_lengths[col]  # Fill with '?' for missing genes
                    
                    row_item = self.table.verticalHeaderItem(row)
                    row_name = row_item.text() if row_item else f"Sequence_{row+1}"
                    if has_sequence:  # Only output rows with at least one sequence
                        f.write(f"{row_name:<30} {seq}\n")
                        
                f.write(";\nEND;\n")
                
                # Add partition information
                f.write("\nBEGIN SETS;\n")
                start = 1
                for col in range(self.table.columnCount()):
                    if col_lengths[col] > 0:  # Only output partitions with sequences
                        end = start + col_lengths[col] - 1
                        partition_item = self.table.horizontalHeaderItem(col)
                        partition_name = partition_item.text() if partition_item else f"Partition_{col+1}"
                        f.write(f"CHARSET {partition_name} = {start}-{end};\n")
                        start = end + 1
                f.write("END;\n")
                
            print(f"[LOG] Exported NEXUS file: {nexus_path}")
            
        except Exception as e:
            print(f"[ERROR] Error exporting files: {str(e)}")

    def eventFilter(self, source, event):
        if event.type() == QEvent.Drop and source is self.table.viewport():
            # Handle drop event only if it's on a valid cell
            pos = event.pos()
            row = self.table.rowAt(pos.y())
            col = self.table.columnAt(pos.x())
            if row >= 0 and col >= 0 and row < self.table.rowCount() and col < self.table.columnCount():
                return False  # Allow the drop event to be processed
            else:
                event.ignore()
                return True
        return super(MainWindow, self).eventFilter(source, event)

    def closeEvent(self, event):
        reply = QMessageBox.question(self, '确认退出',
                                     "你确定要退出吗?",
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())
