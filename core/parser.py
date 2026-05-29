# core/parser.py — Analizador Sintáctico y Semántico del compilador Costeñol
import re
import ply.yacc as yacc
from tkinter import simpledialog, messagebox

from core.lexer import tokens, lexer, palabras_reservadas_minusculas  # noqa: F401
from core.simbolos import ErrorCompilacion, TablaDeSimbolos

tabla = TablaDeSimbolos()
salida_programa: list[str] = []

# ── Helpers para AST y evaluación ────────────────────────────────────────────


def tipo_expresion(expr):
    if expr is None:
        return None

    if isinstance(expr, tuple):
        etiqueta = expr[0]

        if etiqueta == "id_ref":
            nombre = expr[1]
            linea = expr[2] if len(expr) > 2 else 0
            info = tabla.buscar(nombre, linea)
            return info["tipo"] if info else None

        if etiqueta == "binop":
            op, izquierda, derecha = expr[1], expr[2], expr[3]
            tipo_izq = tipo_expresion(izquierda)
            tipo_der = tipo_expresion(derecha)
            if tipo_izq is None or tipo_der is None:
                return None

            if op in {"+", "-", "*", "/"}:
                if tipo_izq == "Texto" or tipo_der == "Texto":
                    if op == "+":
                        return "Texto"
                    tabla._error(
                        f"Operador '{op}' no es válido para tipos Texto",
                        0,
                    )
                    return None
                if tipo_izq == "Real" or tipo_der == "Real":
                    return "Real"
                return "Entero"

            if op in {"==", "!=", "<", ">", "<=", ">="}:
                return "Logico"

            if op in {"&&", "||"}:
                return "Logico"

        if etiqueta == "not":
            tipo = tipo_expresion(expr[1])
            if tipo != "Logico":
                tabla._error(
                    "Operador '!' requiere una expresión Lógica",
                    0,
                )
                return None
            return "Logico"

        return None

    return TablaDeSimbolos.tipo_de_literal(expr)


def evaluar_expresion(expr):
    if expr is None:
        return None

    if isinstance(expr, tuple):
        etiqueta = expr[0]

        if etiqueta == "id_ref":
            nombre = expr[1]
            linea = expr[2] if len(expr) > 2 else 0
            info = tabla.buscar(nombre, linea)
            return info["valor"] if info else None

        if etiqueta == "binop":
            op, izquierda, derecha = expr[1], expr[2], expr[3]
            valor_izq = evaluar_expresion(izquierda)
            valor_der = evaluar_expresion(derecha)
            if valor_izq is None or valor_der is None:
                return None

            if op == "+":
                if isinstance(valor_izq, (int, float)) and isinstance(
                    valor_der, (int, float)
                ):
                    return valor_izq + valor_der
                return str(valor_izq) + str(valor_der)
            if op == "-":
                return valor_izq - valor_der
            if op == "*":
                return valor_izq * valor_der
            if op == "/":
                if valor_der == 0:
                    tabla._error("División por cero", 0)
                    return 0
                return valor_izq / valor_der
            if op == "==":
                return valor_izq == valor_der
            if op == "!=":
                return valor_izq != valor_der
            if op == "<":
                return valor_izq < valor_der
            if op == ">":
                return valor_izq > valor_der
            if op == "<=":
                return valor_izq <= valor_der
            if op == ">=":
                return valor_izq >= valor_der
            if op == "&&":
                return bool(valor_izq) and bool(valor_der)
            if op == "||":
                return bool(valor_izq) or bool(valor_der)

        if etiqueta == "not":
            return not bool(evaluar_expresion(expr[1]))

        return None

    return expr


def evaluar_argumento(arg):
    if isinstance(arg, tuple) and arg[0] == "id_ref":
        linea = arg[2] if len(arg) > 2 else 0
        info = tabla.buscar(arg[1], linea)
        return info["valor"] if info else None
    return arg


def ejecutar_ast(ast):
    if isinstance(ast, tuple) and ast and ast[0] == "programa":
        ast = ast[1]

    for sentencia in ast:
        if sentencia[0] == "declaracion":
            continue

        if sentencia[0] == "asignacion":
            nombre, expr = sentencia[1], sentencia[2]
            valor = evaluar_expresion(expr)
            if tabla.tiene_errores():
                return
            tabla.tabla[nombre]["valor"] = valor
            continue

        if sentencia[0] == "captura_asignacion":
            nombre, tipo_captura = sentencia[1], sentencia[2]
            valor = pedir_captura(tipo_captura)
            tabla.tabla[nombre]["valor"] = valor
            continue

        if sentencia[0] == "impresion":
            args = sentencia[1]
            partes = []
            for arg in args:
                if isinstance(arg, tuple) and arg[0] == "id_ref":
                    linea = arg[2] if len(arg) > 2 else 0
                    info = tabla.buscar(arg[1], linea)
                    if info:
                        partes.append(
                            str(info["valor"])
                            if info["valor"] is not None
                            else f"<{arg[1]}>"
                        )
                    else:
                        partes.append(f"<{arg[1]}:no declarada>")
                else:
                    partes.append(str(arg))
            salida_programa.append(" ".join(partes))
            continue

    return


# ── Precedencia de operadores (menor → mayor prioridad) ───────────────────────
precedence = (
    ("left", "O"),
    ("left", "Y"),
    ("right", "NO"),
    (
        "nonassoc",
        "IGUAL_IGUAL",
        "DIFERENTE",
        "MENOR",
        "MAYOR",
        "MENOR_IGUAL",
        "MAYOR_IGUAL",
    ),
    ("left", "MAS", "MENOS"),
    ("left", "POR", "ENTRE"),
)

# Patrones para detectar sentencias incompletas (sin punto y coma)
_PATRON_ID_SUELTO = re.compile(r"^[A-Za-z_]\w*$")
_PATRON_DECLARACION = re.compile(r"^([A-Za-z_]\w*)\s+(Entero|Real|Texto|Logico)$")
_PATRON_ASIGNACION = re.compile(r"^[A-Za-z_]\w*\s*=\s*.+[^;]$")


# ── Captura de datos en tiempo de ejecución ───────────────────────────────────


def pedir_captura(tipo: str):
    """Abre un diálogo de tkinter para leer un valor del tipo indicado."""
    titulo = f"Captura — {tipo}"
    mensaje = f"Ingresa un valor de tipo {tipo}:"

    if tipo == "Texto":
        valor = simpledialog.askstring(titulo, mensaje)
        return valor if valor is not None else ""

    if tipo == "Entero":
        valor = simpledialog.askinteger(titulo, mensaje)
        return valor if valor is not None else 0

    if tipo == "Real":
        valor = simpledialog.askfloat(titulo, mensaje)
        return valor if valor is not None else 0.0

    if tipo == "Logico":
        return messagebox.askyesno(
            titulo, "¿Verdadero o Falso?\n  Sí = Verdadero\n  No = Falso"
        )

    return None


# ── Pre-validación de sentencias incompletas ──────────────────────────────────


def validar_sentencias_incompletas(codigo: str) -> str:
    """
    Recorre el código línea por línea antes de pasarlo al parser y detecta:
      - Declaraciones sin ';'  →  'num1 Entero'   en vez de  'num1 Entero;'
      - Asignaciones sin ';'   →  'num1 = 5'      en vez de  'num1 = 5;'
      - Identificador suelto   →  'nombre'         (sin tipo ni valor)
    Las líneas con error se borran para que el parser no genere mensajes confusos
    encima del error real.
    """
    lineas_limpias = []
    for num, linea in enumerate(codigo.splitlines(keepends=True), start=1):
        contenido = linea.strip()

        # Ignorar líneas vacías o comentarios
        if not contenido or contenido.startswith("//"):
            lineas_limpias.append(linea)
            continue

        # Caso 1: declaración sin ';'  →  'num1 Entero'
        if _PATRON_DECLARACION.fullmatch(contenido):
            tabla._error(
                f"Falta ';' al final de la declaración: '{contenido}'",
                num,
            )
            break

        # Caso 2: asignación sin ';'  →  'num1 = 5'
        elif _PATRON_ASIGNACION.fullmatch(contenido):
            tabla._error(
                f"Falta ';' al final de la asignación: '{contenido}'",
                num,
            )
            break

        # Caso 3: identificador suelto  →  'nombre'
        elif _PATRON_ID_SUELTO.fullmatch(contenido):
            tabla._error(
                f"Sentencia incompleta: '{contenido}' no es una declaración ni asignación",
                num,
            )
            break

        else:
            lineas_limpias.append(linea)

    return "".join(lineas_limpias)


# ── Gramática ─────────────────────────────────────────────────────────────────


def p_programa(p):
    """programa : lista_sentencias"""
    p[0] = ("programa", p[1])


def p_lista_sentencias_multiple(p):
    """lista_sentencias : lista_sentencias sentencia"""
    p[0] = p[1] + [p[2]]


def p_lista_sentencias_una(p):
    """lista_sentencias : sentencia"""
    p[0] = [p[1]]


def p_sentencia_declaracion(p):
    """sentencia : declaracion"""
    p[0] = p[1]


def p_sentencia_asignacion(p):
    """sentencia : asignacion"""
    p[0] = p[1]


def p_sentencia_impresion(p):
    """sentencia : impresion"""
    p[0] = p[1]


# ── Declaración ───────────────────────────────────────────────────────────────


def p_declaracion(p):
    """declaracion : ID tipo PUNTO_COMA"""
    nombre = p[1]
    tipo = p[2]
    linea = p.lineno(1)
    tabla.declarar(nombre, tipo, linea)
    p[0] = ("declaracion", nombre, tipo)


def p_tipo_entero(p):
    """tipo : ENTERO_T"""
    p[0] = "Entero"


def p_tipo_real(p):
    """tipo : REAL_T"""
    p[0] = "Real"


def p_tipo_texto(p):
    """tipo : TEXTO_T"""
    p[0] = "Texto"


def p_tipo_logico(p):
    """tipo : LOGICO_T"""
    p[0] = "Logico"


# ── Asignación ────────────────────────────────────────────────────────────────


def p_asignacion_expresion(p):
    """asignacion : ID IGUAL expresion PUNTO_COMA"""
    nombre = p[1]
    expresion = p[3]
    linea = p.lineno(1)

    if expresion is None:
        p[0] = ("asignacion_error", nombre)
        return

    tipo_val = tipo_expresion(expresion)
    if tipo_val is None:
        p[0] = ("asignacion_error", nombre)
        return

    if not tabla.asignar(nombre, tipo_val, None, linea):
        p[0] = ("asignacion_error", nombre)
        return

    p[0] = ("asignacion", nombre, expresion)


def p_asignacion_captura(p):
    """asignacion : ID IGUAL captura PUNTO_COMA"""
    nombre = p[1]
    tipo_captura = p[3]
    linea = p.lineno(1)

    if not tabla.existe(nombre):
        tabla._error(f"Variable '{nombre}' no declarada antes de Captura", linea)
        p[0] = ("captura_asignacion_error", nombre)
        return

    tipo_var = tabla.tabla[nombre]["tipo"]
    if tipo_var != tipo_captura:
        tabla._error(
            f"Tipo incompatible en Captura: '{nombre}' es '{tipo_var}' "
            f"pero Captura.{tipo_captura}() retorna '{tipo_captura}'",
            linea,
        )
        p[0] = ("captura_asignacion_error", nombre)
        return

    p[0] = ("captura_asignacion", nombre, tipo_captura)


def p_captura(p):
    """captura : CAPTURA PUNTO tipo PAREN_IZQ PAREN_DER"""
    p[0] = p[3]


# ── Impresión ─────────────────────────────────────────────────────────────────


def p_impresion(p):
    """impresion : MENSAJE PUNTO TEXTO_T PAREN_IZQ argumentos PAREN_DER PUNTO_COMA"""
    p[0] = ("impresion", p[5])


def p_argumentos_multiples(p):
    """argumentos : argumentos COMA argumento"""
    p[0] = p[1] + [p[3]]


def p_argumentos_uno(p):
    """argumentos : argumento"""
    p[0] = [p[1]]


def p_argumento_cadena(p):
    """argumento : CADENA"""
    p[0] = p[1]


def p_argumento_id(p):
    """argumento : ID"""
    p[0] = ("id_ref", p[1])


# ── Expresiones ───────────────────────────────────────────────────────────────


def p_expresion_logica(p):
    """expresion : expresion Y expresion
    | expresion O expresion"""
    p[0] = ("binop", p[2], p[1], p[3])


def p_expresion_no(p):
    """expresion : NO expresion"""
    p[0] = ("not", p[2])


def p_expresion_relacional(p):
    """expresion : expresion IGUAL_IGUAL expresion
    | expresion DIFERENTE   expresion
    | expresion MENOR       expresion
    | expresion MAYOR       expresion
    | expresion MENOR_IGUAL expresion
    | expresion MAYOR_IGUAL expresion"""
    p[0] = ("binop", p[2], p[1], p[3])


def p_expresion_binaria(p):
    """expresion : expresion MAS   termino
    | expresion MENOS termino"""
    p[0] = ("binop", p[2], p[1], p[3])


def p_expresion_termino(p):
    """expresion : termino"""
    p[0] = p[1]


def p_termino_binario(p):
    """termino : termino POR   factor
    | termino ENTRE factor"""
    p[0] = ("binop", p[2], p[1], p[3])


def p_termino_factor(p):
    """termino : factor"""
    p[0] = p[1]


def p_factor_numero_entero(p):
    """factor : NUMERO_ENTERO"""
    p[0] = p[1]


def p_factor_numero_real(p):
    """factor : NUMERO_REAL"""
    p[0] = p[1]


def p_factor_cadena(p):
    """factor : CADENA"""
    p[0] = p[1]


def p_factor_verdadero(p):
    """factor : VERDADERO"""
    p[0] = True


def p_factor_falso(p):
    """factor : FALSO"""
    p[0] = False


def p_factor_id(p):
    """factor : ID"""
    nombre = p[1]
    linea = p.lineno(1)

    if nombre.lower() in palabras_reservadas_minusculas:
        tabla._error(
            f"Palabra reservada '{nombre}' mal escrita; "
            f"use mayúscula inicial (ej: '{nombre.capitalize()}')",
            linea,
        )
        p[0] = None
        return

    p[0] = ("id_ref", nombre, linea)


def p_factor_paren(p):
    """factor : PAREN_IZQ expresion PAREN_DER"""
    p[0] = p[2]


# ── Error sintáctico ──────────────────────────────────────────────────────────


def p_error(p):
    if p:
        tabla._error(
            f"Error sintáctico: token inesperado '{p.value}' (tipo {p.type})",
            p.lineno,
        )
    else:
        tabla._error(
            "Error sintáctico: fin de archivo inesperado — "
            "posiblemente falta ';' al final de la última sentencia"
        )


# Instancia global del parser
parser = yacc.yacc(write_tables=False)


# ── Punto de entrada ──────────────────────────────────────────────────────────


def compilar(codigo: str, ejecutar: bool = False) -> dict:
    """
    Compila un programa Costeñol y retorna un diccionario con:
        - exito   : bool
        - ast     : árbol sintáctico (tuplas anidadas)
        - errores : lista de strings con errores léxicos/sintácticos/semánticos
        - salida  : lista de strings producidos por Mensaje.Texto(...)
        - tabla   : snapshot de la tabla de símbolos
    """
    tabla.limpiar()
    salida_programa.clear()
    lexer.lineno = 1

    try:
        codigo_limpio = validar_sentencias_incompletas(codigo)
        lexer.lineno = 1

        # Si la validación previa ya encontró un error, no continuar
        if tabla.tiene_errores():
            raise ErrorCompilacion("Error previo detectado")

        ast = parser.parse(codigo_limpio, lexer=lexer)

        if ejecutar and not tabla.tiene_errores() and ast is not None:
            ejecutar_ast(ast)

    except ErrorCompilacion:
        ast = None

    return {
        "exito": not tabla.tiene_errores() and ast is not None,
        "ast": ast,
        "errores": list(tabla.errores),
        "salida": list(salida_programa),
        "tabla": dict(tabla.tabla),
    }
