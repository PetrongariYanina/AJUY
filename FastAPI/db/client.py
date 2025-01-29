import os
from pymongo import MongoClient

# Obtener la variable de entorno directamente
mongodb_url = (MONGODB_URL)

# Manejar el caso en que no esté configurada
if not mongodb_url:
    raise ValueError("La variable de entorno 'MONGODB_URL' no está configurada.")

# Crear el cliente de MongoDB
db_client = MongoClient(mongodb_url).Proyecto

""" db_client = MongoClient().Proyecto """
