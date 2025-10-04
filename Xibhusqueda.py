# buscador_pdfs_pyside6.py
import sys
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Set

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QFileDialog, QMessageBox, QLineEdit, QLabel, QProgressBar, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QInputDialog
)
from PySide6.QtCore import Qt, QThread, Signal

import PyPDF2

# --------- Worker Thread ----------
class SearchWorker(QThread):
    update_progress = Signal(int, int)  # processed, total
    found_pdf = Signal(str, str)  # keyword, pdf_path
    log_message = Signal(str)
    finished_search = Signal()
    
    def __init__(self, folders: List[str], keywords: List[str], output_dir: str, parent=None):
        super().__init__(parent)
        self.folders = folders
        self.keywords = [k.strip() for k in keywords if k.strip()]
        self.output_dir = output_dir
        self._is_running = True

    def run(self):
        try:
            pdf_paths = self._gather_pdfs(self.folders)
            total = len(pdf_paths)
            processed = 0
            self.log_message.emit(f"Iniciando búsqueda: {total} PDF(s) a revisar.")
            
            # Keep a set of keywords found to avoid repeated logging per PDF if you prefer
            for pdf in pdf_paths:
                if not self._is_running:
                    self.log_message.emit("Búsqueda cancelada por el usuario.")
                    break
                processed += 1
                try:
                    matches = self._check_pdf_for_keywords(pdf, self.keywords)
                    if matches:
                        # For each matched keyword emit a found signal (one per keyword)
                        for kw in matches:
                            self.found_pdf.emit(kw, pdf)
                        self.log_message.emit(f"[{processed}/{total}] Encontrado en: {pdf} -> {', '.join(matches)}")
                    else:
                        self.log_message.emit(f"[{processed}/{total}] No encontrado en: {pdf}")
                except Exception as e:
                    self.log_message.emit(f"Error procesando {pdf}: {e}")
                self.update_progress.emit(processed, total)
        finally:
            self.finished_search.emit()

    def stop(self):
        self._is_running = False

    def _gather_pdfs(self, folders: List[str]) -> List[str]:
        pdf_list = []
        for folder in folders:
            for root, _, files in os.walk(folder):
                for f in files:
                    if f.lower().endswith(".pdf"):
                        pdf_list.append(os.path.join(root, f))
        return pdf_list

    def _check_pdf_for_keywords(self, pdf_path: str, keywords: List[str]) -> Set[str]:
        matched = set()
        with open(pdf_path, "rb") as fh:
            reader = PyPDF2.PdfReader(fh)
            # Iterate pages one by one and stop early if all keywords matched
            for page in reader.pages:
                if not self._is_running:
                    break
                try:
                    text = page.extract_text() or ""
                except Exception:
                    text = ""
                if not text:
                    continue
                text_lower = " ".join(text.split()).lower()
                for kw in keywords:
                    if kw.lower() in text_lower:
                        matched.add(kw)
                # small optimization: if all keywords matched, break
                # (optional; remove if you want to find duplicates across PDF)
                # if len(matched) == len(keywords):
                #     break
        return matched

# --------- Main Application ----------
class PDFSearcherApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("XibhusquedaPDF")
        self.resize(900, 600)
        
        # Paths relative to this script/executable
        self.base_dir = Path(sys.argv[0]).resolve().parent
        self.output_dir = str(self.base_dir / "PDF")
        os.makedirs(self.output_dir, exist_ok=True)
        self.results_txt = str(self.base_dir / "rutas_encontradas.txt")
        
        self.folders: List[str] = []
        self.keywords: List[str] = []
        
        self.worker: SearchWorker | None = None
        
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Folder controls
        fh_layout = QHBoxLayout()
        btn_add_folder = QPushButton("Añadir carpetas")
        btn_add_folder.clicked.connect(self.add_folders)
        btn_remove_folder = QPushButton("Eliminar carpeta seleccionada")
        btn_remove_folder.clicked.connect(self.remove_selected_folder)
        fh_layout.addWidget(btn_add_folder)
        fh_layout.addWidget(btn_remove_folder)
        layout.addLayout(fh_layout)

        self.list_folders = QListWidget()
        layout.addWidget(QLabel("Carpetas donde buscar:"))
        layout.addWidget(self.list_folders)

        # Keywords controls
        kw_layout = QHBoxLayout()
        btn_load_txt = QPushButton("Cargar .txt (lista de series)")
        btn_load_txt.clicked.connect(self.load_keywords_from_txt)
        btn_add_kw = QPushButton("Añadir manualmente")
        btn_add_kw.clicked.connect(self.add_keyword_manual)
        btn_remove_kw = QPushButton("Eliminar seleccionado")
        btn_remove_kw.clicked.connect(self.remove_selected_keyword)
        kw_layout.addWidget(btn_load_txt)
        kw_layout.addWidget(btn_add_kw)
        kw_layout.addWidget(btn_remove_kw)
        layout.addLayout(kw_layout)

        self.list_keywords = QListWidget()
        layout.addWidget(QLabel("Números de serie / textos a buscar:"))
        layout.addWidget(self.list_keywords)

        # Action buttons
        act_layout = QHBoxLayout()
        self.btn_start = QPushButton("Iniciar búsqueda")
        self.btn_start.clicked.connect(self.start_search)
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.clicked.connect(self.cancel_search)
        self.btn_cancel.setEnabled(False)
        btn_open_output = QPushButton("Abrir carpeta destino")
        btn_open_output.clicked.connect(lambda: os.startfile(self.output_dir) if os.name == "nt" else os.system(f'xdg-open "{self.output_dir}"'))
        act_layout.addWidget(self.btn_start)
        act_layout.addWidget(self.btn_cancel)
        act_layout.addWidget(btn_open_output)
        layout.addLayout(act_layout)

        # Progress and results table
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Texto encontrado", "Archivo copiado (nombre)", "Ruta original"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.table)

        # Bottom: save results button
        bottom_layout = QHBoxLayout()
        btn_save_results = QPushButton("Guardar rutas encontradas ahora")
        btn_save_results.clicked.connect(self.save_results_now)
        bottom_layout.addWidget(btn_save_results)
        layout.addLayout(bottom_layout)

        self.setLayout(layout)

    # ----- Folder management -----
    def add_folders(self):
        folders = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta (Pulse Cancel para seleccionar varias con repetición)...")
        # PySide6 QFileDialog doesn't natively support multi-directory selection across platforms,
        # so allow repeated selection. Alternatively, use native file dialogs in a loop.
        if folders:
            self.folders.append(folders)
            self.list_folders.addItem(folders)

    def remove_selected_folder(self):
        row = self.list_folders.currentRow()
        if row >= 0:
            self.folders.pop(row)
            self.list_folders.takeItem(row)

    # ----- Keywords management -----
    def load_keywords_from_txt(self):
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo .txt", filter="Text Files (*.txt);;All Files (*)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
            # Add ignoring duplicates
            existing = set(self.keywords)
            added = 0
            for l in lines:
                if l not in existing:
                    self.keywords.append(l)
                    self.list_keywords.addItem(l)
                    existing.add(l)
                    added += 1
            QMessageBox.information(self, "Cargado", f"Se han cargado {len(lines)} líneas. {added} nuevas añadidas.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo leer el archivo: {e}")

    def add_keyword_manual(self):
        text, ok = QInputDialog.getText(self, "Añadir texto", "Introduce el número de serie o texto:")
        if ok and text.strip():
            if text.strip() not in self.keywords:
                self.keywords.append(text.strip())
                self.list_keywords.addItem(text.strip())

    def remove_selected_keyword(self):
        row = self.list_keywords.currentRow()
        if row >= 0:
            self.keywords.pop(row)
            self.list_keywords.takeItem(row)

    # ----- Search control -----
    def start_search(self):
        if not self.folders:
            QMessageBox.warning(self, "Atención", "Añade al menos una carpeta donde buscar.")
            return
        if not self.keywords:
            QMessageBox.warning(self, "Atención", "Añade al menos un número de serie / texto a buscar.")
            return

        # Disable UI controls that shouldn't be used during search
        self.btn_start.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.table.setRowCount(0)
        self.progress_bar.setValue(0)

        # Start worker thread
        self.worker = SearchWorker(self.folders, self.keywords, self.output_dir)
        self.worker.update_progress.connect(self._on_progress_update)
        self.worker.found_pdf.connect(self._on_found_pdf)
        self.worker.log_message.connect(self._on_log)
        self.worker.finished_search.connect(self._on_finished_search)
        self.worker.start()

    def cancel_search(self):
        if self.worker:
            self.worker.stop()
            self.btn_cancel.setEnabled(False)

    # ----- Worker signals handlers -----
    def _on_progress_update(self, processed: int, total: int):
        if total > 0:
            percent = int(processed / total * 100)
            self.progress_bar.setValue(percent)
        else:
            self.progress_bar.setValue(0)

    def _on_found_pdf(self, keyword: str, pdf_path: str):
        # Copy the file to output_dir with unique name
        src = Path(pdf_path)
        dest_name = src.name
        dest = Path(self.output_dir) / dest_name
        base = dest.stem
        ext = dest.suffix
        counter = 1
        while dest.exists():
            dest = Path(self.output_dir) / f"{base}({counter}){ext}"
            counter += 1
        try:
            shutil.copy2(src, dest)
        except Exception as e:
            self._on_log(f"Error copiando {src} -> {e}")
            return

        # Add a row to the results table
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(keyword))
        self.table.setItem(row, 1, QTableWidgetItem(dest.name))
        self.table.setItem(row, 2, QTableWidgetItem(str(src)))

        # Append original path to rutas_encontradas.txt
        try:
            with open(self.results_txt, "a", encoding="utf-8") as f:
                f.write(f"{datetime.now().isoformat()} - {keyword} - {src}\n")
        except Exception as e:
            self._on_log(f"Error guardando ruta en {self.results_txt}: {e}")

    def _on_log(self, msg: str):
        # For now, we just print logs to stdout; could be redirected to a GUI log area.
        print(msg)

    def _on_finished_search(self):
        self.btn_start.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.progress_bar.setValue(100)
        QMessageBox.information(self, "Finalizado", "La búsqueda ha terminado (o se ha cancelado).")

    def save_results_now(self):
        # Allow user to save the table to a chosen .txt (optional)
        if self.table.rowCount() == 0:
            QMessageBox.information(self, "Sin resultados", "No hay resultados para guardar.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Guardar rutas encontradas", str(self.base_dir / "rutas_encontradas.txt"), "Text Files (*.txt);;All Files (*)")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                for r in range(self.table.rowCount()):
                    kw = self.table.item(r, 0).text()
                    copied = self.table.item(r, 1).text()
                    original = self.table.item(r, 2).text()
                    f.write(f"{kw} - {copied} - {original}\n")
            QMessageBox.information(self, "Guardado", f"Resultados guardados en {path}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo guardar: {e}")

# --------- Run ----------
def main():
    app = QApplication(sys.argv)
    w = PDFSearcherApp()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
