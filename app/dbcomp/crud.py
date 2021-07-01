import sqlalchemy
from sqlalchemy.orm import Session
from dbcomp import access, models
from . import models, schemas, access
import pickle, sys

# Receives user id in UserBase, gets DB data for this user, returns it
def get_user(db: Session, user: schemas.UserBase):
	error = {}
	try:
		db_user = db.query(models.User).filter(
			models.User.pbla_uid == user.pbla_uid).first()
		return db_user
	# sometimes token may be corrupted or NULL, this will give an unpickling error, we handle it here
	except pickle.UnpicklingError as e:
		error = {"user_id": user.pbla_uid, "cadastrado": True,
				 "integrado": False, "info¨": "Token corrompido"}
		return error

# if a user integrates before being added to any turma (class), this function should be called to create a user in DB from google data
def create_user_fromgdrive(db: Session, user_to_create: schemas.UserCreate):
	if not db.query(models.User).filter(models.User.driveapi_email == user_to_create.driveapi_email).first():

		db_user = models.User(pbla_uid=user_to_create.pbla_uid,
							  driveapi_token=user_to_create.pblacore_token,
							  driveapi_name=user_to_create.driveapi_name,
							  driveapi_email=user_to_create.driveapi_email)
		db.add(db_user)
		db.commit()
		db.refresh(db_user)
		return {"adicionado": True,"msg": f"A conta do Google Drive de {db_user.driveapi_email} foi integrada ao usuário do PBL Analytics com ID {db_user.pbla_uid}."}
	return {"adicionado": False, "msg": "Já existe um usuário cadastrado com esse e-mail"}

# if a user was added to turma (class) before requesting integration, this function should be called to create a user in DB from pbla-core data
def create_user_fromcore(db: Session, user_to_create: schemas.UserBase):
	if not db.query(models.User).filter(models.User.driveapi_email == user_to_create.pblacore_email).first():

		db_user = models.User(pbla_uid=user_to_create.pbla_uid,
							  pblacore_email=user_to_create.pblacore_email,
							  pblacore_nome=user_to_create.pblacore_nome)
		db.add(db_user)
		db.commit()
		db.refresh(db_user)
		return {"msg": f"A conta do PBL Core com ID {db_user.pbla_uid} foi adicionada ao gateway de integração."}
	return {"msg": "Esse usuário já está cadastrado"}

# crud operation to simply update a user's google credentials in database 
def update_token(db: Session, user_to_update: schemas.UserCreate):
	# in case a token is corrupted, we need to record a NULL on token field in DB, or we will get an error
	# em caso de token corrompido, é preciso gravar um NULL no field, senão o query em seguida falha
	db_connection = access.engine_app_db.connect()
	db_connection.execute(
		f'UPDATE users SET driveapi_token = NULL WHERE pbla_uid = {user_to_update.pbla_uid};')
	db_connection.close()
	db_user = db.query(models.User).filter(
		models.User.pbla_uid == user_to_update.pbla_uid).first()
	db_user.driveapi_token = user_to_update.pblacore_token
	db_user.driveapi_email = user_to_update.driveapi_email
	db_user.driveapi_name = user_to_update.driveapi_name
	db.commit()
	db.refresh(db_user)
	return {"msg": f"A conta do Google Drive de {db_user.driveapi_email} teve seu token atualizado no PBL Analytics com ID {db_user.pbla_uid}."}

# crud operation to simply update a user's google credentials in database 
def update_core_user_data(db: Session, user_to_update: schemas.UserBase):
	if db.query(models.User).filter(models.User.pbla_uid == user_to_update.pbla_uid).first():
		db_user = db.query(models.User).filter(
			models.User.pbla_uid == user_to_update.pbla_uid).first()
		db_user.pblacore_email = user_to_update.pblacore_email
		db_user.pblacore_nome = user_to_update.pblacore_nome
		db.commit()
		db.refresh(db_user)
		return {"msg": f"O usuário do PBL Analytics com ID {db_user.pbla_uid} teve dados de e-mail e nome agregados."}
	return {"msg": "Não existe um usuário cadastrado com esse pbla_uid"}

# crud operation to add the google account id to a user record in DB
def add_gaccount_info(db: Session, user_to_update: schemas.UserBase):
	if db.query(models.User).filter(models.User.pbla_uid == user_to_update.pbla_uid).first():
		db_user = db.query(models.User).filter(
			models.User.pbla_uid == user_to_update.pbla_uid).first()
		db_user.driveapi_account_id = user_to_update.driveapi_account_id
		db.commit()
		db.refresh(db_user)
		return {"msg": f"O usuário do PBL Analytics com ID {db_user.pbla_uid} teve o account id do google agregado."}
	return {"msg": "Não existe um usuário cadastrado com esse pbla_uid"}


def create_file_record(db: Session, driveapi_fileid: str, file_record: schemas.FileRecords):
	# print("                        nome:",file_record.file_fields['name'])
	# print("                        mimetype:",file_record.file_fields['mimeType'])
	# print("                        file_revision TYPE:",type(file_record.file_revision))
	# file_record.file_revision.seek(0)
	# file_record.file_revision = file_record.file_revision.read()

	db_file_record = models.FileRecords(record_date = file_record.record_date,
										source_pbla_uid = file_record.source_pbla_uid,
										tag_turma = file_record.tag_turma,
										tag_equipe = file_record.tag_equipe,
										driveapi_fileid = file_record.driveapi_fileid,
										file_fields = file_record.file_fields,
										activity_fields = file_record.activity_fields,
										file_revision = file_record.file_revision
										)
	db.add(db_file_record)
	db.commit()


# retrieve file record.
def retrieve_latest_record(db: Session, driveapi_fileid: str):
	with access.engine_app_db.connect() as db_connection:
		result = db_connection.execute(
			f'SELECT * FROM files_records WHERE driveapi_fileid = \'{driveapi_fileid}\' ORDER BY sequencial DESC LIMIT 1;')  
		db_connection.close()
		return result