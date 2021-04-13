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
from . import auth, gateway
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

BLOCKED_MIMETYPES = ["application/vnd.google-apps.form",
					 "application/vnd.google-apps.shortcut"]

router = APIRouter()

# creates and endpoint for receiving file listing requests
@router.get('/api/integ/gdrive/status/user/{user_id}/files/')
def list_files(user_id: int, db: Session = Depends(access.get_app_db)):
	# get user status
	user_status = auth.check_integ_status(user_id=user_id, db=db)
	# create a user schema object, load id in it and get DB user record
	user = schemas.UserBase
	user.pbla_uid = user_id
	db_user = crud.get_user(db=db, user=user)
	# if 'crud.get_user' returns a dict, than it's an error. so...
	if type(db_user) == dict:
		return db_user  # just return that error
	elif user_status['integrado'] == True:
		# get list of turmas for a user from pbla_core microsservice
		turmas = gateway.get_turmas_from_core(user_id)
		# print(type(turmas))
		# create som variables that we will use later
		page_token = None
		previous_file = None
		loop_index = 1
		# get credentials and build google service
		creds = db_user.driveapi_token
		service = build('drive', 'v3', credentials=creds)
		# if user is in at least one turma...
		if turmas:
			# create a dict with a empty list of turmas
			result = {'user': {'pblcore_uid': user_id, 'turmas': []}}
			# loop through each turma
			for turma in turmas:
				# create a empty list to be populated with files that a user have with that turma tag in google drive
				full_list = []
				# load tag turma
				tag_turma = turma
				tag_equipe = turmas[tag_turma]
				# prepare a string to be the search query used in drive API
				searchQuery = f"fullText contains '{tag_turma}' and mimeType != 'application/vnd.google-apps.folder' and trashed != true"
				# initiate a loop to be stopped when all the result pages end
				while True:
					# create service
					response = service.files().list(pageSize=100, q=searchQuery,
													includeItemsFromAllDrives='true',
													corpora='allDrives',
													spaces='drive',
													supportsAllDrives='true',
													fields=FILE_FIELDS, pageToken=page_token).execute()
					# for each file in file list...
					for file in response.get('files', []):
						# create an object of file schema
						# file_schema = schemas.File
						# if we are in first loop...
						if loop_index is 1:
							# add file to list
							full_list.append(file)							
						# on the subsequent loop indexes..
						else:
							last_item_index = len(full_list) - 1
							# to avoid duplicates, only append new file if the present file in the loop is different from the latest file in full_list.
							if file['id'] != full_list[last_item_index]['id']:
								# then do the same as above
								full_list.append(file)
						# extra manually add to the loop index
						loop_index = loop_index + 1
					# get next page token. if it is none, break the loop
					page_token = response.get('nextPageToken', None)
					if page_token is None:
						break
				# reset loop index
				loop_index = 1
				# append all the data to the final result
				result['user']['turmas'].append(
					{'tag_turma': tag_turma, 'tag_equipe': tag_equipe, 'files': full_list})	
			return result
		return {"user_in_turmas": False}
	return {"integrado": False}


# get file metadata from google drive API
def get_file_metadata(user_id: int, resource_id: str, db_app: Session = Depends(access.get_app_db)):
	user_status = auth.check_integ_status(
		user_id=user_id, db=db_app)  # allways check status
	if user_status['integrado'] == True:  # if authorization is valid
		user = schemas.UserBase  # create user object
		user.pbla_uid = user_id  # load id in it
		# get db user (and all its data)
		db_user = crud.get_user(user=user, db=db_app)
		creds = db_user.driveapi_token  # load credentials from db
		# buid google service
		service = build('drive', 'v3', credentials=creds)
		try:  # we need to handle connection problems with google
			response = service.files().get(
				fileId=resource_id, fields='*',
				supportsAllDrives='true').execute()  # gets file metadata
			return response  # return metadata
		except HttpError as err:
			print(err)
			if err.resp.status in [404]:
				return {"msg": f"Arquivo com ID {resource_id} não encontrado"}
	else:
		return user_status


# get file activity function definition, used by some of the endpoints.
# @router.get('/api/integ/gdrive/file/activity')
def get_file_activity(user_id: int, resource_id: str, db_app: Session = Depends(access.get_app_db), **kwargs):
	# initialize a variable with a possibly passed kwarg named 'db_latest_activity' and default value of None, if none is passed:
	db_latest_activity = kwargs.get('db_latest_activity', None)
	user_status = auth.check_integ_status(user_id=user_id, db=db_app)
	if user_status['integrado'] == True:
		# create user object, load provided file_id, get DB user and its credentials, build google API service:
		user = schemas.UserBase
		user.pbla_uid = user_id
		db_user = crud.get_user(user=user, db=db_app)
		creds = db_user.driveapi_token
		service = build('driveactivity', 'v2', credentials=creds)
		# start an empty page token variable and a loop index:
		page_token = None
		full_list = []
		loop_index = 1
		try:  # we need to handle connection problems with google
			while True:  # this means it will paginate until we break the loop with a return statement
				if db_latest_activity == None:  # if no db_latest_activity was passed
					# define a service query for a specific file's activity in google drive
					activityResults = service.activity().query(
						body={'pageToken': page_token, 'pageSize': 100, "itemName": f"items/{resource_id}"}).execute()
				elif db_latest_activity:  # if db_latest_activity was passed...
					# we define a service query that includes only events after db_latest_activity time record
					activityResults = service.activity().query(
						body={'pageToken': page_token, 'pageSize': 100, 'filter': f'time > \"{db_latest_activity}\"', "itemName": f"items/{resource_id}"}).execute()
				# get results from Drive API based on the above on above conditions
				response = activityResults.get('activities', [])
				# get next page token, which may be None
				page_token = activityResults.get('nextPageToken')
				# if page_token is None, it means there are no additional results, so just return what we have
				# the index is needed because if page token is none and we are not in the first loop...
				# we need to return the 'full_list' of appended activity results
				if page_token is None and loop_index == 1:
					return response
				else:  # in every other case, loop trough all the activity records in the API response e append it to the full_list of activities
					for activity in response:
						full_list.append(activity)
					if page_token is None:  # return full_list of activity records only when there is no next page token
						return full_list

				loop_index = loop_index + 1
		# error handling
		except HttpError as err:
			print(err)
			if err.resp.status in [404]:
				return {"msg": f"Arquivo com ID {resource_id} não encontrado"}
	else:  # if user_status is different from True
		return user_status


# download file function definition, used by some of the endpoints.
# @router.get('/api/integ/gdrive/file/download')
def download_file(user_id: int, resource_id: str, db_app: Session = Depends(access.get_app_db)):
	user_status = auth.check_integ_status(user_id=user_id, db=db_app)
	if user_status['integrado'] == True:
		# create user object, load provided file_id, get DB user and its credentials, build google API service:
		user = schemas.UserBase
		user.pbla_uid = user_id
		db_user = crud.get_user(user=user, db=db_app)
		creds = db_user.driveapi_token
		service = build('drive', 'v3', credentials=creds)
		try:
			# get metadata from a file selected by passing the received 'resource_id'
			metadata = get_file_metadata(
				user_id=user_id, resource_id=resource_id, db_app=db_app)
			# get its mimeType. We need this to treat different mimeType properly
			mimetype = metadata['mimeType']
			# some mimeTypes are not of a binary type, that can be contained on a blob, so we can't download them
			if mimetype not in BLOCKED_MIMETYPES:
				# we call 'mimetype_mapper', which is define on an imported mimetypes module.
				# mimetype_mapper maps native Google Drive formats like Google Slides and Google Drawings to open formats like pptx and png
				switch = mimetypes.mimetype_mapper(mimetype)
				if switch:  # if there is a switch, it means the mimetype was mapped to a open one
					# we get the mapped mimetype and ask google API to send us a converted version of the file converted to the open format
					new_mimetype = switch()
					request = service.files().export_media(
						fileId=resource_id, mimeType=new_mimetype)
				else:  # if there is no switch, it means there is no mimetype to be mapped.
					request = service.files().get_media(fileId=resource_id)  # simply get the media

				binary_file = io.BytesIO()  # create empty BytesIO objetc
				# download the request result into binary, in memory file
				downloader = MediaIoBaseDownload(binary_file, request)
				# while there are chunks of the file available, keep downloading it, and then return the binary file
				done = False
				while done is False:
					status, done = downloader.next_chunk()
					# print(
					#     f"Download do arquivo {metadata['name']}, de tipo {metadata['mimeType']} e id {metadata['id']}: {str(int(status.progress() * 100))}%")
				return binary_file
			return None

		except HttpError as err:
			print(err)
			if err.resp.status in [404]:
				return {"msg": f"Arquivo com ID {resource_id} não encontrado"}
	else:
		return user_status


# this endpoint receives a simple a empty request on this endpoint and simply updates all the file records for all users
@router.post('/api/integ/gdrive/allusers/update/records')
def add_users_files_records(db_app: Session = Depends(access.get_app_db)):
	users = db_app.query(models.User).all()  # get all uses from db
	
	# iterate through users, check integration, if ok, get a list of files per turma (school class) from the current user...
	# iterate through files and 'add_file_records' to each one
	for user in users:
		# print(user)
		user_status = auth.check_integ_status(
			user_id=user.pbla_uid, db=db_app)
		if user_status['integrado'] == True:
			file_list = list_files(user_id=user.pbla_uid, db=db_app)
			for turma in file_list['user']['turmas']:
				for file in turma['files']:
					# print("                    all users",turma['tag_equipe'])					
					add_file_record(
						user_id=user.pbla_uid, resource_id=file['id'], db_app=db_app, tag_turma=turma['tag_turma'], tag_equipe=turma['tag_equipe'])
		else:
			print("user com id", user.pbla_uid, "não está integrado")
	return {'msg': 'records added for EVERY file associated with EVERY user'}


# this endpoint receives a empty request and simply updates all the file records for a specific user. same as above, but for the user that is passed as parameter.
@router.post('/api/integ/gdrive/user/update/records')
def add_user_files_records(user_id: int, db_app: Session = Depends(access.get_app_db)):
	user_status = auth.check_integ_status(user_id=user_id, db=db_app)
	file_list = list_files(user_id=user_id, db=db_app)
	if user_status['integrado'] == True and 'user_in_turmas' not in file_list:
		for turma in file_list['user']['turmas']:
			for file in turma['files']:
				# print("                    single user",turma['tag_equipe'])
				add_file_record(
					user_id=user_id, resource_id=file['id'], db_app=db_app, tag_turma=turma['tag_turma'], tag_equipe=turma['tag_equipe'])
		return {'msg': 'records added for EVERY file associated with user'}
	return {"msg": "O usuário não está integrado ao G Drive"}


# this function calls above methods to fetch activity, metadata, binary file and store them in database
# @router.post('/api/integ/gdrive/file/add/record')
def add_file_record(user_id: int, resource_id: str, tag_turma: str, tag_equipe: str, db_app: Session = Depends(access.get_app_db)):
	# print("                          tag_equipe no add file record:",tag_equipe)
	db_record = crud.retrieve_latest_record(
		db=db_app, driveapi_fileid=resource_id)
	latest_file_record = db_record.fetchone()	
	# if there are still no file record for that file...
	# get activity, metadata, binary file, load them in file_schema object and call create_file_record to write everthing to DB
	if latest_file_record == None:
		activity = get_file_activity(
			user_id=user_id, resource_id=resource_id, db_app=db_app)
		metadata = get_file_metadata(
			user_id=user_id, resource_id=resource_id, db_app=db_app)
		download = download_file(
			user_id=user_id, resource_id=resource_id, db_app=db_app)
		file_record = schemas.FileRecords
		file_record.driveapi_fileid = resource_id
		file_record.source_pbla_uid = user_id
		file_record.file_fields = metadata
		file_record.activity_fields = activity
		file_record.tag_turma = tag_turma
		file_record.tag_equipe = tag_equipe
		# print("                             file_record.tag_equipe (latest_file_record == None):",file_record.tag_equipe)
		if download != None:
			file_record.file_revision = download
		create_file_record(db_app=db_app,
						   file_record=file_record,
						   driveapi_fileid=resource_id)
	# if there already are file records for that file...
	else:
		db_latest_activity = latest_file_record[7][0]['timestamp']

		# get activity, metadata, binary file. the use of do_latest_activity argument returns data added only after db_latest_activity timestamp 
		activity = get_file_activity(
			user_id=user_id, resource_id=resource_id, db_app=db_app, db_latest_activity=db_latest_activity)
		if activity == []: # if there is no new activity return a msg stating that there is nothing new to add
			# print("                             tag_equipe (activity == []):",tag_equipe)
			return {'msg': 'nada de novo para adicionar'}
		else: # if there is new activity
			# get activity, metadata, binary file, load them in file_schema object and call create_file_record to write everthing to DB
			metadata = get_file_metadata(
				user_id=user_id, resource_id=resource_id, db_app=db_app)
			download = download_file(
				user_id=user_id, resource_id=resource_id, db_app=db_app)
			file_record = schemas.FileRecords
			file_record.driveapi_fileid = resource_id
			file_record.source_pbla_uid = user_id
			file_record.file_fields = metadata
			file_record.activity_fields = activity
			file_record.tag_turma = tag_turma
			file_record.tag_equipe = tag_equipe
			# print("                             file_record.tag_equipe (else):",file_record.tag_equipe)
			if download != None:
				file_record.file_revision = download
			create_file_record(db_app=db_app,
							   file_record=file_record,
							   driveapi_fileid=resource_id)

	return {'msg': 'activity, metadata and a copy of the file were added to the database'}

# the function that finally calls 'crud.create_file_record' to persist information
def create_file_record(driveapi_fileid: str, file_record: schemas.FileRecords, db_app: Session = Depends(access.get_app_db)):

	# file_fields_json = json.dumps(file_record.file_fields)
	# file_record.file_fields = file_fields_json
	# activity_fields_json = json.dumps(file_record.activity_fields)
	# file_record.activity_fields = activity_fields_json

	# get current time, to be added with the file record in the DB
	now = datetime.now()
	file_record.record_date = now = datetime.now()
	# call crud.create_file_record passing the file_record as parameter
	# print("                  file_record:",file_record.tag_equipe)
	crud.create_file_record(
		db=db_app, driveapi_fileid=driveapi_fileid, file_record=file_record)