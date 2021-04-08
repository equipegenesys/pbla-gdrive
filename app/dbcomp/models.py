from __future__ import annotations
from sqlalchemy import Table, Boolean, Column, ForeignKey, Integer, String, PickleType, BigInteger
from sqlalchemy import LargeBinary, JSON, Binary, DateTime
from sqlalchemy.orm import relationship
from .access import BaseA, engine_app_db
import sqlalchemy.types as types
from sqlalchemy.dialects.postgresql import UUID
import uuid

# user_turma_table = Table('user_turma_association', BaseA.metadata,
# 						 Column('pblacore_uid', Integer,
# 								ForeignKey('users.pblacore_uid')),
# 						 Column('pblacore_tag_turma', String,
# 								ForeignKey('turmas.pblacore_tag_turma'))
						#  )

user_file_table=Table('user_file_association', BaseA.metadata,
						Column('pblacore_uid', Integer,
							   ForeignKey('users.pblacore_uid')),
						Column('local_fileid', Integer,
							   ForeignKey('files.local_fileid'))
						)

# file_turma_table = Table('file_turma_association', BaseA.metadata,
# 						 Column('local_fileid', Integer,
# 								ForeignKey('files.local_fileid')),
# 						 Column('pblacore_tag_turma', String,
# 								ForeignKey('turmas.pblacore_tag_turma'))
# 						 )


class User(BaseA):
	__tablename__ = "users"

	pblacore_uid = Column(BigInteger, primary_key=True, index=True)
	pblacore_email = Column(String)
	pblacore_nome = Column(String)

	driveapi_account_id = Column(String, unique=True, index=True)
	driveapi_name = Column(String, index=True)
	driveapi_email = Column(String, unique=True, index=True)
	driveapi_token = Column(PickleType)

	is_active = Column(Boolean, default=True)

	# turmas = relationship("Turma", secondary=user_turma_table,
	# 					  back_populates="users")

	files = relationship("File", secondary=user_file_table,
						 back_populates="users", cascade="all,delete")

	files_records = relationship("FileRecords", cascade="all,delete")

	def basicData(self):
		return {'pblacore_uid': self.pblacore_uid, 'driveapi_name': self.driveapi_name, 
		'driveapi_email': self.driveapi_email, 'is_active': self.is_active}


# class Turma(BaseA):
# 	__tablename__ = "turmas"

# 	pblacore_tag_turma = Column(String, primary_key=True, index=True)
# 	pblacore_disci_turma = Column(String, index=True)
# 	pblacore_ano_turma = Column(Integer, index=True)
# 	pblacore_semestre_turma = Column(Integer, index=True)

# 	users = relationship("User", secondary=user_turma_table,
# 						 back_populates="turmas")

# 	files = relationship("File", secondary=file_turma_table,
# 						 back_populates="turmas")


class File(BaseA):
	__tablename__ = "files"

	local_fileid = Column(Integer, primary_key=True, index=True)

	driveapi_fileid = Column(String, unique=True, index=True)

	is_active = Column(Boolean, default=True)

	channel_id = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4)

	users = relationship("User", secondary=user_file_table,
						 back_populates="files", cascade="all,delete")

	files_records = relationship("FileRecords", cascade="all,delete")

	# turmas = relationship("Turma", secondary=file_turma_table,
	# 					  back_populates="files")


class FileRecords(BaseA):
	__tablename__ = "files_records"
	
	sequencial = Column(Integer, primary_key=True, index=True)

	local_fileid = Column(Integer, ForeignKey('files.local_fileid'), index=True)

	records_for_files = relationship("File", back_populates="files_records")

	pblacore_uid = Column(Integer, ForeignKey('users.pblacore_uid'), index=True)

	records_for_users = relationship("User", back_populates="files_records")
	
	tag_turma = Column(String, index=True)
	
	record_date = Column(DateTime, index=True)
	
	file_fields = Column(JSON)
	
	activity_fields = Column(JSON)
	
	file_revision = Column(Binary)

BaseA.metadata.create_all(bind=engine_app_db)
