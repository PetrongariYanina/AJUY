from fastapi import APIRouter, status
from bson import ObjectId
from db.schemas.publicaciones import publicaciones_schema, publicacion_schema
from db.client import db_client
from db.models.publicaciones import Publicacion
from fastapi_pagination import Page, paginate



router = APIRouter(prefix="/publicaciones", 
                   tags=["publicaciones"],
                   responses={status.HTTP_404_NOT_FOUND: {"message": "No encontrado 123"}})


# Cuenta todas las publicaciones
@router.get("/count", response_model=int)
async def count_publicaciones():
    """
   Cuenta el número total de publicaciones en la base de datos.

   Retorna:
   - int: Número total de publicaciones
   """
    count = db_client.publicaciones.count_documents({})
    return count


#Encuentra publicacion por id publicacion
@router.get("/{id}", response_model=Publicacion) 
async def publicaciones(id: str) -> Publicacion:
    """
   Recupera una publicación específica por su ID, incluyendo detalles de los autores.

   Parámetros:
   - id (str): Identificador único de la publicación

   Retorna:
   - Publicacion: Detalles de la publicación con información de los autores
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
    publicacion = db_client.publicaciones.aggregate(pipeline).next()
    return publicacion_schema(publicacion)

@router.get("/autor/{id}", response_model= Page[Publicacion])
async def publicaciones(id: str) -> Page[Publicacion]:
    """
   Recupera una lista paginada de publicaciones de un autor específico.

   Parámetros:
   - id (str): Identificador único del autor

   Retorna:
   - Page[Publicacion]: Página de publicaciones del autor, ordenadas por título
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
    publicaciones = list(db_client.publicaciones.aggregate(pipeline))
    return paginate(publicaciones_schema(publicaciones))


