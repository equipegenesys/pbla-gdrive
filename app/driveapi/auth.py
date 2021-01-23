from fastapi import APIRouter
from fastapi.responses import RedirectResponse
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import google.oauth2.credentials, googleapiclient.discovery, os
import json

CLIENT_SECRETS_FILE = '/app/driveapi/credentials.json'
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly', 'https://www.googleapis.com/auth/drive.activity.readonly']
API_SERVICE_NAME = 'drive'
API_VERSION = 'v3'

router = APIRouter()

@router.get('/api/integ/gdrive/status/user/{user_id}')
def check_integ_status(user_id: int):
	userTokenPath = '/app/driveapi/tokens/' + str(user_id)
	if os.path.exists(userTokenPath+'/token.pickle'):
		with open(userTokenPath+'/token.pickle', 'rb') as token:
			creds = pickle.load(token)
		service = build('drive', 'v3', credentials=creds)
		results = service.about().get(fields="user(emailAddress)").execute()
		mail = str(results.get('user').get('emailAddress'))
		if results:
			return f"O usuário com ID {user_id} está integrado à conta do Google Drive do usuário com e-mail {mail}."
		else:
			return f"O usuário com ID {user_id} não está integrado a nenhuma conta do Google Drive."
	return f"O usuário com ID {user_id} não está integrado a nenhuma conta do Google Drive."

@router.get('/api/integ/gdrive/new/user/{user_id}')
def new_integ(user_id: int):
	userTokenPath = '/app/driveapi/tokens/' + str(user_id)

	if not os.path.exists(userTokenPath):
		os.mkdir(userTokenPath)
	creds = None
	if os.path.exists(userTokenPath + '/token.pickle'):
		with open(userTokenPath + '/token.pickle', 'rb') as token:
			creds = pickle.load(token)
	if not (creds and creds.valid):
		if creds and creds.expired and creds.refresh_token:
			creds.refresh(Request())
		else:
			flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES)
			flow.redirect_uri = 'https://analytics.pbl.tec.br/api/integ/gdrive/new/user/oauthlisten/'
			authorization_url, state = flow.authorization_url(prompt='consent', access_type='offline', include_granted_scopes='true', state=user_id)
			return RedirectResponse(authorization_url)
	else:
		return [{'credentials already present': 'true'}]

@router.get('/api/integ/gdrive/new/user/oauthlisten/')
def oauthlisten(state: str, code: str, scope: str):
	userTokenPath = '/app/driveapi/tokens/' + str(state)

	flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
	flow.redirect_uri = 'https://analytics.pbl.tec.br/api/integ/gdrive/new/user/oauthlisten/'
	flow.fetch_token(code=code)

	creds = flow.credentials

	with open(userTokenPath+'/token.pickle', 'wb') as token:
		pickle.dump(creds, token)

	return RedirectResponse('https://analytics.pbl.tec.br/api/integ/gdrive/status/user/'+state[0])