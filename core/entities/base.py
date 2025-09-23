from pydantic import BaseModel


class Base(BaseModel):
    class Creation(BaseModel):
        pass

    class Update(BaseModel):
        pass
