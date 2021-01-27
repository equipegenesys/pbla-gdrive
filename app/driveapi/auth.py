from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import google.oauth2.credentials
import googleapiclient.discovery
import os
import json
from sqlalchemy.orm import Session
from dbcomp import crud, access

CLIENT_SECRETS_FILE = '/app/driveapi/credentials.json'
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly',
		  'https://www.googleapis.com/auth/drive.activity.readonly']
API_SERVICE_NAME = 'drive'
API_VERSION = 'v3'

router = APIRouter()


@router.get('/api/integ/gdrive/status/user/{user_id}')
def check_integ_status(user_id: int, db: Session = Depends(access.get_db)):
	db_user = crud.get_user(db, user_id=user_id)

	if db_user:
		if db_user.driveapi_token != None:
			creds = db_user.driveapi_token
			service = build('drive', 'v3', credentials=creds)
			results = service.about().get(fields="user(emailAddress, displayName)").execute()
			mail = str(results.get('user').get('emailAddress'))
			name = str(results.get('user').get('displayName'))
			basicUserData = db_user.basicData()
			if basicUserData["driveapi_name"] == name and basicUserData["driveapi_email"] == mail:
				db_user.is_active=True
				return db_user.basicData()
		else:
			return {"user_id": user_id, "integrado": False}
	return {"msg": "Usuário ainda não cadatrado"}


@router.get('/api/integ/gdrive/new/user/{user_id}')
def new_integ(user_id: int, db: Session = Depends(access.get_db)):
	db_user = crud.get_user(db, user_id=user_id)
	if db_user == None:
		flow = Flow.from_client_secrets_file(
			CLIENT_SECRETS_FILE, scopes=SCOPES)
		flow.redirect_uri = 'https://analytics.pbl.tec.br/api/integ/gdrive/new/user/oauthlisten/'
		authorization_url, state = flow.authorization_url(
			prompt='consent', access_type='offline', include_granted_scopes='true', state=user_id)
		return RedirectResponse(authorization_url)
	else:
		return "Este usuário ja existe"


@router.get('/api/integ/gdrive/new/user/oauthlisten/')
def oauthlisten(state: str, code: str, scope: str, db: Session = Depends(access.get_db)):
	flow = Flow.from_client_secrets_file(
		CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
	flow.redirect_uri = 'https://analytics.pbl.tec.br/api/integ/gdrive/new/user/oauthlisten/'
	flow.fetch_token(code=code)
	creds = flow.credentials

	service = build('drive', 'v3', credentials=creds)
	results = service.about().get(fields="user(emailAddress, displayName)").execute()
	mail = str(results.get('user').get('emailAddress'))
	name = str(results.get('user').get('displayName'))

	crud.create_user(db=db, user_id=state, creds=creds, name=name, mail=mail)

	return RedirectResponse('https://analytics.pbl.tec.br/api/integ/gdrive/status/user/'+state[0])
