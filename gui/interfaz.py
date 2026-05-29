# gui/interfaz.py — Ventana principal del compilador Costeñol
import random
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

from core.parser import compilar
from core.lexer  import tokenizar
from gui.temas   import (
    COLORES, FUENTES,
    TAGS_RESULTADO, TAGS_TOKENS,
    MENSAJES_EXITO, MENSAJES_ERROR, MENSAJE_SIN_CODIGO,
    CODIGO_EJEMPLO,
)


class VentanaCompilador:
    def __init__(self, root: tk.Tk):
        self.root = root
        self._configurar_ventana()
        self._construir_interfaz()
        self._cargar_ejemplo()

    # ── Configuración de ventana ──────────────────────────────────────────────

    def _configurar_ventana(self):
        self.root.title("COSTEÑOL")
        self.root.geometry("1200x720")
        self.root.minsize(850, 520)
        self.root.configure(bg=COLORES["fondo"])
        try:
            self.root.iconbitmap(default="")
        except Exception:
            pass

    # ── Construcción de la interfaz ───────────────────────────────────────────

    def _construir_interfaz(self):
        self._construir_barra_superior()
        self._construir_cuerpo()
        self._construir_barra_estado()

    def _construir_barra_superior(self):
        barra = tk.Frame(self.root, bg=COLORES["panel"], height=52)
        barra.pack(fill="x")
        barra.pack_propagate(False)

        tk.Label(
            barra,
            text="COSTEÑOL",
            bg=COLORES["panel"],
            fg=COLORES["titulo_fg"],
            font=FUENTES["titulo"],
        ).pack(side="left", padx=18, pady=10)

        self._boton_barra(barra, "🗑  Limpiar",  COLORES["btn_limpiar"],  COLORES["btn_limpiar_hover"],  self.limpiar_todo)
        self._boton_barra(barra, "▶  Compilar", COLORES["btn_compilar"], COLORES["btn_compilar_hover"], self.compilar)

        tk.Frame(self.root, bg=COLORES["borde"], height=1).pack(fill="x")

    def _boton_barra(self, parent, texto, color, hover, comando):
        b = tk.Button(
            parent,
            text=texto,
            bg=color,
            fg="#FFFFFF",
            activebackground=hover,
            activeforeground="#FFFFFF",
            font=FUENTES["boton"],
            relief="flat",
            padx=16,
            pady=6,
            cursor="hand2",
            bd=0,
            command=comando,
        )
        b.pack(side="right", padx=(0, 10), pady=9)
        return b

    def _construir_cuerpo(self):
        cuerpo = tk.Frame(self.root, bg=COLORES["fondo"])
        cuerpo.pack(fill="both", expand=True)
        self._construir_editor(cuerpo)
        self._construir_panel_resultados(cuerpo)

    # ── Editor de código ──────────────────────────────────────────────────────

    def _construir_editor(self, parent):
        frame = tk.Frame(parent, bg=COLORES["borde"], bd=0)
        frame.pack(side="left", fill="both", expand=True, padx=(0, 1))

        # Encabezado
        header = tk.Frame(frame, bg=COLORES["borde"], height=28)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(
            header,
            text="  »  COSTEÑOL",
            bg=COLORES["borde"],
            fg=COLORES["subtitulo_fg"],
            font=FUENTES["subtitulo"],
            anchor="w",
        ).pack(side="left", fill="x", padx=4)

        # Números de línea + área de texto
        frame_texto = tk.Frame(frame, bg=COLORES["editor_bg"])
        frame_texto.pack(fill="both", expand=True)

        self.nums_linea = tk.Text(
            frame_texto,
            width=4,
            bg=COLORES["linea_num_bg"],
            fg=COLORES["linea_num_fg"],
            font=FUENTES["codigo"],
            state="disabled",
            bd=0,
            padx=6,
            selectbackground=COLORES["linea_num_bg"],
        )
        self.nums_linea.pack(side="left", fill="y")

        tk.Frame(frame_texto, bg=COLORES["borde"], width=1).pack(side="left", fill="y")

        self.editor = tk.Text(
            frame_texto,
            bg=COLORES["editor_bg"],
            fg=COLORES["editor_fg"],
            font=FUENTES["codigo"],
            insertbackground=COLORES["cursor"],
            selectbackground=COLORES["seleccion"],
            selectforeground=COLORES["editor_fg"],
            undo=True,
            bd=0,
            padx=10,
            pady=6,
            wrap="none",
            relief="flat",
        )
        self.editor.pack(side="left", fill="both", expand=True)

        scroll_y = tk.Scrollbar(frame_texto, orient="vertical", bg=COLORES["borde"])
        scroll_y.pack(side="right", fill="y")
        self.editor["yscrollcommand"]    = self._sync_scroll(scroll_y.set)
        self.nums_linea["yscrollcommand"] = scroll_y.set
        scroll_y["command"]              = self._scroll_ambos

        scroll_x = tk.Scrollbar(frame, orient="horizontal", command=self.editor.xview)
        scroll_x.pack(fill="x")
        self.editor["xscrollcommand"] = scroll_x.set

        self.editor.bind("<KeyRelease>",  self._actualizar_numeros_linea)
        self.editor.bind("<MouseWheel>",  lambda e: self._actualizar_numeros_linea())
        self._actualizar_numeros_linea()

    # ── Panel de resultados (notebook con 3 pestañas) ─────────────────────────

    def _construir_panel_resultados(self, parent):
        frame = tk.Frame(parent, bg=COLORES["fondo"])
        frame.pack(side="right", fill="both", expand=True)

        estilo = ttk.Style()
        estilo.theme_use("default")
        estilo.configure("TNotebook",
            background=COLORES["panel"], borderwidth=0, tabmargins=[0, 0, 0, 0])
        estilo.configure("TNotebook.Tab",
            background=COLORES["borde"], foreground=COLORES["subtitulo_fg"],
            padding=[14, 5], font=FUENTES["subtitulo"], borderwidth=0)
        estilo.map("TNotebook.Tab",
            background=[("selected", COLORES["editor_bg"])],
            foreground=[("selected", COLORES["titulo_fg"])],
        )

        self.notebook = ttk.Notebook(frame)
        self.notebook.pack(fill="both", expand=True)

        self._construir_tab_resultado()
        self._construir_tab_tabla()
        self._construir_tab_tokens()

    def _construir_tab_resultado(self):
        frame = tk.Frame(self.notebook, bg=COLORES["resultado_bg"])
        self.notebook.add(frame, text="  ✦ Resultado  ")

        self.texto_resultado = scrolledtext.ScrolledText(
            frame,
            bg=COLORES["resultado_bg"],
            fg="#94A3B8",
            font=FUENTES["resultado"],
            state="disabled",
            bd=0, padx=14, pady=10,
            wrap="word", relief="flat",
        )
        self.texto_resultado.pack(fill="both", expand=True)

        for tag, opts in TAGS_RESULTADO.items():
            self.texto_resultado.tag_configure(tag, **opts)

    def _construir_tab_tabla(self):
        frame = tk.Frame(self.notebook, bg=COLORES["tabla_bg"])
        self.notebook.add(frame, text="  ◈ Tabla de Símbolos  ")

        cols = ("Variable", "Tipo", "Valor", "Línea")
        estilo = ttk.Style()
        estilo.configure("Tabla.Treeview",
            background=COLORES["tabla_bg"], foreground=COLORES["tabla_fg"],
            fieldbackground=COLORES["tabla_bg"], rowheight=30, font=FUENTES["tokens"])
        estilo.configure("Tabla.Treeview.Heading",
            background=COLORES["borde"], foreground="#60A5FA", font=FUENTES["boton"])
        estilo.map("Tabla.Treeview",
            background=[("selected", COLORES["seleccion"])])

        self.tabla_view = ttk.Treeview(
            frame, columns=cols, show="headings", style="Tabla.Treeview"
        )
        anchos = {"Variable": 150, "Tipo": 100, "Valor": 160, "Línea": 70}
        for col in cols:
            self.tabla_view.heading(col, text=col)
            self.tabla_view.column(col, width=anchos[col], anchor="w")

        scroll_t = ttk.Scrollbar(frame, orient="vertical", command=self.tabla_view.yview)
        self.tabla_view["yscrollcommand"] = scroll_t.set
        self.tabla_view.pack(side="left", fill="both", expand=True)
        scroll_t.pack(side="right", fill="y")

    def _construir_tab_tokens(self):
        frame = tk.Frame(self.notebook, bg=COLORES["panel"])
        self.notebook.add(frame, text="  ⟨/⟩ Tokens  ")

        self.texto_tokens = scrolledtext.ScrolledText(
            frame,
            bg=COLORES["panel"],
            fg=COLORES["tabla_fg"],
            font=FUENTES["tokens"],
            state="disabled",
            bd=0, padx=14, pady=8, relief="flat",
        )
        self.texto_tokens.pack(fill="both", expand=True)

        for tag, opts in TAGS_TOKENS.items():
            self.texto_tokens.tag_configure(tag, **opts)

    # ── Barra de estado ───────────────────────────────────────────────────────

    def _construir_barra_estado(self):
        tk.Frame(self.root, bg=COLORES["borde"], height=1).pack(fill="x", side="bottom")
        barra = tk.Frame(self.root, bg=COLORES["panel"], height=26)
        barra.pack(fill="x", side="bottom")
        barra.pack_propagate(False)

        self.lbl_estado = tk.Label(
            barra,
            text="Escribe código y presiona Compilar",
            bg=COLORES["panel"],
            fg="#334155",
            font=FUENTES["ui"],
            anchor="w",
        )
        self.lbl_estado.pack(side="left", fill="x", padx=4)

    # ── Acciones principales ──────────────────────────────────────────────────

    def compilar(self):
        codigo = self.editor.get("1.0", "end-1c").strip()
        if not codigo:
            messagebox.showwarning(
                MENSAJE_SIN_CODIGO["titulo"],
                MENSAJE_SIN_CODIGO["cuerpo"],
            )
            return

        resultado = compilar(codigo)
        self._mostrar_resultado(resultado)
        self._mostrar_tabla(resultado["tabla"])
        self._mostrar_tokens(codigo)

        if resultado["exito"]:
            self.lbl_estado.config(text="  ● Compilación exitosa", fg="#22C55E")
            messagebox.showinfo(
                MENSAJES_EXITO["titulo"],
                random.choice(MENSAJES_EXITO["cuerpos"]),
            )
        else:
            n = len(resultado["errores"])
            self.lbl_estado.config(text=f"  ●  {n} error(es) encontrado(s)", fg="#EF4444")
            messagebox.showerror(
                MENSAJES_ERROR["titulo"],
                random.choice(MENSAJES_ERROR["cuerpos"]),
            )

        self.notebook.select(0)

    def limpiar_todo(self):
        self.editor.delete("1.0", "end")
        self._actualizar_numeros_linea()

        for widget in (self.texto_resultado, self.texto_tokens):
            widget.config(state="normal")
            widget.delete("1.0", "end")
            widget.config(state="disabled")

        for row in self.tabla_view.get_children():
            self.tabla_view.delete(row)

        self.lbl_estado.config(
            text="Escribe código y presiona Compilar", fg="#334155"
        )

    # ── Renderizado de resultados ─────────────────────────────────────────────

    def _mostrar_resultado(self, resultado: dict):
        t = self.texto_resultado
        t.config(state="normal")
        t.delete("1.0", "end")

        def w(texto: str, tag: str = "normal"):
            t.insert("end", texto + "\n", tag)

        def sep():
            w("─" * 46, "sep")

        sep()
        if resultado["exito"]:
            w("  ESOO VAMOS BIEN", "exito")
        else:
            w("  ERROR CAPA 8", "error")
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
            w("  ERRORES", "titulo")
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
            self.tabla_view.insert("", "end", values=(var, info["tipo"], val, info["linea"]))

    def _mostrar_tokens(self, codigo: str):
        t = self.texto_tokens
        t.config(state="normal")
        t.delete("1.0", "end")

        lista = tokenizar(codigo)
        t.insert("end", f"  {'LÍN':<5}  {'TIPO':<18}  VALOR\n", "cabecera")
        t.insert("end", "  " + "─" * 44 + "\n", "sep")
        for tipo, valor, linea in lista:
            t.insert("end", f"  {linea:<5}  ", "linea")
            t.insert("end", f"{tipo:<18}  ", "tipo")
            t.insert("end", f"{repr(valor)}\n", "valor")

        t.config(state="disabled")

    # ── Utilidades del editor ─────────────────────────────────────────────────

    def _actualizar_numeros_linea(self, event=None):
        contenido  = self.editor.get("1.0", "end-1c")
        num_lineas = contenido.count("\n") + 1

        self.nums_linea.config(state="normal")
        self.nums_linea.delete("1.0", "end")
        for i in range(1, num_lineas + 1):
            self.nums_linea.insert("end", f"{i:>3}\n")
        self.nums_linea.config(state="disabled")

    def _scroll_ambos(self, *args):
        self.editor.yview(*args)
        self.nums_linea.yview(*args)

    def _sync_scroll(self, scrollbar_set):
        def handler(*args):
            scrollbar_set(*args)
            self.nums_linea.yview("moveto", args[0])
        return handler

    # ── Ejemplo inicial ───────────────────────────────────────────────────────

    def _cargar_ejemplo(self):
        self.editor.insert("1.0", CODIGO_EJEMPLO)
        self._actualizar_numeros_linea()


# ── Punto de entrada ──────────────────────────────────────────────────────────

def iniciar_interfaz():
    root = tk.Tk()
    VentanaCompilador(root)
    root.mainloop()


if __name__ == "__main__":
    iniciar_interfaz()
