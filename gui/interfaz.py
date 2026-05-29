# gui/interfaz.py — Ventana principal del compilador Costeñol
import os
import random
import re
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog

from core.parser import compilar
from core.lexer import tokenizar
from gui.temas import (
    C,
    FUENTES,
    alternar_tema,
    cambiar_tema,
    tema_nombre,
    tags_resultado,
    tags_tokens,
    MENSAJES_EXITO,
    MENSAJES_ERROR,
    MENSAJE_SIN_CODIGO,
    CODIGO_EJEMPLO,
)
from gui.editor import GestorPestanas


class VentanaCompilador:
    def __init__(self, root: tk.Tk):
        self.root = root
        self._construir()

    # ── Construcción general ──────────────────────────────────────────────────

    def _construir(self):
        # Establecer tema claro por defecto
        cambiar_tema("claro")

        c = C()
        self.root.title("COSTEÑOL IDE")
        # Iniciar en pantalla completa
        self.root.state("zoomed")
        self.root.minsize(920, 560)
        self.root.configure(bg=c["fondo"])

        self._construir_menu()
        self._construir_barra_superior()
        self._construir_cuerpo()
        self._construir_barra_estado()
        self._registrar_atajos()

    # ── Menú ──────────────────────────────────────────────────────────────────

    def _construir_menu(self):
        c = C()
        self.menubar = tk.Menu(
            self.root,
            bg=c["menu_bg"],
            fg=c["menu_fg"],
            activebackground=c["menu_activo_bg"],
            activeforeground=c["menu_activo_fg"],
            bd=0,
            relief="flat",
            tearoff=0,
        )
        self.root.config(menu=self.menubar)

        kw = dict(
            bg=c["menu_bg"],
            fg=c["menu_fg"],
            activebackground=c["menu_activo_bg"],
            activeforeground=c["menu_activo_fg"],
            tearoff=0,
        )

        # ── Archivo
        m_arch = tk.Menu(self.menubar, **kw)
        self.menubar.add_cascade(label="Archivo", menu=m_arch)
        m_arch.add_command(
            label="Nueva pestaña         Ctrl+T", command=self._nueva_pestana
        )
        m_arch.add_command(
            label="Abrir archivo...      Ctrl+O", command=self.abrir_archivo
        )
        m_arch.add_separator()
        m_arch.add_command(
            label="Guardar               Ctrl+S", command=self.guardar_archivo
        )
        m_arch.add_command(
            label="Guardar como...  Ctrl+Shift+S", command=self.guardar_como
        )
        m_arch.add_separator()
        m_arch.add_command(
            label="Cerrar pestaña        Ctrl+W", command=self._cerrar_tab_activa
        )
        m_arch.add_separator()
        m_arch.add_command(label="Salir", command=self.root.quit)

        # ── Compilar
        m_comp = tk.Menu(self.menubar, **kw)
        self.menubar.add_cascade(label="Compilar", menu=m_comp)
        m_comp.add_command(label="Compilar    F5", command=self.compilar)
        m_comp.add_command(label="Limpiar     F6", command=self.limpiar_todo)

        # ── Ver
        m_ver = tk.Menu(self.menubar, **kw)
        self.menubar.add_cascade(label="Ver", menu=m_ver)
        m_ver.add_command(
            label="Alternar tema  Ctrl+Shift+T", command=self._alternar_tema
        )

        self._menubar_ref = m_arch  # guardamos para reconfigurar en cambio de tema

    def _registrar_atajos(self):
        bind = self.root.bind
        bind("<Control-t>", lambda e: self._nueva_pestana())
        bind("<Control-o>", lambda e: self.abrir_archivo())
        bind("<Control-s>", lambda e: self.guardar_archivo())
        bind("<Control-S>", lambda e: self.guardar_como())
        bind("<Control-w>", lambda e: self._cerrar_tab_activa())
        bind("<F5>", lambda e: self.compilar())
        bind("<F6>", lambda e: self.limpiar_todo())
        bind("<Control-T>", lambda e: self._alternar_tema())

    # ── Barra superior ────────────────────────────────────────────────────────

    def _construir_barra_superior(self):
        c = C()
        self.barra_sup = tk.Frame(self.root, bg=c["panel"], height=52)
        self.barra_sup.pack(fill="x")
        self.barra_sup.pack_propagate(False)

        tk.Label(
            self.barra_sup,
            text="⟨/⟩  COSTEÑOL IDE",
            bg=c["panel"],
            fg=c["titulo_fg"],
            font=FUENTES["titulo"],
        ).pack(side="left", padx=18, pady=10)

        self.btn_tema = tk.Button(
            self.barra_sup,
            text="☀" if tema_nombre() == "oscuro" else "🌙",
            bg=c["btn_tema_bg"],
            fg=c["btn_tema_fg"],
            activebackground=c["seleccion"],
            activeforeground=c["titulo_fg"],
            font=("Segoe UI", 13),
            relief="flat",
            padx=8,
            pady=4,
            cursor="hand2",
            bd=0,
            command=self._alternar_tema,
        )
        self.btn_tema.pack(side="right", padx=(0, 8), pady=10)

        self._boton_barra(
            "🗑  Limpiar", c["btn_limpiar"], c["btn_limpiar_hover"], self.limpiar_todo
        )
        self._boton_barra(
            "▶  Compilar  F5", c["btn_compilar"], c["btn_compilar_hover"], self.compilar
        )

        tk.Frame(self.root, bg=c["borde"], height=1).pack(fill="x")

    def _boton_barra(self, texto: str, color: str, hover: str, cmd) -> tk.Button:
        b = tk.Button(
            self.barra_sup,
            text=texto,
            bg=color,
            fg="#FFFFFF",
            activebackground=hover,
            activeforeground="#FFFFFF",
            font=FUENTES["boton"],
            relief="flat",
            padx=14,
            pady=5,
            cursor="hand2",
            bd=0,
            command=cmd,
        )
        b.pack(side="right", padx=(0, 8), pady=10)
        return b

    # ── Cuerpo ────────────────────────────────────────────────────────────────

    def _construir_cuerpo(self):
        c = C()
        self.cuerpo = tk.Frame(self.root, bg=c["fondo"])
        self.cuerpo.pack(fill="both", expand=True)

        # Explorador de archivos (izquierda)
        self._construir_explorador()
        tk.Frame(self.cuerpo, bg=c["borde"], width=1).pack(side="left", fill="y")

        # Editor principal
        self.editor_mgr = GestorPestanas(self.cuerpo, self)
        self.editor_mgr.frame_ext.pack(side="left", fill="both", expand=True)

        # Separador redimensionable
        self.sep = tk.Frame(
            self.cuerpo, bg=c["borde"], width=6, cursor="sb_h_double_arrow"
        )
        self.sep.pack(side="left", fill="y", padx=1)
        self.sep.bind("<B1-Motion>", self._redimensionar)
        self.sep.bind("<ButtonPress-1>", self._iniciar_redimensionar)

        # Panel de resultados (derecha)
        self._construir_panel_resultados()

    def _iniciar_redimensionar(self, event):
        """Bloquea el tamaño cuando comienza el arrastre"""
        self.editor_mgr.frame_ext.pack_propagate(False)
        self.panel_res.pack_propagate(False)
        self._redimensionar(event)

    def _redimensionar(self, event):
        """Redimensiona mientras se arrastra"""
        x = event.x_root - self.cuerpo.winfo_rootx()
        total = self.cuerpo.winfo_width()
        sep_width = self.sep.winfo_width()
        new_panel_width = total - x - sep_width
        if 250 < new_panel_width < total - 250:
            self.panel_res.config(width=new_panel_width)
            self.cuerpo.update_idletasks()

    def _construir_explorador(self):
        c = C()
        self.explorador_frame = tk.Frame(self.cuerpo, bg=c["panel"], width=260)
        self.explorador_frame.pack(side="left", fill="y")
        self.explorador_frame.pack_propagate(False)

        self.lbl_explorador = tk.Label(
            self.explorador_frame,
            text="EXPLORADOR",
            bg=c["panel"],
            fg=c["tab_fg_act"],
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        )
        self.lbl_explorador.pack(fill="x", padx=14, pady=(14, 8))

        self._explorer_style = ttk.Style()
        self._explorer_style.theme_use("default")
        self._explorer_style.configure(
            "Explorer.Treeview",
            background=c["panel"],
            fieldbackground=c["panel"],
            foreground=c["tabla_fg"],
            font=FUENTES["ui"],
            rowheight=24,
            borderwidth=0,
        )
        self._explorer_style.map(
            "Explorer.Treeview",
            background=[("selected", c["seleccion"])],
            foreground=[("selected", c["tab_fg_act"])],
        )

        self.tree_explorer = ttk.Treeview(
            self.explorador_frame,
            show="tree",
            style="Explorer.Treeview",
            selectmode="browse",
            columns=("path",),
        )
        self.tree_explorer.column("path", width=0, stretch=False)
        self.tree_explorer.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.tree_explorer.bind("<Double-1>", self._on_explorer_activate)

        self._cargar_explorador()

    def _cargar_explorador(self):
        self.tree_explorer.delete(*self.tree_explorer.get_children())
        examples_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "examples")
        )
        root_id = self.tree_explorer.insert(
            "",
            "end",
            text="examples",
            open=True,
            values=(examples_dir,),
        )
        self._agregar_items_explorador(root_id, examples_dir)

    def _agregar_items_explorador(self, parent, ruta):
        try:
            nombres = sorted(os.listdir(ruta), key=str.lower)
        except OSError:
            return
        for nombre in nombres:
            abs_path = os.path.join(ruta, nombre)
            if os.path.isdir(abs_path):
                node = self.tree_explorer.insert(
                    parent,
                    "end",
                    text=nombre,
                    values=(abs_path,),
                    open=False,
                )
                self._agregar_items_explorador(node, abs_path)
            else:
                self.tree_explorer.insert(
                    parent,
                    "end",
                    text=nombre,
                    values=(abs_path,),
                )

    def _on_explorer_activate(self, event):
        item = self.tree_explorer.focus()
        if not item:
            return
        values = self.tree_explorer.item(item, "values")
        if not values:
            return
        ruta = values[0]
        if os.path.isdir(ruta):
            self.tree_explorer.item(
                item, open=not self.tree_explorer.item(item, "open")
            )
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
            messagebox.showerror("Error al abrir", str(e))

    def _seleccionar_tab_por_ruta(self, ruta: str) -> bool:
        for tid, datos in self.editor_mgr.pestanas.items():
            if datos.get("ruta") == ruta:
                self.editor_mgr.seleccionar(tid)
                return True
        return False

    # ── Panel de resultados ───────────────────────────────────────────────────

    def _construir_panel_resultados(self):
        c = C()
        self.panel_res = tk.Frame(self.cuerpo, bg=c["fondo"], width=420)
        self.panel_res.pack(side="right", fill="both", expand=False)
        self.panel_res.pack_propagate(False)

        self._nb_style = ttk.Style()
        self._aplicar_estilo_notebook()

        self.notebook = ttk.Notebook(self.panel_res, style="Res.TNotebook")
        self.notebook.pack(fill="both", expand=True)

        self._construir_tab_resultado()
        self._construir_tab_tabla()
        self._construir_tab_tokens()

    def _aplicar_estilo_notebook(self):
        c = C()
        s = self._nb_style
        s.theme_use("default")
        s.configure(
            "Res.TNotebook",
            background=c["panel"],
            borderwidth=0,
            tabmargins=[0, 2, 0, 0],
        )
        s.configure(
            "Res.TNotebook.Tab",
            background=c["tab_inactiva"],
            foreground=c["tab_fg_inact"],
            padding=[14, 6],
            font=FUENTES["boton"],
            borderwidth=0,
        )
        s.map(
            "Res.TNotebook.Tab",
            background=[("selected", c["tab_activa"])],
            foreground=[("selected", c["tab_fg_act"])],
        )
        s.configure(
            "Explorer.Treeview",
            background=c["panel"],
            fieldbackground=c["panel"],
            foreground=c["tabla_fg"],
        )

    def _construir_tab_resultado(self):
        c = C()
        self.frame_res = tk.Frame(self.notebook, bg=c["resultado_bg"])
        self.notebook.add(self.frame_res, text="  ✦ Resultado  ")

        # Frame para el texto con scrollbar inteligente
        frame_scroll = tk.Frame(self.frame_res, bg=c["resultado_bg"])
        frame_scroll.pack(fill="both", expand=True)

        self.texto_resultado = tk.Text(
            frame_scroll,
            bg=c["resultado_bg"],
            fg=c["tag_normal"],
            font=FUENTES["resultado"],
            state="disabled",
            bd=0,
            padx=16,
            pady=12,
            wrap="word",
            relief="flat",
        )
        self.texto_resultado.pack(side="left", fill="both", expand=True)

        # Scrollbar vertical (solo si es necesario)
        scroll_res = tk.Scrollbar(
            frame_scroll, orient="vertical", command=self.texto_resultado.yview
        )
        self.scroll_resultado_ref = scroll_res

        def make_scroll_handler(text_widget, scrollbar):
            def handler(*args):
                if float(args[0]) <= 0.0 and float(args[1]) >= 1.0:
                    if scrollbar.winfo_manager():
                        scrollbar.pack_forget()
                else:
                    if not scrollbar.winfo_manager():
                        scrollbar.pack(side="right", fill="y")
                text_widget.yview_moveto(args[0])

            return handler

        self.texto_resultado["yscrollcommand"] = make_scroll_handler(
            self.texto_resultado, scroll_res
        )

        for tag, opts in tags_resultado().items():
            self.texto_resultado.tag_configure(tag, **opts)

    def _construir_tab_tabla(self):
        c = C()
        frame = tk.Frame(self.notebook, bg=c["tabla_bg"])
        self.notebook.add(frame, text="  ◈ Símbolos  ")

        s = self._nb_style
        s.configure(
            "Sym.Treeview",
            background=c["tabla_bg"],
            foreground=c["tabla_fg"],
            fieldbackground=c["tabla_bg"],
            rowheight=28,
            font=FUENTES["tokens"],
        )
        s.configure(
            "Sym.Treeview.Heading",
            background=c["borde"],
            foreground=c["tag_tok_cab"],
            font=FUENTES["boton"],
        )
        s.map("Sym.Treeview", background=[("selected", c["seleccion"])])

        cols = ("Variable", "Tipo", "Valor", "Línea")
        self.tabla_view = ttk.Treeview(
            frame, columns=cols, show="headings", style="Sym.Treeview"
        )
        anchos = {"Variable": 130, "Tipo": 90, "Valor": 140, "Línea": 60}
        for col in cols:
            self.tabla_view.heading(col, text=col)
            self.tabla_view.column(col, width=anchos[col], anchor="w")

        scroll_t = ttk.Scrollbar(
            frame, orient="vertical", command=self.tabla_view.yview
        )
        self.tabla_view["yscrollcommand"] = scroll_t.set
        self.tabla_view.pack(side="left", fill="both", expand=True)
        scroll_t.pack(side="right", fill="y")

    def _construir_tab_tokens(self):
        c = C()
        frame = tk.Frame(self.notebook, bg=c["panel"])
        self.notebook.add(frame, text="  ⟨/⟩ Tokens  ")

        # Frame para el texto con scrollbar inteligente
        frame_scroll_tok = tk.Frame(frame, bg=c["panel"])
        frame_scroll_tok.pack(fill="both", expand=True)

        self.texto_tokens = tk.Text(
            frame_scroll_tok,
            bg=c["panel"],
            fg=c["tabla_fg"],
            font=FUENTES["tokens"],
            state="disabled",
            bd=0,
            padx=14,
            pady=8,
            relief="flat",
        )
        self.texto_tokens.pack(side="left", fill="both", expand=True)

        # Scrollbar vertical (solo si es necesario)
        scroll_tok = tk.Scrollbar(
            frame_scroll_tok, orient="vertical", command=self.texto_tokens.yview
        )
        self.scroll_tokens_ref = scroll_tok

        def make_scroll_handler_tokens(text_widget, scrollbar):
            def handler(*args):
                if float(args[0]) <= 0.0 and float(args[1]) >= 1.0:
                    if scrollbar.winfo_manager():
                        scrollbar.pack_forget()
                else:
                    if not scrollbar.winfo_manager():
                        scrollbar.pack(side="right", fill="y")
                text_widget.yview_moveto(args[0])

            return handler

        self.texto_tokens["yscrollcommand"] = make_scroll_handler_tokens(
            self.texto_tokens, scroll_tok
        )

        for tag, opts in tags_tokens().items():
            self.texto_tokens.tag_configure(tag, **opts)

    # ── Barra de estado ───────────────────────────────────────────────────────

    def _construir_barra_estado(self):
        c = C()
        tk.Frame(self.root, bg=c["borde"], height=1).pack(fill="x", side="bottom")
        self.barra_estado = tk.Frame(self.root, bg=c["status_bg"], height=26)
        self.barra_estado.pack(fill="x", side="bottom")
        self.barra_estado.pack_propagate(False)

        def sep():
            tk.Frame(self.barra_estado, bg=c["borde"], width=1).pack(
                side="left", fill="y", pady=4
            )

        self.lbl_compilacion = tk.Label(
            self.barra_estado,
            text="● Sin compilar",
            bg=c["status_bg"],
            fg=c["status_fg"],
            font=FUENTES["ui"],
            anchor="w",
        )
        self.lbl_compilacion.pack(side="left", padx=(10, 6))
        sep()

        self.lbl_vars = tk.Label(
            self.barra_estado,
            text="Variables: 0",
            bg=c["status_bg"],
            fg=c["status_fg"],
            font=FUENTES["ui"],
        )
        self.lbl_vars.pack(side="left", padx=(8, 6))
        sep()

        self.lbl_posicion = tk.Label(
            self.barra_estado,
            text="Ln 1, Col 1",
            bg=c["status_bg"],
            fg=c["status_fg"],
            font=FUENTES["ui"],
        )
        self.lbl_posicion.pack(side="left", padx=(8, 6))

        self.lbl_info = tk.Label(
            self.barra_estado,
            text=f"COSTEÑOL  |  UTF-8  |  {tema_nombre().capitalize()}",
            bg=c["status_bg"],
            fg=c["status_fg"],
            font=FUENTES["ui"],
        )
        self.lbl_info.pack(side="right", padx=10)

    def actualizar_estado(self):
        """Actualiza línea/columna. Llamado por GestorPestanas en cada evento."""
        editor = self.editor_mgr.editor_activo()
        if not editor:
            return
        try:
            lin, col = editor.index("insert").split(".")
            self.lbl_posicion.config(text=f"Ln {lin}, Col {int(col) + 1}")
        except Exception:
            pass

    # ── Cambio de tema ────────────────────────────────────────────────────────

    def _alternar_tema(self):
        alternar_tema()
        self.btn_tema.config(text="☀" if tema_nombre() == "oscuro" else "🌙")
        self._reaplicar_tema()

    def _reaplicar_tema(self):
        c = C()
        self.root.config(bg=c["fondo"])

        # Barra superior
        self.barra_sup.config(bg=c["panel"])
        for w in self.barra_sup.winfo_children():
            if isinstance(w, tk.Label):
                w.config(bg=c["panel"], fg=c["titulo_fg"])

        # Cuerpo y separador
        self.cuerpo.config(bg=c["fondo"])
        self.sep.config(bg=c["borde"])

        # Editor (gestiona sus propios widgets)
        self.editor_mgr.aplicar_tema()

        # Notebook de resultados
        self.panel_res.config(bg=c["fondo"])
        self._aplicar_estilo_notebook()

        self.frame_res.config(bg=c["resultado_bg"])
        self.texto_resultado.config(bg=c["resultado_bg"], fg=c["tag_normal"])
        for tag, opts in tags_resultado().items():
            self.texto_resultado.tag_configure(tag, **opts)

        self.texto_tokens.config(bg=c["panel"], fg=c["tabla_fg"])
        for tag, opts in tags_tokens().items():
            self.texto_tokens.tag_configure(tag, **opts)

        if hasattr(self, "explorador_frame"):
            self.explorador_frame.config(bg=c["panel"])
            self.lbl_explorador.config(bg=c["panel"], fg=c["tab_fg_act"])
            self._explorer_style.configure(
                "Explorer.Treeview",
                background=c["panel"],
                fieldbackground=c["panel"],
                foreground=c["tabla_fg"],
            )

        self._nb_style.configure(
            "Sym.Treeview",
            background=c["tabla_bg"],
            foreground=c["tabla_fg"],
            fieldbackground=c["tabla_bg"],
        )
        self._nb_style.configure(
            "Sym.Treeview.Heading", background=c["borde"], foreground=c["tag_tok_cab"]
        )

        # Barra de estado
        self.barra_estado.config(bg=c["status_bg"])
        for w in self.barra_estado.winfo_children():
            if isinstance(w, tk.Label):
                w.config(bg=c["status_bg"], fg=c["status_fg"])

        self.lbl_info.config(
            text=f"COSTEÑOL  |  UTF-8  |  {tema_nombre().capitalize()}"
        )

    # ── Acciones de archivo ───────────────────────────────────────────────────

    def _nueva_pestana(self):
        self.editor_mgr.nueva_pestana()

    def _cerrar_tab_activa(self):
        if self.editor_mgr.tab_activa:
            self.editor_mgr.cerrar_pestana(self.editor_mgr.tab_activa)

    def abrir_archivo(self):
        ruta = filedialog.askopenfilename(
            title="Abrir archivo Costeñol",
            filetypes=[("Costeñol", "*.pqek"), ("Todos", "*.*")],
        )
        if not ruta:
            return
        try:
            with open(ruta, encoding="utf-8") as f:
                contenido = f.read()
            import os

            self.editor_mgr.nueva_pestana(
                nombre=os.path.basename(ruta),
                contenido=contenido,
                ruta=ruta,
            )
        except Exception as e:
            messagebox.showerror("Error al abrir", str(e))

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
        ruta = filedialog.asksaveasfilename(
            title="Guardar como",
            defaultextension=".pqek",
            filetypes=[("Costeñol", "*.pqek"), ("Todos", "*.*")],
        )
        if ruta:
            import os

            datos["ruta"] = ruta
            datos["nombre"] = os.path.basename(ruta)
            self._escribir(ruta, datos)

    def _escribir(self, ruta: str, datos: dict):
        try:
            contenido = datos["editor"].get("1.0", "end-1c")
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(contenido)
            self.editor_mgr.marcar_modificado(self.editor_mgr.tab_activa, False)
            self.lbl_compilacion.config(text=f"💾 Guardado", fg=C()["status_ok"])
        except Exception as e:
            messagebox.showerror("Error al guardar", str(e))

    # ── Compilación ───────────────────────────────────────────────────────────

    def compilar(self):
        editor = self.editor_mgr.editor_activo()
        if not editor:
            return

        codigo = editor.get("1.0", "end-1c").strip()
        if not codigo:
            messagebox.showwarning(
                MENSAJE_SIN_CODIGO["titulo"],
                MENSAJE_SIN_CODIGO["cuerpo"],
            )
            return

        self.editor_mgr.limpiar_errores()

        resultado = compilar(codigo)
        self._mostrar_resultado(resultado)
        self._mostrar_tabla(resultado["tabla"])
        self._mostrar_tokens(codigo)

        n_vars = len(resultado["tabla"])
        self.lbl_vars.config(text=f"Variables: {n_vars}")

        if resultado["exito"]:
            self.lbl_compilacion.config(
                text="✔ Compilación exitosa", fg=C()["status_ok"]
            )
            messagebox.showinfo(
                MENSAJES_EXITO["titulo"],
                random.choice(MENSAJES_EXITO["cuerpos"]),
            )
        else:
            n = len(resultado["errores"])
            self.lbl_compilacion.config(text=f"✘  {n} error(es)", fg=C()["status_err"])
            # Subrayar líneas con error en el editor
            lineas_err = []
            for err in resultado["errores"]:
                m = re.search(r"[Ll]ínea\s+(\d+)|line\s+(\d+)", err)
                if m:
                    lineas_err.append(int(next(g for g in m.groups() if g)))
            if lineas_err:
                self.editor_mgr.marcar_errores(lineas_err)

            messagebox.showerror(
                MENSAJES_ERROR["titulo"],
                random.choice(MENSAJES_ERROR["cuerpos"]),
            )

        self.notebook.select(0)

    def limpiar_todo(self):
        editor = self.editor_mgr.editor_activo()
        if editor:
            editor.delete("1.0", "end")
            self.editor_mgr.limpiar_errores()
            # re-highlight (vacío) y sincronizar números
            tab_id = self.editor_mgr.tab_activa
            self.editor_mgr._highlight(tab_id)
            self.editor_mgr._sync_nums(tab_id)

        for widget in (self.texto_resultado, self.texto_tokens):
            widget.config(state="normal")
            widget.delete("1.0", "end")
            widget.config(state="disabled")

        for row in self.tabla_view.get_children():
            self.tabla_view.delete(row)

        self.lbl_compilacion.config(text="● Sin compilar", fg=C()["status_fg"])
        self.lbl_vars.config(text="Variables: 0")

    # ── Renderizado de resultados ─────────────────────────────────────────────

    def _mostrar_resultado(self, resultado: dict):
        t = self.texto_resultado
        t.config(state="normal")
        t.delete("1.0", "end")

        def w(texto: str, tag: str = "normal"):
            t.insert("end", texto + "\n", tag)

        def sep():
            w("─" * 48, "sep")

        sep()
        w(
            (
                "  ✔  COMPILACIÓN EXITOSA"
                if resultado["exito"]
                else "  ✘  ERRORES EN EL CÓDIGO"
            ),
            "exito" if resultado["exito"] else "error",
        )
        sep()

        if resultado["salida"]:
            w("")
            w("  SALIDA DEL PROGRAMA", "titulo")
            w("")
            for linea in resultado["salida"]:
                w(f"  ▸  {linea}", "salida")
            w("")
            sep()

        if resultado["errores"]:
            w("")
            w("  ERRORES DETECTADOS", "titulo")
            w("")
            for i, err in enumerate(resultado["errores"], 1):
                t.insert("end", f"  [{i}]  ", "num_error")
                t.insert("end", err + "\n", "error")
            w("")
            sep()

        if not resultado["salida"] and not resultado["errores"]:
            w("")
            w("  (sin salida registrada)", "normal")

        t.config(state="disabled")

    def _mostrar_tabla(self, tabla_dict: dict):
        for row in self.tabla_view.get_children():
            self.tabla_view.delete(row)
        for var, info in tabla_dict.items():
            val = str(info["valor"]) if info["valor"] is not None else "—"
            self.tabla_view.insert(
                "", "end", values=(var, info["tipo"], val, info["linea"])
            )

    def _mostrar_tokens(self, codigo: str):
        t = self.texto_tokens
        t.config(state="normal")
        t.delete("1.0", "end")
        lista = tokenizar(codigo)
        t.insert("end", f"  {'LÍN':<5}  {'TIPO':<20}  VALOR\n", "cabecera")
        t.insert("end", "  " + "─" * 46 + "\n", "sep")
        for tipo, valor, linea in lista:
            t.insert("end", f"  {linea:<5}  ", "linea")
            t.insert("end", f"{tipo:<20}  ", "tipo")
            t.insert("end", f"{repr(valor)}\n", "valor")
        t.config(state="disabled")

    # ── Ejemplo inicial ───────────────────────────────────────────────────────

    def _cargar_ejemplo(self):
        self.editor_mgr.nueva_pestana(
            nombre="ejemplo.pqek",
            contenido=CODIGO_EJEMPLO,
        )


# ── Punto de entrada ──────────────────────────────────────────────────────────


def iniciar_interfaz():
    root = tk.Tk()
    VentanaCompilador(root)
    root.mainloop()


if __name__ == "__main__":
    iniciar_interfaz()
