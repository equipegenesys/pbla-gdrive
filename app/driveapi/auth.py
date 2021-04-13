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
from driveapi import files

CLIENT_SECRETS_FILE = '/app/driveapi/credentials.json'
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly',
		  'https://www.googleapis.com/auth/drive.activity.readonly',
		  'https://www.googleapis.com/auth/drive.readonly',
		  'https://www.googleapis.com/auth/userinfo.profile']
API_SERVICE_NAME = 'drive'
API_VERSION = 'v3'

router = APIRouter()

# the decorator creates an endpoint to check if our app has a user (user_id) authorization to access his data.
# we call this 'integration status', so we define a 'check_integ_status' function that will be called every time the right HTTP GET arrives.
@router.get('/api/integ/gdrive/status/user/{user_id}') 
def check_integ_status(user_id: int, db: Session = Depends(access.get_app_db)):
	user = schemas.UserBase # creates an object named 'user' of the 'UserBase' schema
	user.pbla_uid = user_id # loads the received 'user_id' value into 'user'
	db_user = crud.get_user(db=db, user=user) # we use 'user' to get information from db about the user
	# if there is a user:
	if db_user:
		if type(db_user) == dict: # when 'crud.get_user' returns an dict, it means it is an error message.
			return db_user # In this case, just return the message. Fast API converts dicts to JSON when returning.
		elif db_user.driveapi_token != None: # if there is already an access token
			creds = db_user.driveapi_token # load it on creds
			service = build('drive', 'v3', credentials=creds) # build api connection as a service
			try: # try to get information about the user
				results = service.about().get(fields="user(emailAddress, displayName)").execute() 
			except RefreshError as re: #if there is an exception, return this error message:
				return {"user_id": user_id, "cadastrado": True, "integrado": False, "info": "O token não pode ser atualizado ou foi revogado"}
			mail = str(results.get('user').get('emailAddress')) # if 'try' works, we get to this point and retrive email address and name from google account 
			name = str(results.get('user').get('displayName'))
			basicUserData = db_user.basicData() #this method returns a dict with this data: pbla_uid, driveapi_name, driveapi_email, is_active
			if basicUserData["driveapi_name"] == name and basicUserData["driveapi_email"] == mail: #we make extra sure that user from google account is the same as user in db
				# if it is true, update db_user status and return info
				db_user.is_active = True
				db.commit
				return {"user_id": user_id, "cadastrado": True, "integrado": db_user.is_active}
				# if it is false, update db_user status and return info
			else:
				db_user.is_active = False
				db.commit
				return {"user_id": user_id, "cadastrado": True, "integrado": db_user.is_active, "info¨": "Há um token de acesso válido, mas o nome e e-mail do usuário do G drive não confere com usuário do PBL Analytics"}
		else: # if there is no access token
			return {"user_id": user_id, "cadastrado": True, "integrado": False, "info": "Não há um token de acesso"}
	# if there is no such user on db, return both 'cadastrado' and 'integrado' as False
	return {"user_id": user_id, "cadastrado": False, "integrado": False}

# creates endpoint to receive request for authorizing our app to access user data
@router.get('/api/integ/gdrive/oauth/user/{user_id}')
def google_oauth(user_id: int, db: Session = Depends(access.get_app_db)):
	integ_status = check_integ_status(db=db, user_id=user_id)
	if integ_status['integrado'] == False:
		# if integration status is False, run google auth flow. It loads the secrets file (credentials.json) and scopes.
		flow = Flow.from_client_secrets_file(
			CLIENT_SECRETS_FILE, scopes=SCOPES)
		# add our callback URL to the flow. This will be used by the Goo API to call back our app.
		flow.redirect_uri = 'https://analytics.pbl.tec.br/api/integ/gdrive/oauthlisten'
		# get the authorization URL and return it. the user needs to be redirected to this URL, so he can authorize ou APP to access his data.
		# state is used to pass the user_id, that is returned when google calls back. this way we make sure the token will be associated with the right user in our DB.
		authorization_url, state = flow.authorization_url(
			prompt='consent', access_type='offline', include_granted_scopes='true', state=user_id)
		print(authorization_url)
		# return RedirectResponse(authorization_url)
		return authorization_url
	else:
		return integ_status

# creates endpoint for receiving google o auth api callbacks
@router.get('/api/integ/gdrive/oauthlisten/', include_in_schema=False)
def oauthlisten(state: str, code: str, scope: str, db: Session = Depends(access.get_app_db)):
	# does all the flow again. wee need this so we can 'fetch_token' with the received 'code'
	flow = Flow.from_client_secrets_file(
		CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
	flow.redirect_uri = 'https://analytics.pbl.tec.br/api/integ/gdrive/oauthlisten'
	flow.fetch_token(code=code)
	creds = flow.credentials # now that 'flow' has a token, it can get the credentials

	# the following code builds the service an get some data from google API
	service = build('drive', 'v3', credentials=creds)
	results = service.about().get(fields="user(emailAddress, displayName)").execute()
	mail = str(results.get('user').get('emailAddress'))
	name = str(results.get('user').get('displayName'))

	# the following code creates a schema object and loads user data in it
	user = schemas.UserCreate
	user.pbla_uid = state
	user.pblacore_token = creds
	user.driveapi_name = name
	user.driveapi_email = mail

	userBase = schemas.UserBase
	userBase.pbla_uid = state

	# if user already exists...
	if crud.get_user(db=db, user=user):
		# update token	
		crud.update_token(db=db, user_to_update=user)
		# call check integ status
		integ_status = check_integ_status(db=db, user_id=user.pbla_uid)
		if integ_status['integrado'] == True:
			# list files (that will update the files table and create individual tables for each file in DB)
			files.list_files(db=db, user_id=user.pbla_uid)
		# calls 'add_gaccount_info', which will add google account id data to appropriate field in DB
		add_gaccount_info(db=db, user_id=state)
		return RedirectResponse('https://analytics.pbl.tec.br/home/estudante')
	# if user does no exist, create new
	else:
		crud.create_user_fromgdrive(db=db, user_to_create=user)
		integ_status = check_integ_status(db=db, user_id=user.pbla_uid)
		if integ_status['integrado'] == True:
			# listar arquivos (o que já atualiza a tabela de arquivos e cria tabelas individuais para cada um)
			files.list_files(db=db, user_id=user.pbla_uid)
		add_gaccount_info(db=db, user_id=state)
		return RedirectResponse('https://analytics.pbl.tec.br/home/estudante')

# function for specifically getting google user account id info and registering in DB
def add_gaccount_info(user_id: int, db: Session = Depends(access.get_app_db)):
	user_schema = schemas.UserBase
	user_schema.pbla_uid = user_id
	
	db_user = crud.get_user(db=db, user=user_schema)
	creds = db_user.driveapi_token
	service = build('people', 'v1', credentials=creds)
	
	gaccount = service.people().get(resourceName='people/me', personFields='metadata').execute()
	user_schema.driveapi_account_id = gaccount['resourceName']
	
	crud.add_gaccount_info(db=db, user_to_update=user_schema)
