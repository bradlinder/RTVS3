"""PySide6 Graphical Test Bench Dialog for Radio & TV Story Segmenter.

Provides a graphical user interface for running and monitoring system diagnostic tests,
inspecting hardware health, and exporting diagnostic reports.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Dict, Optional

if TYPE_CHECKING:
    from test_runner import DiagnosticEngine, DiagnosticItem


def create_diagnostic_dialog(parent=None, include_dev_tests: Optional[bool] = None):
    """Builds the Diagnostic Test Bench Qt Dialog."""
    from PySide6.QtCore import Qt, QThread, Signal, QObject
    from PySide6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTreeWidget, QTreeWidgetItem, QProgressBar, QTextEdit,
        QHeaderView, QMessageBox, QFrame
    )
    from PySide6.QtGui import QColor, QFont, QIcon

    from test_runner import DiagnosticEngine, DiagnosticItem, generate_diagnostic_report

    class TestRunnerWorker(QObject):
        item_updated = Signal(object)
        finished = Signal()

        def __init__(self, engine: DiagnosticEngine):
            super().__init__()
            self.engine = engine
            self._is_stopped = False

        def stop(self):
            self._is_stopped = True

        def run(self):
            self.engine.on_update = lambda it: self.item_updated.emit(it)
            self.engine.run_all(stop_requested_fn=lambda: self._is_stopped)
            self.finished.emit()

    class DiagnosticDialog(QDialog):
        def __init__(self, parent=None, include_dev_tests: Optional[bool] = None):
            super().__init__(parent)
            self.setWindowTitle("System Diagnostic Test Bench & Hardware Health")
            self.resize(880, 620)
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)
            self.engine = DiagnosticEngine(include_dev_tests=include_dev_tests)
            self.worker_thread: Optional[QThread] = None
            self.worker: Optional[TestRunnerWorker] = None

            layout = QVBoxLayout(self)
            layout.setContentsMargins(16, 16, 16, 16)
            layout.setSpacing(12)

            # Top Header Card
            header_layout = QVBoxLayout()
            title_lbl = QLabel("System Diagnostic Test Bench")
            title_font = QFont()
            title_font.setPointSize(14)
            title_font.setBold(True)
            title_lbl.setFont(title_font)
            header_layout.addWidget(title_lbl)

            subtitle_lbl = QLabel(
                "Executes comprehensive health checks across audio engines, subtitle formatters, "
                "AI runtime frameworks, model storage pipelines, and boundary detectors."
            )
            subtitle_lbl.setWordWrap(True)
            subtitle_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
            header_layout.addWidget(subtitle_lbl)
            layout.addLayout(header_layout)

            # Progress Bar
            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, len(self.engine.items))
            self.progress_bar.setValue(0)
            self.progress_bar.setTextVisible(True)
            self.progress_bar.setFormat("%v / %m Tests Completed")
            layout.addWidget(self.progress_bar)

            # Category / Test Tree
            self.tree = QTreeWidget()
            self.tree.setHeaderLabels(["Test Name", "Status", "Duration", "Result Summary"])
            self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            self.tree.header().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
            self.tree.setAlternatingRowColors(True)
            layout.addWidget(self.tree, 1)

            # Populate Tree Categories
            self.category_nodes: Dict[str, QTreeWidgetItem] = {}
            self.item_nodes: Dict[str, QTreeWidgetItem] = {}

            for cat in self.engine.CATEGORIES:
                cat_node = QTreeWidgetItem(self.tree, [cat, "", "", ""])
                f = cat_node.font(0)
                f.setBold(True)
                cat_node.setFont(0, f)
                cat_node.setExpanded(True)
                self.category_nodes[cat] = cat_node

            for it in self.engine.items:
                cat_node = self.category_nodes.get(it.category, self.tree.invisibleRootItem())
                node = QTreeWidgetItem(cat_node, [it.name, "Ready", "—", it.description])
                self.item_nodes[it.name] = node

            # Bottom Controls & Buttons
            bottom_layout = QHBoxLayout()

            self.status_lbl = QLabel("Ready to run diagnostics.")
            self.status_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
            bottom_layout.addWidget(self.status_lbl)
            bottom_layout.addStretch()

            self.run_btn = QPushButton("▶ Run All Diagnostics")
            self.run_btn.setMinimumHeight(32)
            self.run_btn.clicked.connect(self.start_diagnostics)
            bottom_layout.addWidget(self.run_btn)

            self.stop_btn = QPushButton("Stop")
            self.stop_btn.setEnabled(False)
            self.stop_btn.clicked.connect(self.stop_diagnostics)
            bottom_layout.addWidget(self.stop_btn)

            self.export_btn = QPushButton("Copy Report")
            self.export_btn.clicked.connect(self.copy_report)
            bottom_layout.addWidget(self.export_btn)

            self.save_btn = QPushButton("Save Report to File...")
            self.save_btn.clicked.connect(self.save_report)
            bottom_layout.addWidget(self.save_btn)

            self.close_btn = QPushButton("Close")
            self.close_btn.clicked.connect(self.accept)
            bottom_layout.addWidget(self.close_btn)

            layout.addLayout(bottom_layout)

        def start_diagnostics(self):
            if self.worker_thread is not None:
                try:
                    if self.worker_thread.isRunning():
                        return
                except RuntimeError:
                    self.worker_thread = None

            self.run_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.progress_bar.setValue(0)
            self.status_lbl.setText("Running diagnostic tests...")

            # Reset tree display
            for it in self.engine.items:
                node = self.item_nodes.get(it.name)
                if node:
                    node.setText(1, "Pending")
                    node.setText(2, "—")
                    node.setForeground(1, QColor("#94a3b8"))

            self.worker_thread = QThread(self)
            self.worker = TestRunnerWorker(self.engine)
            self.worker.moveToThread(self.worker_thread)

            self.worker_thread.started.connect(self.worker.run)
            self.worker.item_updated.connect(self.on_item_updated)
            self.worker.finished.connect(self.on_diagnostics_finished)
            self.worker.finished.connect(self.worker_thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.worker_thread.finished.connect(self.worker_thread.deleteLater)

            self.worker_thread.start()

        def stop_diagnostics(self):
            if self.worker is not None:
                try:
                    self.worker.stop()
                except RuntimeError:
                    self.worker = None
                self.status_lbl.setText("Stopping tests...")
                self.stop_btn.setEnabled(False)

        def on_item_updated(self, item: DiagnosticItem):
            node = self.item_nodes.get(item.name)
            if not node:
                return

            node.setText(0, item.name)
            node.setText(1, item.status)
            node.setText(2, f"{item.duration_sec:.2f}s" if item.duration_sec > 0 else "—")
            node.setText(3, item.message or item.description)

            # Status Colors
            if item.status == "PASS":
                node.setForeground(1, QColor("#10b981"))  # Green
            elif item.status == "FAIL":
                node.setForeground(1, QColor("#ef4444"))  # Red
            elif item.status == "WARNING":
                node.setForeground(1, QColor("#f59e0b"))  # Amber
            elif item.status == "RUNNING":
                node.setForeground(1, QColor("#38bdf8"))  # Cyan/Blue
            else:
                node.setForeground(1, QColor("#94a3b8"))  # Slate Gray

            # Update overall progress
            completed_count = sum(1 for it in self.engine.items if it.status in ("PASS", "FAIL", "WARNING", "SKIP"))
            self.progress_bar.setValue(completed_count)

        def on_diagnostics_finished(self):
            self.run_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            passed = sum(1 for it in self.engine.items if it.status == "PASS")
            failed = sum(1 for it in self.engine.items if it.status == "FAIL")
            warn = sum(1 for it in self.engine.items if it.status == "WARNING")
            self.status_lbl.setText(f"Diagnostics complete: {passed} passed, {failed} failed, {warn} warnings.")
            self.worker = None
            self.worker_thread = None

        def copy_report(self):
            from PySide6.QtGui import QGuiApplication
            report_text = generate_diagnostic_report(self.engine)
            QGuiApplication.clipboard().setText(report_text)
            QMessageBox.information(
                self,
                "Report Copied",
                "The comprehensive system, pipeline, and diagnostic report has been copied to your clipboard.\n\n"
                "It includes host environment specifications, out-of-process worker status, and actionable troubleshooting guidance."
            )

        def save_report(self):
            from PySide6.QtWidgets import QFileDialog
            report_text = generate_diagnostic_report(self.engine)
            default_name = f"RTVS_Diagnostic_Report_{time.strftime('%Y%m%d_%H%M%S')}.txt"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Diagnostic Report",
                default_name,
                "Text Files (*.txt);;All Files (*)"
            )
            if file_path:
                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(report_text)
                    QMessageBox.information(
                        self,
                        "Report Saved",
                        f"Diagnostic report successfully saved to:\n{file_path}"
                    )
                except Exception as exc:
                    QMessageBox.critical(
                        self,
                        "Error Saving Report",
                        f"Could not write diagnostic report to file:\n{exc}"
                    )

        def closeEvent(self, event):
            try:
                if self.worker_thread is not None:
                    is_running = False
                    try:
                        is_running = self.worker_thread.isRunning()
                    except RuntimeError:
                        is_running = False

                    if is_running:
                        if self.worker is not None:
                            try:
                                self.worker.stop()
                            except RuntimeError:
                                pass
                        self.worker_thread.quit()
                        self.worker_thread.wait(1000)
            except Exception:
                pass
            finally:
                self.worker = None
                self.worker_thread = None
                event.accept()

    return DiagnosticDialog(parent, include_dev_tests=include_dev_tests)
