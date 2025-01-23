from db.schemas.utilidades_schemas.utilidad_schema import autores_schema


def tesi_schema(tesi) -> dict:
    """
    Transforma un documento de tesis de MongoDB en un diccionario estructurado.

    Parámetros:
    - tesi (dict): Documento de tesis de MongoDB

    Retorna:
    - dict: Diccionario con información detallada de la tesis
    """
    return {"id": tesi["_id"].__str__(), 
            "Título": tesi["Título"], 
            "Autores": autores_schema(tesi["Autores"]),
            "Director": autores_schema(tesi["Director/a"]),
            "Clasificación_UNESCO": tesi["Clasificación_UNESCO"],
            "Colección": tesi["Colección"],
            "Departamento": tesi["Departamento"],
            "Descripción": tesi["Descripción"],
            "Fecha_de_publicación": tesi["Fecha_de_publicación"],
            "Palabras_clave": tesi["Palabras_clave"],
            "PDF": tesi["PDF"],
            "Resumen": tesi["Resumen"],
            "URI": tesi["URI"]}

def tesis_schema(tesis) -> list[dict]:
    """
    Convierte una lista de documentos de tesis a una lista de esquemas de tesis.

    Parámetros:
    - tesis (list): Lista de documentos de tesis de MongoDB

    Retorna:
    - list[dict]: Lista de esquemas de tesis
    """
    return [tesi_schema(tesi) for tesi in tesis]
