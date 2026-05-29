# gui/panel_resultados.py — Panel derecho del IDE Costeñol (consola, símbolos, tokens)
import re

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import (
    QColor,
    QFont,
    QTextCursor,
)
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QLabel,
    QFrame,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QSizePolicy,
    QToolButton,
    QAbstractItemView,
    QStackedWidget,
)

from gui.temas import C, FUENTES

ANCHO_PANEL_MIN = 260
ANCHO_PANEL_MAX = 700
ANCHO_PANEL_DEFAULT = 380


# ── Utilidades HTML ───────────────────────────────────────────────────────────


def _esc(texto: str) -> str:
    return texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ── Widget de consola ─────────────────────────────────────────────────────────


class ConsolaWidget(QWidget):
    """Solo muestra salida y errores con apariencia de terminal. No es funcional."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._construir()

    def _construir(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._cabecera = self._construir_cabecera()
        layout.addWidget(self._cabecera)

        self._texto = QTextEdit()
        self._texto.setReadOnly(True)
        self._texto.setFont(QFont(FUENTES["codigo"][0], FUENTES["codigo"][1] - 1))
        layout.addWidget(self._texto)

        self._aplicar_estilos()
        self._limpiar_contenido()

    def _construir_cabecera(self) -> QWidget:
        cab = QFrame()
        cab.setFixedHeight(38)
        lay = QHBoxLayout(cab)
        lay.setContentsMargins(12, 0, 8, 0)
        lay.setSpacing(8)

        self._lbl_proceso = QLabel("costeñol — resultado")
        lay.addWidget(self._lbl_proceso)
        lay.addStretch()

        self._lbl_estado = QLabel("●")
        self._lbl_estado.setFixedWidth(16)
        lay.addWidget(self._lbl_estado)

        self._btn_limpiar = QToolButton()
        self._btn_limpiar.setText("⌫")
        self._btn_limpiar.setToolTip("Limpiar consola")
        self._btn_limpiar.clicked.connect(self.limpiar)
        lay.addWidget(self._btn_limpiar)

        self._btn_copiar = QToolButton()
        self._btn_copiar.setText("⎘")
        self._btn_copiar.setToolTip("Copiar salida")
        self._btn_copiar.clicked.connect(self._copiar)
        lay.addWidget(self._btn_copiar)

        return cab

    def _aplicar_estilos(self):
        c = C()
        self._cabecera.setStyleSheet(f"""
            QFrame {{
                background: {c['panel']};
                border-bottom: 1px solid {c['borde']};
            }}
            QLabel {{
                color: {c['subtitulo_fg']};
                font-family: 'Cascadia Code', monospace;
                font-size: 8pt;
                background: transparent;
            }}
            QToolButton {{
                background: transparent;
                border: none;
                border-radius: 4px;
                color: {c['subtitulo_fg']};
                font-size: 11pt;
                padding: 2px 4px;
            }}
            QToolButton:hover {{
                background: {c['borde']};
                color: {c['tab_fg_act']};
            }}
        """)
        self._texto.setStyleSheet(f"""
            QTextEdit {{
                background: {c['editor_bg']};
                color: {c['editor_fg']};
                border: none;
                padding: 12px 16px;
                selection-background-color: {c['seleccion']};
            }}
            QScrollBar:vertical {{
                background: {c['scrollbar_bg']};
                width: 8px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {c['scrollbar_handle']};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {c['scrollbar_handle_hover']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)
        self._lbl_estado.setStyleSheet(f"color: {c['subtitulo_fg']}; font-size: 8pt;")

    def aplicar_tema(self):
        self._aplicar_estilos()

    # ── Helpers HTML ──────────────────────────────────────────────────────────

    def _span(self, texto: str, color: str, bold: bool = False) -> str:
        w = "font-weight:bold;" if bold else ""
        return f'<span style="color:{color};{w}">{_esc(texto)}</span>'

    def _set_html(self, html: str):
        c = C()
        fuente = FUENTES["codigo"][0]
        tam = FUENTES["codigo"][1] - 1
        self._texto.setHtml(
            f'<div style="font-family:{fuente},monospace;font-size:{tam}pt;'
            f'background:{c["editor_bg"]};color:{c["editor_fg"]};">'
            f"{html}</div>"
        )
        self._texto.moveCursor(QTextCursor.MoveOperation.End)

    def _limpiar_contenido(self):
        self._set_html("")

    # ── API pública ───────────────────────────────────────────────────────────

    def mostrar_resultado(self, resultado: dict):
        c = C()
        exito = resultado.get("exito", False)
        salida = resultado.get("salida", [])
        errores = resultado.get("errores", [])

        html = ""

        if exito:
            html += (
                self._span("✔  COMPILACIÓN EXITOSA", c["tag_exito"], bold=True) + "<br>"
            )
        else:
            html += (
                self._span("✘  ERRORES EN EL CÓDIGO", c["tag_error"], bold=True)
                + "<br>"
            )

        html += "<br>"

        if salida:
            html += self._span("SALIDA DEL PROGRAMA", c["tag_titulo"]) + "<br><br>"
            for s in salida:
                html += (
                    self._span("▸  ", c["tag_salida"])
                    + self._span(s, c["tag_salida"])
                    + "<br>"
                )
            html += "<br>"

        if errores:
            html += self._span("ERRORES DETECTADOS", c["tag_titulo"]) + "<br><br>"
            for i, err in enumerate(errores, 1):
                html += (
                    self._span(f"[{i}]  ", c["tag_num_error"], bold=True)
                    + self._span(err, c["tag_error"])
                    + "<br>"
                )
            html += "<br>"

        if not salida and not errores:
            html += self._span("(sin salida registrada)", c["tag_normal"]) + "<br>"

        self._set_html(html)

        color_estado = c["tag_exito"] if exito else c["tag_error"]
        self._lbl_estado.setStyleSheet(f"color: {color_estado}; font-size: 8pt;")
        self._lbl_proceso.setText(
            "costeñol — ✔ éxito" if exito else "costeñol — ✘ error"
        )

    def limpiar(self):
        c = C()
        self._lbl_estado.setStyleSheet(f"color: {c['subtitulo_fg']}; font-size: 8pt;")
        self._lbl_proceso.setText("costeñol — resultado")
        self._limpiar_contenido()

    def _copiar(self):
        from PyQt6.QtWidgets import QApplication

        QApplication.clipboard().setText(self._texto.toPlainText())


# ── Tabla de símbolos ─────────────────────────────────────────────────────────


class TablaSimbolosWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._construir()

    def _construir(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        cab = QFrame()
        cab.setFixedHeight(38)
        cab_lay = QHBoxLayout(cab)
        cab_lay.setContentsMargins(12, 0, 8, 0)
        cab_lay.setSpacing(8)

        lbl = QLabel("◈  TABLA DE SÍMBOLOS")
        cab_lay.addWidget(lbl)
        cab_lay.addStretch()

        self._lbl_conteo = QLabel("0 variables")
        cab_lay.addWidget(self._lbl_conteo)

        self._cab = cab
        layout.addWidget(cab)

        cols = ["Variable", "Tipo", "Valor", "Línea"]
        self._tabla = QTableWidget(0, len(cols))
        self._tabla.setHorizontalHeaderLabels(cols)
        self._tabla.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self._tabla.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self._tabla.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self._tabla.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )
        self._tabla.horizontalHeader().setStretchLastSection(True)
        self._tabla.verticalHeader().setVisible(False)
        self._tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._tabla.setShowGrid(False)
        self._tabla.setAlternatingRowColors(True)
        self._tabla.setFont(QFont(FUENTES["tokens"][0], FUENTES["tokens"][1]))
        self._tabla.verticalHeader().setDefaultSectionSize(32)
        layout.addWidget(self._tabla)

        self._aplicar_estilos()

    def _aplicar_estilos(self):
        c = C()
        self._cab.setStyleSheet(f"""
            QFrame {{
                background: {c['panel']};
                border-bottom: 1px solid {c['borde']};
            }}
            QLabel {{
                color: {c['tag_tok_cab']};
                font-family: 'Segoe UI', sans-serif;
                font-size: 8pt;
                font-weight: bold;
                background: transparent;
            }}
        """)
        self._lbl_conteo.setStyleSheet(
            f"color: {c['subtitulo_fg']}; font-family: 'Cascadia Code', monospace; font-size: 8pt;"
        )
        self._tabla.setStyleSheet(f"""
            QTableWidget {{
                background: {c['tabla_bg']};
                color: {c['tabla_fg']};
                border: none;
                gridline-color: transparent;
                alternate-background-color: {c['panel']};
                outline: none;
            }}
            QHeaderView::section {{
                background: {c['panel']};
                color: {c['tag_tok_cab']};
                padding: 6px 10px;
                border: none;
                border-bottom: 2px solid {c['tab_indicador']};
                font-family: 'Segoe UI', sans-serif;
                font-size: 8pt;
                font-weight: bold;
                text-transform: uppercase;
            }}
            QTableWidget::item {{
                padding: 4px 10px;
                border-bottom: 1px solid {c['borde']};
            }}
            QTableWidget::item:selected {{
                background: {c['seleccion']};
                color: {c['tab_fg_act']};
            }}
            QScrollBar:vertical {{
                background: {c['scrollbar_bg']};
                width: 8px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {c['scrollbar_handle']};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {c['scrollbar_handle_hover']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

    def aplicar_tema(self):
        self._aplicar_estilos()

    def actualizar(self, tabla_dict: dict):
        c = C()
        self._tabla.setRowCount(0)
        tipo_colores = {
            "Entero": c["syn_number"],
            "Real": c["syn_number"],
            "Texto": c["syn_string"],
            "Logico": c["syn_builtin"],
        }
        for var, info in tabla_dict.items():
            row = self._tabla.rowCount()
            self._tabla.insertRow(row)
            val = str(info["valor"]) if info["valor"] is not None else "—"
            tipo = info["tipo"]
            tipo_color = tipo_colores.get(tipo, c["tabla_fg"])
            datos = [
                (var, c["tag_tok_tipo"], QFont.Weight.Bold),
                (tipo, tipo_color, QFont.Weight.Normal),
                (
                    val,
                    c["syn_string"] if tipo == "Texto" else c["tabla_fg"],
                    QFont.Weight.Normal,
                ),
                (str(info["linea"]), c["subtitulo_fg"], QFont.Weight.Normal),
            ]
            for col, (texto, color, peso) in enumerate(datos):
                item = QTableWidgetItem(texto)
                item.setForeground(QColor(color))
                f = QFont(FUENTES["tokens"][0], FUENTES["tokens"][1])
                f.setWeight(peso)
                item.setFont(f)
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
                )
                self._tabla.setItem(row, col, item)
        n = len(tabla_dict)
        self._lbl_conteo.setText(f"{n} variable{'s' if n != 1 else ''}")

    def limpiar(self):
        self._tabla.setRowCount(0)
        self._lbl_conteo.setText("0 variables")


# ── Vista de tokens ───────────────────────────────────────────────────────────


class TokensWidget(QWidget):
    _CATEGORIAS = {
        "KEYWORD": "syn_keyword",
        "TYPE": "syn_type",
        "STRING": "syn_string",
        "NUMBER": "syn_number",
        "BUILTIN": "syn_builtin",
        "OPERATOR": "syn_operator",
        "PUNCT": "syn_punct",
        "ID": "syn_id",
        "COMMENT": "syn_comment",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._construir()

    def _construir(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        cab = QFrame()
        cab.setFixedHeight(38)
        cab_lay = QHBoxLayout(cab)
        cab_lay.setContentsMargins(12, 0, 8, 0)
        cab_lay.setSpacing(8)

        lbl = QLabel("⟨/⟩ TOKENS")
        cab_lay.addWidget(lbl)
        cab_lay.addStretch()

        self._lbl_conteo = QLabel("0 tokens")
        cab_lay.addWidget(self._lbl_conteo)

        self._cab = cab
        layout.addWidget(cab)

        cols = ["#", "Línea", "Tipo", "Valor"]
        self._tabla = QTableWidget(0, len(cols))
        self._tabla.setHorizontalHeaderLabels(cols)
        self._tabla.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self._tabla.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self._tabla.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self._tabla.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch
        )
        self._tabla.horizontalHeader().setStretchLastSection(True)
        self._tabla.verticalHeader().setVisible(False)
        self._tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._tabla.setShowGrid(False)
        self._tabla.setAlternatingRowColors(True)
        self._tabla.setFont(QFont(FUENTES["tokens"][0], FUENTES["tokens"][1]))
        self._tabla.verticalHeader().setDefaultSectionSize(28)
        layout.addWidget(self._tabla)

        self._aplicar_estilos()

    def _aplicar_estilos(self):
        c = C()
        self._cab.setStyleSheet(f"""
            QFrame {{
                background: {c['panel']};
                border-bottom: 1px solid {c['borde']};
            }}
            QLabel {{
                color: {c['tag_tok_cab']};
                font-family: 'Segoe UI', sans-serif;
                font-size: 8pt;
                font-weight: bold;
                background: transparent;
            }}
        """)
        self._lbl_conteo.setStyleSheet(
            f"color: {c['subtitulo_fg']}; font-family: 'Cascadia Code', monospace; font-size: 8pt;"
        )
        self._tabla.setStyleSheet(f"""
            QTableWidget {{
                background: {c['tabla_bg']};
                color: {c['tabla_fg']};
                border: none;
                gridline-color: transparent;
                alternate-background-color: {c['panel']};
                outline: none;
            }}
            QHeaderView::section {{
                background: {c['panel']};
                color: {c['tag_tok_cab']};
                padding: 6px 10px;
                border: none;
                border-bottom: 2px solid {c['tab_indicador']};
                font-family: 'Segoe UI', sans-serif;
                font-size: 8pt;
                font-weight: bold;
            }}
            QTableWidget::item {{
                padding: 2px 10px;
                border-bottom: 1px solid {c['borde']};
            }}
            QTableWidget::item:selected {{
                background: {c['seleccion']};
                color: {c['tab_fg_act']};
            }}
            QScrollBar:vertical {{
                background: {c['scrollbar_bg']};
                width: 8px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {c['scrollbar_handle']};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {c['scrollbar_handle_hover']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            QScrollBar:horizontal {{
                background: {c['scrollbar_bg']};
                height: 8px;
                border: none;
            }}
            QScrollBar::handle:horizontal {{
                background: {c['scrollbar_handle']};
                border-radius: 4px;
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
        """)

    def aplicar_tema(self):
        self._aplicar_estilos()

    def actualizar(self, codigo: str):
        from core.lexer import tokenizar

        c = C()
        lista = tokenizar(codigo)
        self._tabla.setRowCount(0)
        for i, (tipo, valor, linea) in enumerate(lista):
            row = self._tabla.rowCount()
            self._tabla.insertRow(row)
            tipo_upper = tipo.upper()
            color_key = None
            for cat, key in self._CATEGORIAS.items():
                if cat in tipo_upper:
                    color_key = key
                    break
            token_color = c[color_key] if color_key else c["tabla_fg"]
            datos = [
                (str(i + 1), c["subtitulo_fg"], False),
                (str(linea), c["tag_tok_linea"], False),
                (tipo, token_color, True),
                (repr(valor), c["tabla_fg"], False),
            ]
            for col, (texto, color, bold) in enumerate(datos):
                item = QTableWidgetItem(texto)
                item.setForeground(QColor(color))
                f = QFont(FUENTES["tokens"][0], FUENTES["tokens"][1])
                if bold:
                    f.setWeight(QFont.Weight.Bold)
                item.setFont(f)
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
                )
                self._tabla.setItem(row, col, item)
        n = len(lista)
        self._lbl_conteo.setText(f"{n} token{'s' if n != 1 else ''}")

    def limpiar(self):
        self._tabla.setRowCount(0)
        self._lbl_conteo.setText("0 tokens")


# ── Panel de resultados completo ──────────────────────────────────────────────


class PanelResultados(QWidget):
    """
    Panel derecho del IDE con tres vistas principales:
    Consola, Símbolos y Tokens.

    Los textos de sección se muestran en un encabezado horizontal arriba del panel.
    """

    _IDX_CONSOLA = 0
    _IDX_SIMBOLOS = 1
    _IDX_TOKENS = 2

    _SECCIONES = [
        ("Resultado", ""),
        ("Tabla de Símbolos", ""),
        ("Tokens", ""),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._vista_activa: int = self._IDX_CONSOLA
        self._construir()

    def _construir(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Encabezado de sección ──────────────────────────────────────────────
        self._cabecera = QFrame()
        cab_lay = QHBoxLayout(self._cabecera)
        cab_lay.setContentsMargins(12, 10, 12, 10)
        cab_lay.setSpacing(24)

        self._etiquetas: list[QLabel] = []
        for idx, (texto, atajo) in enumerate(self._SECCIONES):
            label = QLabel(texto + (f" ({atajo})" if atajo else ""))
            label.setCursor(Qt.CursorShape.PointingHandCursor)
            label.mousePressEvent = lambda event, i=idx: self._cambiar_vista(i)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
            )
            label.setFixedHeight(28)
            cab_lay.addWidget(label)
            self._etiquetas.append(label)
        layout.addWidget(self._cabecera)

        # ── Stack de contenido ────────────────────────────────────────────────
        self._stack = QStackedWidget()
        self._stack.setMinimumWidth(ANCHO_PANEL_MIN)
        self._stack.setMaximumWidth(ANCHO_PANEL_MAX)
        self._stack.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        self.consola = ConsolaWidget()
        self.tabla_simbolos = TablaSimbolosWidget()
        self.tokens = TokensWidget()

        self._stack.addWidget(self.consola)
        self._stack.addWidget(self.tabla_simbolos)
        self._stack.addWidget(self.tokens)
        self._stack.setCurrentIndex(self._IDX_CONSOLA)

        layout.addWidget(self._stack)
        self._aplicar_estilos()
        self._actualizar_estilos_encabezado()

    # ── Lógica de cambio de vista ──────────────────────────────────────────────

    def _cambiar_vista(self, idx: int):
        self._vista_activa = idx
        self._stack.setCurrentIndex(idx)
        self._actualizar_estilos_encabezado()

    def _actualizar_estilos_encabezado(self):
        c = C()
        for idx, label in enumerate(self._etiquetas):
            color = c["tag_exito"] if idx == self._vista_activa else c["tab_fg_inact"]
            weight = "font-weight:bold;" if idx == self._vista_activa else ""
            label.setStyleSheet(
                f"color: {color}; {weight} font-family: 'Segoe UI'; font-size: 9pt;"
                f"padding: 4px 8px; border-bottom: {'2px solid ' + c['tag_exito'] if idx == self._vista_activa else '2px solid transparent'};"
            )

    # ── Estilos ───────────────────────────────────────────────────────────────

    def _aplicar_estilos(self):
        c = C()
        self._cabecera.setStyleSheet(f"""
            QFrame {{
                background: {c['panel']};
                border-bottom: 1px solid {c['borde']};
            }}
        """)
        self._actualizar_estilos_encabezado()

    def aplicar_tema(self):
        self._aplicar_estilos()
        self.consola.aplicar_tema()
        self.tabla_simbolos.aplicar_tema()
        self.tokens.aplicar_tema()

    # ── API principal ─────────────────────────────────────────────────────────

    def mostrar_resultado(self, resultado: dict, codigo: str = ""):
        self.consola.mostrar_resultado(resultado)
        self.tabla_simbolos.actualizar(resultado.get("tabla", {}))
        if codigo:
            self.tokens.actualizar(codigo)
        self._cambiar_vista(self._IDX_CONSOLA)

    def limpiar_todo(self):
        self.consola.limpiar()
        self.tabla_simbolos.limpiar()
        self.tokens.limpiar()

    def ir_a_consola(self):
        self._cambiar_vista(self._IDX_CONSOLA)

    def ir_a_simbolos(self):
        self._cambiar_vista(self._IDX_SIMBOLOS)

    def ir_a_tokens(self):
        self._cambiar_vista(self._IDX_TOKENS)
