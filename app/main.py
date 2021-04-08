from typing import Optional
from fastapi import FastAPI
from fastapi import APIRouter
# import os

from typing import List
from sqlalchemy.orm import Session

from driveapi import auth, files
from dbcomp import crud, models, schemas, access

# from .access import SessionLocal, engine

# access.BaseA.metadata.create_all(bind=access.engine)

app = FastAPI(openapi_url="/api/integ/gdrive/openapi.json",
              docs_url="/api/integ/gdrive/docs", redoc_url=None,
              title="PBL Analytics - G Drive Integation API",
              description="Use este API para integrar contas de estudante e monitorar documentos tagueados.",
              version = "alpha 0.1")

app.include_router(auth.router)

app.include_router(files.router)

# app.include_router(gateway.router)

# @app.get("/api/integ/gdrive")
# def read_root():
#     return {"Hello": "Galera"}

# @app.get("/api/integ/gdrive/items/{item_id}")
# def read_item(item_id: int, q: Optional[str] = None):
#     return {"item_id": item_id, "q": q}
