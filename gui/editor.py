from PyQt6.QtCore import Qt, QRegularExpression, pyqtSignal
from PyQt6.QtGui import (
    QColor,
    QFont,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextCursor,
    QPainter,
    QTextFormat,
)
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPlainTextEdit,
    QTextEdit,
    QTabWidget,
)

from gui.temas import C, FUENTES

# ── Syntax Highlighter

_REGLAS_SYNTAX = [
    (r"//[^\n]*", "comment"),
    (r'"[^"]*"', "string"),
    (r"\b[0-9]+(?:[,\.][0-9]+)?\b", "number"),
    (r"\b[A-Za-z_]\w*\b", "id"),
    (r"\b(?:Mensaje|Captura)\b", "builtin"),
    (r"\b(?:Si|Sino|Mientras|Para|Retornar|Fin|Hacer|Verdadero|Falso)\b", "keyword"),
    (r"\b(?:Entero|Real|Texto|Logico)\b", "type_kw"),
    (r"[+\-*/=<>!&|]+", "operator"),
    (r"[();,.]", "punct"),
]


def _fmt(color: str, bold: bool = False, italic: bool = False) -> QTextCharFormat:
    f = QTextCharFormat()
    f.setForeground(QColor(color))
    if bold:
        f.setFontWeight(QFont.Weight.Bold)
    if italic:
        f.setFontItalic(True)
    return f


class CosteñolHighlighter(QSyntaxHighlighter):
    def __init__(self, doc):
        super().__init__(doc)
        self._reglas: list[tuple] = []
        self._construir_reglas()

    def _construir_reglas(self):
        c = C()
        mapping = {
            "comment": (c["syn_comment"], False, True),
            "string": (c["syn_string"], False, False),
            "number": (c["syn_number"], False, False),
            "builtin": (c["syn_builtin"], True, False),
            "keyword": (c["syn_keyword"], True, False),
            "type_kw": (c["syn_type"], True, False),
            "operator": (c["syn_operator"], False, False),
            "punct": (c["syn_punct"], False, False),
            "id": (c["syn_id"], False, False),
        }
        self._reglas = []
        for patron, nombre in _REGLAS_SYNTAX:
            color, bold, italic = mapping[nombre]
            self._reglas.append((QRegularExpression(patron), _fmt(color, bold, italic)))

    def rehighlight_theme(self):
        self._construir_reglas()
        self.rehighlight()

    def highlightBlock(self, text: str):
        for regex, fmt in self._reglas:
            it = regex.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)


# ── Área de números de línea


class LineNumberArea(QWidget):
    def __init__(self, editor: "EditorWidget"):
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self):
        from PyQt6.QtCore import QSize

        return QSize(self._editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self._editor.line_number_area_paint_event(event)


# ── Widget de editor individual


class EditorWidget(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._line_number_area = LineNumberArea(self)
        self._highlighter = CosteñolHighlighter(self.document())

        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._highlight_current_line)

        self._update_line_number_area_width(0)
        self._aplicar_estilo()

    def _aplicar_estilo(self):
        c = C()
        f = QFont(FUENTES["codigo"][0], FUENTES["codigo"][1])
        self.setFont(f)
        self.setStyleSheet("")
        palette = self.palette()
        palette.setColor(palette.ColorRole.Text, QColor(c["editor_fg"]))
        palette.setColor(palette.ColorRole.Base, QColor(c["editor_bg"]))
        palette.setColor(palette.ColorRole.Highlight, QColor(c["seleccion"]))
        palette.setColor(palette.ColorRole.HighlightedText, QColor(c["editor_fg"]))
        self.setPalette(palette)

        self._line_number_area.setStyleSheet(
            f"background-color: {c['linea_num_bg']}; color: {c['linea_num_fg']};"
        )
        self._highlight_current_line()

    def aplicar_tema(self):
        self._aplicar_estilo()
        self._highlighter.rehighlight_theme()

    # ── Números de línea

    def line_number_area_width(self) -> int:
        digits = max(1, len(str(self.blockCount())))
        return 10 + self.fontMetrics().horizontalAdvance("9") * (digits + 1)

    def _update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect, dy):
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(
                0, rect.y(), self._line_number_area.width(), rect.height()
            )
        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        from PyQt6.QtCore import QRect

        self._line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def line_number_area_paint_event(self, event):
        c = C()
        painter = QPainter(self._line_number_area)
        painter.fillRect(event.rect(), QColor(c["linea_num_bg"]))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(
            self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        )
        bottom = top + int(self.blockBoundingRect(block).height())

        font = QFont(FUENTES["codigo"][0], FUENTES["codigo"][1] - 1)
        painter.setFont(font)

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.setPen(QColor(c["linea_num_fg"]))
                painter.drawText(
                    0,
                    top,
                    self._line_number_area.width() - 6,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    str(block_number + 1),
                )
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    # ── Resaltado de línea activa

    def _highlight_current_line(self):
        c = C()
        extras = []
        if not self.isReadOnly():
            sel = QTextEdit.ExtraSelection()
            sel.format.setBackground(QColor(c["linea_activa"]))
            sel.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            sel.cursor = self.textCursor()
            sel.cursor.clearSelection()
            extras.append(sel)
        self.setExtraSelections(extras)

    # ── Marcado de errores

    def marcar_errores(self, lineas: list[int]):
        c = C()
        extras = list(self.extraSelections())
        doc = self.document()
        for n in lineas:
            block = doc.findBlockByLineNumber(n - 1)
            if not block.isValid():
                continue
            sel = QTextEdit.ExtraSelection()
            sel.format.setBackground(QColor(c["error_bg"]))
            sel.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            cursor = QTextCursor(block)
            sel.cursor = cursor
            extras.append(sel)
        self.setExtraSelections(extras)

    def limpiar_errores(self):
        self._highlight_current_line()


# ── Gestor de pestañas


class GestorPestanas(QWidget):
    def __init__(self, parent: QWidget, app):
        super().__init__(parent)
        self.app = app
        self._contador = 0
        self.pestanas: dict[str, dict] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self._on_close_request)
        self.tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.tabs)

        self._aplicar_estilo_tabs()

    # ── Estilo

    def _aplicar_estilo_tabs(self):
        c = C()
        self.setStyleSheet(f"""
            GestorPestanas {{
                background: {c['editor_bg']};
            }}
        """)
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: {c['editor_bg']};
            }}
            QTabBar {{
                background: {c['panel']};
            }}
            QTabBar::tab {{
                background: {c['tab_inactiva']};
                color: {c['tab_fg_inact']};
                padding: 7px 16px;
                border: none;
                font-family: 'Segoe UI';
                font-size: 9pt;
                min-width: 100px;
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
            QTabBar::close-button {{
                image: none;
                subcontrol-position: right;
            }}
        """)

    # ── API pública

    def nueva_pestana(
        self, nombre: str | None = None, contenido: str = "", ruta: str | None = None
    ) -> str:
        self._contador += 1
        if nombre is None:
            nombre = f"sin_titulo_{self._contador}.pqek"

        tab_id = f"tab_{self._contador}"
        editor = EditorWidget()
        editor.textChanged.connect(lambda t=tab_id: self._on_text_changed(t))
        editor.cursorPositionChanged.connect(lambda: self.app.actualizar_estado())

        idx = self.tabs.addTab(editor, nombre)
        self.tabs.setCurrentIndex(idx)

        self.pestanas[tab_id] = {
            "editor": editor,
            "idx": idx,
            "ruta": ruta,
            "nombre": nombre,
            "modificado": False,
        }
        editor.setProperty("tab_id", tab_id)
        editor.blockSignals(True)
        editor.setPlainText(contenido)
        editor.blockSignals(False)
        editor._highlighter.rehighlight()

        return tab_id

    def seleccionar(self, tab_id: str):
        d = self.pestanas.get(tab_id)
        if d:
            self.tabs.setCurrentWidget(d["editor"])

    def cerrar_pestana(self, tab_id: str):
        if tab_id not in self.pestanas:
            return
        d = self.pestanas[tab_id]
        if d["modificado"]:
            from PyQt6.QtWidgets import QMessageBox

            r = QMessageBox.question(
                self,
                "Cerrar pestaña",
                f"'{d['nombre']}' tiene cambios sin guardar. ¿Cerrar de todas formas?",
            )
            if r != QMessageBox.StandardButton.Yes:
                return
        idx = self.tabs.indexOf(d["editor"])
        self.tabs.removeTab(idx)
        del self.pestanas[tab_id]

    @property
    def tab_activa(self) -> str | None:
        w = self.tabs.currentWidget()
        if w is None:
            return None
        return w.property("tab_id")

    def editor_activo(self) -> EditorWidget | None:
        return self.tabs.currentWidget()

    def datos_activos(self) -> dict | None:
        tid = self.tab_activa
        if tid:
            return self.pestanas.get(tid)
        return None

    def marcar_errores(self, lineas: list[int]):
        editor = self.editor_activo()
        if editor:
            editor.marcar_errores(lineas)

    def limpiar_errores(self):
        editor = self.editor_activo()
        if editor:
            editor.limpiar_errores()

    def marcar_modificado(self, tab_id: str, valor: bool = True):
        if tab_id not in self.pestanas:
            return
        self.pestanas[tab_id]["modificado"] = valor
        self._actualizar_titulo_tab(tab_id)

    def aplicar_tema(self):
        self._aplicar_estilo_tabs()
        for d in self.pestanas.values():
            d["editor"].aplicar_tema()

    # ── Slots internos

    def _on_close_request(self, idx: int):
        w = self.tabs.widget(idx)
        if w is None:
            return
        tab_id = w.property("tab_id")
        if tab_id:
            self.cerrar_pestana(tab_id)

    def _on_tab_changed(self, idx: int):
        if hasattr(self.app, "editor_mgr"):
            self.app.actualizar_estado()

    def _on_text_changed(self, tab_id: str):
        if tab_id in self.pestanas and not self.pestanas[tab_id]["modificado"]:
            self.marcar_modificado(tab_id, True)

    def _actualizar_titulo_tab(self, tab_id: str):
        d = self.pestanas[tab_id]
        nombre = ("● " if d["modificado"] else "") + d["nombre"]
        idx = self.tabs.indexOf(d["editor"])
        if idx >= 0:
            self.tabs.setTabText(idx, nombre)
