import inspect
import sys
from typing import Union, Dict, Any, Tuple, List

def validate_data(**tipos_parametros):
    """
    Decorador para validar tipos de datos de parámetros específicos.
    
    Uso:
    @validate_data(nombre_param=int, otro_param=(str, float), param_opcional=str)
    def mi_funcion(nombre_param, otro_param, param_opcional=None):
        pass
    
    Args:
        **tipos_parametros: Diccionario donde las claves son nombres de parámetros
                           y los valores son tipos o tuplas de tipos esperados
    """
    def decorador(func):
        def wrapper(*args, **kwargs):
            sig = inspect.signature(func)
            param_names = list(sig.parameters.keys())
            frame = sys._getframe(1)
            linea_error = frame.f_lineno
            archivo = frame.f_code.co_filename
            errores = []
            
            def normalizar_tipos(tipos):
                """Convierte tipos individuales a tuplas para procesamiento uniforme"""
                if isinstance(tipos, (list, tuple)):
                    return tuple(tipos)
                return (tipos,)
            
            def crear_detalle_objeto(arg, tipo_recibido):
                """Crea una representación detallada del objeto recibido"""
                if hasattr(arg, '__dict__'):
                    return f"{tipo_recibido.__name__}({arg.__dict__})"
                elif isinstance(arg, (list, tuple, set)):
                    if len(arg) <= 5:
                        return f"{tipo_recibido.__name__}({list(arg)})"
                    else:
                        return f"{tipo_recibido.__name__}([{', '.join(map(str, list(arg)[:3]))}, ...]) con {len(arg)} elementos"
                elif isinstance(arg, dict):
                    if len(arg) <= 3:
                        return f"{tipo_recibido.__name__}({dict(arg)})"
                    else:
                        primeros_items = dict(list(arg.items())[:3])
                        return f"{tipo_recibido.__name__}({primeros_items}...) con {len(arg)} elementos"
                elif isinstance(arg, str):
                    if len(arg) <= 50:
                        return f"{tipo_recibido.__name__}('{arg}')"
                    else:
                        return f"{tipo_recibido.__name__}('{arg[:47]}...') con {len(arg)} caracteres"
                else:
                    return f"{tipo_recibido.__name__}({repr(arg)})"
            
            # Detectar si es método de clase
            es_metodo_clase = len(args) > 0 and len(param_names) > 0 and param_names[0] in ['self', 'cls']
            
            if es_metodo_clase:
                instancia_clase = args[0]
                nombre_clase = instancia_clase.__class__.__name__ if param_names[0] == 'self' else args[0].__name__
                contexto = f"Método: {nombre_clase}.{func.__name__}()"
                args_a_validar = args[1:]
                offset_posicion = 1
            else:
                contexto = f"Función: {func.__name__}()"
                args_a_validar = args
                offset_posicion = 0
            
            # Crear un diccionario con todos los argumentos (posicionales y con nombre)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validar cada parámetro especificado en tipos_parametros
            for param_name, tipos_esperados in tipos_parametros.items():
                if param_name not in bound_args.arguments:
                    # El parámetro no existe en la función
                    continue
                
                arg_value = bound_args.arguments[param_name]
                tipos_esperados_tupla = normalizar_tipos(tipos_esperados)
                tipo_recibido = type(arg_value)
                
                # Validar si el argumento es del tipo esperado
                if not any(isinstance(arg_value, tipo) for tipo in tipos_esperados_tupla):
                    # Determinar si es posicional o con nombre
                    param_index = param_names.index(param_name)
                    es_posicional = param_index < len(args)
                    
                    objeto_detalle = crear_detalle_objeto(arg_value, tipo_recibido)
                    tipos_esperados_str = " | ".join([tipo.__name__ for tipo in tipos_esperados_tupla])
                    
                    error_info = {
                        'tipo': 'posicional' if es_posicional else 'con_nombre',
                        'nombre': param_name,
                        'posicion': param_index + 1 if es_posicional else None,
                        'tipo_esperado': tipos_esperados_str,
                        'tipo_recibido': tipo_recibido.__name__,
                        'objeto_detalle': objeto_detalle
                    }
                    errores.append(error_info)
            
            # Si hay errores, lanzar excepción
            if errores:
                error_msg = f"\n{'='*70}\n"
                error_msg += f"ERROR DE VALIDACIÓN DE TIPOS - MÚLTIPLES ERRORES ENCONTRADOS\n"
                error_msg += f"{'='*70}\n"
                error_msg += f"Archivo: {archivo}\n"
                error_msg += f"Línea: {linea_error}\n"
                error_msg += f"{contexto}\n"
                error_msg += f"Total de errores: {len(errores)}\n"
                error_msg += f"{'='*70}\n"
                
                for i, error in enumerate(errores, 1):
                    error_msg += f"\n--- ERROR {i} ---\n"
                    if error['tipo'] == 'posicional':
                        error_msg += f"Parámetro: '{error['nombre']}' (posición {error['posicion']})\n"
                    else:
                        error_msg += f"Parámetro: '{error['nombre']}' (argumento con nombre)\n"
                    error_msg += f"Tipos esperados: {error['tipo_esperado']}\n"
                    error_msg += f"Tipo recibido: {error['tipo_recibido']}\n"
                    error_msg += f"Objeto recibido: {error['objeto_detalle']}\n"
                
                error_msg += f"\n{'='*70}"
                raise TypeError(error_msg)
            
            return func(*args, **kwargs)
        return wrapper
    return decorador


# Ejemplos de uso:

# Ejemplo 1: Validación básica
@validate_data(nombre=str, edad=int)
def crear_usuario(nombre, edad):
    return f"Usuario: {nombre}, Edad: {edad}"

# Ejemplo 2: Múltiples tipos permitidos
@validate_data(id=(int, str), precio=(int, float))
def crear_producto(id, precio, descripcion=""):
    return f"Producto {id}: ${precio}"

# Ejemplo 3: Con método de clase
class Calculadora:
    @validate_data(x=(int, float), y=(int, float))
    def sumar(self, x, y):
        return x + y
    
    @validate_data(numeros=list)
    def promedio(self, numeros):
        return sum(numeros) / len(numeros)

# Ejemplo 4: Validación de tipos complejos
@validate_data(datos=dict, opciones=list)
def procesar_datos(datos, opciones=None):
    if opciones is None:
        opciones = []
    return f"Procesando {len(datos)} elementos con {len(opciones)} opciones"

# Función de prueba para demostrar el funcionamiento
def test_validator():
    print("=== PRUEBAS DEL VALIDADOR ===\n")
    
    # Prueba exitosa
    try:
        resultado = crear_usuario("Juan", 25)
        print(f"✓ Éxito: {resultado}")
    except TypeError as e:
        print(f"✗ Error: {e}")
    
    # Prueba con error
    try:
        resultado = crear_usuario(123, "veinticinco")  # Error: tipos incorrectos
        print(f"✓ Éxito: {resultado}")
    except TypeError as e:
        print(f"✗ Error detectado correctamente:\n{e}")
    
    # Prueba con clase
    try:
        calc = Calculadora()
        resultado = calc.sumar(5, 3.5)
        print(f"✓ Éxito calculadora: {resultado}")
    except TypeError as e:
        print(f"✗ Error calculadora: {e}")
    
    # Prueba con error en clase
    try:
        calc = Calculadora()
        resultado = calc.promedio("no es una lista")  # Error: tipo incorrecto
        print(f"✓ Éxito calculadora: {resultado}")
    except TypeError as e:
        print(f"✗ Error detectado en clase:\n{e}")

if __name__ == "__main__":
    test_validator()
