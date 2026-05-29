# gui/interfaz.py — Ventana principal del compilador Costeñol (PyQt6)
import os
import random
import re

from PyQt6.QtCore import Qt, QDir
from PyQt6.QtGui import QAction, QColor, QFont, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QTabWidget,
    QLabel,
    QPushButton,
    QStatusBar,
    QFileDialog,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QTextEdit,
    QFrame,
    QToolBar,
    QSizePolicy,
    QScrollArea,
)

from gui.temas import (
    C,
    FUENTES,
    alternar_tema,
    cambiar_tema,
    tema_nombre,
    MENSAJES_EXITO,
    MENSAJES_ERROR,
    MENSAJE_SIN_CODIGO,
)
from gui.editor import GestorPestanas

# ── Helpers de formato de texto ───────────────────────────────────────────────


def _html_span(texto: str, color: str, bold: bool = False) -> str:
    w = "font-weight:bold;" if bold else ""
    return f'<span style="color:{color};{w}">{texto}</span>'


def _texto_a_html(texto: str) -> str:
    return texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ── Ventana principal ─────────────────────────────────────────────────────────


class VentanaCompilador(QMainWindow):
    def __init__(self):
        super().__init__()
        cambiar_tema("claro")
        self._construir()

    # ── Construcción general ──────────────────────────────────────────────────

    def _construir(self):
        self.setWindowTitle("COSTEÑOL IDE")
        self.setMinimumSize(920, 560)

        self._construir_menu()
        self._construir_barra_superior()
        self._construir_cuerpo()
        self._construir_barra_estado()
        self._aplicar_estilos_globales()

        from PyQt6.QtCore import QTimer

        QTimer.singleShot(0, self.showMaximized)

    # ── Menú ──────────────────────────────────────────────────────────────────

    def _construir_menu(self):
        mb = self.menuBar()

        # ── Archivo
        m_arch = mb.addMenu("Archivo")
        m_arch.addAction(self._accion("Nueva pestaña", self._nueva_pestana, "Ctrl+T"))
        m_arch.addAction(self._accion("Abrir archivo...", self.abrir_archivo, "Ctrl+O"))
        m_arch.addSeparator()
        m_arch.addAction(self._accion("Guardar", self.guardar_archivo, "Ctrl+S"))
        m_arch.addAction(
            self._accion("Guardar como...", self.guardar_como, "Ctrl+Shift+S")
        )
        m_arch.addSeparator()
        m_arch.addAction(
            self._accion("Cerrar pestaña", self._cerrar_tab_activa, "Ctrl+W")
        )
        m_arch.addSeparator()
        m_arch.addAction(self._accion("Salir", self.close, "Alt+F4"))

        # ── Compilar
        m_comp = mb.addMenu("Compilar")
        m_comp.addAction(self._accion("Compilar", self.compilar, "F5"))
        m_comp.addAction(self._accion("Ejecutar", self.ejecutar, "F9"))
        m_comp.addAction(self._accion("Limpiar", self.limpiar_todo, "F6"))

        # ── Ver
        m_ver = mb.addMenu("Ver")
        m_ver.addAction(
            self._accion("Alternar tema", self._alternar_tema, "Ctrl+Shift+T")
        )

    def _accion(self, nombre: str, slot, atajo: str = None) -> QAction:
        a = QAction(nombre, self)
        if atajo:
            a.setShortcut(QKeySequence(atajo))
        a.triggered.connect(slot)
        return a

    # ── Barra superior ────────────────────────────────────────────────────────

    def _construir_barra_superior(self):
        c = C()
        self._toolbar = QToolBar()
        self._toolbar.setMovable(False)
        self._toolbar.setFloatable(False)
        self._toolbar.setFixedHeight(54)
        self._toolbar.setStyleSheet(f"""
            QToolBar {{
                background: {c['panel']};
                border: none;
                border-bottom: 1px solid {c['borde']};
                padding: 0 12px;
                spacing: 8px;
            }}
        """)
        self.addToolBar(self._toolbar)

        # Título
        self._lbl_titulo = QLabel("⟨/⟩  COSTEÑOL IDE")
        self._lbl_titulo.setStyleSheet(
            f"color: {c['titulo_fg']}; font-family: 'Segoe UI'; font-size: 14pt; font-weight: bold;"
        )
        self._toolbar.addWidget(self._lbl_titulo)

        # Espaciador
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._toolbar.addWidget(spacer)

        # Botones
        self._btn_compilar = self._boton_toolbar(
            "▶  Compilar  F5", c["btn_compilar"], c["btn_compilar_hover"], self.compilar
        )
        self._btn_ejecutar = self._boton_toolbar(
            "▶  Ejecutar  F9", c["btn_compilar"], c["btn_compilar_hover"], self.ejecutar
        )
        self._btn_limpiar = self._boton_toolbar(
            "🗑  Limpiar", c["btn_limpiar"], c["btn_limpiar_hover"], self.limpiar_todo
        )

        self._toolbar.addWidget(self._btn_compilar)
        self._toolbar.addWidget(self._btn_ejecutar)
        self._toolbar.addWidget(self._btn_limpiar)

        # Botón tema
        self._btn_tema = QPushButton("🌙" if tema_nombre() == "claro" else "☀")
        self._btn_tema.setFixedSize(36, 36)
        self._btn_tema.clicked.connect(self._alternar_tema)
        self._toolbar.addWidget(self._btn_tema)
        self._estilizar_btn_tema()

    def _boton_toolbar(self, texto: str, color: str, hover: str, slot) -> QPushButton:
        btn = QPushButton(texto)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(slot)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {color};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 7px 16px;
                font-family: 'Segoe UI';
                font-size: 9pt;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {hover};
            }}
            QPushButton:pressed {{
                opacity: 0.85;
            }}
        """)
        return btn

    def _estilizar_btn_tema(self):
        c = C()
        self._btn_tema.setStyleSheet(f"""
            QPushButton {{
                background: {c['btn_tema_bg']};
                color: {c['btn_tema_fg']};
                border: none;
                border-radius: 6px;
                font-size: 13pt;
            }}
            QPushButton:hover {{
                background: {c['seleccion']};
            }}
        """)

    # ── Cuerpo ────────────────────────────────────────────────────────────────

    def _construir_cuerpo(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setHandleWidth(5)
        layout.addWidget(self._splitter)

        # Explorador
        self._construir_explorador()

        # Editor
        self.editor_mgr = GestorPestanas(self._splitter, self)
        self._splitter.addWidget(self.editor_mgr)

        # Panel resultados
        self._construir_panel_resultados()

        self._splitter.setSizes([220, 700, 380])
        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)
        self._splitter.setStretchFactor(2, 0)

    # ── Explorador de archivos ────────────────────────────────────────────────

    def _construir_explorador(self):
        c = C()
        self._explorador_frame = QWidget()
        self._explorador_frame.setFixedWidth(240)
        lay = QVBoxLayout(self._explorador_frame)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._lbl_explorador = QLabel("  EXPLORADOR")
        self._lbl_explorador.setFixedHeight(36)
        self._lbl_explorador.setStyleSheet(
            f"background:{c['panel']}; color:{c['tab_fg_act']};"
            "font-family:'Segoe UI'; font-size:9pt; font-weight:bold;"
            f"border-bottom:1px solid {c['borde']};"
        )
        lay.addWidget(self._lbl_explorador)

        self._tree_explorer = QTreeWidget()
        self._tree_explorer.setHeaderHidden(True)
        self._tree_explorer.setRootIsDecorated(True)
        self._tree_explorer.itemDoubleClicked.connect(self._on_explorer_activate)
        lay.addWidget(self._tree_explorer)

        self._splitter.addWidget(self._explorador_frame)
        self._estilizar_explorador()
        self._cargar_explorador()

    def _estilizar_explorador(self):
        c = C()
        self._explorador_frame.setStyleSheet(
            f"background:{c['panel']}; border-right:1px solid {c['borde']};"
        )
        self._tree_explorer.setStyleSheet(f"""
            QTreeWidget {{
                background: {c['panel']};
                color: {c['tabla_fg']};
                border: none;
                font-family: 'Segoe UI';
                font-size: 9pt;
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 3px 6px;
                border: none;
            }}
            QTreeWidget::item:selected {{
                background: {c['seleccion']};
                color: {c['tab_fg_act']};
                border-radius: 4px;
            }}
            QTreeWidget::item:hover {{
                background: {c['borde']};
            }}
        """)

    def _cargar_explorador(self):
        self._tree_explorer.clear()
        examples_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "examples")
        )
        root_item = QTreeWidgetItem(self._tree_explorer, ["examples"])
        root_item.setData(0, Qt.ItemDataRole.UserRole, examples_dir)
        self._agregar_items_explorador(root_item, examples_dir)
        root_item.setExpanded(True)

    def _agregar_items_explorador(self, parent, ruta: str):
        try:
            nombres = sorted(os.listdir(ruta), key=str.lower)
        except OSError:
            return
        for nombre in nombres:
            abs_path = os.path.join(ruta, nombre)
            item = QTreeWidgetItem(parent, [nombre])
            item.setData(0, Qt.ItemDataRole.UserRole, abs_path)
            if os.path.isdir(abs_path):
                self._agregar_items_explorador(item, abs_path)

    def _on_explorer_activate(self, item: QTreeWidgetItem, _col: int):
        ruta = item.data(0, Qt.ItemDataRole.UserRole)
        if not ruta:
            return
        if os.path.isdir(ruta):
            item.setExpanded(not item.isExpanded())
            return
        self._abrir_archivo_desde_explorador(ruta)

    def _abrir_archivo_desde_explorador(self, ruta: str):
        if self._seleccionar_tab_por_ruta(ruta):
            return
        try:
            with open(ruta, encoding="utf-8") as f:
                contenido = f.read()
            self.editor_mgr.nueva_pestana(
                nombre=os.path.basename(ruta),
                contenido=contenido,
                ruta=ruta,
            )
        except Exception as e:
            QMessageBox.critical(self, "Error al abrir", str(e))

    def _seleccionar_tab_por_ruta(self, ruta: str) -> bool:
        for tid, datos in self.editor_mgr.pestanas.items():
            if datos.get("ruta") == ruta:
                self.editor_mgr.seleccionar(tid)
                return True
        return False

    # ── Panel de resultados ───────────────────────────────────────────────────

    def _construir_panel_resultados(self):
        c = C()
        self._panel_res = QWidget()
        self._panel_res.setMinimumWidth(320)
        lay = QVBoxLayout(self._panel_res)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._nb_resultados = QTabWidget()
        self._nb_resultados.setStyleSheet(self._estilo_notebook())
        lay.addWidget(self._nb_resultados)

        self._construir_tab_resultado()
        self._construir_tab_tabla()
        self._construir_tab_tokens()

        self._splitter.addWidget(self._panel_res)

    def _estilo_notebook(self) -> str:
        c = C()
        return f"""
            QTabWidget::pane {{
                border: none;
                background: {c['resultado_bg']};
            }}
            QTabBar {{
                background: {c['panel']};
                border-bottom: 1px solid {c['borde']};
            }}
            QTabBar::tab {{
                background: {c['tab_inactiva']};
                color: {c['tab_fg_inact']};
                padding: 8px 16px;
                border: none;
                font-family: 'Segoe UI';
                font-size: 9pt;
                font-weight: bold;
            }}
            QTabBar::tab:selected {{
                background: {c['tab_activa']};
                color: {c['tab_fg_act']};
                border-top: 2px solid {c['tab_indicador']};
            }}
            QTabBar::tab:hover:!selected {{
                background: {c['borde']};
                color: {c['tab_fg_act']};
            }}
        """

    def _construir_tab_resultado(self):
        c = C()
        frame = QWidget()
        frame.setStyleSheet(f"background:{c['resultado_bg']};")
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(0, 0, 0, 0)

        self.texto_resultado = QTextEdit()
        self.texto_resultado.setReadOnly(True)
        self.texto_resultado.setFont(
            QFont(FUENTES["resultado"][0], FUENTES["resultado"][1])
        )
        self.texto_resultado.setStyleSheet(f"""
            QTextEdit {{
                background: {c['resultado_bg']};
                color: {c['tag_normal']};
                border: none;
                padding: 12px 16px;
            }}
        """)
        lay.addWidget(self.texto_resultado)
        self._nb_resultados.addTab(frame, "  ✦ Resultado  ")

    def _construir_tab_tabla(self):
        c = C()
        frame = QWidget()
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(0, 0, 0, 0)

        cols = ["Variable", "Tipo", "Valor", "Línea"]
        self.tabla_view = QTableWidget(0, len(cols))
        self.tabla_view.setHorizontalHeaderLabels(cols)
        self.tabla_view.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )
        self.tabla_view.horizontalHeader().setDefaultSectionSize(120)
        self.tabla_view.verticalHeader().setVisible(False)
        self.tabla_view.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_view.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_view.setShowGrid(False)
        self.tabla_view.setAlternatingRowColors(True)
        self.tabla_view.setFont(QFont(FUENTES["tokens"][0], FUENTES["tokens"][1]))
        self._estilizar_tabla()
        lay.addWidget(self.tabla_view)
        self._nb_resultados.addTab(frame, "  ◈ Símbolos  ")

    def _estilizar_tabla(self):
        c = C()
        self.tabla_view.setStyleSheet(f"""
            QTableWidget {{
                background: {c['tabla_bg']};
                color: {c['tabla_fg']};
                border: none;
                gridline-color: {c['borde']};
                alternate-background-color: {c['panel']};
            }}
            QHeaderView::section {{
                background: {c['borde']};
                color: {c['tag_tok_cab']};
                padding: 6px;
                border: none;
                font-family: 'Segoe UI';
                font-size: 9pt;
                font-weight: bold;
            }}
            QTableWidget::item:selected {{
                background: {c['seleccion']};
                color: {c['tab_fg_act']};
            }}
        """)

    def _construir_tab_tokens(self):
        c = C()
        frame = QWidget()
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(0, 0, 0, 0)

        self.texto_tokens = QTextEdit()
        self.texto_tokens.setReadOnly(True)
        self.texto_tokens.setFont(QFont(FUENTES["tokens"][0], FUENTES["tokens"][1]))
        self.texto_tokens.setStyleSheet(f"""
            QTextEdit {{
                background: {c['panel']};
                color: {c['tabla_fg']};
                border: none;
                padding: 8px 14px;
            }}
        """)
        lay.addWidget(self.texto_tokens)
        self._nb_resultados.addTab(frame, "  ⟨/⟩ Tokens  ")

    # ── Barra de estado ───────────────────────────────────────────────────────

    def _construir_barra_estado(self):
        c = C()
        self._status = self.statusBar()
        self._status.setStyleSheet(f"""
            QStatusBar {{
                background: {c['status_bg']};
                color: {c['status_fg']};
                border-top: 1px solid {c['borde']};
                font-family: 'Segoe UI';
                font-size: 9pt;
                padding: 0 10px;
            }}
            QStatusBar::item {{
                border: none;
            }}
        """)

        self._lbl_compilacion = QLabel("● Sin compilar")
        self._lbl_vars = QLabel("Variables: 0")
        self._lbl_posicion = QLabel("Ln 1, Col 1")
        self._lbl_info = QLabel(f"COSTEÑOL  |  UTF-8  |  {tema_nombre().capitalize()}")

        def sep():
            f = QFrame()
            f.setFrameShape(QFrame.Shape.VLine)
            f.setFixedHeight(14)
            f.setStyleSheet(f"color:{c['borde']};")
            return f

        for w in [
            self._lbl_compilacion,
            sep(),
            self._lbl_vars,
            sep(),
            self._lbl_posicion,
        ]:
            self._status.addWidget(w)
        self._status.addPermanentWidget(self._lbl_info)

        self._estilizar_status_labels(c["status_fg"])

    def _estilizar_status_labels(self, color: str):
        style = f"color:{color}; font-family:'Segoe UI'; font-size:9pt; background:transparent;"
        for lbl in [
            self._lbl_compilacion,
            self._lbl_vars,
            self._lbl_posicion,
            self._lbl_info,
        ]:
            lbl.setStyleSheet(style)

    def actualizar_estado(self):
        editor = self.editor_mgr.editor_activo()
        if not editor:
            return
        cursor = editor.textCursor()
        lin = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        self._lbl_posicion.setStyleSheet(
            f"color:{C()['status_fg']}; font-family:'Segoe UI'; font-size:9pt; background:transparent;"
        )
        self._lbl_posicion.setText(f"Ln {lin}, Col {col}")

    # ── Estilos globales ──────────────────────────────────────────────────────

    def _aplicar_estilos_globales(self):
        c = C()
        self.setStyleSheet(f"""
            QMainWindow {{
                background: {c['fondo']};
            }}
            QMenuBar {{
                background: {c['menu_bg']};
                color: {c['menu_fg']};
                border-bottom: 1px solid {c['borde']};
                font-family: 'Segoe UI';
                font-size: 9pt;
                padding: 2px;
            }}
            QMenuBar::item:selected {{
                background: {c['menu_activo_bg']};
                color: {c['menu_activo_fg']};
                border-radius: 4px;
            }}
            QMenu {{
                background: {c['menu_bg']};
                color: {c['menu_fg']};
                border: 1px solid {c['borde']};
                padding: 4px;
                font-family: 'Segoe UI';
                font-size: 9pt;
            }}
            QMenu::item:selected {{
                background: {c['menu_activo_bg']};
                color: {c['menu_activo_fg']};
                border-radius: 4px;
            }}
            QSplitter::handle {{
                background: {c['borde']};
            }}
            QScrollBar:vertical {{
                background: {c['scrollbar_bg']};
                width: 10px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {c['scrollbar_handle']};
                border-radius: 5px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {c['scrollbar_handle_hover']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            QScrollBar:horizontal {{
                background: {c['scrollbar_bg']};
                height: 10px;
                border: none;
            }}
            QScrollBar::handle:horizontal {{
                background: {c['scrollbar_handle']};
                border-radius: 5px;
                min-width: 20px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {c['scrollbar_handle_hover']};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0;
            }}
            /* Evitar que cualquier regla ancestro tape el syntax highlighter */
            QPlainTextEdit {{
                border: none;
            }}
        """)

    # ── Cambio de tema ────────────────────────────────────────────────────────

    def _alternar_tema(self):
        alternar_tema()
        self._btn_tema.setText("🌙" if tema_nombre() == "claro" else "☀")
        self._reaplicar_tema()

    def _reaplicar_tema(self):
        c = C()
        self._aplicar_estilos_globales()

        # Toolbar
        self._toolbar.setStyleSheet(f"""
            QToolBar {{
                background: {c['panel']};
                border: none;
                border-bottom: 1px solid {c['borde']};
                padding: 0 12px;
                spacing: 8px;
            }}
        """)
        self._lbl_titulo.setStyleSheet(
            f"color: {c['titulo_fg']}; font-family: 'Segoe UI'; font-size: 14pt; font-weight: bold;"
        )
        self._btn_compilar.setStyleSheet(
            self._btn_compilar.styleSheet().replace(
                self._btn_compilar.styleSheet(),
                f"""
            QPushButton {{
                background: {c['btn_compilar']};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 7px 16px;
                font-family: 'Segoe UI';
                font-size: 9pt;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {c['btn_compilar_hover']};
            }}
        """,
            )
        )
        self._btn_limpiar.setStyleSheet(f"""
            QPushButton {{
                background: {c['btn_limpiar']};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 7px 16px;
                font-family: 'Segoe UI';
                font-size: 9pt;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {c['btn_limpiar_hover']};
            }}
        """)
        self._estilizar_btn_tema()

        # Explorador
        self._estilizar_explorador()
        self._lbl_explorador.setStyleSheet(
            f"background:{c['panel']}; color:{c['tab_fg_act']};"
            "font-family:'Segoe UI'; font-size:9pt; font-weight:bold;"
            f"border-bottom:1px solid {c['borde']};"
        )

        # Editor
        self.editor_mgr.aplicar_tema()

        # Resultados
        self._nb_resultados.setStyleSheet(self._estilo_notebook())
        self.texto_resultado.setStyleSheet(f"""
            QTextEdit {{
                background: {c['resultado_bg']};
                color: {c['tag_normal']};
                border: none;
                padding: 12px 16px;
            }}
        """)
        self.texto_tokens.setStyleSheet(f"""
            QTextEdit {{
                background: {c['panel']};
                color: {c['tabla_fg']};
                border: none;
                padding: 8px 14px;
            }}
        """)
        self._estilizar_tabla()

        # Status
        self._status.setStyleSheet(f"""
            QStatusBar {{
                background: {c['status_bg']};
                color: {c['status_fg']};
                border-top: 1px solid {c['borde']};
                font-family: 'Segoe UI';
                font-size: 9pt;
                padding: 0 10px;
            }}
            QStatusBar::item {{ border: none; }}
        """)
        self._estilizar_status_labels(c["status_fg"])
        self._lbl_info.setText(f"COSTEÑOL  |  UTF-8  |  {tema_nombre().capitalize()}")

    # ── Acciones de archivo ───────────────────────────────────────────────────

    def _nueva_pestana(self):
        self.editor_mgr.nueva_pestana()

    def _cerrar_tab_activa(self):
        tab_id = self.editor_mgr.tab_activa
        if tab_id:
            self.editor_mgr.cerrar_pestana(tab_id)

    def abrir_archivo(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Abrir archivo Costeñol", "", "Costeñol (*.pqek);;Todos (*.*)"
        )
        if not ruta:
            return
        try:
            with open(ruta, encoding="utf-8") as f:
                contenido = f.read()
            self.editor_mgr.nueva_pestana(
                nombre=os.path.basename(ruta),
                contenido=contenido,
                ruta=ruta,
            )
        except Exception as e:
            QMessageBox.critical(self, "Error al abrir", str(e))

    def guardar_archivo(self):
        datos = self.editor_mgr.datos_activos()
        if not datos:
            return
        if datos["ruta"]:
            self._escribir(datos["ruta"], datos)
        else:
            self.guardar_como()

    def guardar_como(self):
        datos = self.editor_mgr.datos_activos()
        if not datos:
            return
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar como", "", "Costeñol (*.pqek);;Todos (*.*)"
        )
        if ruta:
            datos["ruta"] = ruta
            datos["nombre"] = os.path.basename(ruta)
            self._escribir(ruta, datos)

    def _escribir(self, ruta: str, datos: dict):
        try:
            contenido = datos["editor"].toPlainText()
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(contenido)
            self.editor_mgr.marcar_modificado(self.editor_mgr.tab_activa, False)
            self._lbl_compilacion.setText("💾 Guardado")
            self._lbl_compilacion.setStyleSheet(
                f"color:{C()['status_ok']}; font-family:'Segoe UI'; font-size:9pt; background:transparent;"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error al guardar", str(e))

    # ── Compilación ───────────────────────────────────────────────────────────

    def compilar(self):
        self._ejecutar_fuente(modo="Compilar")

    def ejecutar(self):
        self._ejecutar_fuente(modo="Ejecutar")

    def _ejecutar_fuente(self, modo: str):
        from core.parser import compilar as compilar_codigo
        from core.lexer import tokenizar

        editor = self.editor_mgr.editor_activo()
        if not editor:
            return

        codigo = editor.toPlainText().strip()
        if not codigo:
            QMessageBox.warning(
                self,
                MENSAJE_SIN_CODIGO["titulo"],
                MENSAJE_SIN_CODIGO["cuerpo"],
            )
            return

        self.editor_mgr.limpiar_errores()

        resultado = compilar_codigo(codigo, ejecutar=(modo == "Ejecutar"))
        self._mostrar_resultado(resultado)
        self._mostrar_tabla(resultado["tabla"])
        self._mostrar_tokens(codigo)

        if resultado["exito"]:
            if modo == "Ejecutar":
                self._lbl_compilacion.setText("▶ Ejecución completa")
            else:
                self._lbl_compilacion.setText("✔ Compilación exitosa")
            self._lbl_compilacion.setStyleSheet(
                f"color:{C()['status_ok']}; font-family:'Segoe UI'; font-size:9pt; background:transparent;"
            )

        n_vars = len(resultado["tabla"])
        self._lbl_vars.setStyleSheet(
            f"color:{C()['status_fg']}; font-family:'Segoe UI'; font-size:9pt; background:transparent;"
        )
        self._lbl_vars.setText(f"Variables: {n_vars}")

        if resultado["exito"]:
            self._lbl_compilacion.setText("✔ Compilación exitosa")
            self._lbl_compilacion.setStyleSheet(
                f"color:{C()['status_ok']}; font-family:'Segoe UI'; font-size:9pt; background:transparent;"
            )
            QMessageBox.information(
                self,
                MENSAJES_EXITO["titulo"],
                random.choice(MENSAJES_EXITO["cuerpos"]),
            )
        else:
            n = len(resultado["errores"])
            self._lbl_compilacion.setText(f"✘  {n} error(es)")
            self._lbl_compilacion.setStyleSheet(
                f"color:{C()['status_err']}; font-family:'Segoe UI'; font-size:9pt; background:transparent;"
            )
            lineas_err = []
            for err in resultado["errores"]:
                m = re.search(r"[Ll]ínea\s+(\d+)|line\s+(\d+)", err)
                if m:
                    lineas_err.append(int(next(g for g in m.groups() if g)))
            if lineas_err:
                self.editor_mgr.marcar_errores(lineas_err)
            QMessageBox.critical(
                self,
                MENSAJES_ERROR["titulo"],
                random.choice(MENSAJES_ERROR["cuerpos"]),
            )

        self._nb_resultados.setCurrentIndex(0)

    def limpiar_todo(self):
        editor = self.editor_mgr.editor_activo()
        if editor:
            editor.setPlainText("")
            self.editor_mgr.limpiar_errores()

        self.texto_resultado.clear()
        self.texto_tokens.clear()
        self.tabla_view.setRowCount(0)

        c = C()
        self._lbl_compilacion.setText("● Sin compilar")
        self._lbl_compilacion.setStyleSheet(
            f"color:{c['status_fg']}; font-family:'Segoe UI'; font-size:9pt; background:transparent;"
        )
        self._lbl_vars.setText("Variables: 0")

    # ── Renderizado de resultados ─────────────────────────────────────────────

    def _mostrar_resultado(self, resultado: dict):
        c = C()

        def esc(t):
            return _texto_a_html(t)

        def lin(html):
            return html + "<br>"

        sep = lin(f'<span style="color:{c["tag_sep"]}">{"─" * 48}</span>')
        titulo_color = c["tag_exito"] if resultado["exito"] else c["tag_error"]
        titulo_txt = (
            "  ✔  COMPILACIÓN EXITOSA"
            if resultado["exito"]
            else "  ✘  ERRORES EN EL CÓDIGO"
        )

        html = ""
        html += sep
        html += lin(
            f'<b style="color:{titulo_color}; font-size:12pt">{esc(titulo_txt)}</b>'
        )
        html += sep

        if resultado["salida"]:
            html += "<br>"
            html += lin(
                f'<span style="color:{c["tag_titulo"]}; font-size:10pt">  SALIDA DEL PROGRAMA</span>'
            )
            html += "<br>"
            for linea in resultado["salida"]:
                html += lin(
                    f'<span style="color:{c["tag_salida"]}">  ▸  {esc(linea)}</span>'
                )
            html += "<br>" + sep

        if resultado["errores"]:
            html += "<br>"
            html += lin(
                f'<span style="color:{c["tag_titulo"]}; font-size:10pt">  ERRORES DETECTADOS</span>'
            )
            html += "<br>"
            for i, err in enumerate(resultado["errores"], 1):
                html += (
                    f'<span style="color:{c["tag_num_error"]}; font-weight:bold">  [{i}]  </span>'
                    f'<span style="color:{c["tag_error"]}">{esc(err)}</span><br>'
                )
            html += "<br>" + sep

        if not resultado["salida"] and not resultado["errores"]:
            html += f'<br><span style="color:{c["tag_normal"]}">  (sin salida registrada)</span>'

        self.texto_resultado.setHtml(
            f'<pre style="font-family:Cascadia Code,monospace">{html}</pre>'
        )

    def _mostrar_tabla(self, tabla_dict: dict):
        self.tabla_view.setRowCount(0)
        for var, info in tabla_dict.items():
            row = self.tabla_view.rowCount()
            self.tabla_view.insertRow(row)
            val = str(info["valor"]) if info["valor"] is not None else "—"
            for col, texto in enumerate([var, info["tipo"], val, str(info["linea"])]):
                item = QTableWidgetItem(texto)
                item.setForeground(QColor(C()["tabla_fg"]))
                self.tabla_view.setItem(row, col, item)

    def _mostrar_tokens(self, codigo: str):
        from core.lexer import tokenizar

        c = C()
        lista = tokenizar(codigo)

        cab = (
            f'<span style="color:{c["tag_tok_cab"]}; font-weight:bold">'
            f'  {"LÍN":<5}  {"TIPO":<20}  VALOR</span><br>'
        )
        sep = f'<span style="color:{c["tag_sep"]}">  {"─" * 46}</span><br>'

        rows = ""
        for tipo, valor, linea in lista:
            rows += (
                f'<span style="color:{c["tag_tok_linea"]}">  {str(linea):<5}  </span>'
                f'<span style="color:{c["tag_tok_tipo"]}">{tipo:<20}  </span>'
                f'<span style="color:{c["tag_tok_valor"]}">{_texto_a_html(repr(valor))}</span><br>'
            )

        self.texto_tokens.setHtml(
            f'<pre style="font-family:Cascadia Code,monospace">{cab}{sep}{rows}</pre>'
        )

    # ── Ejemplo inicial ───────────────────────────────────────────────────────


# ── Punto de entrada ──────────────────────────────────────────────────────────


def iniciar_interfaz():
    import sys

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    ventana = VentanaCompilador()
    sys.exit(app.exec())


if __name__ == "__main__":
    iniciar_interfaz()
