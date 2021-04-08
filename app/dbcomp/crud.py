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
			models.User.pblacore_uid == user.pblacore_uid).first()
		return db_user
	# sometimes token may be corrupted or NULL, this will give an unpickling error, we handle it here
	except pickle.UnpicklingError as e:
		error = {"user_id": user.pblacore_uid, "cadastrado": True,
				 "integrado": False, "info¨": "Token corrompido"}
		return error

# if a user integrates before being added to any turma (class), this function should be called to create a user in DB from google data
def create_user_fromgdrive(db: Session, user_to_create: schemas.UserCreate):
	if not db.query(models.User).filter(models.User.driveapi_email == user_to_create.driveapi_email).first():

		db_user = models.User(pblacore_uid=user_to_create.pblacore_uid,
							  driveapi_token=user_to_create.pblacore_token,
							  driveapi_name=user_to_create.driveapi_name,
							  driveapi_email=user_to_create.driveapi_email)
		db.add(db_user)
		db.commit()
		db.refresh(db_user)
		return {"msg": f"A conta do Google Drive de {db_user.driveapi_email} foi integrada ao usuário do PBL Analytics com ID {db_user.pblacore_uid}."}
	return {"msg": "Já existe um usuário cadastrado com esse e-mail"}

# if a user was added to turma (class) before requesting integration, this function should be called to create a user in DB from pbla-core data
def create_user_fromcore(db: Session, user_to_create: schemas.UserBase):
	if not db.query(models.User).filter(models.User.driveapi_email == user_to_create.pblacore_email).first():

		db_user = models.User(pblacore_uid=user_to_create.pblacore_uid,
							  pblacore_email=user_to_create.pblacore_email,
							  pblacore_nome=user_to_create.pblacore_nome)
		db.add(db_user)
		db.commit()
		db.refresh(db_user)
		return {"msg": f"A conta do PBL Core com ID {db_user.pblacore_uid} foi adicionada ao gateway de integração."}
	return {"msg": "Esse usuário já está cadastrado"}

# crud operation to simply update a user's google credentials in database 
def update_token(db: Session, user_to_update: schemas.UserCreate):
	# in case a token is corrupted, we need to record a NULL on token field in DB, or we will get an error
	# em caso de token corrompido, é preciso gravar um NULL no field, senão o query em seguida falha
	db_connection = access.engine_app_db.connect()
	db_connection.execute(
		f'UPDATE users SET driveapi_token = NULL WHERE pblacore_uid = {user_to_update.pblacore_uid};')
	db_connection.close()
	db_user = db.query(models.User).filter(
		models.User.pblacore_uid == user_to_update.pblacore_uid).first()
	db_user.driveapi_token = user_to_update.pblacore_token
	db_user.driveapi_email = user_to_update.driveapi_email
	db_user.driveapi_name = user_to_update.driveapi_name
	db.commit()
	db.refresh(db_user)
	return {"msg": f"A conta do Google Drive de {db_user.driveapi_email} teve seu token atualizado no PBL Analytics com ID {db_user.pblacore_uid}."}

# crud operation to simply update a user's google credentials in database 
def update_core_user_data(db: Session, user_to_update: schemas.UserBase):
	if db.query(models.User).filter(models.User.pblacore_uid == user_to_update.pblacore_uid).first():
		db_user = db.query(models.User).filter(
			models.User.pblacore_uid == user_to_update.pblacore_uid).first()
		db_user.pblacore_email = user_to_update.pblacore_email
		db_user.pblacore_nome = user_to_update.pblacore_nome
		db.commit()
		db.refresh(db_user)
		return {"msg": f"O usuário do PBL Analytics com ID {db_user.pblacore_uid} teve dados de e-mail e nome agregados."}
	return {"msg": "Não existe um usuário cadastrado com esse pblacore_uid"}

# crud operation to add the google account id to a user record in DB
def add_gaccount_info(db: Session, user_to_update: schemas.UserBase):
	if db.query(models.User).filter(models.User.pblacore_uid == user_to_update.pblacore_uid).first():
		db_user = db.query(models.User).filter(
			models.User.pblacore_uid == user_to_update.pblacore_uid).first()
		db_user.driveapi_account_id = user_to_update.driveapi_account_id
		db.commit()
		db.refresh(db_user)
		return {"msg": f"O usuário do PBL Analytics com ID {db_user.pblacore_uid} teve o account id do google agregado."}
	return {"msg": "Não existe um usuário cadastrado com esse pblacore_uid"}

# get the data for a file
def get_files(db: Session, file: schemas.FileBase):
	return db.query(models.File).filter(models.File.driveapi_fileid == file.driveapi_fileid).first()

# create a file record in DB
def create_file(db: Session, file: schemas.TurmaAddUser, user: schemas.UserBase, turma: schemas.TurmaBase):
	db_file = models.File(driveapi_fileid=file.driveapi_fileid,
						  is_active=file.is_active)
	# files are always associated to users and turmas (classes)
	db_file.users.append(user)
	db_file.turmas.append(turma)

	db.add(db_file)
	db.commit()
	created_db_file = get_files(db=db, file=db_file)
	models.tableCreator(tablename=created_db_file.local_fileid)

# update file status, associated users and turmas (classes)
def update_file(db: Session, file_to_update: str, user: int, turma: str):
	db_user = db.query(models.User).filter(
		models.User.pblacore_uid == user).first()
	db_turma = db.query(models.Turma).filter(
		models.Turma.pblacore_tag_turma == turma).first()
	if db.query(models.File).filter(models.File.driveapi_fileid == file_to_update).first():
		db_file = db.query(models.File).filter(
			models.File.driveapi_fileid == file_to_update).first()
		db_file.is_active = True
		db_file.users.append(db_user)
		db_file.turmas.append(db_turma)
		db.commit()
		db.refresh(db_file)

# create file record. that means adding a row in the file activity table, cotaining activity, metadata and a binary copy of the file
def create_file_record(db: Session, table_name: str, file_record: schemas.FileRecords):
	file_record.file_revision.seek(0)
	read = file_record.file_revision.read()
	db_connection = access.engine_data_db.connect()
	sql = sqlalchemy.text(f"INSERT INTO \"{table_name}\" (source_uid, record_date, file_fields, activity_fields, file_revision) VALUES(:source_uid, :record_date, :file_fields, :activity_fields, :file_revision);").params(
		source_uid = file_record.source_uid,
		record_date = file_record.record_date,
		activity_fields = file_record.activity_fields,
		file_fields = file_record.file_fields,
		file_revision = read
	)
	db_connection.execute(sql)
	db_connection.close()

# retrieve file record.
def retrieve_latest_record(db: Session, table_name: str):
	with access.engine_data_db.connect() as db_connection:
		result = db_connection.execute(
			f'SELECT * FROM \"{table_name}\" ORDER BY sequencial DESC LIMIT 1;')  
		db_connection.close()
		return result

# # Receives turma (class) tag in UserBase, gets DB data for this turma, returns it
# def get_turma(db: Session, turma: schemas.TurmaBase):
# 	return db.query(models.Turma).filter(models.Turma.pblacore_tag_turma == turma).first()

# # creates a new turma (class) in DB and add users to it
# def create_turma(db: Session, turma_to_create: schemas.TurmaAdd):
# 	db_turma = models.Turma(pblacore_tag_turma=turma_to_create.pblacore_tag_turma,
# 							pblacore_disci_turma=turma_to_create.pblacore_disci_turma,
# 							pblacore_ano_turma=turma_to_create.pblacore_ano_turma,
# 							pblacore_semestre_turma=turma_to_create.pblacore_semestre_turma)
# 	db.add(db_turma)
# 	db.commit()

# 	if turma_to_create.users != None:
# 		user_query = schemas.UserBase
# 		for user in turma_to_create.users:
# 			user_query.pblacore_uid = user
# 			db_user = get_user(db=db, user=user_query)
# 			if db_user:
# 				db_turma.users.append(db_user)
# 				db.commit()

# 	db.refresh(db_turma)
# 	return db_turma

# # creates a new turma (class) in DB without adding users
# def create_turma_simples(db: Session, turma_to_create: schemas.TurmaBase):
# 	db_turma = models.Turma(pblacore_tag_turma=turma_to_create.pblacore_tag_turma,
# 							pblacore_disci_turma=turma_to_create.pblacore_disci_turma,
# 							pblacore_ano_turma=turma_to_create.pblacore_ano_turma,
# 							pblacore_semestre_turma=turma_to_create.pblacore_semestre_turma)
# 	db.add(db_turma)
# 	db.commit()

# # add specific users to turma 
# def add_user_turma(db: Session, turma: schemas.TurmaAddUser):
# 	selected_turma = db.query(models.Turma).get(turma.pblacore_tag_turma)
# 	if turma.users is not None:
# 		user_query = schemas.UserBase
# 		for user in turma.users:
# 			user_query.pblacore_uid = user
# 			db_user = get_user(db=db, user=user_query)
# 			if db_user is not None:
# 				selected_turma.users.append(db_user)
# 				db.commit()
# 		estudantes = {'estudantes': []}
# 		for user in selected_turma.users:
# 			userDict = user.basicData()
# 			estudantes['estudantes'].append(userDict)
# 		return {'turma': estudantes}
# 	return {"msg": "Não a há usuários no corpo do HTTP POST"}

# # add specific users to turma (simplified)
# def add_user_turma_simples(db: Session, turma: str, user: str):
# 	selected_turma = db.query(models.Turma).get(turma.pblacore_tag_turma)
# 	db_user = get_user(db=db, user=user)
# 	selected_turma.users.append(db_user)
# 	db.commit()

# # check if user is in turma (this should not be here?)
# def check_user_in_turma(db: Session, turma: str, user: str):
# 	rquery = db.query(models.user_turma_table).join(models.Turma).join(models.User).filter(
# 		models.Turma.pblacore_tag_turma == turma, models.User.pblacore_uid == user).first()
# 	return rquery