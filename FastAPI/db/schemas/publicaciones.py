
from db.schemas.utilidades_schemas.utilidad_schema import autores_schema



def publicacion_schema(publicacion) -> dict:
    """
    Transforma un documento de publicación de MongoDB en un diccionario estructurado.

    Parámetros:
    - publicacion (dict): Documento de publicación de MongoDB

    Retorna:
    - dict: Diccionario con información detallada de la publicación
    """
    return {"id": publicacion["_id"].__str__(), 
            "Título": publicacion["Título"], 
            "Autores": autores_schema(publicacion["Autores"]),
            "Clasificación_UNESCO": publicacion["Clasificación_UNESCO"],
            "Colección": publicacion["Colección"],
            "DOI": publicacion["DOI"],
            "Fecha_de_publicación": publicacion["Fecha_de_publicación"],
            "Fuente": publicacion["Fuente"],
            "ISSN": publicacion["ISSN"],
            "Palabras_clave": publicacion["Palabras_clave"],
            "PDF": publicacion["PDF"],
            "Resumen": publicacion["Resumen"],
            "URI": publicacion["URI"]}

def publicaciones_schema(publicaciones) -> list[dict]:
    """
    Convierte una lista de documentos de publicaciones a una lista de esquemas de publicaciones.

    Parámetros:
    - publicaciones (list): Lista de documentos de publicaciones de MongoDB

    Retorna:
    - list[dict]: Lista de esquemas de publicaciones
    """
    return [publicacion_schema(publicacion) for publicacion in publicaciones]

