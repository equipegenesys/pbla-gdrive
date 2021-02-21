from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dbcomp import dbconfig

#SETUP DB APP
engine_app_db = create_engine(f"postgresql://micros-gdrive:{dbconfig.password}@pbla_db_1/micros-gdrive-app")
SessionLocalA = sessionmaker(autocommit=False, autoflush=False, bind=engine_app_db)
BaseA = declarative_base()
# BaseA.metadata.create_all(bind=engine_app_db)

def get_app_db():
    db = SessionLocalA()
    try:
        yield db
    finally:
        db.close()

#SETUP DB DATA
engine_data_db = create_engine(f"postgresql://micros-gdrive:{dbconfig.password}@pbla_db_1/micros-gdrive-data")
SessionLocalB = sessionmaker(autocommit=False, autoflush=False, bind=engine_data_db)
BaseB = declarative_base()
# BaseB.metadata.create_all(bind=engine_data_db)

def get_data_db():
    db = SessionLocalB()
    try:
        yield db
    finally:
        db.close()