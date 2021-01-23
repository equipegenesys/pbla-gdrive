from typing import Optional
from fastapi import FastAPI
from fastapi import APIRouter
# import os
from driveapi import auth

app = FastAPI(openapi_url="/api/integ/gdrive/openapi.json", docs_url="/api/integ/gdrive/docs", redoc_url=None)

app.include_router(auth.router)

# @app.get("/api/integ/gdrive")
# def read_root():
#     return {"Hello": "Galera"}

# @app.get("/api/integ/gdrive/items/{item_id}")
# def read_item(item_id: int, q: Optional[str] = None):
#     return {"item_id": item_id, "q": q}