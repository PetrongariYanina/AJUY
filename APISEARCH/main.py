# Importación de librerías necesarias para la funcionalidad de la API
from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional, Dict, Union
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import numpy as np
import time
import spacy
import os
import json
from fastapi.middleware.cors import CORSMiddleware
from bson import ObjectId
import logging
from fuzzywuzzy import process
from spellchecker import SpellChecker
from datetime import datetime
from pymongo import MongoClient

# Configuración del logger para registrar información sobre la ejecución
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carga del modelo de lenguaje SpaCy
try:
    nlp = spacy.load("es_core_news_sm")
    logger.info("Modelo SpaCy cargado correctamente")
except Exception as e:
    logger.error(f"Error cargando modelo SpaCy: {e}")
    logger.error("Instala el modelo con: python -m spacy download es_core_news_sm")
    raise

# Inicialización del corrector ortográfico
spell = SpellChecker(language='es')

# Clase para representar un autor
class Autor(BaseModel):
    id: str  # ID único del autor
    nombre: str  # Nombre del autor

# Clase para representar un resultado de búsqueda
class SearchResult(BaseModel):
    id: str  # ID único del documento
    titulo: str  # Título del documento
    tipo: str  # Tipo de documento (tesis, publicación, etc.)
    resumen: Optional[str] = None  # Resumen opcional del documento
    autores: Optional[List[Autor]] = None  # Lista de autores relacionados
    score: Optional[float] = None  # Puntaje de similitud
    relevancia: Optional[float] = None  # Grado de relevancia
    palabras_clave: Optional[List[str]] = None  # Lista de palabras clave asociadas
    fecha_publicacion: Optional[str] = None  # Fecha de publicación del documento
    url: Optional[str] = None  # Enlace al documento

    class Config:
        arbitrary_types_allowed = True  # Permitir tipos arbitrarios en esta clase

# Clase para representar la respuesta de una búsqueda
class SearchResponse(BaseModel):
    total: int  # Número total de resultados
    resultados: List[SearchResult]  # Lista de resultados de búsqueda
    tiempo_busqueda: float  # Tiempo que tomó realizar la búsqueda
    consulta_procesada: Optional[str] = None  # Consulta procesada después de aplicar NLP

# Clase para representar una sugerencia de autocompletado
class AutocompleteSuggestion(BaseModel):
    id: str  # ID único del término sugerido
    text: str  # Texto sugerido
    tipo: str  # Tipo de elemento (por ejemplo, título, autor)
    score: float  # Puntaje de relevancia

# Clase para representar la respuesta de autocompletado
class AutocompleteResponse(BaseModel):
    suggestions: List[AutocompleteSuggestion]  # Lista de sugerencias

# Creación de la instancia de la API
app = FastAPI(title="API de Búsqueda Académica")

# Conexión a MongoDB utilizando la URL proporcionada como variable de entorno
mongodb_url = os.getenv("MONGODB_URL", "mongodb+srv://alopma83:1234@cluster0.anxmn.mongodb.net/Proyecto?retryWrites=true&w=majority")
if not mongodb_url:
    raise ValueError("La variable de entorno 'MONGODB_URL' no está configurada.")

# Conexión al cliente MongoDB
db_client = MongoClient(mongodb_url).Proyecto

# Configuración de CORS para permitir solicitudes desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],  # Métodos permitidos
    allow_headers=["*"],  # Encabezados permitidos
)

# Carga del modelo de embeddings para procesamiento de texto
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# Clase para gestionar búsquedas
class SearchService:
    def __init__(self, db):
        self.db = db  # Conexión a la base de datos
        self.model = model  # Modelo para generar embeddings

    # Generar un embedding para un texto dado
    async def generate_embedding(self, text: str) -> np.ndarray:
        try:
            return self.model.encode(text)
        except Exception as e:
            logger.error(f"Error generando embedding: {e}")
            raise

    # Calcular la similitud entre dos embeddings
    async def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        try:
            return float(np.dot(embedding1, embedding2) / 
                         (np.linalg.norm(embedding1) * np.linalg.norm(embedding2)))
        except Exception as e:
            logger.error(f"Error calculando similitud: {e}")
            return 0.0

    # Procesar información de un autor a partir de su ID
    async def process_author(self, autor_id) -> Autor:
        try:
            autor_doc = await self.db.Proyecto.autores.find_one({"_id": ObjectId(autor_id)})
            if autor_doc:
                return Autor(
                    id=str(autor_id),
                    nombre=autor_doc.get("Nombre", "Nombre no encontrado")
                )
            return Autor(id=str(autor_id), nombre="Autor no encontrado")
        except Exception as e:
            logger.error(f"Error procesando autor: {e}")
            return Autor(id=str(autor_id), nombre="Error")

    # Procesar palabras clave y convertirlas en una lista
    def process_keywords(self, keywords) -> Optional[List[str]]:
        if not keywords:
            return None
        if isinstance(keywords, list):
            return keywords
        if isinstance(keywords, str):
            return [k.strip() for k in keywords.split(',') if k.strip()]
        return None

# Clase para procesar consultas con NLP
class NLPProcessor:
    def __init__(self):
        # Mapeo de términos a colecciones en la base de datos
        self.tipo_mapping = {
            "tesis": "Proyecto.tesis",
            "publicación": "Proyecto.publicaciones",
            "publicaciones": "Proyecto.publicaciones",
            "publicacion": "Proyecto.publicaciones",
            "patente": "Proyecto.patentes",
            "patentes": "Proyecto.patentes",
            "proyecto": "Proyecto.proyectos",
            "proyectos": "Proyecto.proyectos"
        }

    # Procesar una consulta para extraer términos relevantes y entidades
    async def process_query(self, query: str) -> Dict:
        doc = nlp(query.lower())  # Procesar la consulta con SpaCy
        search_params = {
            "tipo": None,  # Tipo de colección (tesis, publicación, etc.)
            "query": "",  # Consulta procesada
            "limit": 10,  # Límite de resultados
            "terms": [],  # Términos relevantes
            "entities": []  # Entidades reconocidas
        }

        # Extraer entidades de la consulta
        entities = [ent.text for ent in doc.ents]
        search_params["entities"] = entities

        relevant_terms = []  # Lista de términos relevantes
        for token in doc:
            # Identificar el tipo de colección basado en el mapeo
            if token.text in self.tipo_mapping:
                search_params["tipo"] = self.tipo_mapping[token.text]
                continue

            # Agregar términos relevantes no considerados como palabras vacías
            if not token.is_stop and token.pos_ in ['NOUN', 'PROPN', 'ADJ']:
                relevant_terms.append(token.text)

        search_params["query"] = " ".join(relevant_terms)
        search_params["terms"] = relevant_terms

        return search_params


# Evento que se ejecuta al iniciar la aplicación
@app.on_event("startup")
async def startup_clients():
    """
    Inicializa los clientes y servicios necesarios al iniciar la aplicación:
    1. Crea una conexión con la base de datos MongoDB.
    2. Instancia los servicios de búsqueda (SearchService) y procesamiento NLP (NLPProcessor).
    3. Verifica que la conexión a MongoDB sea exitosa.
    """
    try:
        # Conexión asíncrona al cliente MongoDB
        app.mongodb_client = AsyncIOMotorClient(mongodb_url)
        app.mongodb = app.mongodb_client.get_database("Proyecto")
        app.search_service = SearchService(app.mongodb)  # Inicialización del servicio de búsqueda
        app.nlp_processor = NLPProcessor()  # Inicialización del procesador NLP
        await app.mongodb.command("ping")  # Verificación de conexión
        logger.info("Conectado a MongoDB Atlas")
    except Exception as e:
        logger.error(f"Error en inicio de clientes: {e}")
        raise

# Evento que se ejecuta al apagar la aplicación
@app.on_event("shutdown")
async def shutdown_clients():
    """
    Cierra la conexión con la base de datos MongoDB al apagar la aplicación.
    """
    app.mongodb_client.close()
    logger.info("Conexión a MongoDB cerrada")

# Endpoint para realizar búsquedas
@app.get("/search/", response_model=SearchResponse)
async def search(query: str, tipo: Optional[str] = None, limit: int = 10):
    """
    Realiza una búsqueda en las colecciones de MongoDB basándose en una consulta de texto.
    
    Parámetros:
    - query (str): Texto de la consulta a buscar.
    - tipo (str, opcional): Tipo de colección en la que realizar la búsqueda (tesis, publicaciones, etc.).
    - limit (int): Número máximo de resultados a devolver (por defecto 10).

    Retorna:
    - SearchResponse: Objeto con los resultados, tiempo de búsqueda y consulta procesada.
    """
    try:
        start_time = time.time()  # Inicia el temporizador
        results = []

        # Crear un patrón regex que maneje vocales con y sin tilde
        query_clean = query.lower()
        regex_pattern = query_clean.replace('i', '[ií]').replace('a', '[aá]').replace('e', '[eé]').replace('o', '[oó]').replace('u', '[uú]')
        logger.info(f"Patrón regex generado: {regex_pattern}")
        
        # Generar embedding para la consulta
        query_embedding = await app.search_service.generate_embedding(query)
        # Si no se especifica un tipo, busca en todas las colecciones
        collections = [tipo] if tipo else ["Proyecto.publicaciones", "Proyecto.tesis", "Proyecto.patentes", "Proyecto.proyectos"]

        # Iterar sobre las colecciones y buscar documentos
        for collection_name in collections:
            collection = app.mongodb[collection_name]
            # Consultar documentos que coincidan con el patrón regex en título, resumen o palabras clave
            cursor = collection.find({
                "$or": [
                    {"Título": {"$regex": regex_pattern, "$options": "i"}},
                    {"Resumen": {"$regex": regex_pattern, "$options": "i"}},
                    {"Palabras_clave": {"$regex": regex_pattern, "$options": "i"}}
                ]
            })
            
            # Procesar cada documento encontrado
            async for doc in cursor:
                doc_embedding = np.array(doc.get("embedding", []))
                if doc_embedding.size == 0:
                    continue

                # Procesar autores relacionados con el documento
                autores = []
                seen_authors = set()
                if "Autores" in doc:
                    for autor_id in doc["Autores"]:
                        if autor_id not in seen_authors:
                            seen_authors.add(autor_id)
                            autor = await app.search_service.process_author(autor_id)
                            autores.append(autor)

                # Calcular similitud entre el embedding de la consulta y el del documento
                similarity_score = await app.search_service.calculate_similarity(query_embedding, doc_embedding)
                
                # Procesar palabras clave
                palabras_clave = app.search_service.process_keywords(doc.get("Palabras_clave"))
                
                # Crear un resultado de búsqueda
                result = SearchResult(
                    id=str(doc["_id"]),
                    titulo=doc.get("Título", "Sin título"),
                    tipo=collection_name,
                    resumen=doc.get("Resumen"),
                    autores=autores,
                    score=similarity_score,
                    palabras_clave=palabras_clave,
                    fecha_publicacion=doc.get("Fecha_de_publicación"),
                    url=doc.get("URI") or doc.get("URL_del_Proyecto")
                )
                results.append(result)

        # Ordenar los resultados por score de similitud y limitar el número de resultados
        results.sort(key=lambda x: x.score, reverse=True)
        results = results[:limit]

        return SearchResponse(
            total=len(results),
            resultados=results,
            tiempo_busqueda=time.time() - start_time,
            consulta_procesada=query
        )

    except Exception as e:
        logger.error(f"Error en búsqueda: {e}")
        raise HTTPException(status_code=500, detail=f"Error realizando la búsqueda: {str(e)}")

# Endpoint para búsquedas procesadas con NLP
@app.get("/nlp-search/", response_model=SearchResponse)
async def nlp_search(query: str):
    """
    Realiza una búsqueda utilizando procesamiento NLP para interpretar y extraer términos relevantes.
    
    Parámetros:
    - query (str): Texto de la consulta.

    Retorna:
    - SearchResponse: Resultados de búsqueda basados en la consulta procesada con NLP.
    """
    try:
        start_time = time.time()  # Inicia el temporizador
        # Procesar la consulta con NLP para extraer términos y tipo
        search_params = await app.nlp_processor.process_query(query)
        # Llamar al endpoint de búsqueda con los parámetros procesados
        search_results = await search(
            query=search_params["query"],
            tipo=search_params["tipo"]
        )
        # Agregar la consulta procesada a los resultados
        search_results.consulta_procesada = search_params["query"]
        return search_results
    except Exception as e:
        logger.error(f"Error en búsqueda NLP: {e}")
        raise HTTPException(status_code=500, detail=f"Error en búsqueda NLP: {str(e)}")

# Endpoint para obtener sugerencias de autocompletado
@app.get("/autocomplete/", response_model=AutocompleteResponse)
async def get_autocomplete_suggestions(query: str, limit: int = 5, search_type: str = "all"):
    """
    Genera sugerencias de autocompletado basadas en una consulta.
    
    Parámetros:
    - query (str): Texto parcial para buscar sugerencias.
    - limit (int): Número máximo de sugerencias (por defecto 5).
    - search_type (str): Tipo de búsqueda (título, autor, o todos).

    Retorna:
    - AutocompleteResponse: Lista de sugerencias de autocompletado.
    """
    try:
        if len(query) < 2:
            return AutocompleteResponse(suggestions=[])

        # Crear patrón regex para manejar vocales con/sin tilde
        query_clean = query.strip('"').lower()
        regex_pattern = query_clean.replace('i', '[ií]').replace('a', '[aá]').replace('e', '[eé]').replace('o', '[oó]').replace('u', '[uú]')
        suggestions = []
        collections = ["Proyecto.publicaciones", "Proyecto.tesis", "Proyecto.patentes", "Proyecto.proyectos"]

        # Buscar sugerencias en las colecciones
        for collection_name in collections:
            if search_type in ["all", "title"]:
                cursor = app.mongodb[collection_name].find(
                    {"Título": {"$regex": regex_pattern, "$options": "i"}},
                    {"_id": 1, "Título": 1}
                )
                titles = []
                async for doc in cursor:
                    titles.append((str(doc["_id"]), doc["Título"]))

                matches = process.extractBests(query, [t[1] for t in titles], limit=10, score_cutoff=50)
                for match, score in matches:
                    doc_id = next(id for id, title in titles if title == match)
                    suggestions.append(AutocompleteSuggestion(
                        id=doc_id,
                        text=match,
                        tipo=f"{collection_name} (título)",
                        score=score
                    ))

            if search_type in ["all", "author"]:
                cursor = app.mongodb.Proyecto.autores.find(
                    {"Nombre": {"$regex": regex_pattern, "$options": "i"}},
                    {"_id": 1, "Nombre": 1}
                )
                authors = []
                async for doc in cursor:
                    authors.append((str(doc["_id"]), doc["Nombre"]))

                matches = process.extractBests(query, [a[1] for a in authors], limit=10, score_cutoff=50)
                for match, score in matches:
                    author_id = next(id for id, name in authors if name == match)
                    suggestions.append(AutocompleteSuggestion(
                        id=author_id,
                        text=match,
                        tipo="autor",
                        score=score
                    ))

        # Ordenar sugerencias por score y limitar el número de resultados
        suggestions.sort(key=lambda x: x.score, reverse=True)
        suggestions = suggestions[:limit]

        return AutocompleteResponse(suggestions=suggestions)

    except Exception as e:
        logger.error(f"Error en autocompletado: {e}")
        raise HTTPException(status_code=500, detail=f"Error en autocompletado: {str(e)}")

# Endpoint para probar la conexión con MongoDB
@app.get("/test")
async def test_connection():
    """
    Prueba la conexión con MongoDB y devuelve el estado de la base de datos.
    """
    try:
        await app.mongodb.command("ping")  # Comando 'ping' para verificar conexión
        return {
            "status": "success",
            "message": "Conectado a MongoDB Atlas",
            "database": "Proyecto"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

# Ejecutar la aplicación FastAPI
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))  # Obtener puerto desde variable de entorno
    uvicorn.run(app, host="0.0.0.0", port=port)
