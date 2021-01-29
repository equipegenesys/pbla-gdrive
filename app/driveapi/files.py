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
	if db_user and db_user.driveapi_token:
		creds = db_user.driveapi_token
		service = build('drive', 'v3', credentials=creds)
		if turmas:
			result = {'userTurmaFiles': []}
			for turma in turmas:
				sku_turma = turma.pblacore_sku_turma
				searchQuery = f"fullText contains '{sku_turma}' and mimeType != 'application/vnd.google-apps.folder' and trashed != true"
				file_list = service.files().list(pageSize=100, q=searchQuery, fields="nextPageToken, files(id, name, mimeType, description)").execute()
				result['userTurmaFiles'].append({sku_turma: file_list})
			return result
		return "O usuário não está em nenhuma turma"
	return "O usuário não está integrado ao G Drive"


# @router.get('/api/integ/gdrive/status/user/{user_id}/files/')
# def list_files(user_id: int, db: Session = Depends(access.get_db)):
# 	user = schemas.UserBase
# 	user.pblacore_uid = user_id
# 	db_user = crud.get_user(db, user=user)
# 	turmas = db_user.turmas
# 	if db_user and db_user.driveapi_token:
# 		creds = db_user.driveapi_token
# 		service = build('drive', 'v3', credentials=creds)
# 		if turmas:
# 			result = {'userTurmaFiles': []}
# 			full_list = []
# 			for turma in turmas:
# 				sku_turma = turma.pblacore_sku_turma
# 				searchQuery = f"fullText contains '{sku_turma}' and mimeType != 'application/vnd.google-apps.folder'"
# 				file_list = service.files().list(pageSize=1, q=searchQuery,
# 												 fields="nextPageToken, files(id, name, mimeType, description)").execute()
# 				if 'nextPageToken' in file_list:
# 					nextPageToken = file_list['nextPageToken']
# 					while 'nextPageToken' in file_list:
# 						nextPageToken = file_list['nextPageToken']
# 						full_list.append(file_list['files'])
# 						file_list = service.files().list(pageToken=nextPageToken, pageSize=1, q=searchQuery,
# 														 fields="nextPageToken, files(id, name, mimeType, description)").execute()
# 						if 'nextPageToken' not in file_list:
# 							full_list.append(file_list['files'])
# 					result['userTurmaFiles'].append({sku_turma: full_list})
# 			return result
# 		return "O usuário não está em nenhuma turma"
# 	return "O usuário não está integrado ao G Drive"
