import os
import shutil

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCursor
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QLabel,
    QToolButton,
    QFrame,
    QMenu,
    QInputDialog,
    QMessageBox,
    QFileDialog,
    QSizePolicy,
)

from gui.temas import C

# ── Iconos emoji por tipo de archivo/carpeta

_ICONOS_EXT = {
    ".pqek": "📄",
    ".py": "🐍",
    ".txt": "📝",
    ".json": "📋",
    ".md": "📖",
    ".csv": "📊",
    ".html": "🌐",
    ".css": "🎨",
    ".js": "⚡",
    ".xml": "🗂️",
    ".ini": "⚙️",
    ".cfg": "⚙️",
    ".log": "🪵",
}
_ICONO_CARPETA_CERRADA = "📁"
_ICONO_CARPETA_ABIERTA = "📂"
_ICONO_ARCHIVO_DEFAULT = "📄"

# Límites de ancho del panel expandido (sin contar la barra de iconos)
ANCHO_PANEL_MIN = 160
ANCHO_PANEL_MAX = 600
ANCHO_PANEL_DEFAULT = 240
ANCHO_BARRA = 42


def _icono_para(nombre: str, es_dir: bool, expandido: bool = False) -> str:
    if es_dir:
        return _ICONO_CARPETA_ABIERTA if expandido else _ICONO_CARPETA_CERRADA
    ext = os.path.splitext(nombre)[1].lower()
    return _ICONOS_EXT.get(ext, _ICONO_ARCHIVO_DEFAULT)


# ── Árbol con menú contextual


class ArbolExplorador(QTreeWidget):
    archivo_abierto = pyqtSignal(str)
    carpeta_cambiada = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setRootIsDecorated(False)
        self.setIndentation(16)
        self.setAnimated(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._menu_contextual)
        self.itemDoubleClicked.connect(self._on_doble_clic)
        self.itemExpanded.connect(lambda item: self._actualizar_icono(item, True))
        self.itemCollapsed.connect(lambda item: self._actualizar_icono(item, False))

    def _actualizar_icono(self, item: QTreeWidgetItem, expandido: bool):
        ruta = item.data(0, Qt.ItemDataRole.UserRole)
        if ruta and os.path.isdir(ruta):
            nombre = item.data(0, Qt.ItemDataRole.UserRole + 1) or os.path.basename(
                ruta
            )
            icono = _icono_para(nombre, True, expandido)
            item.setText(0, f"  {icono}  {nombre}")

    def _on_doble_clic(self, item: QTreeWidgetItem, _col: int):
        ruta = item.data(0, Qt.ItemDataRole.UserRole)
        if not ruta:
            return
        if os.path.isdir(ruta):
            item.setExpanded(not item.isExpanded())
        else:
            self.archivo_abierto.emit(ruta)

    def _menu_contextual(self, pos):
        item = self.itemAt(pos)
        ruta = item.data(0, Qt.ItemDataRole.UserRole) if item else None
        es_dir = os.path.isdir(ruta) if ruta else False

        c = C()
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background: {c['menu_bg']};
                color: {c['menu_fg']};
                border: 1px solid {c['borde']};
                border-radius: 6px;
                padding: 4px;
                font-family: 'Segoe UI';
                font-size: 9pt;
            }}
            QMenu::item {{
                padding: 6px 20px 6px 10px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background: {c['menu_activo_bg']};
                color: {c['menu_activo_fg']};
            }}
            QMenu::separator {{
                height: 1px;
                background: {c['borde']};
                margin: 4px 0;
            }}
        """)

        if ruta and es_dir:
            dir_padre = ruta
        elif ruta and not es_dir:
            dir_padre = os.path.dirname(ruta)
        else:
            dir_padre = self._raiz()

        act_nuevo_archivo = menu.addAction("📄  Nuevo archivo")
        act_nueva_carpeta = menu.addAction("📁  Nueva carpeta")
        menu.addSeparator()

        act_renombrar = None
        act_eliminar = None
        if ruta:
            act_renombrar = menu.addAction("✏️  Renombrar")
            act_eliminar = menu.addAction("🗑️  Eliminar")

        accion = menu.exec(QCursor.pos())
        if accion is None:
            return

        if accion == act_nuevo_archivo:
            self._crear_archivo(dir_padre)
        elif accion == act_nueva_carpeta:
            self._crear_carpeta(dir_padre)
        elif accion == act_renombrar and ruta:
            self._renombrar(item, ruta)
        elif accion == act_eliminar and ruta:
            self._eliminar(item, ruta)

    def set_raiz(self, ruta: str):
        self._raiz_real = ruta

    def _raiz(self) -> str:
        return getattr(self, "_raiz_real", os.path.expanduser("~"))

    def _crear_archivo(self, directorio: str):
        nombre, ok = QInputDialog.getText(self, "Nuevo archivo", "Nombre del archivo:")
        if not ok or not nombre.strip():
            return
        ruta = os.path.join(directorio, nombre.strip())
        try:
            with open(ruta, "w", encoding="utf-8"):
                pass
            self.carpeta_cambiada.emit(self._raiz())
            self.archivo_abierto.emit(ruta)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _crear_carpeta(self, directorio: str):
        nombre, ok = QInputDialog.getText(
            self, "Nueva carpeta", "Nombre de la carpeta:"
        )
        if not ok or not nombre.strip():
            return
        ruta = os.path.join(directorio, nombre.strip())
        try:
            os.makedirs(ruta, exist_ok=True)
            self.carpeta_cambiada.emit(self._raiz())
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _renombrar(self, item: QTreeWidgetItem, ruta: str):
        nombre_viejo = os.path.basename(ruta)
        nombre_nuevo, ok = QInputDialog.getText(
            self, "Renombrar", "Nuevo nombre:", text=nombre_viejo
        )
        if not ok or not nombre_nuevo.strip() or nombre_nuevo == nombre_viejo:
            return
        nueva_ruta = os.path.join(os.path.dirname(ruta), nombre_nuevo.strip())
        try:
            os.rename(ruta, nueva_ruta)
            self.carpeta_cambiada.emit(self._raiz())
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _eliminar(self, item: QTreeWidgetItem, ruta: str):
        nombre = os.path.basename(ruta)
        resp = QMessageBox.question(
            self,
            "Eliminar",
            f"¿Eliminar '{nombre}'? Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if resp != QMessageBox.StandardButton.Yes:
            return
        try:
            if os.path.isdir(ruta):
                shutil.rmtree(ruta)
            else:
                os.remove(ruta)
            self.carpeta_cambiada.emit(self._raiz())
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    # ── API pública

    def colapsar_todas(self):
        """Colapsa todas las carpetas hijas (no el root)."""
        root = self.invisibleRootItem()
        if root.childCount() == 0:
            return
        raiz_item = root.child(0)
        for i in range(raiz_item.childCount()):
            hijo = raiz_item.child(i)
            ruta = hijo.data(0, Qt.ItemDataRole.UserRole)
            if ruta and os.path.isdir(ruta):
                hijo.setExpanded(False)


# ── Widget completo del explorador


class PanelExplorador(QWidget):
    archivo_abierto = pyqtSignal(str)
    visibilidad_cambiada = pyqtSignal(bool)
    ancho_cambiado = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._expandido = True
        self._raiz_actual: str | None = None
        self._ancho_panel = ANCHO_PANEL_DEFAULT
        self._construir_ui()

    # ── Construcción

    def _construir_ui(self):
        self.setMinimumWidth(ANCHO_BARRA)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._barra = QFrame()
        self._barra.setFixedWidth(ANCHO_BARRA)
        barra_lay = QVBoxLayout(self._barra)
        barra_lay.setContentsMargins(0, 8, 0, 8)
        barra_lay.setSpacing(4)
        barra_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._btn_toggle = self._boton_icono("📁", "Explorador  (Ctrl+B)", self._toggle)
        self._btn_toggle.setCheckable(True)
        self._btn_toggle.setChecked(True)
        barra_lay.addWidget(self._btn_toggle)
        layout.addWidget(self._barra)
        self._panel = QFrame()
        self._panel.setMinimumWidth(ANCHO_PANEL_MIN)
        self._panel.setMaximumWidth(ANCHO_PANEL_MAX)
        self._panel.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        panel_lay = QVBoxLayout(self._panel)
        panel_lay.setContentsMargins(0, 0, 0, 0)
        panel_lay.setSpacing(0)
        self._cabecera = self._construir_cabecera()
        panel_lay.addWidget(self._cabecera)
        self._arbol = ArbolExplorador()
        self._arbol.archivo_abierto.connect(self.archivo_abierto)
        self._arbol.carpeta_cambiada.connect(self.cargar_carpeta)
        panel_lay.addWidget(self._arbol)
        layout.addWidget(self._panel)
        self._aplicar_estilos()

    def _construir_cabecera(self) -> QWidget:
        cab = QWidget()
        cab.setFixedHeight(36)
        lay = QHBoxLayout(cab)
        lay.setContentsMargins(8, 0, 4, 0)
        lay.setSpacing(2)

        self._lbl_titulo = QLabel("EXPLORADOR")
        self._lbl_titulo.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        lay.addWidget(self._lbl_titulo)
        lay.addStretch()

        # Botones: nuevo archivo | nueva carpeta | colapsar todo | actualizar
        for icono, tooltip, slot in [
            ("📄", "Nuevo archivo", lambda: self._nuevo_en_raiz(False)),
            ("📁", "Nueva carpeta", lambda: self._nuevo_en_raiz(True)),
            ("⇱", "Colapsar todo", self._colapsar_todas_carpetas),
            ("↺", "Actualizar", self._recargar),
        ]:
            lay.addWidget(self._boton_icono(icono, tooltip, slot, pequeno=True))

        return cab

    def _boton_icono(
        self, icono: str, tooltip: str, slot, pequeno: bool = False
    ) -> QToolButton:
        btn = QToolButton()
        btn.setText(icono)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        sz = 28 if pequeno else 36
        btn.setFixedSize(sz, sz)
        btn.clicked.connect(slot)
        return btn

    # ── Estilos

    def _aplicar_estilos(self):
        c = C()
        self._barra.setStyleSheet(f"""
            QFrame {{
                background: {c['panel']};
                border-right: 1px solid {c['borde']};
            }}
            QToolButton {{
                background: transparent;
                border: none;
                border-radius: 6px;
                font-size: 16pt;
                color: {c['tab_fg_inact']};
            }}
            QToolButton:hover {{
                background: {c['borde']};
                color: {c['tab_fg_act']};
            }}
            QToolButton:checked {{
                color: {c['tab_indicador']};
                border-left: 2px solid {c['tab_indicador']};
                border-radius: 0;
            }}
        """)
        self._panel.setStyleSheet(f"""
            QFrame {{
                background: {c['panel']};
                border-right: 1px solid {c['borde']};
            }}
        """)
        self._cabecera.setStyleSheet(f"""
            QWidget {{
                background: {c['panel']};
                border-bottom: 1px solid {c['borde']};
            }}
            QLabel {{
                color: {c['tab_fg_inact']};
                font-family: 'Segoe UI';
                font-size: 8pt;
                font-weight: bold;
                background: transparent;
            }}
            QToolButton {{
                background: transparent;
                border: none;
                border-radius: 4px;
                font-size: 11pt;
                color: {c['tab_fg_inact']};
            }}
            QToolButton:hover {{
                background: {c['borde']};
                color: {c['tab_fg_act']};
            }}
        """)
        self._arbol.setStyleSheet(f"""
            QTreeWidget {{
                background: {c['panel']};
                color: {c['tabla_fg']};
                border: none;
                font-family: 'Segoe UI';
                font-size: 9pt;
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 3px 4px;
                border: none;
                border-radius: 4px;
            }}
            QTreeWidget::item:selected {{
                background: {c['seleccion']};
                color: {c['tab_fg_act']};
            }}
            QTreeWidget::item:hover:!selected {{
                background: {c['borde']};
            }}
            QTreeWidget::branch {{
                background: transparent;
            }}
        """)

    def aplicar_tema(self):
        self._aplicar_estilos()

    # ── Colapsar / expandir el panel completo

    def _toggle(self):
        if self._expandido:
            self._colapsar()
        else:
            self._expandir()

    def _expandir(self):
        self._expandido = True
        self._panel.setVisible(True)
        self._btn_toggle.setChecked(True)
        self.visibilidad_cambiada.emit(True)

    def _colapsar(self):
        self._expandido = False
        self._panel.setVisible(False)
        self._btn_toggle.setChecked(False)
        self.visibilidad_cambiada.emit(False)

    # ── Colapsar todas las carpetas del árbol

    def _colapsar_todas_carpetas(self):
        self._arbol.colapsar_todas()

    # ── Carga de carpeta

    def cargar_carpeta(self, ruta: str):
        self._raiz_actual = ruta
        self._arbol.set_raiz(ruta)
        self._arbol.clear()

        nombre = os.path.basename(ruta) or ruta
        self._lbl_titulo.setText(nombre.upper())
        self._poblar_raiz(ruta)

    def _poblar_raiz(self, directorio: str):
        """Puebla los hijos directos del directorio raíz como items de primer nivel."""
        try:
            entradas = sorted(
                os.listdir(directorio),
                key=lambda n: (
                    not os.path.isdir(os.path.join(directorio, n)),
                    n.lower(),
                ),
            )
        except OSError:
            return

        for nombre in entradas:
            if nombre.startswith("."):
                continue
            ruta = os.path.join(directorio, nombre)
            es_dir = os.path.isdir(ruta)
            icono = _icono_para(nombre, es_dir, False)

            item = QTreeWidgetItem(self._arbol)
            item.setText(0, f"  {icono}  {nombre}")
            item.setData(0, Qt.ItemDataRole.UserRole, ruta)
            item.setData(0, Qt.ItemDataRole.UserRole + 1, nombre)

            if es_dir:
                self._poblar(item, ruta)

    def _poblar(self, parent: QTreeWidgetItem, directorio: str):
        """Puebla recursivamente los hijos de una carpeta."""
        try:
            entradas = sorted(
                os.listdir(directorio),
                key=lambda n: (
                    not os.path.isdir(os.path.join(directorio, n)),
                    n.lower(),
                ),
            )
        except OSError:
            return

        for nombre in entradas:
            if nombre.startswith("."):
                continue
            ruta = os.path.join(directorio, nombre)
            es_dir = os.path.isdir(ruta)
            icono = _icono_para(nombre, es_dir, False)

            item = QTreeWidgetItem(parent)
            item.setText(0, f"  {icono}  {nombre}")
            item.setData(0, Qt.ItemDataRole.UserRole, ruta)
            item.setData(0, Qt.ItemDataRole.UserRole + 1, nombre)

            if es_dir:
                self._poblar(item, ruta)

    def _recargar(self):
        if self._raiz_actual:
            self.cargar_carpeta(self._raiz_actual)

    def _nuevo_en_raiz(self, carpeta: bool):
        dir_base = self._raiz_actual or os.path.expanduser("~")
        if carpeta:
            nombre, ok = QInputDialog.getText(self, "Nueva carpeta", "Nombre:")
            if ok and nombre.strip():
                try:
                    os.makedirs(os.path.join(dir_base, nombre.strip()), exist_ok=True)
                    self._recargar()
                except Exception as e:
                    QMessageBox.critical(self, "Error", str(e))
        else:
            nombre, ok = QInputDialog.getText(self, "Nuevo archivo", "Nombre:")
            if ok and nombre.strip():
                ruta = os.path.join(dir_base, nombre.strip())
                try:
                    with open(ruta, "w", encoding="utf-8"):
                        pass
                    self._recargar()
                    self.archivo_abierto.emit(ruta)
                except Exception as e:
                    QMessageBox.critical(self, "Error", str(e))

    # ── API pública

    def cargar_carpeta_examples(self):
        examples_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "examples")
        )
        if os.path.isdir(examples_dir):
            self.cargar_carpeta(examples_dir)

    @property
    def expandido(self) -> bool:
        return self._expandido
