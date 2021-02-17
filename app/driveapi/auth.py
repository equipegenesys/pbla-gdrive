import pickle
import os
import json

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
import google.oauth2.credentials
import googleapiclient.discovery

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from dbcomp import crud, access, schemas
from driveapi import files, auth

CLIENT_SECRETS_FILE = '/app/driveapi/credentials.json'
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly',
		  'https://www.googleapis.com/auth/drive.activity.readonly']
API_SERVICE_NAME = 'drive'
API_VERSION = 'v3'

router = APIRouter()


@router.get('/api/integ/gdrive/status/user/{user_id}')
def check_integ_status(user_id: int, db: Session = Depends(access.get_app_db)):
	user = schemas.UserBase
	user.pblacore_uid = user_id
	db_user = crud.get_user(db=db, user=user)

	if db_user:
		if type(db_user) == dict:
			return db_user
		elif db_user.driveapi_token != None:
			creds = db_user.driveapi_token
			service = build('drive', 'v3', credentials=creds)
			try:
				results = service.about().get(fields="user(emailAddress, displayName)").execute()
			except RefreshError as re:
				# await renew_integ(user_id = user_id)
				return {"user_id": user_id, "cadastrado": True, "integrado": False, "info": "O token não pode ser atualizado ou foi revogado"}
			mail = str(results.get('user').get('emailAddress'))
			name = str(results.get('user').get('displayName'))
			basicUserData = db_user.basicData()
			if basicUserData["driveapi_name"] == name and basicUserData["driveapi_email"] == mail:
				db_user.is_active = True
				return {"user_id": user_id, "cadastrado": True, "integrado": db_user.is_active}
				# return db_user.basicData()
			else:
				return {"user_id": user_id, "cadastrado": True, "integrado": False, "info¨": "Há um token de acesso válido, mas o nome e e-mail do usuário do G drive não confere com usuário do PBL Analytics"}
		else:
			return {"user_id": user_id, "cadastrado": True, "integrado": False, "info": "Não há um token de acesso"}
	return {"user_id": user_id, "cadastrado": False, "integrado": False}


@router.get('/api/integ/gdrive/new/user/{user_id}')
def new_integ(user_id: int, db: Session = Depends(access.get_app_db)):
	integ_status = check_integ_status(db=db, user_id=user_id)
	if integ_status['integrado'] == False:
		flow = Flow.from_client_secrets_file(
			CLIENT_SECRETS_FILE, scopes=SCOPES)
		flow.redirect_uri = 'https://analytics.pbl.tec.br/api/integ/gdrive/oauthlisten/'
		authorization_url, state = flow.authorization_url(
			prompt='consent', access_type='offline', include_granted_scopes='true', state=user_id)
		print(authorization_url)
		# return RedirectResponse(authorization_url)
		return authorization_url
	else:
		return "Este usuário ja existe"


@router.get('/api/integ/gdrive/renew/user/{user_id}')
def renew_integ(user_id: int, db: Session = Depends(access.get_app_db)):
	flow = Flow.from_client_secrets_file(
		CLIENT_SECRETS_FILE, scopes=SCOPES)
	flow.redirect_uri = 'https://analytics.pbl.tec.br/api/integ/gdrive/oauthlisten/'
	authorization_url, state = flow.authorization_url(
		prompt='consent', access_type='offline', include_granted_scopes='true', state=user_id)
	print(authorization_url)
	return authorization_url
	# return RedirectResponse(authorization_url)
	# return {"msg": f"Token para o usuário com ID {user_id} não renovado, mas tá precisando!"}


@router.get('/api/integ/gdrive/oauthlisten/', include_in_schema=False)
def oauthlisten(state: str, code: str, scope: str, db: Session = Depends(access.get_app_db)):
	flow = Flow.from_client_secrets_file(
		CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
	flow.redirect_uri = 'https://analytics.pbl.tec.br/api/integ/gdrive/oauthlisten/'
	flow.fetch_token(code=code)
	creds = flow.credentials

	service = build('drive', 'v3', credentials=creds)
	results = service.about().get(fields="user(emailAddress, displayName)").execute()
	mail = str(results.get('user').get('emailAddress'))
	name = str(results.get('user').get('displayName'))

	user = schemas.UserCreate
	user.pblacore_uid = state
	user.pblacore_token = creds
	user.driveapi_name = name
	user.driveapi_email = mail

	userBase = schemas.UserBase
	userBase.pblacore_uid = state

	# return RedirectResponse('https://analytics.pbl.tec.br/api/integ/gdrive/status/user/'+state[0])
	if crud.get_user(db=db, user=user):
		# statement = text("""UPDATE users SET driveapi_token = '0' VALUES(:id, :title, :primary_author)""")
		# print(user.pblacore_token)
		crud.update_token(db=db, user_to_update=user)
		integ_status = auth.check_integ_status(db=db, user_id=user.pblacore_uid)
		if integ_status['integrado'] == True:
			# listar arquivos (o que já atualiza a tabela de arquivos e cria tabelas individuais para cada um)
			files.list_files(db=db, user_id=user.pblacore_uid)
		return integ_status
	else:
		crud.create_user_fromgdrive(db=db, user_to_create=user)
		integ_status = auth.check_integ_status(db=db, user_id=user.pblacore_uid)
		if integ_status['integrado'] == True:
			# listar arquivos (o que já atualiza a tabela de arquivos e cria tabelas individuais para cada um)
			files.list_files(db=db, user_id=user.pblacore_uid)
		return integ_status