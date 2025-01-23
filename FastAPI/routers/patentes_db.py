from fastapi import APIRouter, status
from bson import ObjectId
from db.schemas.patentes import patentes_schema, patente_schema
from db.client import db_client
from db.models.patentes import Patente
from fastapi_pagination import Page, paginate



router = APIRouter(prefix="/patentes", 
                   tags=["patentes"],
                   responses={status.HTTP_404_NOT_FOUND: {"message": "No encontrado 123"}})

""" #Encuentra Patente por id patente
@router.get("/{id}", response_model=Patente) 
async def patentes(id: str) -> Patente:
    return patente_schema(db_client.patentes.find_one()) """

# Cuenta todas las patentes
@router.get("/count", response_model=int)
async def count_patentes():
    """
   Cuenta el número total de patentes en la base de datos.

   Parámetros:
   - Ninguno

   Retorna:
   - int: Número total de patentes
   """
    count = db_client.patentes.count_documents({})
    return count


@router.get("/{id}", response_model=Patente) 
async def patentes(id: str) -> Patente:
    """
   Busca una patente específica por su ID, incluyendo detalles de los autores.

   Parámetros:
   - id (str): Identificador único de la patente

   Retorna:
   - Patente: Detalles de la patente con información de los autores
   """
    pipeline = [
        {"$match": {"_id": ObjectId(id)}},
        {"$lookup": {
            "from": "autores",
            "localField": "Autores",
            "foreignField": "_id",
            "as": "Autores"
        }}
    ]
    patente = db_client.patentes.aggregate(pipeline).next()
    return patente_schema(patente)


#Encuentra Patente por id autor
@router.get("/autor/{id}", response_model= Page[Patente])
async def patentes(id: str) -> Page[Patente]:
    """
   Recupera una lista paginada de patentes de un autor específico.

   Parámetros:
   - id (str): Identificador único del autor

   Retorna:
   - Page[Patente]: Página de patentes del autor, ordenadas por título
   """
    pipeline = [
            {"$match": {"Autores": ObjectId(id)}},
            {"$lookup": {
                "from": "autores",
                "localField": "Autores",
                "foreignField": "_id",
                "as": "Autores"
            }},
            {"$sort": {"Título": 1, "_id": 1}}
        ]
    patentes = list(db_client.patentes.aggregate(pipeline))
    return paginate(patentes_schema(patentes))
