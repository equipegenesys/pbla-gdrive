from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel
# from .models import Tag, File, User

class UserBase(BaseModel):
    driveapi_email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    pblacore_uid: int
   
    driveapi_account_id: str
    driveapi_name: str
    driveapi_email: str

    is_active: bool

    tags: List[Tag] = []

    files: List[File] = []

    class Config:
        orm_mode = True

class TagBase(BaseModel):
    title: str
    description: Optional[str] = None

class TagCreate(TagBase):
    pass

class Tag(TagBase):
    pblacore_tag: str
    pblacore_disci: str
    pblacore_ano: int
    pblacore_semestre: int
    users: List[User] = []

    class Config:
        orm_mode = True


class FileBase(BaseModel):
    title: str
    description: Optional[str] = None


class FileCreate(FileBase):
    pass


class File(FileBase):
    local_fileid: str
    pblacore_tag: str
    driveapi_file_id: int
    driveapi_owner: int
    driveapi_lastmod: str
    driveapi_lastmod_user: str
    is_active: bool

    users: List[User] = []

    class Config:
        orm_mode = True

User.update_forward_refs()