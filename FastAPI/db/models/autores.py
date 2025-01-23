from pydantic import BaseModel

class Autor(BaseModel):
    id: str
    Nombre: str
    Email: str

