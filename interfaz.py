import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parser import compilar
from lexer import tokenizar

# colores de la interfaz
COLORES = {
    'fondo':        '#0F1117',
    'panel':        '#090C12',
    'borde':        '#1C2333',
    'editor_bg':    '#161B27',
    'editor_fg':    '#C9D1E0',
    'resultado_bg': '#0F1117',
    'tabla_bg':     '#161B27',
    'tabla_fg':     '#CBD5E1',
    'btn_compilar': '#2563EB',
    'btn_limpiar':  '#15803D',
    'titulo_fg':    '#E2E8F0',
    'subtitulo_fg': '#64748B',
    'linea_num_bg': '#0D1016',
    'linea_num_fg': '#3D4F6B',
    'cursor':       '#3B82F6',
    'seleccion':    '#1E3A5F',
}

FUENTE_CODIGO = ('Cascadia Code', 12)


class VentanaCompilador:
    def __init__(self, root):
        self.root = root
        self._configurar_ventana()
        self._construir_interfaz()
        self._cargar_ejemplo()


    def _configurar_ventana(self):
        self.root.title("COSTEÑOL")
        self.root.geometry("1200x720")
        self.root.minsize(850, 520)
        self.root.configure(bg=COLORES['fondo'])
        try:
            self.root.iconbitmap(default='')
        except Exception:
            pass

    def _construir_interfaz(self):
        self._construir_barra_superior()
        self._construir_cuerpo()
        self._construir_barra_estado()

    def _construir_barra_superior(self):
        barra = tk.Frame(self.root, bg=COLORES['panel'], height=52)
        barra.pack(fill='x')
        barra.pack_propagate(False)

        tk.Label(
            barra,
            text="COSTEÑOL",
            bg=COLORES['panel'],
            fg=COLORES['titulo_fg'],
            font=('Segoe UI', 15, 'bold'),
        ).pack(side='left', padx=18, pady=10)

        def btn(texto, color, hover, comando):
            b = tk.Button(
                barra,
                text=texto,
                bg=color,
                fg='#FFFFFF',
                activebackground=hover,
                activeforeground='#FFFFFF',
                font=('Segoe UI', 10, 'bold'),
                relief='flat',
                padx=16, pady=6,
                cursor='hand2',
                bd=0,
                command=comando,
            )
            b.pack(side='right', padx=(0, 10), pady=9)
            return b

        btn("🗑  Limpiar",  COLORES['btn_limpiar'], '#166534', self.limpiar_todo)
        btn("▶  Compilar", COLORES['btn_compilar'], '#1D4ED8', self.compilar)

        tk.Frame(self.root, bg=COLORES['borde'], height=1).pack(fill='x')


    def _construir_cuerpo(self):
        cuerpo = tk.Frame(self.root, bg=COLORES['fondo'])
        cuerpo.pack(fill='both', expand=True)
        self._construir_editor(cuerpo)
        self._construir_panel_resultados(cuerpo)


    def _construir_editor(self, parent):
        frame = tk.Frame(parent, bg=COLORES['borde'], bd=0)
        frame.pack(side='left', fill='both', expand=True, padx=(0, 1))

        # Encabezado
        header = tk.Frame(frame, bg=COLORES['borde'], height=28)
        header.pack(fill='x')
        header.pack_propagate(False)
        tk.Label(
            header,
            text="  »  COSTEÑOL",
            bg=COLORES['borde'],
            fg=COLORES['subtitulo_fg'],
            font=('Segoe UI', 9, 'bold'),
            anchor='w',
        ).pack(side='left', fill='x', padx=4)

        # Números de línea + editor
        frame_texto = tk.Frame(frame, bg=COLORES['editor_bg'])
        frame_texto.pack(fill='both', expand=True)

        self.nums_linea = tk.Text(
            frame_texto,
            width=4,
            bg=COLORES['linea_num_bg'],
            fg=COLORES['linea_num_fg'],
            font=FUENTE_CODIGO,
            state='disabled',
            bd=0, padx=6,
            selectbackground=COLORES['linea_num_bg'],
        )
        self.nums_linea.pack(side='left', fill='y')

        tk.Frame(frame_texto, bg=COLORES['borde'], width=1).pack(side='left', fill='y')

        self.editor = tk.Text(
            frame_texto,
            bg=COLORES['editor_bg'],
            fg=COLORES['editor_fg'],
            font=FUENTE_CODIGO,
            insertbackground=COLORES['cursor'],
            selectbackground=COLORES['seleccion'],
            selectforeground=COLORES['editor_fg'],
            undo=True,
            bd=0, padx=10, pady=6,
            wrap='none', relief='flat',
        )
        self.editor.pack(side='left', fill='both', expand=True)

        scroll_y = tk.Scrollbar(frame_texto, orient='vertical', bg=COLORES['borde'])
        scroll_y.pack(side='right', fill='y')
        self.editor['yscrollcommand']     = self._sync_scroll(scroll_y.set)
        self.nums_linea['yscrollcommand'] = scroll_y.set
        scroll_y['command'] = self._scroll_ambos

        scroll_x = tk.Scrollbar(frame, orient='horizontal', command=self.editor.xview)
        scroll_x.pack(fill='x')
        self.editor['xscrollcommand'] = scroll_x.set

        self.editor.bind('<KeyRelease>', self._actualizar_numeros_linea)
        self.editor.bind('<MouseWheel>', lambda e: self._actualizar_numeros_linea())
        self._actualizar_numeros_linea()

    # PANEL RESULTADOS
    def _construir_panel_resultados(self, parent):
        frame = tk.Frame(parent, bg=COLORES['fondo'])
        frame.pack(side='right', fill='both', expand=True)

        estilo = ttk.Style()
        estilo.theme_use('default')
        estilo.configure('TNotebook',
            background=COLORES['panel'], borderwidth=0, tabmargins=[0,0,0,0])
        estilo.configure('TNotebook.Tab',
            background=COLORES['borde'],
            foreground=COLORES['subtitulo_fg'],
            padding=[14, 5],
            font=('Segoe UI', 9, 'bold'),
            borderwidth=0)
        estilo.map('TNotebook.Tab',
            background=[('selected', COLORES['editor_bg'])],
            foreground=[('selected', COLORES['titulo_fg'])])

        self.notebook = ttk.Notebook(frame)
        self.notebook.pack(fill='both', expand=True)

        self._construir_tab_resultado()
        self._construir_tab_tabla()
        self._construir_tab_tokens()

    # TAB 1 — Resultado
    def _construir_tab_resultado(self):
        frame = tk.Frame(self.notebook, bg=COLORES['resultado_bg'])
        self.notebook.add(frame, text='  ✦ Resultado  ')

        self.texto_resultado = scrolledtext.ScrolledText(
            frame,
            bg=COLORES['resultado_bg'],
            fg='#94A3B8',
            font=('Courier New', 11),
            state='disabled',
            bd=0, padx=14, pady=10,
            wrap='word', relief='flat',
        )
        self.texto_resultado.pack(fill='both', expand=True)

        self.texto_resultado.tag_configure('exito',
            foreground='#4ADE80', font=('Courier New', 12, 'bold'))
        self.texto_resultado.tag_configure('error',
            foreground='#F87171')
        self.texto_resultado.tag_configure('num_error',
            foreground='#FB923C', font=('Courier New', 11, 'bold'))
        self.texto_resultado.tag_configure('salida',
            foreground='#67E8F9')
        self.texto_resultado.tag_configure('titulo',
            foreground='#334155', font=('Courier New', 10))
        self.texto_resultado.tag_configure('normal',
            foreground='#475569')
        self.texto_resultado.tag_configure('sep',
            foreground='#1A2235')

    # TAB 2 — Tabla de Símbolos
    def _construir_tab_tabla(self):
        frame = tk.Frame(self.notebook, bg=COLORES['tabla_bg'])
        self.notebook.add(frame, text='  ◈ Tabla de Símbolos  ')

        cols = ('Variable', 'Tipo', 'Valor', 'Línea')
        estilo = ttk.Style()
        estilo.configure('Tabla.Treeview',
            background=COLORES['tabla_bg'],
            foreground=COLORES['tabla_fg'],
            fieldbackground=COLORES['tabla_bg'],
            rowheight=30,
            font=('Courier New', 11))
        estilo.configure('Tabla.Treeview.Heading',
            background=COLORES['borde'],
            foreground='#60A5FA',
            font=('Segoe UI', 10, 'bold'))
        estilo.map('Tabla.Treeview',
            background=[('selected', COLORES['seleccion'])])

        self.tabla_view = ttk.Treeview(
            frame, columns=cols, show='headings', style='Tabla.Treeview')
        anchos = {'Variable': 150, 'Tipo': 100, 'Valor': 160, 'Línea': 70}
        for col in cols:
            self.tabla_view.heading(col, text=col)
            self.tabla_view.column(col, width=anchos[col], anchor='w')

        scroll_t = ttk.Scrollbar(frame, orient='vertical', command=self.tabla_view.yview)
        self.tabla_view['yscrollcommand'] = scroll_t.set
        self.tabla_view.pack(side='left', fill='both', expand=True)
        scroll_t.pack(side='right', fill='y')

    # TAB 3 — Tokens
    def _construir_tab_tokens(self):
        frame = tk.Frame(self.notebook, bg=COLORES['panel'])
        self.notebook.add(frame, text='  ⟨/⟩ Tokens  ')

        self.texto_tokens = scrolledtext.ScrolledText(
            frame,
            bg=COLORES['panel'],
            fg=COLORES['tabla_fg'],
            font=('Courier New', 11),
            state='disabled',
            bd=0, padx=14, pady=8, relief='flat',
        )
        self.texto_tokens.pack(fill='both', expand=True)
        self.texto_tokens.tag_configure('cabecera',
            foreground='#3B82F6', font=('Courier New', 11, 'bold'))
        self.texto_tokens.tag_configure('tipo',  foreground='#818CF8')
        self.texto_tokens.tag_configure('valor', foreground='#4ADE80')
        self.texto_tokens.tag_configure('linea', foreground='#475569')
        self.texto_tokens.tag_configure('sep',   foreground='#1A2235')

    # BARRA DE ESTADO
    def _construir_barra_estado(self):
        tk.Frame(self.root, bg=COLORES['borde'], height=1).pack(fill='x', side='bottom')
        barra = tk.Frame(self.root, bg=COLORES['panel'], height=26)
        barra.pack(fill='x', side='bottom')
        barra.pack_propagate(False)

        self.lbl_estado = tk.Label(
            barra,
            text="Escribe codigo y presiona Compilar",
            bg=COLORES['panel'],
            fg='#334155',
            font=('Segoe UI', 9),
            anchor='w',
        )
        self.lbl_estado.pack(side='left', fill='x', padx=4)

        tk.Label(
            barra,
            text="",
            bg=COLORES['panel'],
            fg='#1E293B',
            font=('Segoe UI', 8),
        ).pack(side='right')

    # ACCIÓN: COMPILAR
    def compilar(self):
        codigo = self.editor.get('1.0', 'end-1c').strip()
        if not codigo:
            messagebox.showwarning("Sin código", "AJA ME ESTAS MAMADO GALLO?")
            return

        resultado = compilar(codigo)
        self._mostrar_resultado(resultado)
        self._mostrar_tabla(resultado['tabla'])
        self._mostrar_tokens(codigo)

        if resultado['exito']:
            self.lbl_estado.config(text=" Compilación exitosa", fg='#22C55E')
            messagebox.showinfo("Qué vaina linda", "Todo salió vacano")
        else:
            n = len(resultado['errores'])
            self.lbl_estado.config(
                text=f"  ●  {n} error(es) encontrado(s)", fg='#EF4444')
            messagebox.showerror("Ey, barro eso","Algo no cuadra en la compilacion")

        self.notebook.select(0)

    #Resultado
    def _mostrar_resultado(self, resultado):
        t = self.texto_resultado
        t.config(state='normal')
        t.delete('1.0', 'end')

        def w(texto, tag='normal'):
            t.insert('end', texto + '\n', tag)

        def sep():
            w('─' * 46, 'sep')

        sep()
        if resultado['exito']:
            w('  ESOO VAMOS BIEN', 'exito')
        else:
            w('  ERROR CAPA 8', 'error')
        sep()

        if resultado['salida']:
            w('')
            w('  SALIDA DEL PROGRAMA', 'titulo')
            w('')
            for linea in resultado['salida']:
                w(f'  ▸  {linea}', 'salida')
            w('')
            sep()

        if resultado['errores']:
            w('')
            w('  ERRORES', 'titulo')
            w('')
            for i, err in enumerate(resultado['errores'], 1):
                t.insert('end', f'  [{i}]  ', 'num_error')
                t.insert('end', err + '\n', 'error')
            w('')
            sep()

        if not resultado['salida'] and not resultado['errores']:
            w('')
            w('  (sin salida registrada)', 'normal')

        t.config(state='disabled')

    # Tabla de Símbolos
    def _mostrar_tabla(self, tabla_dict):
        for row in self.tabla_view.get_children():
            self.tabla_view.delete(row)
        for var, info in tabla_dict.items():
            val = str(info['valor']) if info['valor'] is not None else '—'
            self.tabla_view.insert('', 'end', values=(
                var, info['tipo'], val, info['linea']))

    #Tokens
    def _mostrar_tokens(self, codigo):
        t = self.texto_tokens
        t.config(state='normal')
        t.delete('1.0', 'end')

        tokens = tokenizar(codigo)
        t.insert('end', f"  {'LÍN':<5}  {'TIPO':<18}  VALOR\n", 'cabecera')
        t.insert('end', '  ' + '─' * 44 + '\n', 'sep')
        for tipo, valor, linea in tokens:
            t.insert('end', f"  {linea:<5}  ", 'linea')
            t.insert('end', f"{tipo:<18}  ", 'tipo')
            t.insert('end', f"{repr(valor)}\n", 'valor')

        t.config(state='disabled')

    # LIMPIAR
    def limpiar_todo(self):
        self.editor.delete('1.0', 'end')
        self._actualizar_numeros_linea()

        for t in [self.texto_resultado, self.texto_tokens]:
            t.config(state='normal')
            t.delete('1.0', 'end')
            t.config(state='disabled')

        for row in self.tabla_view.get_children():
            self.tabla_view.delete(row)

        self.lbl_estado.config(
            text="escribe codigo y presiona Compilar",
            fg='#334155')


    # lineas
    def _actualizar_numeros_linea(self, event=None):
        contenido = self.editor.get('1.0', 'end-1c')
        num_lineas = contenido.count('\n') + 1
        self.nums_linea.config(state='normal')
        self.nums_linea.delete('1.0', 'end')
        for i in range(1, num_lineas + 1):
            self.nums_linea.insert('end', f"{i:>3}\n")
        self.nums_linea.config(state='disabled')


    def _scroll_ambos(self, *args):
        self.editor.yview(*args)
        self.nums_linea.yview(*args)

    def _sync_scroll(self, scrollbar_set):
        def handler(*args):
            scrollbar_set(*args)
            self.nums_linea.yview('moveto', args[0])
        return handler

    # EJEMPLO INICIAL
    def _cargar_ejemplo(self):
        ejemplo = """\
edad Entero;
nombre Texto;
pi Real;
activo Logico;

edad = 25;
nombre = "Maria";
pi = 3,14;
activo = Verdadero;

Mensaje.Texto("Hola, soy", nombre);
Mensaje.Texto("Tengo", edad);
"""
        self.editor.insert('1.0', ejemplo)
        self._actualizar_numeros_linea()

# ARRANQUE
def iniciar_interfaz():
    root = tk.Tk()
    VentanaCompilador(root)
    root.mainloop()

if __name__ == '__main__':
    iniciar_interfaz()