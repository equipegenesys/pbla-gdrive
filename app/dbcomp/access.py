# this module sets up database access

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dbcomp import dbconfig

#SETUP DB APP
engine_app_db = create_engine(f"postgresql://micros-gdrive:{dbconfig.password}@pbla_db_1/db-micros-gdrive")
SessionLocalA = sessionmaker(autocommit=False, autoflush=False, bind=engine_app_db)
BaseA = declarative_base()
# BaseA.metadata.create_all(bind=engine_app_db)

def get_app_db():
    db = SessionLocalA()
    try:
        yield db
    finally:
        db.close()