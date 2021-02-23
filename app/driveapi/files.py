from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
import pickle
import io

from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
import google.oauth2.credentials
import googleapiclient.discovery

import os
import sys
import json
from sqlalchemy.orm import Session
from dbcomp import crud, access, schemas, models
from driveapi import mimetypes
from google.auth.exceptions import RefreshError
from . import auth
from datetime import datetime

# from access import BaseB

CLIENT_SECRETS_FILE = '/app/driveapi/credentials.json'
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly',
		  'https://www.googleapis.com/auth/drive.activity.readonly',
		  'https://www.googleapis.com/auth/drive.readonly',
		  'https://www.googleapis.com/auth/userinfo.profile']
API_SERVICE_NAME = 'drive'
API_VERSION = 'v3'

# FILE_FIELDS = 'nextPageToken, files(id, name, starred, description, mimeType, properties, appProperties, version, thumbnailLink, viewedByMe, viewedByMeTime, createdTime, modifiedTime, modifiedByMeTime, sharedWithMeTime, sharingUser, owners, lastModifyingUser, lastModifyingUser, ownedByMe, fileExtension, size, md5Checksum, contentHints)'
FILE_FIELDS = 'nextPageToken, files(id, name, mimeType, fileExtension)'

router = APIRouter()


@router.get('/api/integ/gdrive/status/user/{user_id}/files/')
def list_files(user_id: int, db: Session = Depends(access.get_app_db), db_data: Session = Depends(access.get_data_db)):
	user = schemas.UserBase
	user.pblacore_uid = user_id
	db_user = crud.get_user(db=db, user=user)
	if type(db_user) == dict:
		return db_user
	else:
		turmas = db_user.turmas
		page_token = None
		previous_file = None
		loop_index = 1
		msg = []
		if db_user and db_user.driveapi_token:
			creds = db_user.driveapi_token
			service = build('drive', 'v3', credentials=creds)
			if turmas:
				result = {'user': {'pblcore_uid': user_id, 'turmas': []}}
				for turma in turmas:
					full_list = []
					sku_turma = turma.pblacore_sku_turma
					print("                                    sku_turma",sku_turma)
					searchQuery = f"fullText contains '{sku_turma}' and mimeType != 'application/vnd.google-apps.folder' and trashed != true"

					while True:
						response = service.files().list(pageSize=100, q=searchQuery,
														spaces='drive',
														fields=FILE_FIELDS, pageToken=page_token).execute()
						for file in response.get('files', []):
							file_schema = schemas.File
							if loop_index is 1:
								full_list.append(file)

								file_schema.driveapi_fileid = file['id']
								file_schema.is_active = True
								if crud.get_files(db=db, file=file_schema) == None:
									crud.create_file(
										db, file_schema, db_user, turma)
								else:
									crud.update_file(
										db=db, file_to_update=file['id'], user=user_id, turma=turma.pblacore_sku_turma)
								msg.append(
									{"msg": f"Arquivo "+"'"+file['name']+"'"+" já existe na base de dados"})

							else:
								last_item_index = len(full_list) - 1
								if file['id'] != full_list[last_item_index]['id']:
									full_list.append(file)

									file_schema.driveapi_fileid = file['id']
									file_schema.is_active = True
									if crud.get_files(db=db, file=file_schema) == None:
										crud.create_file(
											db, file_schema, db_user, turma)
									else:
										crud.update_file(
											db=db, file_to_update=file['id'], user=user_id, turma=turma.pblacore_sku_turma)
									msg.append(
										{"msg": f"Arquivo "+"'"+file['name']+"'"+" já existe na base de dados"})

							loop_index = loop_index + 1
						page_token = response.get('nextPageToken', None)
						if page_token is None:
							break
					loop_index = 1
					{'user': {'pblcore_uid': user_id, 'turmas': []}}

					result['user']['turmas'].append(
						{'sku_turma': sku_turma, 'files': full_list})
				return result
			return {"msg": "O usuário não está em nenhuma turma"}
		return {"msg": "O usuário não está integrado ao G Drive"}


# @router.get('/api/integ/gdrive/file/metadata')
def get_file_metadata(user_id: int, resource_id: str, db_app: Session = Depends(access.get_app_db), db_data: Session = Depends(access.get_data_db)):
	user_status = auth.check_integ_status(user_id=user_id, db=db_app)
	if user_status['integrado'] == True:
		user = schemas.UserBase
		user.pblacore_uid = user_id
		db_user = crud.get_user(user=user, db=db_app)
		creds = db_user.driveapi_token
		service = build('drive', 'v3', credentials=creds)
		try:
			response = service.files().get(fileId=resource_id, fields='*').execute()
			return response
		except HttpError as err:
			print(err)
			if err.resp.status in [404]:
				return {"msg": f"Arquivo com ID {resource_id} não encontrado"}
	else:
		return user_status


# @router.get('/api/integ/gdrive/file/activity')
def get_file_activity(user_id: int, resource_id: str, db_app: Session = Depends(access.get_app_db), db_data: Session = Depends(access.get_data_db)):
	user_status = auth.check_integ_status(user_id=user_id, db=db_app)
	if user_status['integrado'] == True:
		user = schemas.UserBase
		user.pblacore_uid = user_id
		db_user = crud.get_user(user=user, db=db_app)
		creds = db_user.driveapi_token
		service = build('driveactivity', 'v2', credentials=creds)
		page_token = None
		full_list = []
		loop_index = 1

		try:
			while True:
				activityResults = service.activity().query(
					body={'pageToken': page_token, 'pageSize': 100, "itemName": f"items/{resource_id}"}).execute()
				response = activityResults.get('activities', [])
				page_token = activityResults.get('nextPageToken')
				if page_token is None and loop_index == 1:
					return response
				else:
					for activity in response:
						full_list.append(activity)
					if page_token is None:
						return full_list

				loop_index = loop_index + 1

		except HttpError as err:
			print(err)
			if err.resp.status in [404]:
				return {"msg": f"Arquivo com ID {resource_id} não encontrado"}
	else:
		return user_status


# @router.get('/api/integ/gdrive/file/download')
def download_file(user_id: int, resource_id: str, db_app: Session = Depends(access.get_app_db), db_data: Session = Depends(access.get_data_db)):
	user_status = auth.check_integ_status(user_id=user_id, db=db_app)
	if user_status['integrado'] == True:
		user = schemas.UserBase
		user.pblacore_uid = user_id
		db_user = crud.get_user(user=user, db=db_app)
		creds = db_user.driveapi_token
		service = build('drive', 'v3', credentials=creds)
		try:
			metadata = get_file_metadata(
				user_id=user_id, resource_id=resource_id, db_app=db_app, db_data=db_data)
			mimetype = metadata['mimeType']

			if mimetype != "application/vnd.google-apps.form":

				switch = mimetypes.mimetype_mapper(mimetype)
				if switch:
					new_mimetype = switch()
					request = service.files().export_media(
						fileId=resource_id, mimeType=new_mimetype)
				else:
					request = service.files().get_media(fileId=resource_id)

				fh = io.BytesIO()
				downloader = MediaIoBaseDownload(fh, request)

				done = False
				while done is False:
					status, done = downloader.next_chunk()
					# print(
					#     f"Download do arquivo {metadata['name']}, de tipo {metadata['mimeType']} e id {metadata['id']}: {str(int(status.progress() * 100))}%")
				return fh
			return None

		except HttpError as err:
			print(err)
			if err.resp.status in [404]:
				return {"msg": f"Arquivo com ID {resource_id} não encontrado"}
	else:
		return user_status


@router.post('/api/integ/gdrive/user/update/records')
def update_user_file_records(user_id: int, db_app: Session = Depends(access.get_app_db), db_data: Session = Depends(access.get_data_db)):
	file_list = list_files(user_id=user_id, db=db_app)
	for turma in file_list['user']['turmas']:
		# print(turma)
		for file in turma['files']:
			add_file_record(
				user_id=user_id, resource_id=file['id'], db_app=db_app, db_data=db_data)
	return {'msg': 'records added for every file associated with user'}


# esta função reune as 3 categorias de dados e chama create_file_record para finalmente criar o registro
@router.post('/api/integ/gdrive/file/add/record')
def add_file_record(user_id: int, resource_id: str, db_app: Session = Depends(access.get_app_db), db_data: Session = Depends(access.get_data_db)):
	metadata = get_file_metadata(
		user_id=user_id, resource_id=resource_id, db_app=db_app, db_data=db_data)
	activity = get_file_activity(
		user_id=user_id, resource_id=resource_id, db_app=db_app, db_data=db_data)
	download = download_file(
		user_id=user_id, resource_id=resource_id, db_app=db_app, db_data=db_data)

	file_schema = schemas.FileBase
	file_schema.driveapi_fileid = resource_id
	db_file = crud.get_files(db=db_app, file=file_schema)
	models.tableCreator(tablename=db_file.local_fileid)

	file_record = schemas.FileRecords
	file_record.source_uid = user_id
	file_record.file_fields = metadata
	file_record.activity_fields = activity
	if download != None:
		file_record.file_revision = download

	create_file_record(db_app=db_app, db_data=db_data, file_record=file_record)
	return "metadata e activity foram adicionadas ao banco de dados do arquivo"


def create_file_record(file_record: schemas.FileRecords, db_app: Session = Depends(access.get_app_db), db_data: Session = Depends(access.get_data_db)):
	file_schema = schemas.FileBase
	file_schema.driveapi_fileid = file_record.file_fields['id']
	db_file = crud.get_files(db=db_app, file=file_schema)

	table_name = db_file.local_fileid

	file_fields_json = json.dumps(file_record.file_fields)
	file_record.file_fields = file_fields_json

	activity_fields_json = json.dumps(file_record.activity_fields)
	file_record.activity_fields = activity_fields_json

	now = datetime.now()
	file_record.record_date = now = datetime.now()
	# file_record.record_date = now.strftime("%d/%m/%Y, %H:%M:%S")

	crud.create_file_record(
		db=db_data, table_name=table_name, file_record=file_record)


@router.get('/api/integ/gdrive/file/latest')
def retrive_latest_revision(user_id: int, resource_id: str, db_app: Session = Depends(access.get_app_db),
							db_data: Session = Depends(access.get_data_db)):
	file_schema = schemas.FileBase
	file_schema.driveapi_fileid = resource_id
	db_file = crud.get_files(db=db_app, file=file_schema)
	# file_schema.local_fileid = db_file.local_fileid
	latest_file_record = crud.retrive_latest_record(
		db=db_data, table_name=db_file.local_fileid)
	db_record = latest_file_record.fetchone()
	file_revision_field = db_record[5]
	fh = open("myfile", "wb")
	fh.write(file_revision_field)
	fh.close
