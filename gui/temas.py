# gui/temas.py — Colores, fuentes, estilos y mensajes del compilador Costeñol

# ── Paleta de colores ─────────────────────────────────────────────────────────
COLORES = {
    # Fondos principales
    "fondo": "#0F1117",
    "panel": "#090C12",
    "borde": "#1C2333",
    "editor_bg": "#161B27",
    "resultado_bg": "#0F1117",
    "tabla_bg": "#161B27",
    # Textos
    "editor_fg": "#C9D1E0",
    "tabla_fg": "#CBD5E1",
    "titulo_fg": "#E2E8F0",
    "subtitulo_fg": "#64748B",
    "linea_num_fg": "#3D4F6B",
    # Fondos especiales
    "linea_num_bg": "#0D1016",
    # Interacción
    "cursor": "#3B82F6",
    "seleccion": "#1E3A5F",
    # Botones
    "btn_compilar": "#2563EB",
    "btn_limpiar": "#15803D",
    "btn_compilar_hover": "#1D4ED8",
    "btn_limpiar_hover": "#166534",
}

# ── Fuentes ───────────────────────────────────────────────────────────────────
FUENTES = {
    "codigo": ("Cascadia Code", 12),
    "resultado": ("Courier New", 11),
    "tokens": ("Courier New", 11),
    "ui": ("Segoe UI", 9),
    "titulo": ("Segoe UI", 15, "bold"),
    "boton": ("Segoe UI", 10, "bold"),
    "subtitulo": ("Segoe UI", 9, "bold"),
}

# ── Tags de texto (colores para los widgets ScrolledText) ─────────────────────
TAGS_RESULTADO = {
    "exito": {"foreground": "#4ADE80", "font": ("Courier New", 12, "bold")},
    "error": {"foreground": "#F87171"},
    "num_error": {"foreground": "#FB923C", "font": ("Courier New", 11, "bold")},
    "salida": {"foreground": "#67E8F9"},
    "titulo": {"foreground": "#334155", "font": ("Courier New", 10)},
    "normal": {"foreground": "#475569"},
    "sep": {"foreground": "#1A2235"},
}

TAGS_TOKENS = {
    "cabecera": {"foreground": "#3B82F6", "font": ("Courier New", 11, "bold")},
    "tipo": {"foreground": "#818CF8"},
    "valor": {"foreground": "#4ADE80"},
    "linea": {"foreground": "#475569"},
    "sep": {"foreground": "#1A2235"},
}

# ── Mensajes divertidos (estilo Costeñol) ─────────────────────────────────────
MENSAJES_EXITO = {
    "titulo": "Que vaina linda",
    "cuerpos": [
        "Melo, Melo, Caramelo",
        "Mas bueno que una quincena de alex char",
        "Ajá, sí que sabes programar",
        "Compiló de una, como debe ser",
    ],
}

MENSAJES_ERROR = {
    "titulo": "Paila",
    "cuerpos": [
        "Tu conoces a yaper",
        "Joda la pasas barro",
        "Revisa eso antes de que pases pena",
    ],
}

MENSAJE_SIN_CODIGO = {
    "titulo": "Sin código",
    "cuerpo": "AJA ME ESTAS MAMANDO GALLO?",
}

# ── Ejemplo inicial que se carga en el editor ─────────────────────────────────
CODIGO_EJEMPLO = """\
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
