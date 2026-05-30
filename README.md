# COSTEÑOL 🌊

Un compilador para **Costeñol**, un lenguaje de programación con sintaxis en español diseñado como proyecto académico en la **Corporación Universitaria Latinoamericana (CUL)**.

---

## ¿Qué es Costeñol?

Costeñol es un lenguaje didáctico que permite escribir programas usando palabras en español. Tiene tipado estático, manejo de variables, operaciones aritméticas, lógicas y de comparación, entrada de datos interactiva y salida por consola visual.

---

## Estructura del proyecto

```
Compilador_costenol/
│
├── core/                  ← lógica del compilador, sin interfaz gráfica
│   ├── __init__.py
│   ├── lexer.py           ← divide el código en tokens
│   ├── parser.py          ← analiza sintaxis y semántica
│   ├── parsetab.py        ← tabla generada por PLY
│   └── simbolos.py        ← tabla de variables y tipos
│
├── gui/                   ← todo lo visual y la interacción con el usuario
│   ├── __init__.py
│   ├── editor.py          ← editor de código integrado
│   ├── explorador.py      ← explorador de archivos/proyectos
│   ├── interfaz.py        ← ventana principal, editor y paneles
│   ├── panel_resultados.py← panel para mostrar resultados/errores
│   └── temas.py           ← colores, fuentes y estilos
│
├── examples/              ← programas escritos en Costeñol listos para probar
│   ├── hola_mundo.pqek
│   ├── operaciones.pqek
│   └── errores.pqek
│
├── main.py                ← punto de entrada, arranca la aplicación
├── requirements.txt       ← dependencias del proyecto (ply)
└── README.md
```

---

## Instalación

**Requisitos:** Python 3.10 o superior.

```bash
# 1. Clona el repositorio
git clone https://github.com/osv-dog/Compilador_costenol.git
cd Compilador_costenol

# 2. Instala las dependencias
pip install -r requirements.txt

# 3. Ejecuta el compilador
python main.py
```

---

## Sintaxis del lenguaje

### Tipos de datos

| Tipo     | Descripción          | Ejemplo          |
| -------- | -------------------- | ---------------- |
| `Entero` | Número entero        | `edad Entero;`   |
| `Real`   | Número decimal       | `pi Real;`       |
| `Texto`  | Cadena de caracteres | `nombre Texto;`  |
| `Logico` | Verdadero o falso    | `activo Logico;` |

### Declaración de variables

```
nombre_variable Tipo;
```

```
edad Entero;
nombre Texto;
pi Real;
activo Logico;
```

### Asignación

```
variable = valor;
```

```
edad = 25;
nombre = "Maria";
pi = 3,14;
activo = Verdadero;
```

### Lectura de datos (entrada del usuario)

```
variable = Captura.Tipo();
```

```
edad = Captura.Entero();
nombre = Captura.Texto();
pi = Captura.Real();
activo = Captura.Logico();
```

### Impresión en pantalla

```
Mensaje.Texto("texto", variable, ...);
```

```
Mensaje.Texto("Hola, soy", nombre);
Mensaje.Texto("La suma es", resultado);
```

### Operadores

| Categoría   | Operadores                  |
| ----------- | --------------------------- |
| Aritméticos | `+` `-` `*` `/`             |
| Comparación | `==` `!=` `<` `>` `<=` `>=` |
| Lógicos     | `&&` `\|\|` `!`             |

### Comentarios

```
// Esto es un comentario de línea
```

---

## Ejemplo completo

```
// Programa de ejemplo en Costeñol
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
```

---

## Arquitectura del compilador

El compilador sigue las fases clásicas:

1. **Análisis léxico** (`core/lexer.py`) — convierte el código fuente en una lista de tokens usando PLY.
2. **Análisis sintáctico** (`core/parser.py`) — valida la gramática y construye el AST (Árbol Sintáctico Abstracto) con PLY YACC.
3. **Análisis semántico** (`core/parser.py` + `core/simbolos.py`) — verifica tipos, variables declaradas y compatibilidad de asignaciones.
4. **Ejecución** — el AST se evalúa directamente durante el análisis (interpretación).

---

## Extensión de archivos

Los programas Costeñol usan la extensión `.pqek`.

---

## Desarrollado en

**Corporación Universitaria Latinoamericana — CUL**  
Materia: Compiladores  
Lenguaje de implementación: Python 3  
Librería: [PLY (Python Lex-Yacc)](https://github.com/dabeaz/ply)
