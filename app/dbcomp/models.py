from __future__ import annotations
from sqlalchemy import Table, Boolean, Column, ForeignKey, Integer, String, LargeBinary, PickleType
from sqlalchemy.orm import relationship
from .access import Base


user_tag_table = Table('user_tag_association', Base.metadata,
                       Column('pblacore_uid', Integer,
                              ForeignKey('users.pblacore_uid')),
                       Column('pblacore_tag', String,
                              ForeignKey('tags.pblacore_tag'))
                       )

user_file_table = Table('user_file_association', Base.metadata,
                        Column('pblacore_uid', Integer,
                               ForeignKey('users.pblacore_uid')),
                        Column('local_fileid', Integer,
                               ForeignKey('files.local_fileid'))
                        )


class User(Base):
    __tablename__ = "users"

    pblacore_uid = Column(Integer, primary_key=True, index=True)
    # pblacore_name = Column(String, index=True)

    driveapi_account_id = Column(String, unique=True, index=True)
    driveapi_name = Column(String, index=True)
    driveapi_email = Column(String, unique=True, index=True)
    driveapi_token = Column(PickleType)

    is_active = Column(Boolean, default=True)

    tags = relationship("Tag", secondary=user_tag_table,
                        back_populates="users")

    files = relationship("File", secondary=user_file_table,
                         back_populates="users")

    def basicData(self):
        return {'pblacore_uid': self.pblacore_uid, 'driveapi_name': self.driveapi_name,
            'driveapi_email': self.driveapi_email, 'is_active': self.is_active}

class Tag(Base):
    __tablename__ = "tags"

    pblacore_tag = Column(String, primary_key=True, index=True)
    pblacore_disci = Column(String, index=True)
    pblacore_ano = Column(Integer, index=True)
    pblacore_semestre = Column(Integer, index=True)

    users = relationship("User", secondary=user_tag_table,
                         back_populates="tags")


class File(Base):
    __tablename__ = "files"

    local_fileid = Column(Integer, primary_key=True, index=True)

    # pblacore_tag = relationship("Tag", back_populates="pblacore_tag")
    driveapi_file_id = Column(String, unique=True, index=True)
    driveapi_owner = Column(String, index=True)
    driveapi_lastmod = Column(String, index=True)
    driveapi_lastmod_user = Column(String, index=True)
    is_active = Column(Boolean, default=True)

    users = relationship("User", secondary=user_file_table,
                         back_populates="files")

# User.update_forward_refs()
