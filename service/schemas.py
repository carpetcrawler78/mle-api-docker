from pydantic import BaseModel, ConfigDict


class UserModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    email: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str


class UserUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    email: str
    password: str
