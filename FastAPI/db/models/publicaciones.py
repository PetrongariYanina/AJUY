from pydantic import BaseModel

class Publicacion(BaseModel):
    id: str
    Título: str
    Autores: list[str]
    Clasificación_UNESCO: str | None
    Colección: str | None
    DOI: str | None
    Fecha_de_publicación: str | None
    Fuente: str | None
    ISSN: str | None
    Palabras_clave: str | None
    PDF: str | None
    Resumen: str | None
    URI: str | None
