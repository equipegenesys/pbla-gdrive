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
from dbcomp import crud, access, schemas

CLIENT_SECRETS_FILE = '/app/driveapi/credentials.json'
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly',
		  'https://www.googleapis.com/auth/drive.activity.readonly']
API_SERVICE_NAME = 'drive'
API_VERSION = 'v3'

router = APIRouter()

@router.get('/api/integ/gdrive/status/user/{user_id}/files/')
def list_files(user_id: int, db: Session = Depends(access.get_db)):
	user = schemas.UserBase
	user.pblacore_uid = user_id
	db_user = crud.get_user(db, user=user)
	turmas = db_user.turmas
	page_token = None
	previous_file = None
	loop_index = 1
	if db_user and db_user.driveapi_token:
		creds = db_user.driveapi_token
		service = build('drive', 'v3', credentials=creds)
		if turmas:
			result = {'userTurmaFiles': []}
			for turma in turmas:
				full_list = []
				sku_turma = turma.pblacore_sku_turma
				searchQuery = f"fullText contains '{sku_turma}' and mimeType != 'application/vnd.google-apps.folder' and trashed != true"

				while True:
					response = service.files().list(pageSize=10, q=searchQuery,
														spaces='drive',
														fields='nextPageToken, files(id, name)', pageToken=page_token).execute()
					for file in response.get('files', []):
						if loop_index is 1:
							full_list.append(file)
						else:
							last_item_index = len(full_list) -1
							if file['id'] != full_list[last_item_index]['id']:
								full_list.append(file)
						loop_index = loop_index + 1				
					page_token = response.get('nextPageToken', None)		
					if page_token is None:
						break
				loop_index = 1
	
				result['userTurmaFiles'].append({sku_turma: full_list})
			return result
		return {"msg": "O usuário não está em nenhuma turma"}
	return {"msg": "O usuário não está integrado ao G Drive"}