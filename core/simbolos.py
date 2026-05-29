class TablaDeSimbolos:

    TIPOS_VALIDOS = {"Entero", "Real", "Texto", "Logico"}

    # Qué tipos de valor se pueden asignar a cada tipo de variable
    COMPATIBILIDAD = {
        "Entero": {"Entero"},
        "Real": {"Real", "Entero"},  # Real acepta también enteros (promoción)
        "Texto": {"Texto"},
        "Logico": {"Logico"},
    }

    def __init__(self):
        self.tabla: dict = {}
        self.errores: list = []

    # ── Operaciones principales ────────────────────────────────────────────────

    def declarar(self, nombre: str, tipo: str, linea: int = 0) -> bool:
        """Registra una nueva variable. Retorna True si tuvo éxito."""
        if tipo not in self.TIPOS_VALIDOS:
            self._error(
                f"Tipo '{tipo}' no válido. Tipos permitidos: {', '.join(sorted(self.TIPOS_VALIDOS))}",
                linea,
            )
            return False

        if nombre in self.tabla:
            self._error(
                f"Variable '{nombre}' ya fue declarada en línea {self.tabla[nombre]['linea']}",
                linea,
            )
            return False

        self.tabla[nombre] = {
            "tipo": tipo,
            "valor": None,
            "linea": linea,
        }
        return True

    def asignar(self, nombre: str, tipo_valor: str, valor, linea: int = 0) -> bool:
        """Asigna un valor a una variable ya declarada, verificando compatibilidad de tipos."""
        if nombre not in self.tabla:
            self._error(f"Variable '{nombre}' no ha sido declarada", linea)
            return False

        tipo_var = self.tabla[nombre]["tipo"]
        compatibles = self.COMPATIBILIDAD.get(tipo_var, set())

        if tipo_valor not in compatibles:
            self._error(
                f"Tipo incompatible: '{nombre}' es '{tipo_var}' "
                f"pero se intenta asignar un valor de tipo '{tipo_valor}'",
                linea,
            )
            return False

        self.tabla[nombre]["valor"] = valor
        return True

    def buscar(self, nombre: str, linea: int = 0) -> dict | None:
        """Busca una variable y retorna su info, o None si no existe."""
        if nombre not in self.tabla:
            self._error(f"Variable '{nombre}' no ha sido declarada", linea)
            return None
        return self.tabla[nombre]

    def existe(self, nombre: str) -> bool:
        return nombre in self.tabla

    # ── Utilidades ─────────────────────────────────────────────────────────────

    @staticmethod
    def tipo_de_literal(valor) -> str | None:
        """Infiere el tipo Costeñol de un valor Python."""
        if isinstance(valor, bool):
            return "Logico"  # bool antes de int (bool es subclase de int)
        if isinstance(valor, int):
            return "Entero"
        if isinstance(valor, float):
            return "Real"
        if isinstance(valor, str):
            return "Texto"
        return None

    def _error(self, mensaje: str, linea: int = 0):
        loc = f" (línea {linea})" if linea else ""
        entrada = f"Error semántico{loc}: {mensaje}"
        self.errores.append(entrada)

    def tiene_errores(self) -> bool:
        return len(self.errores) > 0

    def limpiar(self):
        self.tabla = {}
        self.errores = []

    # ── Representación visual ──────────────────────────────────────────────────

    def mostrar(self) -> str:
        """Retorna la tabla de símbolos formateada como texto."""
        if not self.tabla:
            return "  (tabla vacía)"

        col_var = max(len(n) for n in self.tabla) + 2
        col_var = max(col_var, 10)
        encabezado = f"  {'Variable':<{col_var}} {'Tipo':<10} {'Valor':<20} {'Línea'}"
        separador = "  " + "-" * (col_var + 10 + 20 + 8)

        filas = [encabezado, separador]
        for nombre, info in self.tabla.items():
            val = str(info["valor"]) if info["valor"] is not None else "(sin valor)"
            filas.append(
                f"  {nombre:<{col_var}} {info['tipo']:<10} {val:<20} {info['linea']}"
            )
        return "\n".join(filas)

    def __repr__(self) -> str:
        return f"<TablaDeSimbolos variables={list(self.tabla.keys())} errores={len(self.errores)}>"
