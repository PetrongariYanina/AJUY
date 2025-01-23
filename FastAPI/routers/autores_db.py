from fastapi import APIRouter, HTTPException, status
from bson import ObjectId
from db.schemas.autores import autores_schema, autor_schema
from db.client import db_client
from db.models.autores import Autor
from fastapi_pagination import Page, paginate




router = APIRouter(prefix="/autores", 
                   tags=["autores"],
                   responses={status.HTTP_404_NOT_FOUND: {"message": "No encontrado"}})


# Encuentra todos los autores
@router.get("/", response_model=Page[Autor]) 
async def autores() -> Page[Autor]:
    """
    Recupera una lista paginada de todos los autores, ordenados por nombre.

    Parámetros:
    - Ninguno

    Retorna:
    - Page[Autor]: Página de autores ordenados alfabéticamente
    """
    return paginate(autores_schema(db_client.autores.find({}).sort({"Nombre": 1, "_id": 1}).to_list()))

# Cuenta todos los autores
@router.get("/count", response_model=int)
async def count_autores():
    """
    Cuenta el número total de autores en la base de datos.

    Parámetros:
    - Ninguno

    Retorna:
    - int: Número total de autores
    """
    count = db_client.autores.count_documents({})
    return count

# Encuentra un autor por du id
@router.get("/{id}", response_model=Autor)
async def autor(id: str):
    """
    Busca un autor específico por su ID.

    Parámetros:
    - id (str): Identificador único del autor

    Retorna:
    - Autor: Detalles del autor encontrado

    Lanza:
    - HTTPException: Si el autor no se encuentra
    """
    return autor_schema(db_client.autores.find_one({"_id": ObjectId(id)}))

