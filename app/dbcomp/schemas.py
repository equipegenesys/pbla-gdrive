from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Json
from datetime import datetime

class UserBase(BaseModel):
	pbla_uid: int
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

	# turmas: List[Turma] = []
	files_records: List[FileRecords] = []

	class Config:
		orm_mode = True

class FileRecords(BaseModel):

	record_date: Optional[datetime]

	source_pbla_uid: int
	
	tag_turma: str

	tag_equipe: str

	driveapi_fileid: str

	file_fields: Json

	activity_fields: Optional[Json]

	file_revision: Optional[bytes]

	class Config:
		orm_mode = True

User.update_forward_refs()