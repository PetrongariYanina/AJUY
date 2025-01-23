from pydantic import BaseModel

class Proyecto(BaseModel):
    id: str
    Título: str
    Investigadores: list[str] 
    fecha_de_inicio: str | None 
    organismo_financiador: str | None
    Referencia: str | None
    Tipo: str | None
    URL_del_proyecto: str | None 

    

 