from pydantic import BaseModel, Field

class Tesis(BaseModel):
    id: str
    Título: str
    Autores: list[str]
    Director:  list[str]
    Clasificación_UNESCO: str | None
    Colección: str | None
    Departamento: str | None
    Descripción: str | None
    Fecha_de_publicación: str | None
    Palabras_clave: str | None
    PDF: str | None
    Resumen: str | None
    URI: str | None