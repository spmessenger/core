from pydantic import BaseModel


class Base(BaseModel):
    id: int

    class Creation(BaseModel):
        pass

    class Update(BaseModel):
        id: int
