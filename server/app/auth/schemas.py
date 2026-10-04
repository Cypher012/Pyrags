from pydantic import BaseModel


class TokenUser(BaseModel):
    id: str
    email: str
