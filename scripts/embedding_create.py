# Importación de librerías necesarias
from sentence_transformers import SentenceTransformer
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import logging
import numpy as np
import traceback
import sys
import pymongo

# Configuración del logger para registrar eventos
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('embedding_generation.log'),  # Guardar logs en archivo
        logging.StreamHandler(sys.stdout)  # Mostrar logs en la consola
    ]
)
logger = logging.getLogger(__name__)

# URL de conexión a la base de datos MongoDB
MONGO_URI = "mongodb+srv://alopma83:1234@cluster0.anxmn.mongodb.net/Proyecto?retryWrites=true&w=majority"

# Carga del modelo de embeddings de SentenceTransformer
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

def safe_str(value):
    """
    Convierte de forma segura cualquier valor a string.
    - Si el valor es None, retorna una cadena vacía.
    - Si el valor es una lista, combina los elementos en una sola cadena.
    - Si el valor no es una lista ni None, lo convierte directamente a string.
    """
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(str(v) for v in value if v is not None)
    return str(value)

def get_campos_embedding(collection_name):
    """
    Obtiene los campos que se deben usar para generar el embedding en función de la colección.
    - Parámetro:
      - collection_name (str): Nombre de la colección.
    - Retorna:
      - Lista de campos específicos para la colección dada.
    """
    campos_mapping = {
        'autores': ['Nombre', 'Email', 'URL_del_perfil'],
        'publicaciones': ['Título', 'Resumen', 'Palabras_clave'],
        'tesis': ['Título', 'Resumen', 'Palabras_clave', 'Descripción'],
        'proyectos': ['Título', 'Tipo', 'Organismo Financiador'],
        'patentes': ['Título', 'Resumen', 'URL']
    }
    # Extrae el nombre base de la colección (sin prefijo)
    collection_key = collection_name.lower().split('.')[-1]
    return campos_mapping.get(collection_key, [])

async def generate_embeddings():
    """
    Genera embeddings para los documentos almacenados en MongoDB:
    1. Conecta a la base de datos.
    2. Itera por cada colección, identificando documentos sin embedding.
    3. Genera embeddings para estos documentos y actualiza la base de datos.
    4. Registra estadísticas y errores del proceso.
    """
    client = None  # Cliente MongoDB
    collection_stats = {}  # Diccionario para estadísticas detalladas por colección

    try:
        # Configuración de opciones para la conexión a MongoDB
        connection_options = {
            'socketTimeoutMS': 60000,
            'connectTimeoutMS': 60000,
            'serverSelectionTimeoutMS': 60000,
            'maxPoolSize': 50,
            'waitQueueTimeoutMS': 30000
        }
        
        logger.info("Intentando conectar a MongoDB...")
        
        # Conexión al cliente MongoDB
        client = AsyncIOMotorClient(MONGO_URI, **connection_options)
        db = client.Proyecto  # Seleccionar la base de datos

        # Listar las colecciones disponibles en la base de datos
        collection_names = await db.list_collection_names()
        logger.info(f"Colecciones encontradas: {collection_names}")
        
        # Estadísticas globales
        total_processed = 0
        total_errors = 0
        
        # Iterar sobre cada colección
        for collection_name in collection_names:
            try:
                collection = db[collection_name]
                
                # Inicializar estadísticas para esta colección
                collection_stats[collection_name] = {
                    'total_documentos': 0,
                    'documentos_sin_embedding': 0,
                    'documentos_procesados': 0,
                    'documentos_con_embedding_existente': 0,
                    'errores': 0
                }
                
                # Contar documentos en la colección
                total_docs = await collection.count_documents({})
                collection_stats[collection_name]['total_documentos'] = total_docs
                
                # Contar documentos sin embedding
                docs_without_embedding = await collection.count_documents({"embedding": {"$exists": False}})
                collection_stats[collection_name]['documentos_sin_embedding'] = docs_without_embedding
                
                # Contar documentos con embedding existente
                docs_with_embedding = await collection.count_documents({"embedding": {"$exists": True}})
                collection_stats[collection_name]['documentos_con_embedding_existente'] = docs_with_embedding
                
                # Procesar documentos sin embedding
                processed_in_collection = 0
                errors_in_collection = 0
                
                # Obtener los campos relevantes para esta colección
                campos_para_embedding = get_campos_embedding(collection_name)
                
                # Procesar documentos faltantes de embedding
                async for doc in collection.find({"embedding": {"$exists": False}}):
                    try:
                        # Construir el texto base para el embedding combinando los campos relevantes
                        texto_para_embedding = ""
                        for campo in campos_para_embedding:
                            valor = doc.get(campo, '')
                            if valor:
                                texto_para_embedding += " " + safe_str(valor)
                        
                        texto_para_embedding = texto_para_embedding.strip()
                        
                        if texto_para_embedding:
                            # Generar embedding usando el modelo
                            embedding = model.encode(texto_para_embedding)
                            
                            # Actualizar el documento en la base de datos
                            await collection.update_one(
                                {"_id": doc["_id"]},
                                {"$set": {"embedding": embedding.tolist(), "embedding_text": texto_para_embedding}}
                            )
                            processed_in_collection += 1
                            
                            # Log de progreso cada 10 documentos procesados
                            if processed_in_collection % 10 == 0:
                                logger.info(f"Procesados {processed_in_collection} documentos en {collection_name}")
                        else:
                            logger.warning(f"Documento {doc.get('_id')} sin texto para procesar")
                            errors_in_collection += 1
                    
                    except Exception as doc_error:
                        # Log de errores a nivel de documento
                        logger.error(f"Error procesando documento en {collection_name}: {doc_error}")
                        logger.error(traceback.format_exc())
                        errors_in_collection += 1
                
                # Actualizar estadísticas para la colección actual
                collection_stats[collection_name]['documentos_procesados'] = processed_in_collection
                collection_stats[collection_name]['errores'] = errors_in_collection
                
                total_processed += processed_in_collection
                total_errors += errors_in_collection
            
            except Exception as collection_error:
                # Log de errores a nivel de colección
                logger.error(f"Error procesando colección {collection_name}: {collection_error}")
        
        # Log de resumen detallado
        logger.info("\n--- RESUMEN DETALLADO DE COLECCIONES ---")
        for collection, stats in collection_stats.items():
            logger.info(f"\nColección: {collection}")
            logger.info(f"  Total documentos: {stats['total_documentos']}")
            logger.info(f"  Documentos sin embedding: {stats['documentos_sin_embedding']}")
            logger.info(f"  Documentos con embedding existente: {stats['documentos_con_embedding_existente']}")
            logger.info(f"  Documentos procesados: {stats['documentos_procesados']}")
            logger.info(f"  Errores: {stats['errores']}")
        
        # Log de resumen final
        logger.info("\nProceso de generación de embeddings completado")
        logger.info(f"Total de documentos procesados: {total_processed}")
        logger.info(f"Total de errores: {total_errors}")
    
    except Exception as main_error:
        # Log de errores generales
        logger.error(f"Error principal: {main_error}")
        logger.error(traceback.format_exc())
    
    finally:
        # Asegurar el cierre de la conexión con MongoDB
        if client:
            client.close()
            logger.info("Conexión a MongoDB cerrada")

# Punto de entrada principal del script
if __name__ == "__main__":
    try:
        asyncio.run(generate_embeddings())  # Ejecutar la función principal
    except KeyboardInterrupt:
        logger.info("Proceso interrumpido por el usuario")
    except Exception as e:
        # Log de errores durante la ejecución
        logger.error(f"Error en la ejecución: {e}")
        logger.error(traceback.format_exc())
