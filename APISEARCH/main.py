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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    nlp = spacy.load("es_core_news_sm")
    logger.info("Modelo SpaCy cargado correctamente")
except Exception as e:
    logger.error(f"Error cargando modelo SpaCy: {e}")
    logger.error("Instala el modelo con: python -m spacy download es_cc8ore_news_sm")
    raise

spell = SpellChecker(language='es')

class Autor(BaseModel):
    id: str
    nombre: str

class SearchResult(BaseModel):
    id: str
    titulo: str
    tipo: str
    resumen: Optional[str] = None
    autores: Optional[List[Autor]] = None
    score: Optional[float] = None
    relevancia: Optional[float] = None
    palabras_clave: Optional[List[str]] = None
    fecha_publicacion: Optional[str] = None
    url: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True

class SearchResponse(BaseModel):
    total: int
    resultados: List[SearchResult]
    tiempo_busqueda: float
    consulta_procesada: Optional[str] = None

class AutocompleteSuggestion(BaseModel):
    id: str
    text: str
    tipo: str
    score: float

class AutocompleteResponse(BaseModel):
    suggestions: List[AutocompleteSuggestion]

app = FastAPI(title="API de Búsqueda Académica")

mongodb_url = os.getenv("MONGODB_URL", "mongodb+srv://alopma83:1234@cluster0.anxmn.mongodb.net/Proyecto?retryWrites=true&w=majority")
if not mongodb_url:
    raise ValueError("La variable de entorno 'MONGODB_URL' no está configurada.")

db_client = MongoClient(mongodb_url).Proyecto

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

class SearchService:
    def __init__(self, db):
        self.db = db
        self.model = model

    async def generate_embedding(self, text: str) -> np.ndarray:
        try:
            return self.model.encode(text)
        except Exception as e:
            logger.error(f"Error generando embedding: {e}")
            raise

    async def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        try:
            return float(np.dot(embedding1, embedding2) / 
                         (np.linalg.norm(embedding1) * np.linalg.norm(embedding2)))
        except Exception as e:
            logger.error(f"Error calculando similitud: {e}")
            return 0.0

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

    def process_keywords(self, keywords) -> Optional[List[str]]:
        if not keywords:
            return None
        if isinstance(keywords, list):
            return keywords
        if isinstance(keywords, str):
            return [k.strip() for k in keywords.split(',') if k.strip()]
        return None

class NLPProcessor:
    def __init__(self):
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

    async def process_query(self, query: str) -> Dict:
        doc = nlp(query.lower())
        search_params = {
            "tipo": None,
            "query": "",
            "limit": 10,
            "terms": [],
            "entities": []
        }

        entities = [ent.text for ent in doc.ents]
        search_params["entities"] = entities

        relevant_terms = []
        for token in doc:
            if token.text in self.tipo_mapping:
                search_params["tipo"] = self.tipo_mapping[token.text]
                continue

            if not token.is_stop and token.pos_ in ['NOUN', 'PROPN', 'ADJ']:
                relevant_terms.append(token.text)

        search_params["query"] = " ".join(relevant_terms)
        search_params["terms"] = relevant_terms

        return search_params

@app.on_event("startup")
async def startup_clients():
    try:
        app.mongodb_client = AsyncIOMotorClient(mongodb_url)
        app.mongodb = app.mongodb_client.get_database("Proyecto")
        app.search_service = SearchService(app.mongodb)
        app.nlp_processor = NLPProcessor()
        await app.mongodb.command("ping")
        logger.info("Conectado a MongoDB Atlas")
    except Exception as e:
        logger.error(f"Error en inicio de clientes: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_clients():
    app.mongodb_client.close()
    logger.info("Conexión a MongoDB cerrada")

@app.get("/search/", response_model=SearchResponse)
async def search(query: str, tipo: Optional[str] = None, limit: int = 10):
    try:
        start_time = time.time()
        results = []

        # Crear patrón regex que coincida con vocales con/sin tilde
        query_clean = query.lower()
        regex_pattern = query_clean.replace('i', '[ií]').replace('a', '[aá]').replace('e', '[eé]').replace('o', '[oó]').replace('u', '[uú]')
        logger.info(f"Patrón regex generado: {regex_pattern}")
        
        query_embedding = await app.search_service.generate_embedding(query)
        collections = [tipo] if tipo else ["Proyecto.publicaciones", "Proyecto.tesis", "Proyecto.patentes", "Proyecto.proyectos"]

        for collection_name in collections:
            collection = app.mongodb[collection_name]
            cursor = collection.find({
                "$or": [
                    {"Título": {"$regex": regex_pattern, "$options": "i"}},
                    {"Resumen": {"$regex": regex_pattern, "$options": "i"}},
                    {"Palabras_clave": {"$regex": regex_pattern, "$options": "i"}}
                ]
            })
            
            async for doc in cursor:
                doc_embedding = np.array(doc.get("embedding", []))
                if doc_embedding.size == 0:
                    continue

                autores = []
                seen_authors = set()
                if "Autores" in doc:
                    for autor_id in doc["Autores"]:
                        if autor_id not in seen_authors:
                            seen_authors.add(autor_id)
                            autor = await app.search_service.process_author(autor_id)
                            autores.append(autor)

                similarity_score = await app.search_service.calculate_similarity(query_embedding, doc_embedding)
                
                palabras_clave = app.search_service.process_keywords(doc.get("Palabras_clave"))
                
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

@app.get("/nlp-search/", response_model=SearchResponse)
async def nlp_search(query: str):
    try:
        start_time = time.time()
        search_params = await app.nlp_processor.process_query(query)
        search_results = await search(
            query=search_params["query"],
            tipo=search_params["tipo"]
        )
        search_results.consulta_procesada = search_params["query"]
        return search_results
    except Exception as e:
        logger.error(f"Error en búsqueda NLP: {e}")
        raise HTTPException(status_code=500, detail=f"Error en búsqueda NLP: {str(e)}")

@app.get("/autocomplete/", response_model=AutocompleteResponse)
async def get_autocomplete_suggestions(query: str, limit: int = 5, search_type: str = "all"):
    try:
        if len(query) < 2:
            return AutocompleteResponse(suggestions=[])

        query_clean = query.strip('"').lower()
        regex_pattern = query_clean.replace('i', '[ií]').replace('a', '[aá]').replace('e', '[eé]').replace('o', '[oó]').replace('u', '[uú]')
        suggestions = []
        collections = ["Proyecto.publicaciones", "Proyecto.tesis", "Proyecto.patentes", "Proyecto.proyectos"]

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

        suggestions.sort(key=lambda x: x.score, reverse=True)
        suggestions = suggestions[:limit]

        return AutocompleteResponse(suggestions=suggestions)

    except Exception as e:
        logger.error(f"Error en autocompletado: {e}")
        raise HTTPException(status_code=500, detail=f"Error en autocompletado: {str(e)}")

@app.get("/test")
async def test_connection():
    try:
        await app.mongodb.command("ping")
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

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)