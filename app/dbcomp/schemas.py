from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel

# from .models import Tag, File, User

class UserBase(BaseModel):
    pblacore_uid: int

class UserCreate(UserBase):
    driveapi_email: str
    driveapi_name: str
    driveapi_token: str

class User(UserBase):
    driveapi_email: str
    driveapi_name: str
    driveapi_token: str
    driveapi_account_id: str

    is_active: bool

    turmas: List[Turma] = []

    files: List[File] = []

    class Config:
        orm_mode = True

class TurmaBase(BaseModel):
    pblacore_sku_turma: str
    # title: Optional[str] = None
    # description: Optional[str] = None

class TurmaCreate(TurmaBase):
    pblacore_disci_turma: str
    pblacore_ano_turma: int
    pblacore_semestre_turma: int
    users: Optional[List[int]] = None

class TurmaAddUser(TurmaBase):
    users: Optional[List[int]] = None

class Turma(TurmaBase):
    pblacore_disci: str
    pblacore_ano: int
    pblacore_semestre: int
    users: Optional[List[User]] = None

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
    title = 'File'
    description = 'Este modelo representa os  arquivos no G Drive que serão monitorados'

    users: List[User] = []

    class Config:
        orm_mode = True

User.update_forward_refs()