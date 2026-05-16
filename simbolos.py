
class TablaDeSimbolos:

    TIPOS_VALIDOS = {'Entero', 'Real', 'Texto', 'Logico'}

    COMPATIBILIDAD = {
        'Entero': {'Entero'},
        'Real': {'Real', 'Entero'},
        'Texto': {'Texto'},
        'Logico': {'Logico'},
    }

    def __init__(self):
        self.tabla = {}
        self.errores = []

# DECLARAR UNA VARIABLE

    def declarar(self, nombre, tipo, linea=0):

        if tipo not in self.TIPOS_VALIDOS:
            self._error(f"Tipo '{tipo}' no es válido. Use: {', '.join(self.TIPOS_VALIDOS)}", linea)
            return False

        if nombre in self.tabla:
            self._error(f"Variable '{nombre}' ya fue declarada (línea {self.tabla[nombre]['linea']})", linea)
            return False

        self.tabla[nombre] = {
            'tipo': tipo,
            'valor': None,
            'linea': linea,
        }
        return True

    def asignar(self, nombre, tipo_valor, valor, linea=0):

        if nombre not in self.tabla:
            self._error(f"Variable '{nombre}' no ha sido declarada", linea)
            return False

        tipo_var = self.tabla[nombre]['tipo']

        compatibles = self.COMPATIBILIDAD.get(tipo_var, set())
        if tipo_valor not in compatibles:
            self._error(
                f"Tipo incompatible: '{nombre}' es '{tipo_var}' "
                f"pero se intenta asignar '{tipo_valor}'",
                linea
            )
            return False

        # Guardar el valor
        self.tabla[nombre]['valor'] = valor
        return True

# BUSCAR UNA VARIABLE

    def buscar(self, nombre, linea=0):

        if nombre not in self.tabla:
            self._error(f"Variable '{nombre}' no ha sido declarada", linea)
            return None
        return self.tabla[nombre]

    def existe(self, nombre):
        return nombre in self.tabla


    @staticmethod
    def tipo_de_literal(valor):

        if isinstance(valor, bool):
            return 'Logico'
        elif isinstance(valor, int):
            return 'Entero'
        elif isinstance(valor, float):
            return 'Real'
        elif isinstance(valor, str):
            return 'Texto'
        return None

# aca los errores semanticos
    def _error(self, mensaje, linea=0):
        loc = f" (línea {linea})" if linea else ""
        entrada = f"Error semántico{loc}: {mensaje}"
        self.errores.append(entrada)


    def mostrar(self):
        if not self.tabla:
            return "  (tabla vacía)"
        lineas = []
        lineas.append(f"  {'Variable':<15} {'Tipo':<10} {'Valor':<15} {'Línea'}")
        lineas.append("  " + "-" * 50)
        for nombre, info in self.tabla.items():
            val = str(info['valor']) if info['valor'] is not None else '(sin valor)'
            lineas.append(f"  {nombre:<15} {info['tipo']:<10} {val:<15} {info['linea']}")
        return "\n".join(lineas)

    def tiene_errores(self):
        return len(self.errores) > 0

    def limpiar(self):
        self.tabla = {}
        self.errores = []