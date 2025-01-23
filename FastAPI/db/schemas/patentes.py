
from db.schemas.utilidades_schemas.utilidad_schema import autores_schema

def patente_schema(patente) -> dict:
    """
    Transforma un documento de patente de MongoDB en un diccionario estructurado.

    Parámetros:
    - patente (dict): Documento de patente de MongoDB

    Retorna:
    - dict: Diccionario con información detallada de la patente
    """
    return {"id": patente["_id"].__str__(), 
            "Título": patente["Título"], 
            "Autores": autores_schema(patente["Autores"]),
            "Colección": patente["Colección"],
            "Fecha_de_publicación": patente["Fecha_de_publicación"],
            "PDF": patente["PDF"],
            "Resumen": patente["Resumen"],
            "URI": patente["URI"],
            "URL": patente["URL"]}
            

def patentes_schema(patentes) -> list[dict]:
    """
    Convierte una lista de documentos de patentes a una lista de esquemas de patentes.

    Parámetros:
    - patentes (list): Lista de documentos de patentes de MongoDB

    Retorna:
    - list[dict]: Lista de esquemas de patentes
    """
    return [patente_schema(patente) for patente in patentes]
