from fastapi import APIRouter, status
from bson import ObjectId
from db.schemas.tesis import tesis_schema, tesi_schema
from db.client import db_client
from db.models.tesis import Tesis
from fastapi_pagination import Page, paginate



router = APIRouter(prefix="/tesis", 
                   tags=["tesis"],
                   responses={status.HTTP_404_NOT_FOUND: {"message": "No encontrado 123"}})


# Cuenta todas las tesis
@router.get("/count", response_model=int)
async def count_tesis():
    """
   Cuenta el número total de tesis en la base de datos.

   Retorna:
   - int: Número total de tesis
   """
    count = db_client.tesis.count_documents({})
    return count

# Encuentra tesis por id tesis
@router.get("/{id}", response_model=Tesis) 
async def tesis(id: str) -> Tesis:
    """
   Recupera una tesis específica por su ID, incluyendo detalles de autores y directores.

   Parámetros:
   - id (str): Identificador único de la tesis

   Retorna:
   - Tesis: Detalles de la tesis con información de autores y directores
   """
    pipeline = [
        {"$match": {"_id": ObjectId(id)}},
        {"$lookup": {
            "from": "autores",
            "localField": "Autores",
            "foreignField": "_id",
            "as": "Autores"
        }},
        {"$lookup": {
            "from": "autores",
            "localField": "Director/a",
            "foreignField": "_id",
            "as": "Director/a"
        }}
    ]
    tesis = db_client.tesis.aggregate(pipeline).next()
    return tesi_schema(tesis)

# Encuentra tesis por id autor
@router.get("/autor/{id}", response_model=Page[Tesis])
async def tesis(id: str) -> Page[Tesis]:
    """
   Recupera una lista paginada de tesis relacionadas con un autor específico.

   Parámetros:
   - id (str): Identificador único del autor

   Retorna:
   - Page[Tesis]: Página de tesis donde el autor es autor o director, ordenadas por título
   """
    pipeline = [
        {"$match": {"$or": [{"Autores": ObjectId(id)}, {"Director/a": ObjectId(id)}]}},
        {"$lookup": {
            "from": "autores",
            "localField": "Autores",
            "foreignField": "_id",
            "as": "Autores"
        }},
        {"$lookup": {
            "from": "autores",
            "localField": "Director/a",
            "foreignField": "_id",
            "as": "Director/a"
        }},
        {"$sort": {"Título": 1, "_id": 1}}
    ]
    tesis = list(db_client.tesis.aggregate(pipeline))
    return paginate(tesis_schema(tesis))