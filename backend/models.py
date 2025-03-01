# models.py
from datetime import datetime
from typing import Optional, Annotated
from pydantic import BaseModel, EmailStr, ConfigDict, GetJsonSchemaHandler
from bson import ObjectId
from typing_extensions import Annotated
from pydantic.json_schema import JsonSchemaValue


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(str(v))

    @classmethod
    def __get_pydantic_json_schema__(
            cls,
            _schema_generator: GetJsonSchemaHandler,
    ) -> JsonSchemaValue:
        return {"type": "string"}


class UserModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    id: Optional[PyObjectId] = None
    username: str
    email: EmailStr
    password: str
    created_at: datetime = datetime.utcnow()

    def dict(self, *args, **kwargs):
        result = super().model_dump(*args, **kwargs)
        if result.get("id"):
            result["id"] = str(result["id"])
        return result


class VideoModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    id: Optional[PyObjectId] = None
    title: str
    description: Optional[str] = None
    file_path: str
    uploader_id: str
    created_at: datetime = datetime.utcnow()
    views: int = 0

    def dict(self, *args, **kwargs):
        result = super().model_dump(*args, **kwargs)
        if result.get("id"):
            result["id"] = str(result["id"])
        return result