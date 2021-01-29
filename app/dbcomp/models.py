from __future__ import annotations
from sqlalchemy import Table, Boolean, Column, ForeignKey, Integer, String, LargeBinary, PickleType
from sqlalchemy.orm import relationship
from .access import Base


user_turma_table = Table('user_turma_association', Base.metadata,
                       Column('pblacore_uid', Integer,
                              ForeignKey('users.pblacore_uid')),
                       Column('pblacore_sku_turma', String,
                              ForeignKey('turmas.pblacore_sku_turma'))
                       )

user_file_table = Table('user_file_association', Base.metadata,
                        Column('pblacore_uid', Integer,
                               ForeignKey('users.pblacore_uid')),
                        Column('driveapi_fileid', String,
                               ForeignKey('files.driveapi_fileid'))
                        )

file_turma_table = Table('file_turma_association', Base.metadata,
                        Column('driveapi_fileid', String,
                               ForeignKey('files.driveapi_fileid')),
                        Column('pblacore_sku_turma', String,
                               ForeignKey('turmas.pblacore_sku_turma'))
                        )
                        
class User(Base):
    __tablename__ = "users"

    pblacore_uid = Column(Integer, primary_key=True, index=True)

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
        return {'pblacore_uid': self.pblacore_uid, 'driveapi_name': self.driveapi_name,
            'driveapi_email': self.driveapi_email, 'is_active': self.is_active}

class Turma(Base):
    __tablename__ = "turmas"

    pblacore_sku_turma = Column(String, primary_key=True, index=True)
    pblacore_disci_turma = Column(String, index=True)
    pblacore_ano_turma = Column(Integer, index=True)
    pblacore_semestre_turma = Column(Integer, index=True)

    users = relationship("User", secondary=user_turma_table,
                         back_populates="turmas")
    
    files = relationship("File", secondary=file_turma_table,
                         back_populates="turmas")


class File(Base):
    __tablename__ = "files"

    driveapi_fileid = Column(String, primary_key=True, index=True)

    driveapi_owner = Column(String, index=True)
    driveapi_lastmod = Column(String, index=True)
    driveapi_lastmod_user = Column(String, index=True)
    
    is_active = Column(Boolean, default=True)

    users = relationship("User", secondary=user_file_table,
                         back_populates="files")

    turmas = relationship("Turma", secondary=file_turma_table,
                         back_populates="files")