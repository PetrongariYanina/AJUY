
# AJUY

El proyecto AJUY tiene como finalidad scrapear sitios web para recopilar información sobre investigadores, sus publicaciones, tesis y patentes, consolidándola en una base de datos unificada. Esto es especialmente útil dado que, generalmente, cada universidad mantiene registros independientes de sus autores y publicaciones.

## Características

- **Rendimiento**: Gracias a FastAPI, AJUY ofrece un alto rendimiento y tiempos de respuesta rápidos.
- **Simplicidad**: La aplicación es fácil de usar y extender.
- **Escalabilidad**: Diseñada para crecer y adaptarse a las necesidades cambiantes.

## Funcionalidades Principales

### 1. Web Scraping
- Los scripts permiten navegar y extraer datos de diversas páginas web académicas y científicas.
- Se enfocan en recolectar información clave sobre investigadores, incluyendo:
  - Publicaciones
  - Tesis dirigidas
  - Patentes registradas

### 2. Procesamiento y Almacenamiento de Datos
- Los datos extraídos son procesados para garantizar su calidad y consistencia.
- La información consolidada se almacena en una base de datos centralizada, facilitando su acceso y análisis.

### 3. Implementación de Inteligencia Artificial
- Algunos scripts incluyen técnicas de **Inteligencia Artificial** para:
  - Mejorar la precisión en la extracción de datos.
  - Clasificar información y predecir relaciones entre datos.
- Estas implementaciones hacen que el scraping sea más eficiente y robusto.


## Requisitos Previos

Antes de instalar y ejecutar AJUY, asegúrese de tener instalado:

- **Python 3.8** o superior.
- **pip**: El gestor de paquetes de Python.

## Instalación

1. **Clone** este repositorio en su máquina local:

   ```bash
   git clone https://github.com/ecorralro/AJUY.git
   ```

2. Navegue al directorio del proyecto:

   ```bash
   cd AJUY
   ```

3. Cree un entorno virtual (opcional pero recomendado):

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # En Windows use `venv\Scripts\activate`
   ```

4. Instale las dependencias necesarias:

   ```bash
   pip install -r requirements.txt
   ```

## Uso

Para iniciar la aplicación, ejecute:

```bash
uvicorn FastAPI.main:app --reload
```

Esto iniciará el servidor en `http://127.0.0.1:8000`. Puede acceder a la documentación interactiva de la API en `http://127.0.0.1:8000/docs`.

## Estructura del Proyecto

- **FastAPI/**: Contiene los módulos principales de la aplicación, como rutas y lógica del servidor.
- **data/**: Almacena los datos recopilados y procesados por la aplicación.
- **scripts/**: Incluye:
  - Scripts responsables del scraping.
  - Scripts que implementan funcionalidades de IA.
- **requirements.txt**: Lista las dependencias necesarias para ejecutar el proyecto.
- **.gitignore**: Archivos y directorios ignorados por Git.

## Conclusión

AJUY es una solución innovadora para centralizar información dispersa sobre investigadores y sus trabajos, utilizando técnicas avanzadas de scraping y **Inteligencia Artificial** para garantizar la calidad y utilidad de los datos recopilados.

## Contribuciones

Las contribuciones son bienvenidas. Por favor, siga estos pasos:

1. **Fork** el repositorio.
2. Cree una nueva rama: `git checkout -b feature/nueva-funcionalidad`.
3. Realice sus cambios y haga un **commit**: `git commit -m 'Añadir nueva funcionalidad'`.
4. Haga un **push** a la rama: `git push origin feature/nueva-funcionalidad`.
5. Abra un **Pull Request**.

## Licencia

Este proyecto está bajo la Licencia MIT. Consulte el archivo LICENSE para más detalles.
