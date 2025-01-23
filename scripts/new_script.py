import requests
from bs4 import BeautifulSoup
import json
import time
import random
import os

# URL base de la página
base_url = "https://accedacris.ulpgc.es"

def get_detalle(publicacion_url):
    try:
        response = requests.get(publicacion_url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error al acceder a la publicación {publicacion_url}: {e}")
        return {}

    soup = BeautifulSoup(response.content, "html.parser")
    detalles = {}

    table = soup.find('table', class_='table itemDisplayTable')
    if table:
        cells = table.find_all('td')
        for i in range(0, len(cells) - 1, 2):
            label = cells[i].get_text(strip=True).replace(":", "")
            value = cells[i + 1]

            if value.find('br'):
                value = ' '.join(value.stripped_strings)
            elif value.find('a'):
                value = ' '.join([a.get_text(strip=True) + f" (Link: {a['href']})" for a in value.find_all('a')])
            else:
                value = value.get_text(strip=True)

            detalles[label] = value
            
    pdf_element = soup.find('a', href=True, target="_blank")
    if pdf_element and pdf_element['href'].endswith('.pdf'):
        detalles['PDF'] = base_url + pdf_element['href']        
            
    return detalles

def get_section_items(perfil_url, section_path, title_id):
    items_list = []
    current_url = f"{perfil_url}/{section_path}.html"
    try:
        response = requests.get(current_url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error al acceder a la sección {section_path}: {e}")
        return items_list

    soup = BeautifulSoup(response.content, "html.parser")
    items = soup.find_all('div', id='item_fields')

    for item in items:
        titulo_element = item.find('div', id=title_id)
        if titulo_element and titulo_element.find('a'):
            titulo = titulo_element.find('a').text.strip()
            item_url = base_url + titulo_element.find('a')['href']
            detalles = get_detalle(item_url)
            items_list.append(detalles)

    return items_list

# Funciones auxiliares para distintas secciones
get_publicaciones = lambda perfil_url: get_section_items(perfil_url, 'publicaciones', 'dc.title')
# get_proyectos = lambda perfil_url: get_section_items(perfil_url, 'projects', 'crisproject.title')
get_tesis = lambda perfil_url: get_section_items(perfil_url, 'tesis', 'dc.title')
get_patentes = lambda perfil_url: get_section_items(perfil_url, 'patentes', 'dc.title')
def get_proyectos(perfil_url):
    """
    Extrae los proyectos de la página de un perfil de investigador.
    
    Args:
        perfil_url (str): URL del perfil del investigador.
    
    Returns:
        list: Lista de diccionarios con los detalles de cada proyecto.
    """
    proyectos_list = []
    current_url = f"{perfil_url}/projects.html"
    
    try:
        response = requests.get(current_url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error al acceder a la sección de proyectos: {e}")
        return proyectos_list

    soup = BeautifulSoup(response.content, "html.parser")
    proyectos = soup.find_all('div', class_='item-container')

    for proyecto in proyectos:
        detalles = {}

        # Extraer la fecha de inicio
        start_date_element = proyecto.find('div', id='crisproject.startdate')
        detalles['Fecha de inicio'] = start_date_element.find('em').text if start_date_element else "No disponible"

        # Extraer la fecha de finalización
        end_date_element = proyecto.find('div', id='crisproject.expdate')
        detalles['Fecha de finalización'] = end_date_element.find('em').text if end_date_element else "No disponible"

        # Extraer el título del proyecto
        title_element = proyecto.find('div', id='crisproject.title')
        if title_element and title_element.find('a'):
            detalles['Título'] = title_element.find('a').text.strip()
            detalles['URL del Proyecto'] = base_url + title_element.find('a')['href']
        else:
            detalles['Título'] = "No disponible"
            detalles['URL del Proyecto'] = "No disponible"

        # Extraer investigador principal
        personal_investigador = get_personal_investigador(proyecto)
        detalles.update(personal_investigador)

        # Extraer tipo de proyecto
        tipo_element = proyecto.find('div', id='crisproject.tipo')
        detalles['Tipo'] = tipo_element.find('em').text.strip() if tipo_element else "No disponible"

        # Extraer organismo financiador
        funder_element = proyecto.find('div', id='crisproject.funderorganization')
        detalles['Organismo Financiador'] = funder_element.find('em').text.strip() if funder_element else "No disponible"

        # Extraer referencia del proyecto
        reference_element = proyecto.find('div', id='crisproject.reference')
        detalles['Referencia'] = reference_element.find('em').text.strip() if reference_element else "No disponible"

        # Añadir el proyecto a la lista
        proyectos_list.append(detalles)

    return proyectos_list

def get_personal_investigador(proyecto):
    """
    Extrae información sobre el personal investigador de un proyecto específico.
    
    Args:
        proyecto (BeautifulSoup): Objeto BeautifulSoup del contenedor del proyecto.
    
    Returns:
        dict: Diccionario con los investigadores principales y el equipo de investigación.
    """
    personal = {
        "Investigador principal": []
    }

    # Extraer investigador principal
    principal_investigator_div = proyecto.find('div', id='crisproject.principalinvestigator')
    if principal_investigator_div:
        investigador_em = principal_investigator_div.find('em')
        investigador_a = principal_investigator_div.find('a')
        if investigador_em and investigador_a:
            personal["Investigador principal"].append({
                "Nombre": investigador_em.text.strip(),
                "URL": base_url + investigador_a['href']
            })

    # Extraer investigador principal 2 (solo agregar nombre si está presente)
    principal_investigator_dos_div = proyecto.find('div', id='crisproject.principalinvestigator_dos')
    if principal_investigator_dos_div:
        investigador_dos_em = principal_investigator_dos_div.find('em')
        if investigador_dos_em and investigador_dos_em.text.strip() != "Investigador principal:":
            personal["Investigador principal"].append({
                "Nombre": investigador_dos_em.text.strip()
            })
        elif principal_investigator_dos_div.text.strip() and principal_investigator_dos_div.text.strip() != "Investigador principal:":
            personal["Investigador principal"].append({
                "Nombre": principal_investigator_dos_div.text.strip()
            })

    return personal

# Proceso principal
def main():
    page_number = 0
    limit_per_page = 50
    block_size = 2  # Número de páginas por bloque
    output_folder = "output_blocks"  # Carpeta donde se guardarán los bloques

    # Crear carpeta si no existe
    os.makedirs(output_folder, exist_ok=True)

    while True:
        investigadores_lista = []
        for _ in range(block_size):
            current_url = f"{base_url}/simple-search?query=&location=researcherprofiles&start={page_number * limit_per_page}"
            try:
                response = requests.get(current_url, timeout=10)
                response.raise_for_status()
            except requests.RequestException as e:
                print(f"Error al acceder a la página {page_number}: {e}")
                break

            soup = BeautifulSoup(response.content, 'html.parser')
            investigadores = soup.find_all('div', class_='item-fields')

            if not investigadores:
                print("No se encontraron más investigadores. Finalizando.")
                return

            for investigador in investigadores:
                nombre_elemento = investigador.find('div', id='crisrp.fullname')
                nombre = nombre_elemento.text.strip() if nombre_elemento else "N/A"
                perfil_url = base_url + nombre_elemento.find('a')['href'].strip() if nombre_elemento and nombre_elemento.find('a') else "N/A"

                try:
                    perfil_response = requests.get(perfil_url, timeout=10)
                    perfil_response.raise_for_status()
                except requests.RequestException as e:
                    print(f"Error al acceder al perfil de {nombre}: {e}")
                    continue

                perfil_soup = BeautifulSoup(perfil_response.content, 'html.parser')
                email_element = perfil_soup.find('div', id='emailDiv')
                email = email_element.text.strip() if email_element else "N/A"

                # Reemplaza estas funciones con tus implementaciones
                publicaciones = get_publicaciones(perfil_url)
                proyectos = get_proyectos(perfil_url)
                tesis = get_tesis(perfil_url)
                patentes = get_patentes(perfil_url)

                investigadores_lista.append({
                    "Nombre": nombre,
                    "URL del perfil": perfil_url,
                    "Perfil": {"Email": email},
                    "Publicaciones": publicaciones,
                    "Proyectos": proyectos,
                    "Tesis": tesis,
                    "Patentes": patentes
                })

                time.sleep(random.uniform(0.5, 2))

            page_number += 1

        # Guardar el bloque en un archivo separado
        block_file = os.path.join(output_folder, f"investigadores_detalle_{page_number // block_size}.json")
        with open(block_file, "w", encoding="utf-8") as file:
            json.dump(investigadores_lista, file, ensure_ascii=False, indent=4)
        print(f"Bloque guardado: {block_file}")

if __name__ == "__main__":
    main()
