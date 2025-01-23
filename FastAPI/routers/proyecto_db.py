from fastapi import APIRouter, status
from bson import ObjectId
from db.schemas.proyectos import proyectos_schema, proyecto_schema
from db.client import db_client
from db.models.proyectos import Proyecto
from fastapi_pagination import Page, paginate



router = APIRouter(prefix="/proyectos", 
                   tags=["proyectos"],
                   responses={status.HTTP_404_NOT_FOUND: {"message": "No encontrado 123"}})


# Cuenta todos los proyectos
@router.get("/count", response_model=int)
async def count_proyectos():
    """
   Cuenta el número total de proyectos en la base de datos.

   Retorna:
   - int: Número total de proyectos
   """
    count = db_client.proyectos.count_documents({})
    return count


#Encuentra proyecto por id proyecto
@router.get("/{id}", response_model=Proyecto) 
async def proyectos(id: str) -> Proyecto:
    """
   Recupera un proyecto específico por su ID, incluyendo detalles de los investigadores.

   Parámetros:
   - id (str): Identificador único del proyecto

   Retorna:
   - Proyecto: Detalles del proyecto con información de los investigadores
   """
    pipeline = [
        {"$match": {"_id": ObjectId(id)}},
        {"$lookup": {
            "from": "autores",
            "localField": "Investigadores",
            "foreignField": "_id",
            "as": "Investigadores"
        }}
    ]
    proyecto = db_client.proyectos.aggregate(pipeline).next()
    return proyecto_schema(proyecto)

#Encuentra proyectos por id investigador
@router.get("/autor/{id}", response_model=Page[Proyecto]) 
async def proyectos(id: str) -> Page[Proyecto]:
    """
   Recupera una lista paginada de proyectos de un investigador específico.

   Parámetros:
   - id (str): Identificador único del investigador

   Retorna:
   - Page[Proyecto]: Página de proyectos del investigador, ordenados por título
   """
    pipeline = [
            {"$match": {"Investigadores": ObjectId(id)}},
            {"$lookup": {
                "from": "autores",
                "localField": "Investigadores",
                "foreignField": "_id",
                "as": "Investigadores"
            }},
            {"$sort": {"Título": 1, "_id": 1}}
        ]
    proyectos = list(db_client.proyectos.aggregate(pipeline))
    return paginate(proyectos_schema(proyectos))
