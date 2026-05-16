# Analizador Sintáctico y Semántico
import ply.yacc as yacc
from lexer import tokens, lexer
from simbolos import TablaDeSimbolos

tabla = TablaDeSimbolos()
salida_programa = []


def p_programa(p):
    '''programa : lista_sentencias'''
    p[0] = ('programa', p[1])

def p_lista_sentencias_multiple(p):
    '''lista_sentencias : lista_sentencias sentencia'''
    p[0] = p[1] + [p[2]]

def p_lista_sentencias_una(p):
    '''lista_sentencias : sentencia'''
    p[0] = [p[1]]


# SENTENCIAS

def p_sentencia_declaracion(p):
    '''sentencia : declaracion'''
    p[0] = p[1]

def p_sentencia_asignacion(p):
    '''sentencia : asignacion'''
    p[0] = p[1]

def p_sentencia_impresion(p):
    '''sentencia : impresion'''
    p[0] = p[1]

# declaraciones

def p_declaracion(p):
    '''declaracion : ID tipo PUNTO_COMA'''
    nombre = p[1]
    tipo   = p[2]
    linea  = p.lineno(1)
    tabla.declarar(nombre, tipo, linea)
    p[0] = ('declaracion', nombre, tipo)


# tipos de datos

def p_tipo_entero(p):
    '''tipo : ENTERO_T'''
    p[0] = 'Entero'

def p_tipo_real(p):
    '''tipo : REAL_T'''
    p[0] = 'Real'

def p_tipo_texto(p):
    '''tipo : TEXTO_T'''
    p[0] = 'Texto'

def p_tipo_logico(p):
    '''tipo : LOGICO_T'''
    p[0] = 'Logico'


#asignacion con expresion

def p_asignacion_expresion(p):
    '''asignacion : ID IGUAL expresion PUNTO_COMA'''
    nombre = p[1]
    valor  = p[3]
    linea  = p.lineno(1)

    tipo_val = tabla.tipo_de_literal(valor) if not isinstance(valor, str) else 'Texto'
    if isinstance(valor, str) and not isinstance(valor, bool):
        tipo_val = 'Texto'

    tabla.asignar(nombre, tipo_val, valor, linea)
    p[0] = ('asignacion', nombre, valor)

# asignacion con captura

def p_asignacion_captura(p):
    '''asignacion : ID IGUAL captura PUNTO_COMA'''
    nombre = p[1]
    tipo_captura = p[3]
    linea  = p.lineno(1)

    if not tabla.existe(nombre):
        tabla._error(f"Variable '{nombre}' no declarada antes de Captura", linea)
    else:
        info = tabla.tabla[nombre]
        if info['tipo'] != tipo_captura:
            tabla._error(
                f"Tipo incompatible en Captura: '{nombre}' es '{info['tipo']}' "
                f"pero Captura devuelve '{tipo_captura}'",
                linea
            )
        else:
            tabla.tabla[nombre]['valor'] = f'<Captura.{tipo_captura}>'

    p[0] = ('captura_asignacion', nombre, tipo_captura)


def p_captura(p):
    '''captura : CAPTURA PUNTO tipo PAREN_IZQ PAREN_DER'''
    p[0] = p[3]

#impresion
def p_impresion(p):
    '''impresion : MENSAJE PUNTO TEXTO_T PAREN_IZQ argumentos PAREN_DER PUNTO_COMA'''
    args  = p[5]
    linea = p.lineno(1)
    partes = []
    for arg in args:
        if isinstance(arg, tuple) and arg[0] == 'id_ref':
            nombre_var = arg[1]
            info = tabla.buscar(nombre_var, linea)
            if info:
                partes.append(str(info['valor']) if info['valor'] is not None else f'<{nombre_var}>')
            else:
                partes.append(f'<{nombre_var}:no declarada>')
        else:
            partes.append(str(arg))

    mensaje = ' '.join(partes)
    salida_programa.append(mensaje)
    p[0] = ('impresion', args)


def p_argumentos_multiples(p):
    '''argumentos : argumentos COMA argumento'''
    p[0] = p[1] + [p[3]]

def p_argumentos_uno(p):
    '''argumentos : argumento'''
    p[0] = [p[1]]

def p_argumento_cadena(p):
    '''argumento : CADENA'''
    p[0] = p[1]

def p_argumento_id(p):
    '''argumento : ID'''
    p[0] = ('id_ref', p[1])

# expresiones

def p_expresion_binaria(p):
    '''expresion : expresion MAS termino
                 | expresion MENOS termino'''
    if p[2] == '+':
        p[0] = p[1] + p[3] if isinstance(p[1], (int, float)) and isinstance(p[3], (int, float)) else str(p[1]) + str(p[3])
    else:
        p[0] = p[1] - p[3]

def p_expresion_termino(p):
    '''expresion : termino'''
    p[0] = p[1]

def p_termino_binario(p):
    '''termino : termino POR factor
               | termino ENTRE factor'''
    if p[2] == '*':
        p[0] = p[1] * p[3]
    else:
        if p[3] == 0:
            tabla._error("División por cero", p.lineno(2))
            p[0] = 0
        else:
            p[0] = p[1] / p[3]

def p_termino_factor(p):
    '''termino : factor'''
    p[0] = p[1]

def p_factor_numero_entero(p):
    '''factor : NUMERO_ENTERO'''
    p[0] = p[1]

def p_factor_numero_real(p):
    '''factor : NUMERO_REAL'''
    p[0] = p[1]

def p_factor_cadena(p):
    '''factor : CADENA'''
    p[0] = p[1]

def p_factor_verdadero(p):
    '''factor : VERDADERO'''
    p[0] = True

def p_factor_falso(p):
    '''factor : FALSO'''
    p[0] = False

def p_factor_id(p):
    '''factor : ID'''
    nombre = p[1]
    linea  = p.lineno(1)
    info   = tabla.buscar(nombre, linea)
    if info and info['valor'] is not None:
        p[0] = info['valor']
    else:
        p[0] = 0

def p_factor_paren(p):
    '''factor : PAREN_IZQ expresion PAREN_DER'''
    p[0] = p[2]

# manejo de errores
def p_error(p):
    if p:
        tabla._error(
            f"Error sintáctico: token inesperado '{p.value}' (tipo {p.type})",
            p.lineno
        )
    else:
        tabla._error("Error sintactico: fin de archivo inesperado")

# parser
parser = yacc.yacc()

# funcion principal
def compilar(codigo):
    tabla.limpiar()
    salida_programa.clear()
    lexer.lineno = 1

    ast = parser.parse(codigo, lexer=lexer)

    return {
        'exito':   not tabla.tiene_errores() and ast is not None,
        'ast':     ast,
        'errores': tabla.errores,
        'salida':  list(salida_programa),
        'tabla':   dict(tabla.tabla),
    }