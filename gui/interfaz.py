import os
import random
import re

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QSplitter,
    QLabel,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QFrame,
    QToolBar,
    QSizePolicy,
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
from gui.explorador import PanelExplorador
from gui.panel_resultados import PanelResultados


class VentanaCompilador(QMainWindow):
    def __init__(self):
        super().__init__()
        cambiar_tema("claro")
        self._construir()

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

    def _construir_menu(self):
        mb = self.menuBar()

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

        m_comp = mb.addMenu("Compilar")
        m_comp.addAction(self._accion("Compilar", self.compilar, "F5"))
        m_comp.addAction(self._accion("Ejecutar", self.ejecutar, "F9"))
        m_comp.addAction(self._accion("Limpiar", self.limpiar_todo, "F6"))

        m_ver = mb.addMenu("Ver")
        m_ver.addAction(
            self._accion("Alternar explorador", self._toggle_explorador, "Ctrl+B")
        )
        m_ver.addAction(
            self._accion("Alternar tema", self._alternar_tema, "Ctrl+Shift+T")
        )

    def _accion(self, nombre: str, slot, atajo: str = None) -> QAction:
        a = QAction(nombre, self)
        if atajo:
            a.setShortcut(QKeySequence(atajo))
        a.triggered.connect(slot)
        return a

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

        self._lbl_titulo = QLabel("⟨/⟩  COSTEÑOL IDE")
        self._lbl_titulo.setStyleSheet(
            f"color: {c['titulo_fg']}; font-family: 'Segoe UI'; font-size: 14pt; font-weight: bold;"
        )
        self._toolbar.addWidget(self._lbl_titulo)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._toolbar.addWidget(spacer)

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

    def _construir_cuerpo(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setHandleWidth(5)
        layout.addWidget(self._splitter)
        self._explorador = PanelExplorador()
        self._explorador.archivo_abierto.connect(self._abrir_archivo_desde_explorador)
        self._explorador.visibilidad_cambiada.connect(self._on_explorador_toggle)
        self._explorador.cargar_carpeta_examples()
        self._splitter.addWidget(self._explorador)
        self.editor_mgr = GestorPestanas(self._splitter, self)
        self._splitter.addWidget(self.editor_mgr)
        self._panel_resultados = PanelResultados()
        self._splitter.addWidget(self._panel_resultados)
        self._splitter.setSizes([282, 700, 380])
        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)
        self._splitter.setStretchFactor(2, 0)

    def _on_explorador_toggle(self, expandido: bool):
        sizes = self._splitter.sizes()
        if expandido:
            self._splitter.setSizes([282, sizes[1] + sizes[0] - 282, sizes[2]])
        else:
            from gui.explorador import ANCHO_BARRA

            self._splitter.setSizes(
                [ANCHO_BARRA, sizes[1] + sizes[0] - ANCHO_BARRA, sizes[2]]
            )

    def _toggle_explorador(self):
        self._explorador._toggle()

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
            QStatusBar::item {{ border: none; }}
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

    def _aplicar_estilos_globales(self):
        c = C()
        self.setStyleSheet(f"""
            QMainWindow {{ background: {c['fondo']}; }}
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
            QSplitter::handle {{ background: {c['borde']}; }}
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
            QScrollBar::handle:vertical:hover {{ background: {c['scrollbar_handle_hover']}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
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
            QScrollBar::handle:horizontal:hover {{ background: {c['scrollbar_handle_hover']}; }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
            QPlainTextEdit {{ border: none; }}
        """)

    def _alternar_tema(self):
        alternar_tema()
        self._btn_tema.setText("🌙" if tema_nombre() == "claro" else "☀")
        self._reaplicar_tema()

    def _reaplicar_tema(self):
        c = C()
        self._aplicar_estilos_globales()

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
        for btn, color, hover in [
            (self._btn_compilar, c["btn_compilar"], c["btn_compilar_hover"]),
            (self._btn_ejecutar, c["btn_compilar"], c["btn_compilar_hover"]),
            (self._btn_limpiar, c["btn_limpiar"], c["btn_limpiar_hover"]),
        ]:
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
                QPushButton:hover {{ background: {hover}; }}
            """)
        self._estilizar_btn_tema()
        self._explorador.aplicar_tema()
        self.editor_mgr.aplicar_tema()
        self._panel_resultados.aplicar_tema()

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
                nombre=os.path.basename(ruta), contenido=contenido, ruta=ruta
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

    def compilar(self):
        self._ejecutar_fuente(modo="Compilar")

    def ejecutar(self):
        self._ejecutar_fuente(modo="Ejecutar")

    def _ejecutar_fuente(self, modo: str):
        from core.parser import compilar as compilar_codigo

        editor = self.editor_mgr.editor_activo()
        if not editor:
            return

        codigo = editor.toPlainText().strip()
        if not codigo:
            QMessageBox.warning(
                self, MENSAJE_SIN_CODIGO["titulo"], MENSAJE_SIN_CODIGO["cuerpo"]
            )
            return

        self.editor_mgr.limpiar_errores()
        resultado = compilar_codigo(codigo, ejecutar=(modo == "Ejecutar"))

        self._panel_resultados.mostrar_resultado(resultado, codigo)

        c = C()
        n_vars = len(resultado["tabla"])
        self._lbl_vars.setStyleSheet(
            f"color:{c['status_fg']}; font-family:'Segoe UI'; font-size:9pt; background:transparent;"
        )
        self._lbl_vars.setText(f"Variables: {n_vars}")

        if resultado["exito"]:
            txt = (
                "▶ Ejecución completa"
                if modo == "Ejecutar"
                else "✔ Compilación exitosa"
            )
            self._lbl_compilacion.setText(txt)
            self._lbl_compilacion.setStyleSheet(
                f"color:{c['status_ok']}; font-family:'Segoe UI'; font-size:9pt; background:transparent;"
            )
            QMessageBox.information(
                self, MENSAJES_EXITO["titulo"], random.choice(MENSAJES_EXITO["cuerpos"])
            )
        else:
            n = len(resultado["errores"])
            self._lbl_compilacion.setText(f"✘  {n} error(es)")
            self._lbl_compilacion.setStyleSheet(
                f"color:{c['status_err']}; font-family:'Segoe UI'; font-size:9pt; background:transparent;"
            )
            lineas_err = []
            for err in resultado["errores"]:
                m = re.search(r"[Ll]ínea\s+(\d+)|line\s+(\d+)", err)
                if m:
                    lineas_err.append(int(next(g for g in m.groups() if g)))
            if lineas_err:
                self.editor_mgr.marcar_errores(lineas_err)
            QMessageBox.critical(
                self, MENSAJES_ERROR["titulo"], random.choice(MENSAJES_ERROR["cuerpos"])
            )

    def limpiar_todo(self):
        editor = self.editor_mgr.editor_activo()
        if editor:
            editor.setPlainText("")
            self.editor_mgr.limpiar_errores()

        self._panel_resultados.limpiar_todo()

        c = C()
        self._lbl_compilacion.setText("● Sin compilar")
        self._lbl_compilacion.setStyleSheet(
            f"color:{c['status_fg']}; font-family:'Segoe UI'; font-size:9pt; background:transparent;"
        )
        self._lbl_vars.setText("Variables: 0")

    def _abrir_archivo_desde_explorador(self, ruta: str):
        if self._seleccionar_tab_por_ruta(ruta):
            return
        try:
            with open(ruta, encoding="utf-8") as f:
                contenido = f.read()
            self.editor_mgr.nueva_pestana(
                nombre=os.path.basename(ruta), contenido=contenido, ruta=ruta
            )
        except Exception as e:
            QMessageBox.critical(self, "Error al abrir", str(e))

    def _seleccionar_tab_por_ruta(self, ruta: str) -> bool:
        for tid, datos in self.editor_mgr.pestanas.items():
            if datos.get("ruta") == ruta:
                self.editor_mgr.seleccionar(tid)
                return True
        return False


def iniciar_interfaz():
    import sys

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    ventana = VentanaCompilador()
    sys.exit(app.exec())


if __name__ == "__main__":
    iniciar_interfaz()
