import inspect
import sys
from typing import Union, Dict, Any, Tuple, List, get_origin, get_args

def validate_data(**tipos_override):
    """
    Decorador para validar tipos de datos usando type hints automáticamente.
    
    Uso básico (usa type hints automáticamente):
    @validate_data()
    def mi_funcion(nombre: str, edad: int, precio: float) -> str:
        pass
    
    Uso con override (sobrescribe type hints específicos):
    @validate_data(edad=(int, str))  # Permite int o str para edad
    def mi_funcion(nombre: str, edad: int, precio: float) -> str:
        pass
    
    Args:
        **tipos_override: Diccionario opcional para sobrescribir tipos específicos
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
            
            def extraer_tipos_de_annotation(annotation):
                """Extrae tipos de las anotaciones de tipo, incluyendo Union"""
                if annotation == inspect.Parameter.empty:
                    return None
                
                # Manejar Union (ej: Union[int, str])
                origin = get_origin(annotation)
                if origin is Union:
                    return get_args(annotation)
                
                # Manejar Optional (que es Union[T, None])
                args = get_args(annotation)
                if origin is Union and len(args) == 2 and type(None) in args:
                    # Es Optional[T], devolver solo T
                    return tuple(arg for arg in args if arg is not type(None))
                
                # Tipo simple
                return (annotation,)
            
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
                offset_posicion = 1
            else:
                contexto = f"Función: {func.__name__}()"
                offset_posicion = 0
            
            # Crear un diccionario con todos los argumentos (posicionales y con nombre)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Recopilar tipos a validar (type hints + overrides)
            tipos_a_validar = {}
            
            # Primero, extraer tipos de los type hints
            for param_name, param in sig.parameters.items():
                if param_name in ['self', 'cls']:
                    continue
                    
                tipos_desde_annotation = extraer_tipos_de_annotation(param.annotation)
                if tipos_desde_annotation:
                    tipos_a_validar[param_name] = tipos_desde_annotation
            
            # Luego, aplicar overrides
            for param_name, tipos_override_param in tipos_override.items():
                tipos_a_validar[param_name] = normalizar_tipos(tipos_override_param)
            
            # Validar cada parámetro
            for param_name, tipos_esperados in tipos_a_validar.items():
                if param_name not in bound_args.arguments:
                    continue
                
                arg_value = bound_args.arguments[param_name]
                
                # Saltar validación si el valor es None y None está permitido
                if arg_value is None and type(None) in tipos_esperados:
                    continue
                
                tipo_recibido = type(arg_value)
                
                # Validar si el argumento es del tipo esperado
                if not any(isinstance(arg_value, tipo) for tipo in tipos_esperados):
                    # Determinar si es posicional o con nombre
                    param_index = param_names.index(param_name)
                    es_posicional = param_index < len(args)
                    
                    objeto_detalle = crear_detalle_objeto(arg_value, tipo_recibido)
                    tipos_esperados_str = " | ".join([tipo.__name__ for tipo in tipos_esperados])
                    
                    # Indicar si el tipo viene de type hint o override
                    fuente_tipo = "override" if param_name in tipos_override else "type hint"
                    
                    error_info = {
                        'tipo': 'posicional' if es_posicional else 'con_nombre',
                        'nombre': param_name,
                        'posicion': param_index + 1 if es_posicional else None,
                        'tipo_esperado': tipos_esperados_str,
                        'tipo_recibido': tipo_recibido.__name__,
                        'objeto_detalle': objeto_detalle,
                        'fuente_tipo': fuente_tipo
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
                    error_msg += f"Tipos esperados: {error['tipo_esperado']} (desde {error['fuente_tipo']})\n"
                    error_msg += f"Tipo recibido: {error['tipo_recibido']}\n"
                    error_msg += f"Objeto recibido: {error['objeto_detalle']}\n"
                
                error_msg += f"\n{'='*70}"
                raise TypeError(error_msg)
            
            return func(*args, **kwargs)
        return wrapper
    return decorador


# Ejemplos de uso:

# Ejemplo 1: Validación automática con type hints
@validate_data()
def crear_usuario(nombre: str, edad: int, activo: bool = True) -> str:
    return f"Usuario: {nombre}, Edad: {edad}, Activo: {activo}"

# Ejemplo 2: Con Union types
@validate_data()
def procesar_id(id: Union[int, str], descripcion: str = "") -> str:
    return f"ID: {id}, Descripción: {descripcion}"

# Ejemplo 3: Con Optional (que es Union[T, None])
from typing import Optional

@validate_data()
def crear_producto(nombre: str, precio: float, descuento: Optional[float] = None) -> str:
    if descuento:
        return f"Producto: {nombre}, Precio: {precio}, Descuento: {descuento}"
    return f"Producto: {nombre}, Precio: {precio}"

# Ejemplo 4: Sobrescribir algunos type hints
@validate_data(edad=(int, str))  # Permite int o str para edad, aunque el type hint sea solo int
def crear_perfil(nombre: str, edad: int, email: str) -> str:
    return f"Perfil: {nombre}, {edad}, {email}"

# Ejemplo 5: Con método de clase
class Calculadora:
    @validate_data()
    def sumar(self, x: Union[int, float], y: Union[int, float]) -> float:
        return x + y
    
    @validate_data()
    def dividir(self, dividendo: float, divisor: float) -> float:
        if divisor == 0:
            raise ValueError("No se puede dividir por cero")
        return dividendo / divisor

# Ejemplo 6: Con tipos complejos
@validate_data()
def procesar_datos(datos: dict, opciones: list, callback: Optional[callable] = None) -> dict:
    resultado = {"procesados": len(datos), "opciones": len(opciones)}
    if callback:
        callback(resultado)
    return resultado

# Función de prueba para demostrar el funcionamiento
def test_validator():
    print("=== PRUEBAS DEL VALIDADOR CON TYPE HINTS ===\n")
    
    # Prueba exitosa con type hints automáticos
    try:
        resultado = crear_usuario("Juan", 25, True)
        print(f"✓ Éxito: {resultado}")
    except TypeError as e:
        print(f"✗ Error: {e}")
    
    # Prueba con Union types
    try:
        resultado1 = procesar_id(123, "ID numérico")
        resultado2 = procesar_id("ABC123", "ID alfanumérico")
        print(f"✓ Éxito Union: {resultado1}")
        print(f"✓ Éxito Union: {resultado2}")
    except TypeError as e:
        print(f"✗ Error Union: {e}")
    
    # Prueba con Optional
    try:
        resultado1 = crear_producto("Laptop", 999.99)
        resultado2 = crear_producto("Mouse", 25.50, 0.1)
        print(f"✓ Éxito Optional: {resultado1}")
        print(f"✓ Éxito Optional: {resultado2}")
    except TypeError as e:
        print(f"✗ Error Optional: {e}")
    
    # Prueba con error de tipo
    try:
        resultado = crear_usuario(123, "veinticinco")  # Error: tipos incorrectos
        print(f"✓ Éxito: {resultado}")
    except TypeError as e:
        print(f"✗ Error detectado correctamente (type hints):\n{e}")
    
    # Prueba con override
    try:
        resultado1 = crear_perfil("Ana", 30, "ana@email.com")  # edad como int
        resultado2 = crear_perfil("Carlos", "25", "carlos@email.com")  # edad como str (permitido por override)
        print(f"✓ Éxito override: {resultado1}")
        print(f"✓ Éxito override: {resultado2}")
    except TypeError as e:
        print(f"✗ Error override: {e}")
    
    # Prueba con clase
    try:
        calc = Calculadora()
        resultado = calc.sumar(5, 3.5)
        print(f"✓ Éxito calculadora: {resultado}")
    except TypeError as e:
        print(f"✗ Error calculadora: {e}")

if __name__ == "__main__":
    test_validator()
