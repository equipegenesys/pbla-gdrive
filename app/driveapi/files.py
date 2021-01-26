from fastapi import APIRouter
from fastapi.responses import RedirectResponse
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import google.oauth2.credentials, googleapiclient.discovery, os
import json
from dbcomp import access

CLIENT_SECRETS_FILE = '/app/driveapi/credentials.json'
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly', 'https://www.googleapis.com/auth/drive.activity.readonly']
API_SERVICE_NAME = 'drive'
API_VERSION = 'v3'

router = APIRouter()

@router.get('/api/integ/gdrive/status/user/{user_id}/files/')
def list_files(user_id: int, tag: str):
	userTokenPath = '/app/driveapi/tokens/' + str(user_id)
	searchQuery = f"fullText contains '{tag}' and mimeType != 'application/vnd.google-apps.folder'" 
	
	if os.path.exists(userTokenPath+'/token.pickle'):
		with open(userTokenPath+'/token.pickle', 'rb') as token:
			creds = pickle.load(token)
		service = build('drive', 'v3', credentials=creds)
		results = service.files().list(pageSize=100, q=searchQuery, fields="*").execute()
		with open(userTokenPath+'/output', 'w') as output:
			jsonObject = json.dumps(results, indent = 4, ensure_ascii=False)
			output.write(jsonObject)
		items = results.get('files', [])
		if not items:
			return 'No files found.'
		else:
			fileList = []
			for item in items:
				fileList.append({'name': item['name'], 'id': item['id'], 'mimeType': item['mimeType']})

			# jsonObject = json.dumps(fileList, indent = 4, ensure_ascii=False)

			return fileList