import sys
import os

# Asegura que la raíz del proyecto esté en el path,
# necesario para que los imports de core/ y gui/ funcionen correctamente
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.interfaz import iniciar_interfaz

if __name__ == "__main__":
    iniciar_interfaz()
