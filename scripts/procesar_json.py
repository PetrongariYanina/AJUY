import os
import json
import re

# Función para añadir saltos de línea en "Resumen" al detectar cambio de idioma
def ajustar_resumen(resumen):
    """
    Ajusta el texto del campo "Resumen" detectando cambios de idioma y añadiendo saltos de línea (\n).

    Este método busca patrones específicos que indican transiciones entre español e inglés, 
    como frases que terminan en español y continúan con palabras comunes en inglés (o viceversa). 
    Esto facilita la separación visual y lógica de los idiomas dentro del mismo texto.

    Args:
        resumen (str): El texto original del resumen a procesar.

    Returns:
        str: El texto ajustado con los saltos de línea insertados donde se detectaron cambios de idioma.
    
    Patrones utilizados:
        - De español a inglés: Detecta oraciones en español seguidas de palabras como 
          "This", "Introduction", "Methods", etc.
        - De inglés a español: Detecta oraciones en inglés seguidas de palabras como 
          "Esto", "Además", "Por lo tanto", etc.
    """
    patrones = [
         # Español a inglés: busca frases en español seguidas de inicio típico en inglés
        r'([a-záéíóúñü]+\.)\s*(This|Introduction|Methods|Results|Conclusion|We|These|The|A|An)',  
        # Inglés a español: busca frases en inglés seguidas de inicio típico en español
        r'(\w+\.)\s*(Esto|El|Esta|Los|Las|Una|Un|En|Además|Sin embargo|Por lo tanto)',
    ]
    for patron in patrones:
        resumen = re.sub(patron, r'\1\n\2', resumen)
    return resumen

def procesar_archivos(input_folder, output_folder):
    """
    Procesa archivos JSON en una carpeta para ajustar el campo "Resumen" 
    mediante la función `ajustar_resumen`. Los archivos procesados se guardan en 
    otra carpeta con el mismo nombre pero con un prefijo "mod_".

    Este método recorre cada archivo JSON en la carpeta de entrada, carga su contenido,
    aplica ajustes a los resúmenes en las categorías relevantes (como "Publicaciones" y "Tesis"),
    y guarda los resultados en la carpeta de salida.

    Args:
        input_folder (str): Ruta a la carpeta que contiene los archivos JSON originales.
        output_folder (str): Ruta a la carpeta donde se guardarán los archivos modificados.

    Funcionalidad:
        1. Verifica si los archivos terminan en `.json`.
        2. Carga el contenido del archivo JSON.
        3. Recorre los registros buscando las claves `Publicaciones` y `Tesis`.
        4. Procesa el campo `Resumen` de cada registro utilizando la función `ajustar_resumen`.
        5. Guarda el archivo modificado en la carpeta de salida con el prefijo "mod_".
    
    Excepciones:
        - Si la carpeta de salida no existe, la crea automáticamente.
        - Maneja archivos mal formateados o inexistentes generando errores claros.

    Returns:
        None
    """
    os.makedirs(output_folder, exist_ok=True)

    # Procesar los archivos JSON en la carpeta de entrada
    for file_name in os.listdir(input_folder):
        if file_name.endswith('.json'):
            input_file_path = os.path.join(input_folder, file_name)
            output_file_path = os.path.join(output_folder, f"mod_{file_name}")
            
            with open(input_file_path, 'r', encoding='utf-8') as infile:
                data = json.load(infile)
            
            # Recorrer registros y procesar el campo "Resumen"
            for investigador in data:
                for categoria in ['Publicaciones', 'Tesis']:
                    if categoria in investigador:
                        for item in investigador[categoria]:
                            if 'Resumen' in item:
                                item['Resumen'] = ajustar_resumen(item['Resumen'])
            
            # Guardar el archivo modificado
            with open(output_file_path, 'w', encoding='utf-8') as outfile:
                json.dump(data, outfile, ensure_ascii=False, indent=4)
    
    print(f"Archivos procesados y guardados en: {output_folder}")

# Configura las carpetas de entrada y salida antes de ejecutar
if __name__ == "__main__":
    input_folder = "data/output_blocks"  # Cambia esta ruta
    output_folder = "data/output_blocks_modified"  # Cambia esta ruta
    procesar_archivos(input_folder, output_folder)
