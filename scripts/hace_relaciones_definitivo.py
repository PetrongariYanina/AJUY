from pymongo import MongoClient
import json
import time
import os

# Conexión a MongoDB con timeout aumentado
client = os.getenv("MONGODB_URL")
db = client["Proyecto"]
autores_col = db["autores"]
publicaciones_col = db["publicaciones"]
proyectos_col = db["proyectos"]
tesis_col = db["tesis"]
patentes_col = db["patentes"]

# Eliminar datos previos
print("Limpiando colecciones...")
publicaciones_col.delete_many({})
proyectos_col.delete_many({})
tesis_col.delete_many({})
patentes_col.delete_many({})
autores_col.delete_many({})

def isAutorInText(text: str, nombre: str, apellido: str):
    """
    Verifica si un nombre de autor está presente en un texto dado.

    Esta función comprueba si tanto el nombre como el apellido de un autor 
    están presentes en un texto, independientemente de las mayúsculas o minúsculas.

    Parámetros:
    - text (str): El texto en el que se realizará la búsqueda
    - nombre (str): El nombre del autor a buscar
    - apellido (str): El apellido del autor a buscar

    Retorna:
    - bool: True si tanto el nombre como el apellido están en el texto, False en caso contrario

    Ejemplo:
    >>> isAutorInText("Juan Perez es un investigador", "Juan", "Perez")
    True
    >>> isAutorInText("Maria Lopez trabaja aquí", "Juan", "Perez")
    False
    """
    if not text:
        return False
    text = text.lower()
    nombre = nombre.lower()
    apellido = apellido.lower()
    return nombre in text and apellido in text

def isAutorInList(list: list, nombre: str, apellido: str):
    """
    Verifica si un autor está presente en alguno de los elementos de una lista.

    Esta función recorre cada elemento de una lista y utiliza isAutorInText() 
    para comprobar si el nombre y apellido del autor están presentes en alguno 
    de los elementos de la lista.

    Parámetros:
    - list (list): Lista de textos donde se realizará la búsqueda
    - nombre (str): El nombre del autor a buscar
    - apellido (str): El apellido del autor a buscar

    Retorna:
    - bool: True si el autor se encuentra en algún elemento de la lista, False en caso contrario

    Ejemplo:
    >>> isAutorInList(["Juan Perez", "Maria Lopez"], "Juan", "Perez")
    True
    >>> isAutorInList(["Maria Lopez", "Carlos Gomez"], "Juan", "Perez")
    False
    """
    if not list:
        return False
    for t in list:
        if isAutorInText(t, nombre, apellido):
            return True
    return False

# Contadores globales
total_autores = 0
total_publicaciones = 0
total_tesis = 0
total_patentes = 0
total_proyectos = 0

# Procesar archivos
todos_los_datos = []
for i in range(1, 32):
    # data/output_blocks
    filename = f"data/output_blocks_modified/mod_investigadores_detalle_{i}.json"
    try:
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)
            todos_los_datos.extend(data)
            print(f"Archivo {filename} cargado. Contiene {len(data)} autores")
    except Exception as e:
        print(f"Error al cargar archivo {filename}: {str(e)}")

print(f"Total de autores a procesar: {len(todos_los_datos)}")

# Procesar todos los datos
for autor in todos_los_datos:
    try:
        # Procesar autor
        autor_doc = {
            "Nombre": autor["Nombre"],
            "Email": autor["Perfil"].get("Email") if autor.get("Perfil") else None,
            "URL_del_perfil": autor["URL del perfil"],
        }
        
        autor_result = autores_col.update_one(
            {"URL_del_perfil": autor["URL del perfil"]}, 
            {"$set": autor_doc}, 
            upsert=True
        )
        
        autor_id = autor_result.upserted_id if autor_result.upserted_id else \
                  autores_col.find_one({"URL_del_perfil": autor["URL del perfil"]})["_id"]

        autor_split = autor.get("Nombre").split(",")
        autor_nombre = autor_split[0].strip()
        autor_apellido = autor_split[1].strip()
        
        # Procesar publicaciones
        for publicacion in autor.get("Publicaciones", []):  # Usar get con valor por defecto
            try:
                pCursor = publicaciones_col.find({"Título": publicacion["Título"]})
                try:
                    p = pCursor.next()
                    publicaciones_col.update_one(
                        {"_id": p["_id"]},
                        {"$addToSet": {"Autores": autor_id}}
                    )
                except StopIteration:
                    publicacionParseada = {
                        "Título": publicacion.get("Título"),
                        "Otros_títulos": publicacion.get("Otros_títulos"),
                        "Autores": [autor_id],
                        "Clasificación_UNESCO": publicacion.get("Clasificación UNESCO"),
                        "Palabras_clave": publicacion.get("Palabras clave"),
                        "Fecha_de_publicación": publicacion.get("Fecha de publicación"),
                        "Publicación_seriada": publicacion.get("Publicación seriada"),
                        "Resumen": publicacion.get("Resumen"),
                        "URI": publicacion.get("URI"),
                        "ISSN": publicacion.get("ISSN"),
                        "DOI": publicacion.get("DOI"),
                        "Fuente": publicacion.get("Fuente"),
                        "Colección": publicacion.get("Colección"),
                        "PDF": publicacion.get("PDF")
                    }
                    publicaciones_col.update_one(
                        {"Título": publicacionParseada["Título"]}, 
                        {"$set": publicacionParseada}, 
                        upsert=True
                    )
                    total_publicaciones += 1
            except Exception as e:
                print(f"Error en publicación: {str(e)}")

        # Procesar tesis
        for tesis in autor["Tesis"]:
        # Autores contiene tesis 
            tCursor= tesis_col.find({"Título": tesis["Título"]})
            
            isAuthor = isAutorInText(tesis.get("Autores/as"), autor_nombre, autor_apellido)
            isDirector = isAutorInText(tesis.get("Director/a "), autor_nombre, autor_apellido)
            # Recorrer cada titulo y ver que no se repita 
            try:
                p = tCursor.next()

        # Si existe, agregar el nuevo autor
                if (isAuthor):
                    tesis_col.update_one(
                    {"_id": p.get("_id")},
                    {"$addToSet": {"Autores": autor_id}}
                )
                if (isDirector):
                    tesis_col.update_one(
                    {"_id": p.get("_id")},
                    {"$addToSet": {"Director/a": autor_id}}
                )

            except StopIteration:
                tesisParseada = { 
                    "Título": tesis.get("Título"),
                    "Autores": [autor_id] if isAuthor else [tesis.get("Autores/as")],
                    "Director/a": [autor_id] if isDirector else [tesis.get("Director/a ")],
                    "Clasificación_UNESCO": tesis.get("Clasificación UNESCO"),
                    "Palabras_clave": tesis.get("Palabras clave"),
                    "Fecha_de_publicación": tesis.get("Fecha de publicación"),
                    "Resumen": tesis.get("Resumen"),
                    "Descripción": tesis.get("Descripción"),
                    "Departamento": tesis.get("Departamento"),
                    "URI": tesis.get("URI"),
                    "Colección": tesis.get("Colección"),
                    "PDF": tesis.get("PDF")
                }
                tesis_col.update_one({"Título": tesisParseada["Título"]}, {"$set": tesisParseada}, upsert=True)
                total_tesis += 1

        # Procesar patentes
        for patente in autor.get("Patentes", []): # Usar get con valor por defecto
            try:
                patentes_col.update_one(
                    {"Título": patente.get("Título")},
                    {
                        "$set": {
                            "Título": patente.get("Título"),
                            "Fecha_de_publicación": patente.get("Fecha de publicación"),
                            "Resumen": patente.get("Resumen"),
                            "URI": patente.get("URI"),
                            "URL": patente.get("URL"),
                            "Colección": patente.get("Colección"),
                            "PDF": patente.get("PDF")
                        },
                        "$addToSet": {"Autores": autor_id}
                    },
                    upsert=True
                )
                total_patentes += 1
            except Exception as e:
                print(f"Error en patente: {str(e)}")

        # Procesar proyectos
        for proyecto in autor.get("Proyectos", []):
            proCursor= proyectos_col.find({"Título": proyecto["Título"]})
            

            try:
                pro= proCursor.next()  
                proyectos_col.update_one(
                {"_id": pro.get("_id")},
                {"$addToSet": {"Investigadores": autor_id}}
                )

            except StopIteration:
                proyectosParseados = {
                    "Fecha de inicio": proyecto.get("Fecha de inicio"),
                    "Fecha de finalización": proyecto.get("Fecha de finalización"),
                    "Título": proyecto.get("Título"),
                    "URL del Proyecto": proyecto.get("URL del Proyecto"),
                    "Tipo": proyecto.get("Tipo"),
                    "Organismo Financiador": proyecto.get("Organismo Financiador"),
                    "Referencia": proyecto.get("Referencia"),
                    "Investigadores": [autor_id]
                }   
                proyectos_col.update_one({"Título": proyectosParseados["Título"]}, {"$set": proyectosParseados}, upsert=True)
                total_proyectos += 1
        
        total_autores += 1
        if total_autores % 100 == 0:
            print(f"Procesados {total_autores} autores")
            print(f"Tesis procesadas: {total_tesis}")
            print(f"Publicaciones procesadas: {total_publicaciones}")
            time.sleep(1)  # Pequeña pausa para evitar sobrecarga

    except Exception as e:
        print(f"Error procesando autor {autor.get('Nombre', 'desconocido')}: {str(e)}")

print("\nProceso completado:")
print(f"Total de autores procesados: {total_autores}")
print(f"Total de publicaciones: {total_publicaciones}")
print(f"Total de tesis: {total_tesis}")
print(f"Total de patentes: {total_patentes}")
print(f"Total de proyectos: {total_proyectos}")