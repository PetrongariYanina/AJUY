

def autor_schema(autor) -> dict:
    """
    Transforma un documento de autor de MongoDB en un diccionario simplificado.

    Parámetros:
    - autor (dict): Documento de autor de MongoDB

    Retorna:
    - dict: Diccionario con información básica del autor
    """
    return {"id": autor["_id"].__str__(), 
            "Nombre": autor["Nombre"], 
            "Email": autor["Email"]}

def autores_schema(autores) -> list[dict]:
    """
    Convierte una lista de documentos de autores a una lista de esquemas de autor.

    Parámetros:
    - autores (list): Lista de documentos de autores de MongoDB

    Retorna:
    - list[dict]: Lista de esquemas de autores
    """
    return [autor_schema(autor) for autor in autores]
