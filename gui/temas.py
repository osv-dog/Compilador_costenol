# gui/temas.py — Colores, fuentes, estilos y mensajes del compilador Costeñol

# ── Paleta de colores (tema oscuro) ──────────────────────────────────────────
_OSCURO = {
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
    "linea_activa": "#1A2130",
    "error_bg": "#3D1515",
    # Interacción
    "cursor": "#3B82F6",
    "seleccion": "#1E3A5F",
    # Botones
    "btn_compilar": "#2563EB",
    "btn_limpiar": "#15803D",
    "btn_compilar_hover": "#1D4ED8",
    "btn_limpiar_hover": "#166534",
    "btn_tema_bg": "#1C2333",
    "btn_tema_fg": "#E2E8F0",
    # Pestañas
    "tab_activa": "#161B27",
    "tab_inactiva": "#090C12",
    "tab_fg_act": "#E2E8F0",
    "tab_fg_inact": "#64748B",
    "tab_indicador": "#3B82F6",
    # Barra de estado
    "status_bg": "#090C12",
    "status_fg": "#64748B",
    "status_ok": "#22C55E",
    "status_err": "#EF4444",
    "status_warn": "#F59E0B",
    # Menú
    "menu_bg": "#0D1117",
    "menu_fg": "#C9D1E0",
    "menu_activo_bg": "#2563EB",
    "menu_activo_fg": "#FFFFFF",
    # Syntax highlighting
    "syn_keyword": "#FF7B72",
    "syn_type": "#79C0FF",
    "syn_string": "#A5D6FF",
    "syn_number": "#F8B886",
    "syn_comment": "#8B949E",
    "syn_builtin": "#D2A8FF",
    "syn_operator": "#FF7B72",
    "syn_punct": "#8B949E",
    "syn_id": "#C9D1E0",
    # Tags resultado / tokens
    "tag_exito": "#4ADE80",
    "tag_error": "#F87171",
    "tag_num_error": "#FB923C",
    "tag_salida": "#67E8F9",
    "tag_titulo": "#334155",
    "tag_normal": "#475569",
    "tag_sep": "#1A2235",
    "tag_tok_cab": "#3B82F6",
    "tag_tok_tipo": "#818CF8",
    "tag_tok_valor": "#4ADE80",
    "tag_tok_linea": "#475569",
}

# ── Paleta de colores (tema claro) ────────────────────────────────────────────
_CLARO = {
    # Fondos principales
    "fondo": "#FFFFFF",
    "panel": "#F6F8FA",
    "borde": "#D0D7DE",
    "editor_bg": "#FFFFFF",
    "resultado_bg": "#F6F8FA",
    "tabla_bg": "#FFFFFF",
    # Textos
    "editor_fg": "#1F2328",
    "tabla_fg": "#1F2328",
    "titulo_fg": "#1F2328",
    "subtitulo_fg": "#656D76",
    "linea_num_fg": "#8C959F",
    # Fondos especiales
    "linea_num_bg": "#F6F8FA",
    "linea_activa": "#F0F6FF",
    "error_bg": "#FFEBE9",
    # Interacción
    "cursor": "#0969DA",
    "seleccion": "#BDD7FF",
    # Botones
    "btn_compilar": "#0969DA",
    "btn_limpiar": "#1A7F37",
    "btn_compilar_hover": "#0860CA",
    "btn_limpiar_hover": "#157530",
    "btn_tema_bg": "#D0D7DE",
    "btn_tema_fg": "#1F2328",
    # Pestañas
    "tab_activa": "#FFFFFF",
    "tab_inactiva": "#F6F8FA",
    "tab_fg_act": "#1F2328",
    "tab_fg_inact": "#656D76",
    "tab_indicador": "#0969DA",
    # Barra de estado
    "status_bg": "#F6F8FA",
    "status_fg": "#656D76",
    "status_ok": "#1A7F37",
    "status_err": "#CF222E",
    "status_warn": "#9A6700",
    # Menú
    "menu_bg": "#FFFFFF",
    "menu_fg": "#1F2328",
    "menu_activo_bg": "#0969DA",
    "menu_activo_fg": "#FFFFFF",
    # Syntax highlighting
    "syn_keyword": "#CF222E",
    "syn_type": "#0550AE",
    "syn_string": "#0A3069",
    "syn_number": "#953800",
    "syn_comment": "#8C959F",
    "syn_builtin": "#8250DF",
    "syn_operator": "#CF222E",
    "syn_punct": "#656D76",
    "syn_id": "#1F2328",
    # Tags resultado / tokens
    "tag_exito": "#1A7F37",
    "tag_error": "#CF222E",
    "tag_num_error": "#953800",
    "tag_salida": "#0550AE",
    "tag_titulo": "#8C959F",
    "tag_normal": "#656D76",
    "tag_sep": "#D0D7DE",
    "tag_tok_cab": "#0969DA",
    "tag_tok_tipo": "#8250DF",
    "tag_tok_valor": "#1A7F37",
    "tag_tok_linea": "#8C959F",
}

# Diccionario de temas disponibles
TEMAS = {
    "oscuro": _OSCURO,
    "claro": _CLARO,
}

# Estado mutable del tema activo (se cambia desde la interfaz)
_tema_activo = "oscuro"


def tema_nombre() -> str:
    return _tema_activo


def C() -> dict:
    """Devuelve el diccionario de colores del tema activo."""
    return TEMAS[_tema_activo]


def cambiar_tema(nombre: str):
    global _tema_activo
    if nombre in TEMAS:
        _tema_activo = nombre


def alternar_tema():
    global _tema_activo
    _tema_activo = "claro" if _tema_activo == "oscuro" else "oscuro"


# ── Fuentes ───────────────────────────────────────────────────────────────────
FUENTES = {
    "codigo": ("Cascadia Code", 12),
    "resultado": ("Cascadia Code", 11),
    "tokens": ("Cascadia Code", 10),
    "ui": ("Segoe UI", 9),
    "titulo": ("Segoe UI", 14, "bold"),
    "boton": ("Segoe UI", 9, "bold"),
    "subtitulo": ("Segoe UI", 9, "bold"),
}


# ── Helpers: construir dicts de tags a partir del tema activo ─────────────────


def tags_resultado() -> dict:
    c = C()
    return {
        "exito": {"foreground": c["tag_exito"], "font": ("Cascadia Code", 12, "bold")},
        "error": {"foreground": c["tag_error"]},
        "num_error": {
            "foreground": c["tag_num_error"],
            "font": ("Cascadia Code", 11, "bold"),
        },
        "salida": {"foreground": c["tag_salida"]},
        "titulo": {"foreground": c["tag_titulo"], "font": ("Cascadia Code", 10)},
        "normal": {"foreground": c["tag_normal"]},
        "sep": {"foreground": c["tag_sep"]},
    }


def tags_tokens() -> dict:
    c = C()
    return {
        "cabecera": {
            "foreground": c["tag_tok_cab"],
            "font": ("Cascadia Code", 10, "bold"),
        },
        "tipo": {"foreground": c["tag_tok_tipo"]},
        "valor": {"foreground": c["tag_tok_valor"]},
        "linea": {"foreground": c["tag_tok_linea"]},
        "sep": {"foreground": c["tag_sep"]},
    }


def tags_syntax() -> dict:
    c = C()
    F = FUENTES["codigo"]
    return {
        "syn_keyword": {"foreground": c["syn_keyword"], "font": (*F[:2], "bold")},
        "syn_type": {"foreground": c["syn_type"], "font": (*F[:2], "bold")},
        "syn_string": {"foreground": c["syn_string"]},
        "syn_number": {"foreground": c["syn_number"]},
        "syn_comment": {"foreground": c["syn_comment"], "font": (*F[:2], "italic")},
        "syn_builtin": {"foreground": c["syn_builtin"], "font": (*F[:2], "bold")},
        "syn_operator": {"foreground": c["syn_operator"]},
        "syn_punct": {"foreground": c["syn_punct"]},
        "syn_id": {"foreground": c["syn_id"]},
    }


# ── Mensajes de la interfaz ───────────────────────────────────────────────────
MENSAJES_EXITO = {
    "titulo": "Qué vaina linda",
    "cuerpos": [
        "Melo, Melo, Caramelo",
        "Más bueno que una quincena de Alex Char",
        "Ajá, sí que sabes programar",
        "Compiló de una, como debe ser",
        "Esooo, sin un solo error",
    ],
}

MENSAJES_ERROR = {
    "titulo": "Paila",
    "cuerpos": [
        "¿Tú conoces a Yaper?",
        "Joda, la pasas barro",
        "Revisa eso antes de que pases pena",
        "Eso no compila ni con agua bendita",
    ],
}

MENSAJE_SIN_CODIGO = {
    "titulo": "Sin código",
    "cuerpo": "AJA ME ESTÁS MAMANDO GALLO?",
}


# ── Código de ejemplo inicial ─────────────────────────────────────────────────
CODIGO_EJEMPLO = """\
// Programa de ejemplo en Costeñol
edad Entero;
nombre Texto;
pi Real;
activo Logico;

edad = 25;
nombre = "Maria";
pi = 3,14;
activo = Verdadero;

Mensaje.Texto("Hola, soy ", nombre);
Mensaje.Texto("Tengo ", edad, " años");
"""
