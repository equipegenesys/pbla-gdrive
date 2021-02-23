from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Json
from datetime import datetime

# from .models import Tag, File, User

class UserBase(BaseModel):
	pblacore_uid: int
	pblacore_email: str
	pblacore_nome: str

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
	pblacore_disci_turma: str
	pblacore_ano_turma: int
	pblacore_semestre_turma: int

class TurmaCreate(TurmaBase):
	users: Optional[List[int]] = None

class TurmaAddUser(TurmaBase):
	users: Optional[List[int]] = None

class Turma(TurmaCreate):
	files: Optional[List[File]] = None

	class Config:
		orm_mode = True

class TurmaAdd(TurmaBase):
	users: List[UserBase]

	class Config:
		orm_mode = True

class FileBase(BaseModel):
	local_fileid: int
	driveapi_fileid: str
	channel_id: uuid.UUID

class FileCreate(FileBase):
	pass


class File(FileBase):
	# driveapi_owner: str
	# driveapi_lastmod: str
	# driveapi_lastmod_user: str

	is_active: bool
	
	users: List[User] = None
	turmas: List[Turma] = None

	class Config:
		orm_mode = True

class FileRecords(BaseModel):
	source_uid: int
	record_date: Optional[datetime]
	file_fields: Json
	activity_fields: Optional[Json]
	file_revision: Optional[bytes]

	class Config:
		orm_mode = True


User.update_forward_refs()