"""Custom Vocabulary & Glossary Dialog.

Provides interactive searching, multi-column sorting, alternate spelling mapping,
and live transcript normalization with undo safety.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from terminology import (
    add_alternate_spelling,
    export_glossary_to_csv,
    export_glossary_to_json,
    format_source_variants,
    import_glossary_from_text,
    parse_glossary,
    sort_glossary_entries,
    split_source_variants,
)


class GlossaryDialog(QDialog):
    """Dialog for editing persistent terminology, proper nouns, and alternate spellings."""

    def __init__(self, parent: Optional[Any] = None):
        qparent = parent if isinstance(parent, QWidget) else None
        super().__init__(qparent)
        self.main_win = parent
        self.is_es = bool(getattr(self.main_win, "language", "en") == "es")
        self._init_ui()

    def _init_ui(self):
        title = "Vocabulario personalizado / glosario" if self.is_es else "Custom Vocabulary / Glossary"
        desc = (
            "Defina la forma preferida de cada término. Marque 'No traducir' para nombres propios, programas o marcas que deben conservarse exactamente en las traducciones."
            if self.is_es else
            "Define the preferred spelling for each term. Check 'Don't translate' for proper nouns, program names, brands, or other terms that must remain unchanged in translations."
        )
        example_text = (
            "Ejemplo: atrévete → Atrévete | Kimberlei Davis, Kimberley Davis → Kimberlei Davis"
            if self.is_es else
            "Example: atrevete → Atrévete | Kimberlei Davis, Kimberley Davis → Kimberlei Davis"
        )

        self.setWindowTitle(title)
        self.resize(840, 540)
        layout = QVBoxLayout(self)

        help_label = QLabel(desc)
        help_label.setWordWrap(True)
        layout.addWidget(help_label)

        example_label = QLabel(example_text)
        example_label.setStyleSheet("color: palette(mid); font-style: italic;")
        layout.addWidget(example_label)

        # Top Controls Row: Search & Sort
        top_bar = QHBoxLayout()

        search_placeholder = "Buscar términos de origen o preferidos..." if self.is_es else "Search source or preferred terms..."
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(search_placeholder)
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._apply_filter)
        top_bar.addWidget(self.search_input, 2)

        sort_label = QLabel("Ordenar:" if self.is_es else "Sort:")
        top_bar.addWidget(sort_label)

        self.sort_combo = QComboBox()
        self.sort_modes = [
            ("alpha_asc", "Término / variantes (A-Z)" if self.is_es else "Source / Alternate Spellings (A-Z)"),
            ("alpha_desc", "Término / variantes (Z-A)" if self.is_es else "Source / Alternate Spellings (Z-A)"),
            ("preferred_asc", "Ortografía preferida (A-Z)" if self.is_es else "Preferred Spelling (A-Z)"),
            ("preferred_desc", "Ortografía preferida (Z-A)" if self.is_es else "Preferred Spelling (Z-A)"),
            ("dnt_first", "No traducir primero" if self.is_es else "Protected (Don't Translate) First"),
            ("match_case_first", "Distinguir mayúsculas primero" if self.is_es else "Case-Sensitive (Match Case) First"),
        ]
        for mode, lbl in self.sort_modes:
            self.sort_combo.addItem(lbl, mode)
        self.sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        top_bar.addWidget(self.sort_combo, 1)

        layout.addLayout(top_bar)

        # 4-Column Table
        source_text = "Término de origen / variantes" if self.is_es else "Source / Alternate Spellings"
        preferred_text = "Ortografía preferida" if self.is_es else "Preferred spelling"
        dnt_text = "No traducir" if self.is_es else "Don't translate"
        mc_text = "Distinguir mayúsculas" if self.is_es else "Match case"

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels([source_text, preferred_text, dnt_text, mc_text])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        layout.addWidget(self.table, 1)

        # Action Buttons Row 1
        add_text = "Añadir término" if self.is_es else "Add Term"
        remove_text = "Eliminar seleccionado" if self.is_es else "Remove Selected"
        import_text = "Importar..." if self.is_es else "Import..."
        export_text = "Exportar..." if self.is_es else "Export..."
        apply_now_text = "Aplicar a transcripción actual" if self.is_es else "Apply to Current Transcript"

        row1 = QHBoxLayout()
        self.add_btn = QPushButton(add_text)
        self.remove_btn = QPushButton(remove_text)
        self.import_btn = QPushButton(import_text)
        self.export_btn = QPushButton(export_text)
        self.apply_now_btn = QPushButton(apply_now_text)

        has_transcript = bool(getattr(self.main_win, "transcript", None) and getattr(self.main_win, "transcript", {}).get("segments"))
        self.apply_now_btn.setEnabled(has_transcript)

        self.add_btn.clicked.connect(lambda: self.add_row("", "", True, False))
        self.remove_btn.clicked.connect(self.remove_rows)
        self.import_btn.clicked.connect(self.import_glossary_file)
        self.export_btn.clicked.connect(self.export_glossary_file)
        self.apply_now_btn.clicked.connect(self._apply_to_current_transcript)

        row1.addWidget(self.add_btn)
        row1.addWidget(self.remove_btn)
        row1.addSpacing(10)
        row1.addWidget(self.import_btn)
        row1.addWidget(self.export_btn)
        row1.addSpacing(10)
        row1.addWidget(self.apply_now_btn)
        row1.addStretch()
        layout.addLayout(row1)

        # Bottom Buttons Row 2
        row2 = QHBoxLayout()
        auto_apply_text = "Aplicar a la transcripción al guardar" if self.is_es else "Apply to current transcript on Save"
        self.auto_apply_cb = QCheckBox(auto_apply_text)
        self.auto_apply_cb.setChecked(has_transcript)
        self.auto_apply_cb.setEnabled(has_transcript)
        row2.addWidget(self.auto_apply_cb)

        row2.addStretch()
        cancel_text = "Cancelar" if self.is_es else "Cancel"
        save_text = "Guardar" if self.is_es else "Save"
        self.cancel_btn = QPushButton(cancel_text)
        self.save_btn = QPushButton(save_text)
        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn.clicked.connect(self.save_glossary)
        row2.addWidget(self.cancel_btn)
        row2.addWidget(self.save_btn)
        layout.addLayout(row2)

        # Populate initial entries
        initial_entries = parse_glossary(getattr(self.main_win, "glossary", []))
        sorted_entries = sort_glossary_entries(initial_entries, mode="alpha_asc")
        self._populate_table(sorted_entries)

    def _populate_table(self, entries: list[dict[str, Any]]):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        for entry in entries:
            self._insert_entry_row(entry)
        self.table.setSortingEnabled(True)
        self._apply_filter(self.search_input.text())

    def _insert_entry_row(self, entry: dict[str, Any], row_idx: Optional[int] = None) -> int:
        if row_idx is None:
            row_idx = self.table.rowCount()
        self.table.insertRow(row_idx)

        src = str(entry.get("source", ""))
        pref = str(entry.get("preferred", ""))
        dnt = bool(entry.get("do_not_translate", True))
        mc = bool(entry.get("match_case", False))

        self.table.setItem(row_idx, 0, QTableWidgetItem(src))
        self.table.setItem(row_idx, 1, QTableWidgetItem(pref))

        dnt_item = QTableWidgetItem()
        dnt_item.setFlags(dnt_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        dnt_item.setCheckState(Qt.CheckState.Checked if dnt else Qt.CheckState.Unchecked)
        self.table.setItem(row_idx, 2, dnt_item)

        mc_item = QTableWidgetItem()
        mc_item.setFlags(mc_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        mc_item.setCheckState(Qt.CheckState.Checked if mc else Qt.CheckState.Unchecked)
        self.table.setItem(row_idx, 3, mc_item)
        return row_idx

    def add_row(self, source_val: str = "", preferred_val: str = "", dnt_val: bool = True, mc_val: bool = False):
        self.table.setSortingEnabled(False)
        row = self._insert_entry_row({
            "source": source_val,
            "preferred": preferred_val,
            "do_not_translate": dnt_val,
            "match_case": mc_val,
        })
        self.table.setSortingEnabled(True)
        self.table.setCurrentCell(row, 0)
        if not source_val and not preferred_val:
            self.table.editItem(self.table.item(row, 0))

    def remove_rows(self):
        selected_rows = sorted({idx.row() for idx in self.table.selectionModel().selectedRows()}, reverse=True)
        if not selected_rows:
            return
        self.table.setSortingEnabled(False)
        for row in selected_rows:
            self.table.removeRow(row)
        self.table.setSortingEnabled(True)

    def _apply_filter(self, query: str):
        q = (query or "").strip().casefold()
        for row in range(self.table.rowCount()):
            if not q:
                self.table.setRowHidden(row, False)
                continue
            src_item = self.table.item(row, 0)
            pref_item = self.table.item(row, 1)
            src_text = (src_item.text() if src_item else "").casefold()
            pref_text = (pref_item.text() if pref_item else "").casefold()
            matches = (q in src_text) or (q in pref_text)
            self.table.setRowHidden(row, not matches)

    def _on_sort_changed(self, index: int):
        mode = self.sort_combo.itemData(index) or "alpha_asc"
        entries = self.get_current_table_entries()
        sorted_entries = sort_glossary_entries(entries, mode=mode)
        self._populate_table(sorted_entries)

    def _show_context_menu(self, pos: QPoint):
        item = self.table.itemAt(pos)
        if not item:
            return
        row = item.row()
        src_item = self.table.item(row, 0)
        pref_item = self.table.item(row, 1)
        src_txt = (src_item.text() if src_item else "").strip()
        pref_txt = (pref_item.text() if pref_item else "").strip()

        menu = QMenu(self)

        alt_act = QAction("Añadir ortografía alternativa..." if self.is_es else "Add Alternate Spelling...", self)
        def _add_alt():
            title = "Añadir ortografía alternativa" if self.is_es else "Add Alternate Spelling"
            prompt = (
                f"Escriba ortografías alternativas para '{pref_txt or src_txt}' (separadas por comas):"
                if self.is_es else
                f"Enter alternate spelling(s) for '{pref_txt or src_txt}' (comma-separated):"
            )
            text, ok = QInputDialog.getText(self, title, prompt)
            if ok and text.strip():
                existing_variants = split_source_variants(src_txt, preferred=pref_txt)
                new_variants = split_source_variants(text.strip())
                combined = existing_variants + new_variants
                formatted = format_source_variants(combined)
                if src_item:
                    src_item.setText(formatted)

        alt_act.triggered.connect(_add_alt)
        menu.addAction(alt_act)

        dup_act = QAction("Duplicar término como nueva fila" if self.is_es else "Duplicate Term as New Row", self)
        def _dup_row():
            dnt_item = self.table.item(row, 2)
            mc_item = self.table.item(row, 3)
            dnt = bool(dnt_item and dnt_item.checkState() == Qt.CheckState.Checked)
            mc = bool(mc_item and mc_item.checkState() == Qt.CheckState.Checked)
            self.table.setSortingEnabled(False)
            new_row = self._insert_entry_row({
                "source": src_txt,
                "preferred": pref_txt,
                "do_not_translate": dnt,
                "match_case": mc,
            }, row_idx=row + 1)
            self.table.setSortingEnabled(True)
            self.table.setCurrentCell(new_row, 0)
            target = self.table.item(new_row, 0)
            if target:
                self.table.editItem(target)

        dup_act.triggered.connect(_dup_row)
        menu.addAction(dup_act)

        menu.addSeparator()
        del_act = QAction("Eliminar seleccionado" if self.is_es else "Remove Selected", self)
        del_act.triggered.connect(self.remove_rows)
        menu.addAction(del_act)

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def get_current_table_entries(self) -> list[dict[str, Any]]:
        """Collect all table rows including hidden ones without data loss."""
        entries_out: list[dict[str, Any]] = []
        seen = set()
        for row in range(self.table.rowCount()):
            src_item = self.table.item(row, 0)
            pref_item = self.table.item(row, 1)
            source = (src_item.text() if src_item else "").strip()
            preferred = (pref_item.text() if pref_item else "").strip()
            if not source and not preferred:
                continue
            if not source:
                source = preferred
            if not preferred:
                preferred = source

            dnt_item = self.table.item(row, 2)
            dnt = bool(dnt_item and dnt_item.checkState() == Qt.CheckState.Checked)

            mc_item = self.table.item(row, 3)
            mc = bool(mc_item and mc_item.checkState() == Qt.CheckState.Checked)

            key = (source if mc else source.casefold(), preferred if mc else preferred.casefold(), mc)
            if key in seen:
                continue
            seen.add(key)
            entries_out.append({
                "source": source,
                "preferred": preferred,
                "do_not_translate": dnt,
                "match_case": mc,
            })
        return entries_out

    def _apply_to_current_transcript(self):
        if hasattr(self.main_win, "apply_glossary_to_current_transcript"):
            entries = self.get_current_table_entries()
            applied = self.main_win.apply_glossary_to_current_transcript(entries)
            if applied:
                QMessageBox.information(
                    self,
                    "Transcripción normalizada" if self.is_es else "Transcript Normalized",
                    "Se aplicaron los términos del glosario a la transcripción actual."
                    if self.is_es else
                    "Glossary terms and contextual spellings were applied to the current transcript."
                )
            else:
                QMessageBox.information(
                    self,
                    "Sin cambios" if self.is_es else "No Changes",
                    "No se requirieron cambios en la transcripción actual."
                    if self.is_es else
                    "No changes were needed for the current transcript."
                )

    def save_glossary(self):
        entries_out = self.get_current_table_entries()
        if self.main_win is not None:
            self.main_win.glossary = entries_out
            if hasattr(self.main_win, "_save_glossary"):
                self.main_win._save_glossary()
            if hasattr(self.main_win, "apply_glossary_to_whisper_context"):
                self.main_win.apply_glossary_to_whisper_context()
            if self.auto_apply_cb.isChecked() and hasattr(self.main_win, "apply_glossary_to_current_transcript"):
                self.main_win.apply_glossary_to_current_transcript(entries_out)
            if hasattr(self.main_win, "statusBar") and self.main_win.statusBar():
                self.main_win.statusBar().showMessage(
                    "Glosario guardado" if self.is_es else "Glossary saved"
                )
        self.accept()

    def export_glossary_file(self):
        entries = self.get_current_table_entries()
        if not entries:
            QMessageBox.information(
                self,
                "Exportar glosario" if self.is_es else "Export Glossary",
                "No hay términos en el glosario para exportar." if self.is_es else "There are no glossary entries to export."
            )
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar vocabulario personalizado / glosario" if self.is_es else "Export Custom Vocabulary / Glossary",
            "glossary.json",
            "JSON Files (*.json);;CSV Files (*.csv);;All Files (*)"
        )
        if not file_path:
            return
        try:
            if file_path.lower().endswith(".csv"):
                content = export_glossary_to_csv(entries)
            else:
                content = export_glossary_to_json(entries)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            QMessageBox.information(
                self,
                "Exportación completada" if self.is_es else "Export Complete",
                f"Se exportaron con éxito {len(entries)} términos a:\n{file_path}"
                if self.is_es else
                f"Successfully exported {len(entries)} glossary entries to:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error de exportación" if self.is_es else "Export Error",
                f"Error al exportar glosario:\n{e}" if self.is_es else f"Failed to export glossary:\n{e}"
            )

    def import_glossary_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Importar vocabulario personalizado / glosario" if self.is_es else "Import Custom Vocabulary / Glossary",
            "",
            "Glossary Files (*.json *.csv *.tsv *.txt);;All Files (*)"
        )
        if not file_path:
            return
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            imported = import_glossary_from_text(content)
            if not imported:
                QMessageBox.warning(
                    self,
                    "Importar glosario" if self.is_es else "Import Glossary",
                    "No se encontraron términos válidos en el archivo seleccionado."
                    if self.is_es else
                    "No valid glossary entries found in the selected file."
                )
                return

            existing = self.get_current_table_entries()
            existing_keys = {
                (e["source"].casefold(), e["preferred"].casefold(), e.get("match_case", False))
                for e in existing
            }
            added = 0
            for entry in imported:
                key = (
                    str(entry.get("source", "")).casefold(),
                    str(entry.get("preferred", "")).casefold(),
                    bool(entry.get("match_case", False)),
                )
                if key not in existing_keys:
                    existing_keys.add(key)
                    existing.append(entry)
                    added += 1

            self._populate_table(sort_glossary_entries(existing, mode=self.sort_combo.currentData() or "alpha_asc"))
            QMessageBox.information(
                self,
                "Importación completada" if self.is_es else "Import Complete",
                f"Se importaron {added} nuevos términos de:\n{file_path}"
                if self.is_es else
                f"Imported {added} new entries from:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error de importación" if self.is_es else "Import Error",
                f"Error al importar glosario:\n{e}" if self.is_es else f"Failed to import glossary:\n{e}"
            )
