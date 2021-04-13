from __future__ import annotations
from sqlalchemy import Table, Boolean, Column, ForeignKey, Integer, String, PickleType, BigInteger
from sqlalchemy import LargeBinary, JSON, Binary, DateTime
from sqlalchemy.orm import relationship
from .access import BaseA, engine_app_db
import sqlalchemy.types as types
from sqlalchemy.dialects.postgresql import UUID
import uuid


class User(BaseA):
	__tablename__ = "users"

	pbla_uid = Column(BigInteger, primary_key=True, index=True)

	driveapi_account_id = Column(String, unique=True, index=True)
	driveapi_name = Column(String, index=True)
	driveapi_email = Column(String, unique=True, index=True)
	driveapi_token = Column(PickleType)

	is_active = Column(Boolean, default=True)

	files_records = relationship("FileRecords", cascade="all,delete")

	def basicData(self):
		return {'pbla_uid': self.pbla_uid, 'driveapi_name': self.driveapi_name, 
		'driveapi_email': self.driveapi_email, 'is_active': self.is_active}


class FileRecords(BaseA):

	__tablename__ = "files_records"
	
	sequencial = Column(Integer, primary_key=True, index=True)

	record_date = Column(DateTime, index=True)

	source_pbla_uid = Column(Integer, ForeignKey('users.pbla_uid'), index=True)

	records_for_users = relationship("User", back_populates="files_records")
	
	tag_turma = Column(String, index=True)
	
	tag_equipe = Column(String, index=True)

	driveapi_fileid = Column(String, index=True)

	file_fields = Column(JSON)
	
	activity_fields = Column(JSON)
	
	file_revision = Column(Binary)


BaseA.metadata.create_all(bind=engine_app_db)