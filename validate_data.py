def validate_data(*tipos_esperados):
    def decorador(func):
        def wrapper(*args, **kwargs):
            sig = inspect.signature(func)
            param_names = list(sig.parameters.keys())
            frame = sys._getframe(1)
            linea_error = frame.f_lineno
            archivo = frame.f_code.co_filename
            errores = []
            def crear_detalle_objeto(arg, tipo_recibido):
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
            for i, arg in enumerate(args_a_validar):
                tipo_recibido = type(arg)
                if not any(isinstance(arg, tipo) for tipo in tipos_esperados):
                    param_index = i + offset_posicion
                    param_name = param_names[param_index] if param_index < len(param_names) else f"arg_{param_index}"
                    objeto_detalle = crear_detalle_objeto(arg, tipo_recibido)
                    tipos_esperados_str = " | ".join([tipo.__name__ for tipo in tipos_esperados])
                    error_info = {'tipo': 'posicional','nombre': param_name,'posicion': i + 1,'tipo_esperado': tipos_esperados_str,'tipo_recibido': tipo_recibido.__name__,'objeto_detalle': objeto_detalle}
                    errores.append(error_info)
            for param_name, arg in kwargs.items():
                tipo_recibido = type(arg)
                if not any(isinstance(arg, tipo) for tipo in tipos_esperados):
                    objeto_detalle = crear_detalle_objeto(arg, tipo_recibido)
                    tipos_esperados_str = " | ".join([tipo.__name__ for tipo in tipos_esperados])
                    error_info = {'tipo': 'con_nombre','nombre': param_name,'posicion': None,'tipo_esperado': tipos_esperados_str,'tipo_recibido': tipo_recibido.__name__,'objeto_detalle': objeto_detalle}
                    errores.append(error_info)
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
