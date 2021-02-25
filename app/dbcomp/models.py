from __future__ import annotations
from sqlalchemy import Table, Boolean, Column, ForeignKey, Integer, String, PickleType, BigInteger
from sqlalchemy import LargeBinary, JSON, Binary, DateTime
from sqlalchemy.orm import relationship
from .access import BaseA, BaseB, engine_data_db, engine_app_db
import sqlalchemy.types as types
from sqlalchemy.dialects.postgresql import UUID
import uuid

user_turma_table = Table('user_turma_association', BaseA.metadata,
						 Column('pblacore_uid', Integer,
								ForeignKey('users.pblacore_uid')),
						 Column('pblacore_sku_turma', String,
								ForeignKey('turmas.pblacore_sku_turma'))
						 )

user_file_table = Table('user_file_association', BaseA.metadata,
						Column('pblacore_uid', Integer,
							   ForeignKey('users.pblacore_uid')),
						Column('local_fileid', Integer,
							   ForeignKey('files.local_fileid'))
						)

file_turma_table = Table('file_turma_association', BaseA.metadata,
						 Column('local_fileid', Integer,
								ForeignKey('files.local_fileid')),
						 Column('pblacore_sku_turma', String,
								ForeignKey('turmas.pblacore_sku_turma'))
						 )


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

	turmas = relationship("Turma", secondary=user_turma_table,
						  back_populates="users")

	files = relationship("File", secondary=user_file_table,
						 back_populates="users")

	def basicData(self):
		return {'pblacore_uid': self.pblacore_uid, 'driveapi_name': self.driveapi_name, 'driveapi_email': self.driveapi_email, 'is_active': self.is_active}


class Turma(BaseA):
	__tablename__ = "turmas"

	pblacore_sku_turma = Column(String, primary_key=True, index=True)
	pblacore_disci_turma = Column(String, index=True)
	pblacore_ano_turma = Column(Integer, index=True)
	pblacore_semestre_turma = Column(Integer, index=True)

	users = relationship("User", secondary=user_turma_table,
						 back_populates="turmas")

	files = relationship("File", secondary=file_turma_table,
						 back_populates="turmas")


class File(BaseA):
	__tablename__ = "files"

	local_fileid = Column(Integer, primary_key=True, index=True)

	driveapi_fileid = Column(String, unique=True, index=True)

	is_active = Column(Boolean, default=True)

	channel_id = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4)

	users = relationship("User", secondary=user_file_table,
						 back_populates="files")

	turmas = relationship("Turma", secondary=file_turma_table,
						  back_populates="files")

def tableCreator(tablename):
	if not engine_data_db.dialect.has_table(engine_data_db, tablename):
		class FileRecords(BaseB):
			__tablename__ = tablename
			sequencial = Column(Integer, primary_key=True, index=True)
			source_uid = Column(Integer)
			record_date = Column(DateTime)
			file_fields = Column(JSON)
			activity_fields = Column(JSON)
			file_revision = Column(Binary)
		BaseB.metadata.create_all(bind=engine_data_db)
		return {"msg": "Tabela do arquivo foi criada no banco de dados"}
	return {"msg": "Tabela do arquivo já existe no banco de dados"}

BaseA.metadata.create_all(bind=engine_app_db)