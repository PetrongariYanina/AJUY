from db.schemas.utilidades_schemas.utilidad_schema import autores_schema


def proyecto_schema(proyecto) -> dict:
    """
    Transforma un documento de proyecto de MongoDB en un diccionario estructurado.

    Parámetros:
    - proyecto (dict): Documento de proyecto de MongoDB

    Retorna:
    - dict: Diccionario con información detallada del proyecto
    """
    return {"id": proyecto["_id"].__str__(), 
            "Título": proyecto["Título"], 
            "Investigadores": autores_schema(proyecto["Investigadores"]),
            "fecha_de_inicio": proyecto["Fecha de inicio"],
            "organismo_financiador": proyecto["Organismo Financiador"],
            "Referencia": proyecto["Referencia"],
            "Tipo": proyecto["Tipo"],
            "URL_del_proyecto": proyecto["URL del Proyecto"]}
            

def proyectos_schema(proyectos) -> list[dict]:
    """
    Convierte una lista de documentos de proyectos a una lista de esquemas de proyectos.

    Parámetros:
    - proyectos (list): Lista de documentos de proyectos de MongoDB

    Retorna:
    - list[dict]: Lista de esquemas de proyectos
    """
    return [proyecto_schema(proyecto) for proyecto in proyectos]
