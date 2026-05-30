#lexer.py — Analizador Léxico del compilador Costeñol
import ply.lex as lex

tokens = (
    "ENTERO_T",
    "REAL_T",
    "TEXTO_T",
    "LOGICO_T",
    "NUMERO_REAL",
    "NUMERO_ENTERO",
    "CADENA",
    "VERDADERO",
    "FALSO",
    "MENSAJE",
    "CAPTURA",
    "ID",
    "MAS",
    "MENOS",
    "POR",
    "ENTRE",
    "IGUAL_IGUAL",
    "DIFERENTE",
    "MENOR",
    "MAYOR",
    "MENOR_IGUAL",
    "MAYOR_IGUAL",
    "Y",
    "O",
    "NO",
    "IGUAL",
    "PUNTO_COMA",
    "PUNTO",
    "COMA",
    "PAREN_IZQ",
    "PAREN_DER",
)

palabras_reservadas = {
    "Entero": "ENTERO_T",
    "Real": "REAL_T",
    "Texto": "TEXTO_T",
    "Logico": "LOGICO_T",
    "Verdadero": "VERDADERO",
    "Falso": "FALSO",
    "Mensaje": "MENSAJE",
    "Captura": "CAPTURA",
}

palabras_reservadas_minusculas = {p.lower() for p in palabras_reservadas}


t_MAS = r"\+"
t_MENOS = r"-"
t_POR = r"\*"
t_ENTRE = r"/"
t_PUNTO_COMA = r";"
t_COMA = r","
t_PAREN_IZQ = r"\("
t_PAREN_DER = r"\)"
t_Y = r"&&"
t_O = r"\|\|"

def t_DIFERENTE(t):
    r"!="
    return t


def t_NO(t):
    r"!"
    return t


def t_IGUAL_IGUAL(t):
    r"=="
    return t


def t_MENOR_IGUAL(t):
    r"<="
    return t


def t_MAYOR_IGUAL(t):
    r">="
    return t


def t_MENOR(t):
    r"<"
    return t


def t_MAYOR(t):
    r">"
    return t


def t_NUMERO_REAL(t):
    r"[0-9]+[,\.][0-9]+"
    # Acepta tanto coma (3,14) como punto (3.14) como separador decimal
    t.value = float(t.value.replace(",", "."))
    return t


def t_NUMERO_ENTERO(t):
    r"[0-9]+"
    t.value = int(t.value)
    return t


def t_CADENA(t):
    r'"[^"\n]*"'  # no permite saltos de línea dentro de la cadena
    t.value = t.value[1:-1]
    return t


def t_IGUAL(t):
    r"="
    return t


def t_PUNTO(t):
    r"\."
    return t


def t_ID(t):
    r"[A-Za-z_]\w*"
    t.type = palabras_reservadas.get(t.value, "ID")
    return t


def t_COMENTARIO(t):
    r"//[^\n]*"
    pass


def t_newline(t):
    r"\n+"
    t.lexer.lineno += len(t.value)


t_ignore = " \t\r"


def t_error(t):
    print(f"  [Léxico] Carácter desconocido '{t.value[0]}' en línea {t.lineno}")
    t.lexer.skip(1)


# Instancia global reutilizable
lexer = lex.lex()


def tokenizar(codigo: str) -> list[tuple]:
    """
    Recibe código fuente Costeñol y retorna la lista de tokens como tuplas:
        (tipo, valor, número_de_línea)
    """
    lexer.lineno = 1
    lexer.input(codigo)
    return [(tok.type, tok.value, tok.lineno) for tok in lexer]
