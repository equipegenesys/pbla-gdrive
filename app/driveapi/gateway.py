from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import google.oauth2.credentials
import googleapiclient.discovery
import os
import json
from sqlalchemy.orm import Session
from dbcomp import crud, access, schemas
from typing import (
	Deque, Dict, FrozenSet, List, Optional, Sequence, Set, Tuple, Union
)

CLIENT_SECRETS_FILE = '/app/driveapi/credentials.json'
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly',
		  'https://www.googleapis.com/auth/drive.activity.readonly']
API_SERVICE_NAME = 'drive'
API_VERSION = 'v3'

router = APIRouter()


@router.post('/api/integ/gdrive/add/turma/')
def new_turma(turma: schemas.TurmaCreate, db: Session = Depends(access.get_db)):
	if crud.get_turma(db, turma=turma.pblacore_sku_turma) != None:
		return "Essa turma já existe"
	return crud.create_turma(db=db, turma_to_create=turma)

@router.post('/api/integ/gdrive/add/user/turma')
def add_user_turma(turma: schemas.TurmaAddUser, db: Session = Depends(access.get_db)):
	if turma.users != None:
		if crud.get_turma(db, turma=turma.pblacore_sku_turma) != None:
			return crud.add_user_turma(db, turma=turma)
			# return "Essa turma já existe"
		return "Turma ainda não foi criada"
	return "Http POST veio sem uma lista de usuários"