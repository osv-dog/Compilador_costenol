# gui/editor.py — Gestor de pestañas del editor con syntax highlighting
import re
import tkinter as tk

from gui.temas import C, FUENTES, tags_syntax

# ── Patrón de syntax highlighting para Costeñol ───────────────────────────────
_PATRON = re.compile(
    r"(?P<comment>//[^\n]*)"
    r"|(?P<string>\"[^\"]*\")"
    r"|(?P<number>\b[0-9]+(?:[,\.][0-9]+)?\b)"
    r"|(?P<builtin>\b(?:Mensaje|Captura)\b)"
    r"|(?P<keyword>\b(?:Si|Sino|Mientras|Para|Retornar|Fin|Hacer|Verdadero|Falso)\b)"
    r"|(?P<type_kw>\b(?:Entero|Real|Texto|Logico)\b)"
    r"|(?P<operator>[+\-*/=<>!&|]+)"
    r"|(?P<punct>[();,.])"
    r"|(?P<id>\b[A-Za-z_]\w*\b)"
)

_TAG_MAP = {
    "comment": "syn_comment",
    "string": "syn_string",
    "number": "syn_number",
    "builtin": "syn_builtin",
    "keyword": "syn_keyword",
    "type_kw": "syn_type",
    "operator": "syn_operator",
    "punct": "syn_punct",
    "id": "syn_id",
}

_TODOS_LOS_TAGS_SYN = list(_TAG_MAP.values())


class GestorPestanas:
    """
    Maneja N pestañas de editor independientes.
    Cada pestaña tiene su propio tk.Text con números de línea,
    syntax highlighting, resaltado de línea activa y marcado de errores.
    """

    def __init__(self, parent: tk.Widget, app):
        self.app = app  # referencia a VentanaCompilador
        self.parent = parent
        self.pestanas: dict[str, dict] = {}
        self._contador = 0

        self._construir_esqueleto()

    # ── Construcción inicial ──────────────────────────────────────────────────

    def _construir_esqueleto(self):
        c = C()
        self.frame_ext = tk.Frame(self.parent, bg=c["borde"])
        # El pack y pack_propagate serán configurados por la ventana principal

        # Barra de pestañas superior
        self.barra_tabs = tk.Frame(self.frame_ext, bg=c["panel"], height=34)
        self.barra_tabs.pack(fill="x")
        self.barra_tabs.pack_propagate(False)

        # Zona donde viven los editores (solo uno visible a la vez)
        self.zona_editor = tk.Frame(self.frame_ext, bg=c["editor_bg"])
        self.zona_editor.pack(fill="both", expand=True)

        self.tab_activa: str | None = None

    # ── API pública ───────────────────────────────────────────────────────────

    def nueva_pestana(
        self, nombre: str | None = None, contenido: str = "", ruta: str | None = None
    ) -> str:
        self._contador += 1
        if nombre is None:
            nombre = f"sin_titulo_{self._contador}.pqek"

        tab_id = f"tab_{self._contador}"
        frame = self._crear_frame_editor(tab_id)
        btn = self._crear_boton_tab(tab_id, nombre)

        self.pestanas[tab_id] = {
            "frame": frame["root"],
            "editor": frame["editor"],
            "nums": frame["nums"],
            "btn_frame": btn["frame"],
            "btn_label": btn["label"],
            "btn_cerrar": btn["cerrar"],
            "ruta": ruta,
            "nombre": nombre,
            "modificado": False,
        }

        if contenido:
            frame["editor"].insert("1.0", contenido)
            self._highlight(tab_id)
            self._sync_nums(tab_id)

        self.seleccionar(tab_id)
        return tab_id

    def seleccionar(self, tab_id: str):
        c = C()
        for tid, d in self.pestanas.items():
            d["frame"].pack_forget()
            activo = tid == tab_id
            d["btn_label"].config(
                bg=c["tab_activa"] if activo else c["tab_inactiva"],
                fg=c["tab_fg_act"] if activo else c["tab_fg_inact"],
            )
            d["btn_cerrar"].config(
                bg=c["tab_activa"] if activo else c["tab_inactiva"],
                fg=c["tab_fg_act"] if activo else c["tab_fg_inact"],
            )

        if tab_id in self.pestanas:
            self.pestanas[tab_id]["frame"].pack(fill="both", expand=True)
            self.tab_activa = tab_id
            # Solo llamar si la app ya terminó de construirse
            if hasattr(self.app, "editor_mgr"):
                self.app.actualizar_estado()

    def cerrar_pestana(self, tab_id: str):
        if tab_id not in self.pestanas:
            return
        d = self.pestanas[tab_id]
        if d["modificado"]:
            from tkinter import messagebox

            if not messagebox.askyesno(
                "Cerrar pestaña",
                f"'{d['nombre']}' tiene cambios sin guardar. ¿Cerrar de todas formas?",
            ):
                return
        d["btn_frame"].destroy()
        d["frame"].destroy()
        del self.pestanas[tab_id]
        if self.pestanas:
            self.seleccionar(list(self.pestanas)[-1])
        else:
            self.tab_activa = None

    def editor_activo(self) -> tk.Text | None:
        d = self.datos_activos()
        return d["editor"] if d else None

    def datos_activos(self) -> dict | None:
        if self.tab_activa and self.tab_activa in self.pestanas:
            return self.pestanas[self.tab_activa]
        return None

    def marcar_errores(self, numeros_linea: list[int]):
        editor = self.editor_activo()
        if not editor:
            return
        for n in numeros_linea:
            editor.tag_add("error_line", f"{n}.0", f"{n}.end+1c")
            editor.see(f"{n}.0")

    def limpiar_errores(self):
        editor = self.editor_activo()
        if editor:
            editor.tag_remove("error_line", "1.0", "end")

    def aplicar_tema(self):
        """Reaplica todos los colores del tema activo a todas las pestañas."""
        c = C()
        self.frame_ext.config(bg=c["borde"])
        self.barra_tabs.config(bg=c["panel"])
        self.zona_editor.config(bg=c["editor_bg"])

        for tab_id, d in self.pestanas.items():
            activo = tab_id == self.tab_activa
            d["frame"].config(bg=c["editor_bg"])
            d["editor"].config(
                bg=c["editor_bg"],
                fg=c["editor_fg"],
                insertbackground=c["cursor"],
                selectbackground=c["seleccion"],
                selectforeground=c["editor_fg"],
            )
            d["nums"].config(bg=c["linea_num_bg"], fg=c["linea_num_fg"])
            d["btn_frame"].config(bg=c["panel"])
            d["btn_label"].config(
                bg=c["tab_activa"] if activo else c["tab_inactiva"],
                fg=c["tab_fg_act"] if activo else c["tab_fg_inact"],
            )
            d["btn_cerrar"].config(
                bg=c["tab_activa"] if activo else c["tab_inactiva"],
                fg=c["tab_fg_act"] if activo else c["tab_fg_inact"],
            )
            self._configurar_tags(tab_id)
            self._highlight(tab_id)

    def marcar_modificado(self, tab_id: str, valor: bool = True):
        if tab_id not in self.pestanas:
            return
        self.pestanas[tab_id]["modificado"] = valor
        self._actualizar_titulo_tab(tab_id)

    # ── Construcción interna ──────────────────────────────────────────────────

    def _crear_frame_editor(self, tab_id: str) -> dict:
        c = C()
        root_frame = tk.Frame(self.zona_editor, bg=c["editor_bg"])

        frame_texto = tk.Frame(root_frame, bg=c["editor_bg"])
        frame_texto.pack(fill="both", expand=True)

        # Números de línea
        nums = tk.Text(
            frame_texto,
            width=4,
            bg=c["linea_num_bg"],
            fg=c["linea_num_fg"],
            font=FUENTES["codigo"],
            state="disabled",
            bd=0,
            padx=6,
            selectbackground=c["linea_num_bg"],
            relief="flat",
        )
        nums.pack(side="left", fill="y")

        tk.Frame(frame_texto, bg=c["borde"], width=1).pack(side="left", fill="y")

        # Editor principal
        editor = tk.Text(
            frame_texto,
            bg=c["editor_bg"],
            fg=c["editor_fg"],
            font=FUENTES["codigo"],
            insertbackground=c["cursor"],
            selectbackground=c["seleccion"],
            selectforeground=c["editor_fg"],
            undo=True,
            bd=0,
            padx=12,
            pady=8,
            wrap="none",
            relief="flat",
            tabs=("1c",),
        )
        editor.pack(side="left", fill="both", expand=True)

        # Frame para scrollbars (los crearemos después para control inteligente)
        frame_scrollbars = tk.Frame(root_frame, bg=c["editor_bg"])
        frame_scrollbars.pack(fill="x")

        # Scrollbars
        scroll_y = tk.Scrollbar(
            frame_texto,
            orient="vertical",
            bg=c["borde"],
            troughcolor=c["borde"],
            width=10,
        )

        def make_sync_y_handler(text_widget, nums_widget, scrollbar):
            def handler(*args):
                # Mostrar/ocultar scrollbar según sea necesario
                if float(args[0]) <= 0.0 and float(args[1]) >= 1.0:
                    if scrollbar.winfo_manager():
                        scrollbar.pack_forget()
                else:
                    if not scrollbar.winfo_manager():
                        scrollbar.pack(side="right", fill="y")
                scrollbar.set(*args)
                nums_widget.yview("moveto", args[0])

            return handler

        editor["yscrollcommand"] = make_sync_y_handler(editor, nums, scroll_y)
        nums["yscrollcommand"] = scroll_y.set
        scroll_y["command"] = self._make_dual_yview(editor, nums)

        scroll_x = tk.Scrollbar(
            frame_scrollbars,
            orient="horizontal",
            command=editor.xview,
            bg=c["borde"],
            troughcolor=c["borde"],
            width=8,
        )

        def make_sync_x_handler(scrollbar):
            def handler(*args):
                # Mostrar/ocultar scrollbar según sea necesario
                if float(args[0]) <= 0.0 and float(args[1]) >= 1.0:
                    if scrollbar.winfo_manager():
                        scrollbar.pack_forget()
                else:
                    if not scrollbar.winfo_manager():
                        scrollbar.pack(fill="x")
                scrollbar.set(*args)

            return handler

        editor["xscrollcommand"] = make_sync_x_handler(scroll_x)

        # Tags iniciales
        self._configurar_tags_en(editor)

        # Eventos
        editor.bind("<KeyRelease>", lambda e, t=tab_id: self._on_key(e, t))
        editor.bind("<ButtonRelease>", lambda e, t=tab_id: self._on_click(e, t))

        return {"root": root_frame, "editor": editor, "nums": nums}

    def _crear_boton_tab(self, tab_id: str, nombre: str) -> dict:
        c = C()
        frame = tk.Frame(self.barra_tabs, bg=c["panel"])
        frame.pack(side="left")

        lbl = tk.Label(
            frame,
            text=f"  {nombre}  ",
            bg=c["tab_inactiva"],
            fg=c["tab_fg_inact"],
            font=FUENTES["ui"],
            cursor="hand2",
            padx=2,
            pady=7,
        )
        lbl.pack(side="left")

        cerrar = tk.Label(
            frame,
            text="×",
            bg=c["tab_inactiva"],
            fg=c["tab_fg_inact"],
            font=("Segoe UI", 11),
            cursor="hand2",
            padx=4,
            pady=7,
        )
        cerrar.pack(side="left")

        lbl.bind("<Button-1>", lambda e, t=tab_id: self.seleccionar(t))
        cerrar.bind("<Button-1>", lambda e, t=tab_id: self.cerrar_pestana(t))

        return {"frame": frame, "label": lbl, "cerrar": cerrar}

    # ── Syntax highlighting ───────────────────────────────────────────────────

    def _configurar_tags(self, tab_id: str):
        self._configurar_tags_en(self.pestanas[tab_id]["editor"])

    def _configurar_tags_en(self, editor: tk.Text):
        c = C()
        for tag, opts in tags_syntax().items():
            editor.tag_configure(tag, **opts)
        editor.tag_configure("error_line", background=c["error_bg"])
        editor.tag_configure("linea_activa", background=c["linea_activa"])

    def _highlight(self, tab_id: str):
        editor = self.pestanas[tab_id]["editor"]
        for tag in _TODOS_LOS_TAGS_SYN:
            editor.tag_remove(tag, "1.0", "end")

        contenido = editor.get("1.0", "end-1c")
        for nlinea, linea in enumerate(contenido.split("\n"), 1):
            for m in _PATRON.finditer(linea):
                tag = _TAG_MAP.get(m.lastgroup)
                if tag:
                    editor.tag_add(tag, f"{nlinea}.{m.start()}", f"{nlinea}.{m.end()}")

    # ── Eventos ───────────────────────────────────────────────────────────────

    def _on_key(self, event, tab_id: str):
        if tab_id not in self.pestanas:
            return
        self._highlight(tab_id)
        self._sync_nums(tab_id)
        self._resaltar_linea_activa(tab_id)
        if not self.pestanas[tab_id]["modificado"]:
            self.marcar_modificado(tab_id, True)
        self.app.actualizar_estado()

    def _on_click(self, event, tab_id: str):
        if tab_id in self.pestanas:
            self._resaltar_linea_activa(tab_id)
            self.app.actualizar_estado()

    # ── Utilidades internas ───────────────────────────────────────────────────

    def _sync_nums(self, tab_id: str):
        d = self.pestanas[tab_id]
        editor, nums = d["editor"], d["nums"]
        n = editor.get("1.0", "end-1c").count("\n") + 1
        nums.config(state="normal")
        nums.delete("1.0", "end")
        for i in range(1, n + 1):
            nums.insert("end", f"{i:>3}\n")
        nums.config(state="disabled")

    def _resaltar_linea_activa(self, tab_id: str):
        editor = self.pestanas[tab_id]["editor"]
        editor.tag_remove("linea_activa", "1.0", "end")
        editor.tag_add("linea_activa", "insert linestart", "insert lineend+1c")

    def _actualizar_titulo_tab(self, tab_id: str):
        d = self.pestanas[tab_id]
        nombre = ("● " if d["modificado"] else "") + d["nombre"]
        d["btn_label"].config(text=f"  {nombre}  ")

    @staticmethod
    def _make_sync_y(scrollbar_set, nums: tk.Text):
        def handler(*args):
            scrollbar_set(*args)
            nums.yview("moveto", args[0])

        return handler

    @staticmethod
    def _make_dual_yview(editor: tk.Text, nums: tk.Text):
        def handler(*args):
            editor.yview(*args)
            nums.yview(*args)

        return handler
